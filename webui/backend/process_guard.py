import json
import os
import signal
import subprocess
import sys
import threading
import time
from typing import List, Optional
import psutil

M7A_BROWSER_TAG = "--march-7th-assistant-sr-cloud-game"
ACTIVE_LOCK_FILE = os.path.abspath("logs/runs/active.json")


def reap_zombie_children() -> int:
    """在 POSIX 系统上回收所有已被重挂载到当前进程的僵尸子进程 (<defunct>)。"""
    if sys.platform == "win32" or not hasattr(os, "waitpid"):
        return 0
    reaped = 0
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid <= 0:
                break
            reaped += 1
        except ChildProcessError:
            break
        except OSError:
            break
    return reaped


def terminate_process_tree(proc: Optional[subprocess.Popen], timeout: float = 6.0) -> None:
    """优雅终止子进程及其整棵进程树，超时后强制杀死并回收僵尸进程。"""
    if proc is None:
        return

    targets: List[psutil.Process] = []
    try:
        parent = psutil.Process(proc.pid)
        children = parent.children(recursive=True)
        targets = children + [parent]
    except psutil.Error:
        pass

    # 1. 发送 SIGTERM / terminate
    if sys.platform != "win32":
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass

    for p in targets:
        try:
            if p.status() != psutil.STATUS_ZOMBIE:
                p.terminate()
        except psutil.Error:
            pass

    if targets:
        _, alive = psutil.wait_procs(targets, timeout=timeout)
        if alive:
            if sys.platform != "win32":
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    pass
            for p in alive:
                try:
                    p.kill()
                except psutil.Error:
                    pass
            psutil.wait_procs(alive, timeout=2.0)

    try:
        proc.wait(timeout=1.0)
    except Exception:
        pass

    reap_zombie_children()


def cleanup_residual_m7a_processes(profile_dir: Optional[str] = None) -> int:
    """
    清理残留的浏览器、chromedriver、crashpad 与 OCR 进程。
    profile_dir 为 None 时清理全部由小助手启动的残留进程（适合账号切换间隙）；
    指定 profile_dir 时仅清理对应 Profile 的浏览器进程。
    """
    reap_zombie_children()
    to_terminate: List[psutil.Process] = []
    norm_profile = os.path.normcase(os.path.abspath(profile_dir)) if profile_dir else None

    browser_names = {
        "chrome",
        "chrome.exe",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "msedge",
        "msedge.exe",
    }
    helper_names = {
        "chromedriver",
        "chromedriver.exe",
        "msedgedriver",
        "msedgedriver.exe",
        "chrome_crashpad_handler",
        "chrome_crashpad",
        "chrome_crashpad_handler.exe",
        "paddleocr-json",
        "paddleocr-json.exe",
    }

    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            if proc.info.get("status") == psutil.STATUS_ZOMBIE:
                continue
            name = (proc.info.get("name") or "").lower()
            cmdline = proc.cmdline()
        except psutil.Error:
            continue

        if name in browser_names and M7A_BROWSER_TAG in cmdline:
            if norm_profile:
                matched = any(
                    arg.startswith("--user-data-dir=")
                    and os.path.normcase(os.path.abspath(arg.split("=", 1)[1])) == norm_profile
                    for arg in cmdline
                )
                if not matched:
                    continue
            to_terminate.append(proc)
        elif not norm_profile and name in helper_names:
            to_terminate.append(proc)

    if not to_terminate:
        reap_zombie_children()
        return 0

    for p in to_terminate:
        try:
            p.terminate()
        except psutil.Error:
            pass

    _, alive = psutil.wait_procs(to_terminate, timeout=4.0)
    for p in alive:
        try:
            p.kill()
        except psutil.Error:
            pass
    if alive:
        psutil.wait_procs(alive, timeout=2.0)

    reap_zombie_children()
    return len(to_terminate)


def clear_stale_active_run_lock(force: bool = False) -> bool:
    """
    检查并清理 logs/runs/active.json 运行锁。
    当上一账号异常中断或被杀死后，若锁文件残留会导致下一账号报 EXIT_BUSY (退出码 4)。
    """
    if not os.path.exists(ACTIVE_LOCK_FILE):
        return False

    if not force:
        try:
            with open(ACTIVE_LOCK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            pid = data.get("pid")
            if isinstance(pid, int) and pid > 0 and psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                if proc.status() != psutil.STATUS_ZOMBIE:
                    return False
        except Exception:
            pass

    try:
        os.remove(ACTIVE_LOCK_FILE)
        return True
    except OSError:
        return False


def start_background_zombie_reaper(interval_sec: float = 10.0) -> None:
    """启动后台守护线程定期回收孤儿僵尸进程。"""
    if sys.platform == "win32":
        return

    def _loop():
        while True:
            try:
                reap_zombie_children()
            except Exception:
                pass
            time.sleep(interval_sec)

    t = threading.Thread(target=_loop, name="m7a-zombie-reaper", daemon=True)
    t.start()
