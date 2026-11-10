import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import requests
from fastapi import Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from webui.backend.account_manager import DATA_DIR, account_manager

security = HTTPBearer(auto_error=False)

SESSION_SECRET_FILE = os.path.join(DATA_DIR, ".session_secret")
SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 days
PKCE_STATE_TTL_SECONDS = 600  # 10 minutes
DISCOVERY_CACHE_TTL_SECONDS = 3600  # 1 hour


def _get_or_create_server_secret() -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(SESSION_SECRET_FILE):
        try:
            with open(SESSION_SECRET_FILE, "r", encoding="utf-8") as f:
                s = f.read().strip()
            if len(s) >= 32:
                return s
        except Exception:
            pass
    new_secret = secrets.token_hex(32)
    try:
        with open(SESSION_SECRET_FILE, "w", encoding="utf-8") as f:
            f.write(new_secret)
    except Exception:
        pass
    return new_secret


_SERVER_SECRET = _get_or_create_server_secret()
_state_lock = threading.Lock()
_pkce_states: Dict[str, Dict[str, Any]] = {}
_discovery_cache: Dict[str, Any] = {}


@dataclass
class AuthContext:
    mode: str  # "oidc" | "token"
    role: str  # "admin" | "user" | "unauthorized"
    username: str = ""
    display_name: str = ""
    avatar: str = ""
    account_ids: List[str] = field(default_factory=list)

    @property
    def primary_account_id(self) -> Optional[str]:
        return self.account_ids[0] if self.account_ids else None


def get_oidc_settings() -> Dict[str, Any]:
    endpoint = (
        os.environ.get("OIDC_ENDPOINT")
        or os.environ.get("OIDC_ISSUER")
        or os.environ.get("OIDC_DISCOVERY_URL")
        or ""
    ).strip()
    client_id = (os.environ.get("OIDC_CLIENT_ID") or os.environ.get("OIDC_ID") or "").strip()
    client_secret = (
        os.environ.get("OIDC_CLIENT_SECRET") or os.environ.get("OIDC_SECRET") or ""
    ).strip()
    brand = (os.environ.get("OIDC_BRAND") or "SSO").strip() or "SSO"
    raw_admins = (
        os.environ.get("OIDC_ADMIN_USERNAME")
        or os.environ.get("OIDC_ADMIN_USER")
        or os.environ.get("ADMIN_USERNAME")
        or ""
    ).strip()
    admin_usernames = {u.strip().lower() for u in raw_admins.split(",") if u.strip()}
    username_claim = (os.environ.get("OIDC_USERNAME_CLAIM") or "").strip()
    scopes = (os.environ.get("OIDC_SCOPES") or "openid profile email").strip()

    enabled = bool(endpoint and client_id and client_secret)
    return {
        "enabled": enabled,
        "endpoint": endpoint,
        "client_id": client_id,
        "client_secret": client_secret,
        "brand": brand,
        "admin_usernames": admin_usernames,
        "username_claim": username_claim,
        "scopes": scopes,
    }


def get_auth_mode() -> str:
    return "oidc" if get_oidc_settings()["enabled"] else "token"


def get_admin_token() -> str:
    return os.environ.get("WEBUI_TOKEN", "12345678")


def _get_signing_key() -> bytes:
    oidc = get_oidc_settings()
    material = f"{_SERVER_SECRET}:{oidc['client_secret'] if oidc['enabled'] else get_admin_token()}"
    return hashlib.sha256(material.encode("utf-8")).digest()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("ascii"))


