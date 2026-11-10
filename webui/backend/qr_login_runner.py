import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def write_status(status_file: str, status: str, message: str = "") -> None:
    try:
        tmp_file = status_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(
                {"status": status, "message": message, "timestamp": time.time()},
                f,
                ensure_ascii=False,
            )
        os.replace(tmp_file, status_file)
    except Exception as e:
        print(f"写入二维码状态失败: {e}", flush=True)


def run_qr_login(profile_dir: str, status_file: str, qr_image_path: str) -> None:
    os.environ["MARCH7TH_USER_PROFILE_DIR"] = profile_dir
    os.environ["MARCH7TH_BROWSER_HEADLESS_ENABLE"] = "true"
    os.environ["MARCH7TH_CLOUD_GAME_ENABLE"] = "true"

    cancel_file = status_file + ".cancel"

    def is_cancelled() -> bool:
        return os.path.exists(cancel_file)

    write_status(status_file, "starting", "正在启动无头浏览器并加载云游戏页面...")

    from module.game import cloud_game

    try:
        if is_cancelled():
            return

        if not cloud_game.start_game_process(headless=True):
            if not is_cancelled():
                write_status(status_file, "failed", "无法启动云游戏浏览器进程，请重试。")
            return

        if is_cancelled():
            return

        write_status(status_file, "checking", "正在检查账号登录状态...")
        if cloud_game._check_login():
            write_status(status_file, "success", "检测到该账号处于已登录状态！")
            time.sleep(2)
            return

        if is_cancelled():
            return

        write_status(status_file, "fetching_qr", "未登录，正在获取米游社登录二维码...")
        cloud_game._switch_to_login_iframe()
        cloud_game._click_qr_login_button()
        qr_img = cloud_game._wait_and_get_qr_img()

        if os.path.exists(qr_image_path):
            try:
                os.remove(qr_image_path)
            except OSError:
                pass

        cloud_game._save_qr_from_src(qr_img, qr_image_path)
        write_status(
            status_file,
            "waiting_scan",
            "请使用米游社 App 扫描二维码（若二维码过期将自动刷新）",
        )

        start_wait = time.monotonic()
        timeout_sec = 300  # 5 分钟超时

        while time.monotonic() - start_wait < timeout_sec:
            if is_cancelled():
                return

            # 1. 检测是否已直接进入登录成功态
            try:
                cloud_game.driver.switch_to.default_content()
                if cloud_game._check_login(timeout=1):
                    write_status(status_file, "success", "登录成功！正在保存登录凭证...")
                    time.sleep(3)
                    return
                cloud_game._switch_to_login_iframe()
            except Exception:
                pass

            # 2. 检测扫码成功提示
            if cloud_game.driver.find_elements(By.XPATH, "//*[contains(text(), '扫码成功')]"):
                write_status(status_file, "scanned", "扫码成功！请在手机米游社上点击「确认登录」...")
                cloud_game.driver.switch_to.default_content()
                confirm_start = time.monotonic()
                while time.monotonic() - confirm_start < 60:
                    if is_cancelled():
                        return
                    if cloud_game._check_login(timeout=2):
                        write_status(status_file, "success", "登录成功！正在保存登录凭证...")
                        time.sleep(3)
                        return
                    time.sleep(1)
                if not is_cancelled():
                    write_status(status_file, "failed", "等待手机端点击确认登录超时。")
                return

            # 3. 检测二维码过期并自动刷新
            expired_els = cloud_game.driver.find_elements(By.CSS_SELECTOR, "div.qr-expired")
            if expired_els and expired_els[0].is_displayed():
                write_status(status_file, "refreshing", "二维码已过期，正在自动刷新...")
                try:
                    qr_wrap = cloud_game.driver.find_element(By.CSS_SELECTOR, "div.qr-wrap")
                    qr_wrap.click()
                    time.sleep(1)
                    WebDriverWait(cloud_game.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img.qr-loaded"))
                    )
                    qr_img = cloud_game.driver.find_element(By.CSS_SELECTOR, "img.qr-loaded")
                    cloud_game._save_qr_from_src(qr_img, qr_image_path)
                    write_status(status_file, "waiting_scan", "二维码已刷新，请使用米游社重新扫描")
                except Exception as e:
                    if not is_cancelled():
                        write_status(status_file, "failed", f"刷新二维码失败: {e}")
                    return

            time.sleep(2)

        if not is_cancelled():
            write_status(status_file, "failed", "二维码等待扫描超时（5 分钟）。")
    except Exception as e:
        if not is_cancelled():
            write_status(status_file, "failed", f"扫码登录过程发生异常: {e}")
    finally:
        try:
            cloud_game.stop_game()
        except Exception:
            pass
        if os.path.exists(qr_image_path):
            try:
                os.remove(qr_image_path)
            except OSError:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python qr_login_runner.py <profile_dir> <status_file> <qr_image_path>")
        sys.exit(1)
    run_qr_login(sys.argv[1], sys.argv[2], sys.argv[3])
