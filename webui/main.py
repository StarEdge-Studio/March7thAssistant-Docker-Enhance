import json
import os
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional

# 兼容 uv run 依据上游 uv.lock 将 typing_extensions 锁定在 4.15.0 时新版 anyio 导入 sentinel 报错的问题
try:
    import typing_extensions
    if not hasattr(typing_extensions, "sentinel") and hasattr(typing_extensions, "Sentinel"):
        typing_extensions.sentinel = typing_extensions.Sentinel
except Exception:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from webui.backend.account_manager import DATA_DIR, account_manager
from webui.backend.auth import (
    AuthContext,
    build_oidc_authorize_url,
    ensure_account_access,
    exchange_oidc_code,
    get_auth_mode,
    get_current_session,
    get_oidc_settings,
    login_with_token,
    require_admin,
    require_authorized,
)
from webui.backend.process_guard import (
    cleanup_residual_m7a_processes,
    reap_zombie_children,
    start_background_zombie_reaper,
    terminate_process_tree,
)
from webui.backend.scheduler import LOGS_DIR, scheduler

app = FastAPI(title="March7thAssistant Docker Enhance WebUI")
app.add_middleware(GZipMiddleware, minimum_size=500)

# 启动后台孤儿/僵尸进程回收守护线程
start_background_zombie_reaper(interval_sec=10.0)


# ==================== 请求模型 ====================

class TokenLoginRequest(BaseModel):
    token: str


class OIDCCallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: Optional[str] = None


class AccountCreateRequest(BaseModel):
    name: str
    username: Optional[str] = ""


class AccountUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    enabled: Optional[bool] = None
    order: Optional[int] = None


class AccountReorderRequest(BaseModel):
    account_ids: List[str]


class RunStartRequest(BaseModel):
    account_id: Optional[str] = None


class RawYamlUpdateRequest(BaseModel):
    raw_yaml: str


# ==================== 认证与前端主题接口 ====================

def get_ui_theme() -> str:
    """
    通过环境变量切换前端设计语言:
    支持 WEBUI_THEME / WEBUI_FRONTEND / WEBUI_UI:
      - 'm3e' (默认): Material 3 Expressive 设计语言前端
      - 'simple': 经典轻量简洁版前端
    """
    raw = (
        os.environ.get("WEBUI_THEME")
        or os.environ.get("WEBUI_FRONTEND")
        or os.environ.get("WEBUI_UI")
        or "m3e"
    ).strip().lower()
    if raw in ("simple", "classic", "legacy"):
        return "simple"
    return "m3e"


@app.get("/api/auth/config")
def api_auth_config():
    oidc = get_oidc_settings()
    return {
        "mode": "oidc" if oidc["enabled"] else "token",
        "brand": oidc["brand"] if oidc["enabled"] else "",
        "ui_theme": get_ui_theme(),
    }


@app.get("/api/auth/oidc/authorize")
def api_oidc_authorize(redirect_uri: str = Query(...)):
    return build_oidc_authorize_url(redirect_uri)


@app.post("/api/auth/oidc/callback")
def api_oidc_callback(req: OIDCCallbackRequest):
    return exchange_oidc_code(req.code, req.state, req.redirect_uri)


@app.post("/api/auth/token")
def api_token_login(req: TokenLoginRequest):
    return login_with_token(req.token)


@app.get("/api/auth/me")
def api_auth_me(ctx: AuthContext = Depends(get_current_session)):
    oidc = get_oidc_settings()
    return {
        "mode": ctx.mode,
        "brand": oidc["brand"] if ctx.mode == "oidc" else "",
        "role": ctx.role,
        "username": ctx.username,
        "display_name": ctx.display_name,
        "avatar": ctx.avatar,
        "account_ids": ctx.account_ids,
        "account_id": ctx.primary_account_id,
    }


# ==================== 状态与全局调度设置 ====================

@app.get("/api/status")
def api_get_status(ctx: AuthContext = Depends(require_authorized)):
    all_accounts = account_manager.get_accounts()
    if ctx.role == "admin":
        visible_accounts = all_accounts
    else:
        allowed = set(ctx.account_ids)
        visible_accounts = [a for a in all_accounts if a["id"] in allowed]

    oidc = get_oidc_settings()
    return {
        "ui_theme": get_ui_theme(),
        "auth": {
            "mode": ctx.mode,
            "brand": oidc["brand"] if ctx.mode == "oidc" else "",
            "role": ctx.role,
            "username": ctx.username,
            "display_name": ctx.display_name,
            "avatar": ctx.avatar,
            "account_ids": ctx.account_ids,
            "account_id": ctx.primary_account_id,
        },
        "scheduler": scheduler.get_status(),
        "accounts": visible_accounts,
    }