def create_session_token(payload: Dict[str, Any]) -> str:
    now = int(time.time())
    body = {
        **payload,
        "iat": now,
        "exp": now + SESSION_TTL_SECONDS,
    }
    raw_body = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_get_signing_key(), raw_body.encode("ascii"), hashlib.sha256).digest()
    return f"m7a.{raw_body}.{_b64url_encode(sig)}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    if not token or not token.startswith("m7a."):
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    _, raw_body, raw_sig = parts
    expected_sig = _b64url_encode(
        hmac.new(_get_signing_key(), raw_body.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(raw_sig, expected_sig):
        return None
    try:
        payload = json.loads(_b64url_decode(raw_body).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def _discover_oidc_metadata(endpoint: str) -> Dict[str, Any]:
    now = time.time()
    with _state_lock:
        cached = _discovery_cache.get(endpoint)
        if cached and now - cached["fetched_at"] < DISCOVERY_CACHE_TTL_SECONDS:
            return cached["data"]

    if endpoint.endswith("/.well-known/openid-configuration"):
        discovery_url = endpoint
    else:
        discovery_url = endpoint.rstrip("/") + "/.well-known/openid-configuration"

    try:
        resp = requests.get(discovery_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"无法获取 OIDC 服务发现配置 ({discovery_url}): {e}",
        ) from e

    if not data.get("authorization_endpoint") or not data.get("token_endpoint"):
        raise HTTPException(
            status_code=502,
            detail="OIDC 发现文档缺少 authorization_endpoint 或 token_endpoint",
        )

    with _state_lock:
        _discovery_cache[endpoint] = {"data": data, "fetched_at": now}
    return data


def _cleanup_expired_pkce_states() -> None:
    now = time.time()
    expired = [
        k for k, v in _pkce_states.items() if now - v.get("created_at", 0) > PKCE_STATE_TTL_SECONDS
    ]
    for k in expired:
        _pkce_states.pop(k, None)


def build_oidc_authorize_url(redirect_uri: str) -> Dict[str, str]:
    oidc = get_oidc_settings()
    if not oidc["enabled"]:
        raise HTTPException(status_code=400, detail="当前未启用 OIDC 认证模式")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="缺少 redirect_uri 参数")

    meta = _discover_oidc_metadata(oidc["endpoint"])
    auth_endpoint = meta["authorization_endpoint"]

    # 生成 PKCE S256 参数
    code_verifier = secrets.token_urlsafe(64)
    challenge_digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = _b64url_encode(challenge_digest)
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    with _state_lock:
        _cleanup_expired_pkce_states()
        _pkce_states[state] = {
            "code_verifier": code_verifier,
            "nonce": nonce,
            "redirect_uri": redirect_uri,
            "created_at": time.time(),
        }

    params = {
        "response_type": "code",
        "client_id": oidc["client_id"],
        "redirect_uri": redirect_uri,
        "scope": oidc["scopes"],
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    sep = "&" if "?" in auth_endpoint else "?"
    return {
        "authorize_url": f"{auth_endpoint}{sep}{urlencode(params)}",
        "state": state,
    }


def _decode_jwt_claims(jwt_token: str) -> Dict[str, Any]:
    parts = (jwt_token or "").split(".")
    if len(parts) < 2:
        return {}
    try:
        return json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    except Exception:
        return {}


def _extract_username(claims: Dict[str, Any], preferred_claim: str = "") -> str:
    if preferred_claim and claims.get(preferred_claim):
        return str(claims[preferred_claim]).strip()
    for key in ("preferred_username", "username", "login", "nickname", "name", "email", "sub"):
        val = claims.get(key)
        if val and isinstance(val, (str, int)):
            s = str(val).strip()
            if s:
                return s
    return ""


def _extract_display_name(claims: Dict[str, Any], fallback: str = "") -> str:
    for key in ("name", "nickname", "display_name", "preferred_username", "username", "login"):
        val = claims.get(key)
        if val and isinstance(val, (str, int)):
            s = str(val).strip()
            if s:
                return s
    return fallback


def _extract_avatar(claims: Dict[str, Any]) -> str:
    for key in ("picture", "avatar", "avatar_url", "profile_picture", "photo"):
        val = claims.get(key)
        if val and isinstance(val, str):
            s = val.strip()
            if s.startswith(("http://", "https://", "data:image/", "/")):
                return s
    return ""


def resolve_oidc_context(
    username: str,
    display_name: str = "",
    avatar: str = "",
) -> AuthContext:
    oidc = get_oidc_settings()
    clean_user = (username or "").strip()
    eff_display = (display_name or clean_user).strip()
    eff_avatar = (avatar or "").strip()
    if not clean_user:
        return AuthContext(
            mode="oidc",
            role="unauthorized",
            username="",
            display_name="",
            avatar="",
            account_ids=[],
        )

    if clean_user.lower() in oidc["admin_usernames"]:
        all_ids = [a["id"] for a in account_manager.get_accounts()]
        return AuthContext(
            mode="oidc",
            role="admin",
            username=clean_user,
            display_name=eff_display,
            avatar=eff_avatar,
            account_ids=all_ids,
        )

    matched = account_manager.get_accounts_by_username(clean_user)
    if matched:
        return AuthContext(
            mode="oidc",
            role="user",
            username=clean_user,
            display_name=eff_display,
            avatar=eff_avatar,
            account_ids=[a["id"] for a in matched],
        )

    return AuthContext(
        mode="oidc",
        role="unauthorized",
        username=clean_user,
        display_name=eff_display,
        avatar=eff_avatar,
        account_ids=[],
    )


def exchange_oidc_code(code: str, state: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    oidc = get_oidc_settings()
    if not oidc["enabled"]:
        raise HTTPException(status_code=400, detail="当前未启用 OIDC 认证模式")

    with _state_lock:
        _cleanup_expired_pkce_states()
        state_data = _pkce_states.pop(state, None)

    if not state_data:
        raise HTTPException(status_code=400, detail="登录状态已过期或 state 校验失败，请重新发起登录")

    meta = _discover_oidc_metadata(oidc["endpoint"])
    token_endpoint = meta["token_endpoint"]
    userinfo_endpoint = meta.get("userinfo_endpoint")

    effective_redirect_uri = redirect_uri or state_data["redirect_uri"]
    form_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": effective_redirect_uri,
        "client_id": oidc["client_id"],
        "client_secret": oidc["client_secret"],
        "code_verifier": state_data["code_verifier"],
    }

    try:
        token_resp = requests.post(
            token_endpoint,
            data=form_data,
            headers={"Accept": "application/json"},
            timeout=12,
        )
        token_resp.raise_for_status()
        token_json = token_resp.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"OIDC 令牌交换失败: {e}") from e

    claims: Dict[str, Any] = {}
    id_token = token_json.get("id_token")
    if id_token:
        id_claims = _decode_jwt_claims(id_token)
        expected_nonce = state_data.get("nonce")
        if expected_nonce and id_claims.get("nonce") and id_claims.get("nonce") != expected_nonce:
            raise HTTPException(status_code=401, detail="OIDC ID Token nonce 校验不匹配")
        claims.update(id_claims)

    access_token = token_json.get("access_token")
    if access_token and userinfo_endpoint:
        try:
            ui_resp = requests.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=10,
            )
            if ui_resp.ok:
                ui_data = ui_resp.json()
                if isinstance(ui_data, dict):
                    claims.update(ui_data)
        except Exception:
            pass

    username = _extract_username(claims, oidc["username_claim"])
    if not username:
        raise HTTPException(status_code=401, detail="无法从 OIDC 响应中解析出有效的用户名 (username)")

    display_name = _extract_display_name(claims, fallback=username)
    avatar = _extract_avatar(claims)

    ctx = resolve_oidc_context(username, display_name=display_name, avatar=avatar)
    session_token = create_session_token(
        {
            "mode": "oidc",
            "username": ctx.username,
            "display_name": ctx.display_name,
            "avatar": ctx.avatar,
            "sub": str(claims.get("sub") or ctx.username),
        }
    )
    return {
        "token": session_token,
        "mode": "oidc",
        "brand": oidc["brand"],
        "role": ctx.role,
        "username": ctx.username,
        "display_name": ctx.display_name,
        "avatar": ctx.avatar,
        "account_ids": ctx.account_ids,
        "account_id": ctx.primary_account_id,
    }


def login_with_token(raw_token: str) -> Dict[str, Any]:
    if get_auth_mode() != "token":
        raise HTTPException(status_code=400, detail="当前系统已配置为 OIDC 登录模式，不支持密钥直接登录")

    clean_token = (raw_token or "").strip()
    if not clean_token:
        raise HTTPException(status_code=401, detail="请输入访问密钥")

    if hmac.compare_digest(clean_token, get_admin_token()):
        all_ids = [a["id"] for a in account_manager.get_accounts()]
        session_token = create_session_token({"mode": "token", "role": "admin", "username": ""})
        return {
            "token": session_token,
            "mode": "token",
            "brand": "",
            "role": "admin",
            "username": "",
            "display_name": "",
            "avatar": "",
            "account_ids": all_ids,
            "account_id": all_ids[0] if all_ids else None,
        }

    acc = account_manager.get_account_by_secret_key(clean_token)
    if acc:
        session_token = create_session_token(
            {
                "mode": "token",
                "role": "user",
                "account_id": acc["id"],
                "secret_key": clean_token,
                "username": acc["name"],
            }
        )
        return {
            "token": session_token,
            "mode": "token",
            "brand": "",
            "role": "user",
            "username": acc["name"],
            "display_name": "",
            "avatar": "",
            "account_ids": [acc["id"]],
            "account_id": acc["id"],
        }

    raise HTTPException(status_code=401, detail="访问密钥无效或已失效")


def get_current_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_query: Optional[str] = Query(None, alias="token"),
) -> AuthContext:
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials.strip()
    elif token_query:
        raw_token = token_query.strip()

    if not raw_token:
        raise HTTPException(status_code=401, detail="未登录或登录凭证缺失")

    mode = get_auth_mode()

    # 1. 验证签名的会话令牌
    payload = verify_session_token(raw_token)
    if payload:
        if payload.get("mode") != mode:
            raise HTTPException(status_code=401, detail="系统认证模式已变更，请重新登录")

        if mode == "oidc":
            return resolve_oidc_context(
                payload.get("username", ""),
                display_name=payload.get("display_name", ""),
                avatar=payload.get("avatar", ""),
            )
        else:
            if payload.get("role") == "admin":
                all_ids = [a["id"] for a in account_manager.get_accounts()]
                return AuthContext(mode="token", role="admin", username="", display_name="", avatar="", account_ids=all_ids)
            acc_id = payload.get("account_id")
            sec_key = payload.get("secret_key")
            acc = account_manager.get_account(acc_id) if acc_id else None
            if acc and (not sec_key or acc.get("secret_key") == sec_key):
                return AuthContext(
                    mode="token",
                    role="user",
                    username=acc["name"],
                    account_ids=[acc["id"]],
                )
            raise HTTPException(status_code=401, detail="该账号密钥已重置或账号已删除，请重新登录")

    # 2. 在 Token 模式下，兼容直接使用原始 WEBUI_TOKEN 或账号 secret_key 作为 Bearer Token
    if mode == "token":
        if hmac.compare_digest(raw_token, get_admin_token()):
            all_ids = [a["id"] for a in account_manager.get_accounts()]
            return AuthContext(mode="token", role="admin", username="admin", account_ids=all_ids)
        acc = account_manager.get_account_by_secret_key(raw_token)
        if acc:
            return AuthContext(
                mode="token",
                role="user",
                username=acc["name"],
                account_ids=[acc["id"]],
            )

    raise HTTPException(status_code=401, detail="登录会话无效或已过期，请重新登录")


def require_authorized(ctx: AuthContext = Depends(get_current_session)) -> AuthContext:
    if ctx.role == "unauthorized":
        raise HTTPException(
            status_code=403,
            detail=f"账号「{ctx.username}」暂无访问权限，请联系管理员在后台为您分配账号",
        )
    return ctx


def require_admin(ctx: AuthContext = Depends(require_authorized)) -> AuthContext:
    if ctx.role != "admin":
        raise HTTPException(status_code=403, detail="此操作需要管理员权限")
    return ctx


def ensure_account_access(ctx: AuthContext, account_id: str) -> None:
    if ctx.role == "unauthorized":
        raise HTTPException(status_code=403, detail="当前登录用户无访问权限")
    if ctx.role == "admin":
        return
    if account_id not in ctx.account_ids:
        raise HTTPException(status_code=403, detail="您没有权限访问或修改该游戏账号")
