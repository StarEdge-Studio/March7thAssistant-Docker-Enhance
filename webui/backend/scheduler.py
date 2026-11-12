import datetime
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional

from webui.backend.account_manager import DATA_DIR, account_manager
from webui.backend.process_guard import (
    cleanup_residual_m7a_processes,
    clear_stale_active_run_lock,
    reap_zombie_children,
    terminate_process_tree,
)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
HISTORY_FILE = os.path.join(DATA_DIR, "run_history.json")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class Scheduler:
    def __init__(self):
        self._lock = threading.RLock()
        os.makedirs(LOGS_DIR, exist_ok=True)
        self.settings: Dict[str, Any] = self._load_settings()
        self.history: List[Dict[str, Any]] = self._load_history()
        self.is_running: bool = False
        self.current_account_id: Optional[str] = None
        self.current_account_name: Optional[str] = None
        self.current_run_id: Optional[str] = None
        self.current_log_file: Optional[str] = None
        self.current_process: Optional[subprocess.Popen] = None
        self.stop_requested: bool = False
        self.internet_retry_info: Optional[Dict[str, Any]] = None
        self._last_scheduled_date: Optional[str] = None

        self._timer_thread = threading.Thread(
            target=self._schedule_loop, name="m7a-scheduler", daemon=True
        )
        self._timer_thread.start()

    def _load_settings(self) -> Dict[str, Any]:
        default_settings = {
            "daily_run_enabled": False,
            "daily_run_time": "04:00",
            "check_internet": False,
            "check_internet_Wait": 60,
            "check_internet_MaxRetries": 3,
            "allow_user_manual_run": True,
            "debug_mode": False,
            "global_log_level": "follow",  # "follow" (跟随账号配置) | "info" (仅INFO) | "debug" (详细)
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    default_settings.update(data)
            except Exception:
                pass
        else:
            self._save_settings_unlocked(default_settings)
        return default_settings

    def _save_settings_unlocked(self, data: Dict[str, Any]) -> None:
        tmp_file = SETTINGS_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, SETTINGS_FILE)

    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        allowed_keys = {
            "daily_run_enabled",
            "daily_run_time",
            "check_internet",
            "check_internet_Wait",
            "check_internet_MaxRetries",
            "allow_user_manual_run",
            "debug_mode",
            "global_log_level",
        }
        with self._lock:
            for k, v in new_settings.items():
                if k in allowed_keys and v is not None:
                    self.settings[k] = v
            self._save_settings_unlocked(self.settings)
            return dict(self.settings)

    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data[:100]
            except Exception:
                pass
        return []

    def _save_history_unlocked(self) -> None:
        self.history = self.history[:100]
        tmp_file = HISTORY_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, HISTORY_FILE)

    def get_history_for_context(self, role: str, account_ids: List[str]) -> List[Dict[str, Any]]:
        with self._lock:
            if role == "admin":
                return list(self.history)
            allowed = set(account_ids)
            return [h for h in self.history if h.get("account_id") in allowed]

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "is_running": self.is_running,
                "current_account_id": self.current_account_id,
                "current_account_name": self.current_account_name,
                "current_run_id": self.current_run_id,
                "current_log_file": self.current_log_file,
                "stop_requested": self.stop_requested,
                "internet_retry_info": self.internet_retry_info,
                "settings": dict(self.settings),
            }

    def start_run(
        self,
        account_id: Optional[str] = None,
        allowed_account_ids: Optional[List[str]] = None,
    ) -> tuple[bool, str]:
        with self._lock:
            if self.is_running:
                return False, "当前已有任务正在运行中，请等待完成或先点击停止"
            self.is_running = True
            self.stop_requested = False

        t = threading.Thread(
            target=self._execute_queue,
            args=(account_id, allowed_account_ids),
            name="m7a-runner",
            daemon=True,
        )
        t.start()
        return True, "任务队列已启动"

    def stop_run(self) -> tuple[bool, str]:
        with self._lock:
            if not self.is_running:
                return False, "当前没有正在运行的任务"
            self.stop_requested = True
            proc = self.current_process

        if proc is not None:
            terminate_process_tree(proc, timeout=5.0)
        cleanup_residual_m7a_processes()
        clear_stale_active_run_lock(force=True)
        return True, "已发送停止指令并清理运行进程"

    def _check_internet_connectivity(self) -> bool:
        for url in ("https://www.mihoyo.com", "https://www.baidu.com", "https://www.qq.com"):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                continue
        return False

    def _execute_queue(
        self,
        target_account_id: Optional[str] = None,
        allowed_account_ids: Optional[List[str]] = None,
    ) -> None:
        try:
            accounts = account_manager.get_accounts()
            if target_account_id:
                queue = [a for a in accounts if a["id"] == target_account_id]
            elif allowed_account_ids is not None:
                allowed_set = set(allowed_account_ids)
                queue = [a for a in accounts if a["id"] in allowed_set and a.get("enabled", True)]
            else:
                queue = [a for a in accounts if a.get("enabled", True)]

            if not queue:
                return

            # 可选：外网连通性检测
            if self.settings.get("check_internet", False):
                wait_sec = max(5, int(self.settings.get("check_internet_Wait", 60)))
                max_retries = max(1, int(self.settings.get("check_internet_MaxRetries", 3)))
                connected = False
                for attempt in range(max_retries + 1):
                    if self.stop_requested:
                        return
                    if self._check_internet_connectivity():
                        connected = True
                        break
                    if attempt < max_retries:
                        self.internet_retry_info = {
                            "retry": attempt + 1,
                            "max_retries": max_retries,
                            "wait": wait_sec,
                        }
                        for _ in range(wait_sec):
                            if self.stop_requested:
                                self.internet_retry_info = None
                                return
                            time.sleep(1)
                self.internet_retry_info = None
                if not connected:
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    run_id = f"net_fail_{int(time.time())}"
                    log_file = f"{run_id}.log"
                    log_path = os.path.join(LOGS_DIR, log_file)
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(
                            f"[{now_str}] ERROR 网络连通性检查失败（已重试 {max_retries} 次），放弃本轮任务执行。\n"
                        )
                    with self._lock:
                        self.history.insert(
                            0,
                            {
                                "run_id": run_id,
                                "account_id": "system",
                                "account_name": "网络检查",
                                "start_time": now_str,
                                "end_time": now_str,
                                "status": "error",
                                "log_file": log_file,
                            },
                        )
                        self._save_history_unlocked()
                    return

            for acc in queue:
                if self.stop_requested:
                    break
                self._run_single_account(acc)
        finally:
            cleanup_residual_m7a_processes()
            clear_stale_active_run_lock(force=True)
            reap_zombie_children()
            with self._lock:
                self.is_running = False
                self.current_account_id = None
                self.current_account_name = None
                self.current_run_id = None
                self.current_process = None
                self.internet_retry_info = None

    def _run_single_account(self, account: Dict[str, Any]) -> None:
        acc_id = account["id"]
        acc_name = account.get("name", acc_id)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"{ts}_{acc_id}"
        log_file = f"{run_id}.log"
        log_path = os.path.join(LOGS_DIR, log_file)

        start_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "run_id": run_id,
            "account_id": acc_id,
            "account_name": acc_name,
            "start_time": start_time_str,
            "end_time": None,
            "status": "running",
            "log_file": log_file,
        }

        with self._lock:
            self.current_account_id = acc_id
            self.current_account_name = acc_name
            self.current_run_id = run_id
            self.current_log_file = log_file
            self.history.insert(0, record)
            self._save_history_unlocked()

        account_manager.update_account(acc_id, last_run_at=start_time_str, last_run_status="running")

        # 账号启动前强制清理任何上一账号遗留的进程与运行锁，彻底杜绝级联失败
        cleanup_residual_m7a_processes()
        clear_stale_active_run_lock(force=True)

        runtime_cfg_path, before_snapshot = account_manager.prepare_runtime_config(acc_id)
        profile_dir = account_manager.get_profile_dir(acc_id)

        env = os.environ.copy()
        env["MARCH7TH_WEBUI_STARTED"] = "true"
        env["MARCH7TH_CONFIG_PATH"] = runtime_cfg_path
        env["MARCH7TH_USER_PROFILE_DIR"] = profile_dir
        env["MARCH7TH_CLOUD_GAME_ENABLE"] = "true"
        env["MARCH7TH_BROWSER_PERSISTENT_ENABLE"] = "true"
        env["MARCH7TH_BROWSER_HEADLESS_ENABLE"] = "true"
        env["MARCH7TH_BROWSER_HEADLESS_RESTART_ON_NOT_LOGGED_IN"] = "false"
        env["MARCH7TH_AFTER_FINISH"] = "Exit"
        env["MARCH7TH_NON_INTERACTIVE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        # 全局日志设置覆盖处理：follow (跟随账号配置) | info (仅INFO) | debug (详细)
        global_log_level = str(self.settings.get("global_log_level", "follow")).lower()
        if global_log_level == "info":
            env["MARCH7TH_LOG_LEVEL"] = "INFO"
        elif global_log_level in ("debug", "verbose"):
            env["MARCH7TH_LOG_LEVEL"] = "DEBUG"
        else:
            env.pop("MARCH7TH_LOG_LEVEL", None)

        debug_mode = bool(self.settings.get("debug_mode", False))
        final_status = "error"

        try:
            with open(log_path, "w", encoding="utf-8") as lf:
                lf.write(f"========== 开始执行账号: {acc_name} ({acc_id}) ==========\n")
                lf.write(f"启动时间: {start_time_str}\n")
                lf.write(f"配置路径: {runtime_cfg_path}\n")
                lf.write(f"数据目录: {profile_dir}\n")
                lf.write("========================================================\n\n")
                lf.flush()

                if debug_mode:
                    self._run_debug_mock(lf, acc_name)
                    final_status = "stopped" if self.stop_requested else "success"
                else:
                    popen_kwargs: Dict[str, Any] = {
                        "stdout": subprocess.PIPE,
                        "stderr": subprocess.STDOUT,
                        "env": env,
                        "text": True,
                        "encoding": "utf-8",
                        "errors": "replace",
                        "bufsize": 1,
                    }
                    if sys.platform != "win32":
                        popen_kwargs["start_new_session"] = True
                    else:
                        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

                    self.current_process = subprocess.Popen(
                        [sys.executable, "-u", "main.py"],
                        **popen_kwargs,
                    )

                    has_fatal_error = False
                    if self.current_process.stdout:
                        for raw_line in iter(self.current_process.stdout.readline, ""):
                            clean_line = ANSI_ESCAPE_RE.sub("", raw_line)
                            lf.write(clean_line)
                            lf.flush()
                            if (
                                "等待云游戏登录超时" in clean_line
                                or "未登录" in clean_line and "超时" in clean_line
                            ):
                                has_fatal_error = True

                    self.current_process.wait()
                    rc = self.current_process.returncode

                    if self.stop_requested:
                        final_status = "stopped"
                        lf.write("\n[WebUI] 任务已被手动终止。\n")
                    elif rc == 0 and not has_fatal_error:
                        final_status = "success"
                        lf.write(f"\n========== 账号 {acc_name} 执行完成 (退出码: 0) ==========\n")
                    else:
                        final_status = "error"
                        lf.write(
                            f"\n========== 账号 {acc_name} 执行失败 (退出码: {rc}) ==========\n"
                        )
        except Exception as e:
            final_status = "error"
            try:
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(f"\n[WebUI 调度器异常] {type(e).__name__}: {e}\n")
            except Exception:
                pass
        finally:
            if self.current_process is not None:
                terminate_process_tree(self.current_process, timeout=5.0)
                self.current_process = None

            cleanup_residual_m7a_processes()
            clear_stale_active_run_lock(force=True)
            reap_zombie_children()

            # 同步运行期产生的时间戳、体力计划、已兑换码等状态回账号独立配置
            try:
                account_manager.sync_runtime_state_back(acc_id, before_snapshot, runtime_cfg_path)
            except Exception:
                pass

            if os.path.exists(runtime_cfg_path):
                try:
                    os.remove(runtime_cfg_path)
                except OSError:
                    pass

            end_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record["end_time"] = end_time_str
            record["status"] = final_status
            with self._lock:
                self._save_history_unlocked()

            is_logged = account_manager.check_profile_logged_in(acc_id)
            account_manager.update_account(
                acc_id,
                last_run_at=end_time_str,
                last_run_status=final_status,
                is_logged_in=is_logged,
            )
            time.sleep(2)

    def _run_debug_mock(self, lf, acc_name: str) -> None:
        steps = [
            f"2026-11-11 04:00:01 | INFO | [调试模式] 正在加载账号「{acc_name}」的独立配置...",
            "2026-11-11 04:00:02 | INFO | ──────────────────── 阶段：启动云·星穹铁道 ────────────────────",
            "2026-11-11 04:00:03 | INFO | 正在启动 chrome 浏览器 (Headless)...",
            "2026-11-11 04:00:04 | INFO | 检测到登录成功，云游戏剩余时长：180 分钟",
            "2026-11-11 04:00:05 | INFO | ──────────────────── 阶段：清开拓力 ────────────────────",
            "2026-11-11 04:00:06 | INFO | 当前开拓力: 240/300，开始挑战拟造花萼（赤）...",
            "2026-11-11 04:00:07 | INFO | ──────────────────── 阶段：每日实训与奖励领取 ────────────────────",
            "2026-11-11 04:00:08 | INFO | 每日实训活跃度已满 500，成功领取星琼奖励！",
            "2026-11-11 04:00:09 | INFO | 关闭浏览器成功",
        ]
        for line in steps:
            if self.stop_requested:
                break
            lf.write(line + "\n")
            lf.flush()
            time.sleep(1)

    def _schedule_loop(self) -> None:
        while True:
            try:
                if self.settings.get("daily_run_enabled", False) and not self.is_running:
                    now = datetime.datetime.now()
                    target_time = str(self.settings.get("daily_run_time", "04:00")).strip()
                    current_hm = now.strftime("%H:%M")
                    today_str = now.strftime("%Y-%m-%d")
                    if current_hm == target_time and self._last_scheduled_date != today_str:
                        self._last_scheduled_date = today_str
                        self.start_run()
            except Exception:
                pass
            time.sleep(15)

    def read_log_chunk(
        self,
        log_file: str,
        offset: int = 0,
        max_bytes: int = 131072,
    ) -> Dict[str, Any]:
        """
        增量或尾部读取日志文件，大幅降低浏览器端轮询日志时的带宽与内存消耗。
        offset < 0 或首次未传时，若文件超过 max_bytes 则自动从尾部截取。
        """
        safe_name = os.path.basename(log_file)
        log_path = os.path.join(LOGS_DIR, safe_name)
        if not os.path.exists(log_path):
            return {
                "log_file": safe_name,
                "content": "",
                "offset": 0,
                "next_offset": 0,
                "total_size": 0,
                "truncated": False,
            }

        total_size = os.path.getsize(log_path)
        truncated = False
        read_start = max(0, offset)

        if offset < 0 or (offset == 0 and total_size > max_bytes):
            read_start = max(0, total_size - max_bytes)
            truncated = read_start > 0

        if read_start >= total_size:
            return {
                "log_file": safe_name,
                "content": "",
                "offset": read_start,
                "next_offset": total_size,
                "total_size": total_size,
                "truncated": False,
            }

        with open(log_path, "rb") as f:
            f.seek(read_start)
            raw_bytes = f.read(max_bytes)
            next_offset = f.tell()

        # 若从文件中间截断，丢弃首行可能被截半的 UTF-8 字符
        if truncated and b"\n" in raw_bytes:
            first_nl = raw_bytes.find(b"\n")
            raw_bytes = raw_bytes[first_nl + 1 :]

        content = raw_bytes.decode("utf-8", errors="replace")
        return {
            "log_file": safe_name,
            "content": content,
            "offset": read_start,
            "next_offset": next_offset,
            "total_size": total_size,
            "truncated": truncated,
        }


scheduler = Scheduler()