@app.get("/api/settings")
def api_get_settings(ctx: AuthContext = Depends(require_admin)):
    return scheduler.settings


@app.put("/api/settings")
def api_update_settings(
    settings_data: Dict[str, Any] = Body(...),
    ctx: AuthContext = Depends(require_admin),
):
    updated = scheduler.update_settings(settings_data)
    return {"status": "ok", "settings": updated}


@app.post("/api/run/start")
def api_start_run(
    req: Optional[RunStartRequest] = Body(default=None),
    ctx: AuthContext = Depends(require_authorized),
):
    target_account_id = req.account_id if req else None
    if ctx.role != "admin":
        if not target_account_id:
            target_account_id = ctx.primary_account_id
        if not target_account_id:
            raise HTTPException(status_code=403, detail="当前未绑定任何可用账号")
        ensure_account_access(ctx, target_account_id)

    ok, msg = scheduler.start_run(account_id=target_account_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "ok", "message": msg}


@app.post("/api/run/stop")
def api_stop_run(ctx: AuthContext = Depends(require_authorized)):
    if ctx.role != "admin":
        cur_acc = scheduler.current_account_id
        if not cur_acc or cur_acc not in ctx.account_ids:
            raise HTTPException(status_code=403, detail="仅管理员或当前正在运行账号的所属用户可停止任务")
    ok, msg = scheduler.stop_run()
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "ok", "message": msg}


# ==================== 账号管理接口 ====================

@app.get("/api/accounts")
def api_list_accounts(ctx: AuthContext = Depends(require_authorized)):
    all_accounts = account_manager.get_accounts()
    if ctx.role == "admin":
        return all_accounts
    allowed = set(ctx.account_ids)
    return [a for a in all_accounts if a["id"] in allowed]


@app.post("/api/accounts")
def api_create_account(
    req: AccountCreateRequest,
    ctx: AuthContext = Depends(require_admin),
):
    return account_manager.add_account(name=req.name, username=req.username or "")


@app.put("/api/accounts/reorder")
def api_reorder_accounts(
    req: AccountReorderRequest,
    ctx: AuthContext = Depends(require_admin),
):
    account_manager.reorder_accounts(req.account_ids)
    return {"status": "ok"}


