import json
import os
import re
import sys
import time
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webui.backend.account_manager import AccountManager


def write_status(
    status_file: str,
    status: str,
    message: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        payload: Dict[str, Any] = {
            "status": status,
            "message": message,
            "timestamp": time.time(),
        }
        if extra:
            payload.update(extra)
        tmp_file = status_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        os.replace(tmp_file, status_file)
    except Exception as e:
        print(f"写入二维码状态失败: {e}", flush=True)


def _query_roles_in_browser(driver: Any) -> Tuple[str, list, bool]:
    """
    通过已登录浏览器上下文调用米哈游角色绑定接口，直接获取当前通行证下的星铁游戏 UID。
    返回 (primary_uid, all_uids, api_ok)。
    """
    if driver is None:
        return "", [], False

    try:
        driver.switch_to.default_content()
        driver.set_script_timeout(8)
        res = driver.execute_async_script(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
                const ctrl = new AbortController();
                const timer = setTimeout(() => ctrl.abort(), 4500);
                try {
                    const resp = await fetch(
                        "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie?game_biz=hkrpg_cn",
                        { credentials: "include", signal: ctrl.signal }
                    );
                    const data = await resp.json();
                    const list = (data && data.data && Array.isArray(data.data.list)) ? data.data.list : [];
                    const uids = [];
                    let primaryUid = "";
                    for (const r of list) {
                        const g = String((r && r.game_uid) || "").trim();
                        if (/^\\d{9}$/.test(g)) {
                            if (!uids.includes(g)) uids.push(g);
                            if (!primaryUid || r.is_chosen) primaryUid = g;
                        }
                    }
                    done({ ok: data && data.retcode === 0, uid: primaryUid, uids: uids });
                } catch (e) {
                    done({ ok: false, uid: "", uids: [] });
                } finally {
                    clearTimeout(timer);
                }
            })();
            """
        )
        if isinstance(res, dict):
            primary_uid = str(res.get("uid") or "").strip()
            all_uids = [str(x).strip() for x in (res.get("uids") or []) if re.fullmatch(r"\d{9}", str(x).strip())]
            return primary_uid, all_uids, bool(res.get("ok"))
    except Exception:
        pass
    return "", [], False


def _extract_browser_identity(cloud_game: Any, account_mgr: AccountManager, account_id: str) -> Tuple[str, str, list, bool]:
    """
    从当前已登录的云游戏浏览器会话（DOM、localStorage、Cookies、角色查询接口及 LevelDB）中提取
    米哈游通行证 ID (mihoyo_aid) 与星穹铁道游戏 UID (game_uid)。
    返回 (aid, primary_uid, all_uids, roles_api_ok)。
    """
    aid = ""
    uid = ""
    all_uids: list = []
    roles_api_ok = False
    driver = getattr(cloud_game, "driver", None)

    for _ in range(8):
        if driver is not None:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

            # 1. 从云游戏欢迎卡片 DOM (div.user-aid.wel-card__aid) 提取通行证 AID
            if not aid:
                try:
                    els = driver.find_elements(By.CSS_SELECTOR, "div.user-aid.wel-card__aid, [class*='wel-card__aid'], .user-aid")
                    for el in els:
                        txt = (el.text or el.get_attribute("textContent") or "").strip()
                        m = re.search(r"([1-9]\d{4,12})", txt)
                        if m:
                            aid = m.group(1)
                            break
                except Exception:
                    pass

            # 2. 从 window.localStorage 提取 accountId / aid / role_id
            if not aid or not uid:
                try:
                    ls_data = driver.execute_script(
                        """
                        const out = { aid: "", uid: "" };
                        try {
                            for (let i = 0; i < window.localStorage.length; i++) {
                                const k = window.localStorage.key(i) || "";
                                const mKey = k.match(/PAYMENT_ABTEST([1-9]\\d{4,12})/);
                                if (mKey && !out.aid) {
                                    out.aid = mKey[1];
                                }
                                const raw = window.localStorage.getItem(k) || "";
                                if (!raw) continue;
                                if (k.includes("clgm-web-app-analysis") || raw.includes("accountId") || raw.includes("app_login_session")) {
                                    const mAcc = raw.match(/"accountId"\\s*:\\s*"([1-9]\\d{4,12})"/g);
                                    if (mAcc && mAcc.length > 0) {
                                        const last = mAcc[mAcc.length - 1].match(/([1-9]\\d{4,12})/);
                                        if (last && !out.aid) out.aid = last[1];
                                    }
                                    const mSess = raw.match(/"app_login_session"\\s*:\\s*"[0-9a-fA-F-]+_([1-9]\\d{4,12})_\\d+"/);
                                    if (mSess && !out.aid) out.aid = mSess[1];
                                }
                                if (k.includes("MIHOYO_H5LOG") || raw.includes("role_id") || raw.includes('"aid"')) {
                                    const mAid = raw.match(/"aid"\\s*:\\s*"([1-9]\\d{4,12})"/g);
                                    if (mAid && mAid.length > 0 && !out.aid) {
                                        const lastAid = mAid[mAid.length - 1].match(/([1-9]\\d{4,12})/);
                                        if (lastAid) out.aid = lastAid[1];
                                    }
                                    const mUid = raw.match(/"role_id"\\s*:\\s*"(\\d{9})"/g);
                                    if (mUid && mUid.length > 0 && !out.uid) {
                                        const lastUid = mUid[mUid.length - 1].match(/(\\d{9})/);
                                        if (lastUid) out.uid = lastUid[1];
                                    }
                                }
                            }
                        } catch (e) {}
                        return out;
                        """
                    )
                    if isinstance(ls_data, dict):
                        if not aid and ls_data.get("aid"):
                            aid = str(ls_data["aid"]).strip()
                        if not uid and ls_data.get("uid"):
                            uid = str(ls_data["uid"]).strip()
                except Exception:
                    pass

            # 3. 从 Cookies 提取 account_id / ltuid
            if not aid:
                try:
                    for ck in driver.get_cookies() or []:
                        ck_name = str(ck.get("name") or "")
                        ck_val = str(ck.get("value") or "").strip()
                        if ck_name in ("account_id", "account_id_v2", "ltuid", "ltuid_v2") and re.fullmatch(r"[1-9]\d{4,12}", ck_val):
                            aid = ck_val
                            break
                except Exception:
                    pass

            # 4. 通过米哈游角色绑定接口查询星铁游戏 UID（刚扫码尚未进入云游戏画面时 localStorage 中还没有 role_id）
            if not uid and not roles_api_ok:
                api_uid, api_uids, roles_api_ok = _query_roles_in_browser(driver)
                if api_uids:
                    all_uids = api_uids
                if api_uid:
                    uid = api_uid

        # 5. 兜底从磁盘 LevelDB 提取
        if not aid or not uid:
            disk_ident = account_mgr.extract_profile_identity(account_id)
            if not aid and disk_ident.get("mihoyo_aid"):
                aid = disk_ident["mihoyo_aid"]
            if not uid and disk_ident.get("game_uid"):
                uid = disk_ident["game_uid"]

        if uid and uid not in all_uids:
            all_uids.append(uid)

        if aid and (uid or roles_api_ok):
            break
        time.sleep(0.5)

    return aid, uid, all_uids, roles_api_ok


def _purge_browser_session(cloud_game: Any, account_mgr: AccountManager, account_id: str) -> None:
    """当检测到扫错账号或重复绑定时，立即清除浏览器及磁盘中的登录状态。"""
    driver = getattr(cloud_game, "driver", None)
    if driver is not None:
        try:
            driver.switch_to.default_content()
            try:
                driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
            except Exception:
                driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        except Exception:
            pass
    try:
        cloud_game.stop_game()
    except Exception:
        pass
    account_mgr.clear_profile_login_data(account_id)


def _validate_and_finalize_login(
    cloud_game: Any,
    profile_dir: str,
    status_file: str,
    account_id: str,
    already_logged_in: bool = False,
) -> bool:
    """
    在扫码登录成功（或检测到已有登录态）时校验账号身份：
    1. 检查是否与系统中其他账号卡片的米哈游通行证 (mihoyo_aid) 或游戏 UID (game_uid) 重复；
    2. 若当前账号卡片名称本身是 9 位 UID，且检测到的实际游戏 UID 与之不一致，则判定为扫错账号；
    3. 校验通过后将 mihoyo_aid / game_uid 写入 accounts.json 与状态文件。
    """
    write_status(status_file, "checking", "登录成功，正在校验米哈游账号身份信息...")
    time.sleep(1.5)

    account_mgr = AccountManager()
    current_acc = account_mgr.get_account(account_id)
    current_name = (current_acc.get("name") or "").strip() if current_acc else ""

    aid, uid, all_uids, roles_api_ok = _extract_browser_identity(cloud_game, account_mgr, account_id)

    # 校验 1：是否存在跨账号卡片重复绑定同一米哈游通行证或游戏 UID
    dup_acc = account_mgr.find_duplicate_account(account_id, mihoyo_aid=aid, game_uid=uid)
    if dup_acc is None and all_uids:
        for candidate_uid in all_uids:
            dup_acc = account_mgr.find_duplicate_account(account_id, game_uid=candidate_uid)
            if dup_acc is not None:
                uid = candidate_uid
                break

    if dup_acc is not None:
        dup_name = dup_acc.get("name") or dup_acc.get("id")
        ident_desc = f"通行证 AID: {aid}" if aid else ""
        if uid:
            ident_desc = f"{ident_desc}, 游戏 UID: {uid}" if ident_desc else f"游戏 UID: {uid}"
        _purge_browser_session(cloud_game, account_mgr, account_id)
        write_status(
            status_file,
            "failed",
            f"扫码绑定被拦截：当前登录的米哈游账号（{ident_desc or '同一通行证'}）已绑定在账号「{dup_name}」中，请勿重复扫码绑定同一账号！请在手机米游社切换正确账号后重试。",
            extra={"mihoyo_aid": aid, "game_uid": uid, "conflict_account": dup_name, "purged": True},
        )
        return False

    # 校验 2：若当前卡片名称为 9 位星铁 UID（如 100887296），且实际游戏 UID 与卡片名称不一致（或该通行证无星铁角色）
    m_card_uid = re.search(r"\b(\d{9})\b", current_name)
    if m_card_uid:
        expected_uid = m_card_uid.group(1)
        if expected_uid in all_uids:
            uid = expected_uid
        elif (uid and uid != expected_uid) or (roles_api_ok and not all_uids):
            actual_desc = f"实际游戏 UID 为 {uid}" if uid else "该通行证下无任何星穹铁道角色"
            _purge_browser_session(cloud_game, account_mgr, account_id)
            write_status(
                status_file,
                "failed",
                f"扫码绑定被拦截：当前账号卡片要求游戏 UID 为 {expected_uid}，但扫码登录的{actual_desc}（通行证 AID: {aid or '未知'}），请切换手机米游社账号后重新扫码！",
                extra={"mihoyo_aid": aid, "game_uid": uid, "purged": True},
            )
            return False

    # 校验通过：持久化到 accounts.json
    update_kwargs: Dict[str, Any] = {"is_logged_in": True}
    if aid:
        update_kwargs["mihoyo_aid"] = aid
    if uid:
        update_kwargs["game_uid"] = uid
    account_mgr.update_account(account_id, **update_kwargs)

    ident_parts = []
    if aid:
        ident_parts.append(f"通行证 AID: {aid}")
    if uid:
        ident_parts.append(f"游戏 UID: {uid}")
    ident_suffix = f"（{' / '.join(ident_parts)}）" if ident_parts else ""

    if already_logged_in:
        msg = f"检测到该账号已处于登录状态{ident_suffix}！"
    else:
        msg = f"登录成功{ident_suffix}！正在保存登录凭证..."

    write_status(
        status_file,
        "success",
        msg,
        extra={
            "mihoyo_aid": aid,
            "game_uid": uid,
            "already_logged_in": bool(already_logged_in),
        },
    )
    time.sleep(2)
    return True


def run_qr_login(
    profile_dir: str,
    status_file: str,
    qr_image_path: str,
    account_id: Optional[str] = None,
) -> None:
    os.environ["MARCH7TH_USER_PROFILE_DIR"] = profile_dir
    os.environ["MARCH7TH_BROWSER_HEADLESS_ENABLE"] = "true"
    os.environ["MARCH7TH_CLOUD_GAME_ENABLE"] = "true"

    resolved_account_id = (account_id or os.path.basename(os.path.normpath(profile_dir))).strip()
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
            _validate_and_finalize_login(
                cloud_game,
                profile_dir,
                status_file,
                resolved_account_id,
                already_logged_in=True,
            )
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
                    _validate_and_finalize_login(
                        cloud_game,
                        profile_dir,
                        status_file,
                        resolved_account_id,
                        already_logged_in=False,
                    )
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
                        _validate_and_finalize_login(
                            cloud_game,
                            profile_dir,
                            status_file,
                            resolved_account_id,
                            already_logged_in=False,
                        )
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
        print("Usage: python qr_login_runner.py <profile_dir> <status_file> <qr_image_path> [account_id]")
        sys.exit(1)
    arg_account_id = sys.argv[4] if len(sys.argv) >= 5 else None
    run_qr_login(sys.argv[1], sys.argv[2], sys.argv[3], arg_account_id)