@app.put("/api/accounts/{account_id}")
def api_update_account(
    account_id: str,
    req: AccountUpdateRequest,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    updates = req.model_dump(exclude_unset=True)
    # 普通用户不允许自行篡改 OIDC 绑定用户名或排序
    if ctx.role != "admin":
        updates.pop("username", None)
        updates.pop("order", None)

    acc = account_manager.update_account(account_id, **updates)
    if not acc:
        raise HTTPException(status_code=404, detail="未找到该账号")
    return acc


@app.post("/api/accounts/{account_id}/regenerate_key")
def api_regenerate_account_key(
    account_id: str,
    ctx: AuthContext = Depends(require_admin),
):
    new_key = account_manager.regenerate_secret_key(account_id)
    if not new_key:
        raise HTTPException(status_code=404, detail="未找到该账号")
    return {"status": "ok", "secret_key": new_key}


@app.delete("/api/accounts/{account_id}")
def api_delete_account(
    account_id: str,
    ctx: AuthContext = Depends(require_admin),
):
    if scheduler.is_running and scheduler.current_account_id == account_id:
        raise HTTPException(status_code=400, detail="该账号正在执行任务，请先停止任务后再删除")
    if not account_manager.delete_account(account_id):
        raise HTTPException(status_code=404, detail="未找到该账号")
    return {"status": "ok"}


# ==================== 单账号独立配置接口 ====================

@app.get("/api/options")
def api_get_options(ctx: AuthContext = Depends(require_authorized)):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    instances = {}
    characters = {}
    try:
        with open(os.path.join(root_dir, "assets", "config", "instance_names.json"), "r", encoding="utf-8") as f:
            instances = json.load(f)
    except Exception:
        pass
    try:
        with open(os.path.join(root_dir, "assets", "config", "character_names.json"), "r", encoding="utf-8") as f:
            characters = json.load(f)
    except Exception:
        pass
    return {"instances": instances, "characters": characters}


@app.get("/api/accounts/{account_id}/config")
def api_get_account_config(
    account_id: str,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    if not account_manager.get_account(account_id):
        raise HTTPException(status_code=404, detail="未找到该账号")
    return account_manager.get_account_config(account_id)


@app.put("/api/accounts/{account_id}/config")
def api_save_account_config(
    account_id: str,
    payload: Dict[str, Any] = Body(...),
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    if not account_manager.get_account(account_id):
        raise HTTPException(status_code=404, detail="未找到该账号")
    config_dict = payload.get("config") if "config" in payload and isinstance(payload.get("config"), dict) else payload
    try:
        result = account_manager.save_account_config_dict(account_id, config_dict)
        return {"status": "ok", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.put("/api/accounts/{account_id}/config/raw")
def api_save_account_config_raw(
    account_id: str,
    req: RawYamlUpdateRequest,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    if not account_manager.get_account(account_id):
        raise HTTPException(status_code=404, detail="未找到该账号")
    try:
        result = account_manager.save_account_config_raw(account_id, req.raw_yaml)
        return {"status": "ok", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/accounts/{account_id}/config/reset")
def api_reset_account_config(
    account_id: str,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    if not account_manager.get_account(account_id):
        raise HTTPException(status_code=404, detail="未找到该账号")
    result = account_manager.reset_account_config(account_id)
    return {"status": "ok", **result}


# ==================== 历史与增量日志接口 ====================

def _verify_log_access(ctx: AuthContext, log_file: str) -> str:
    safe_name = os.path.basename(log_file)
    if ctx.role != "admin":
        allowed = any(safe_name.endswith(f"_{aid}.log") for aid in ctx.account_ids)
        if not allowed:
            raise HTTPException(status_code=403, detail="无权查看该账号的运行日志")
    return safe_name


@app.get("/api/history")
def api_get_history(ctx: AuthContext = Depends(require_authorized)):
    return scheduler.get_history_for_context(ctx.role, ctx.account_ids)


@app.get("/api/logs/{log_file}")
def api_get_log_chunk(
    log_file: str,
    offset: int = Query(0, description="读取起始字节偏移量，负数表示仅读取尾部"),
    max_bytes: int = Query(131072, ge=4096, le=1048576),
    ctx: AuthContext = Depends(require_authorized),
):
    safe_name = _verify_log_access(ctx, log_file)
    return scheduler.read_log_chunk(safe_name, offset=offset, max_bytes=max_bytes)


@app.get("/api/logs/{log_file}/download")
def api_download_log(
    log_file: str,
    ctx: AuthContext = Depends(require_authorized),
):
    safe_name = _verify_log_access(ctx, log_file)
    log_path = os.path.join(LOGS_DIR, safe_name)
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="日志文件不存在")
    return FileResponse(
        log_path,
        media_type="text/plain; charset=utf-8",
        filename=safe_name,
    )


# ==================== 扫码登录管理 ====================

_qr_lock = threading.Lock()
_qr_processes: Dict[str, subprocess.Popen] = {}


def _cleanup_qr_process(account_id: str) -> None:
    with _qr_lock:
        proc = _qr_processes.pop(account_id, None)
    if proc is not None:
        terminate_process_tree(proc, timeout=4.0)
    profile_dir = account_manager.get_profile_dir(account_id)
    cleanup_residual_m7a_processes(profile_dir=profile_dir)
    reap_zombie_children()


@app.post("/api/accounts/{account_id}/qr_login/start")
def api_start_qr_login(
    account_id: str,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    if scheduler.is_running:
        raise HTTPException(status_code=400, detail="当前有自动化任务正在运行，请等待其结束后再扫码登录")

    acc = account_manager.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="未找到该账号")

    # 停止当前其它正在进行的扫码登录进程
    for existing_id in list(_qr_processes.keys()):
        _cleanup_qr_process(existing_id)

    profile_dir = account_manager.get_profile_dir(account_id)
    status_file = os.path.abspath(os.path.join(DATA_DIR, f"qr_status_{account_id}.json"))
    cancel_file = status_file + ".cancel"
    qr_image = os.path.abspath(os.path.join(DATA_DIR, f"qr_{account_id}.png"))

    for fpath in (status_file, cancel_file, qr_image):
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError:
                pass

    runtime_cfg_path, _ = account_manager.prepare_runtime_config(account_id)
    env = os.environ.copy()
    env["MARCH7TH_CONFIG_PATH"] = runtime_cfg_path
    env["MARCH7TH_USER_PROFILE_DIR"] = profile_dir
    env["PYTHONIOENCODING"] = "utf-8"

    runner_script = os.path.abspath("webui/backend/qr_login_runner.py")
    popen_kwargs: Dict[str, Any] = {"env": env}
    if sys.platform != "win32":
        popen_kwargs["start_new_session"] = True
    else:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        [sys.executable, "-u", runner_script, profile_dir, status_file, qr_image],
        **popen_kwargs,
    )
    with _qr_lock:
        _qr_processes[account_id] = proc

    return {"status": "ok", "message": "已启动扫码登录向导"}


@app.get("/api/accounts/{account_id}/qr_login/status")
def api_get_qr_login_status(
    account_id: str,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    status_file = os.path.abspath(os.path.join(DATA_DIR, f"qr_status_{account_id}.json"))
    qr_image = os.path.abspath(os.path.join(DATA_DIR, f"qr_{account_id}.png"))

    reap_zombie_children()

    with _qr_lock:
        proc = _qr_processes.get(account_id)
    is_alive = proc is not None and proc.poll() is None

    if not os.path.exists(status_file):
        return {
            "status": "starting" if is_alive else "idle",
            "message": "正在初始化无头浏览器..." if is_alive else "未启动",
            "has_qr": False,
        }

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"status": "starting", "message": "正在读取状态..."}

    has_qr = os.path.exists(qr_image) and data.get("status") in ("waiting_scan", "refreshing")
    data["has_qr"] = has_qr
    if has_qr:
        try:
            data["qr_mtime"] = os.path.getmtime(qr_image)
        except OSError:
            data["qr_mtime"] = time.time()

    if data.get("status") == "success":
        account_manager.update_account(account_id, is_logged_in=True)

    if not is_alive and data.get("status") not in ("success", "failed", "idle"):
        data["status"] = "failed"
        data["message"] = "扫码登录进程意外退出，请重试。"

    return data


@app.get("/api/accounts/{account_id}/qr_login/image")
def api_get_qr_login_image(
    account_id: str,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    qr_image = os.path.abspath(os.path.join(DATA_DIR, f"qr_{account_id}.png"))
    if not os.path.exists(qr_image):
        raise HTTPException(status_code=404, detail="二维码图片尚未生成")
    return FileResponse(qr_image, media_type="image/png")


@app.post("/api/accounts/{account_id}/qr_login/stop")
def api_stop_qr_login(
    account_id: str,
    ctx: AuthContext = Depends(require_authorized),
):
    ensure_account_access(ctx, account_id)
    status_file = os.path.abspath(os.path.join(DATA_DIR, f"qr_status_{account_id}.json"))
    cancel_file = status_file + ".cancel"
    try:
        with open(cancel_file, "w", encoding="utf-8") as f:
            f.write("1")
    except OSError:
        pass

    time.sleep(0.5)
    _cleanup_qr_process(account_id)

    for fpath in (status_file, cancel_file, os.path.abspath(os.path.join(DATA_DIR, f"qr_{account_id}.png"))):
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError:
                pass

    return {"status": "ok"}


# ==================== 前端静态资源托管 ====================

STATIC_DIR = os.path.abspath("webui/static")
if os.path.exists(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        candidate = os.path.abspath(os.path.join(STATIC_DIR, full_path))
        if candidate.startswith(STATIC_DIR) and os.path.isfile(candidate) and os.path.basename(candidate) != "index.html":
            return FileResponse(candidate)
        index_path = os.path.join(STATIC_DIR, "index.html")
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            theme_script = f'<script>window.__M7A_UI_THEME__ = "{get_ui_theme()}";</script>'
            if "</head>" in html_content:
                html_content = html_content.replace("</head>", f"  {theme_script}\n</head>", 1)
            return HTMLResponse(content=html_content)
        except Exception:
            return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
