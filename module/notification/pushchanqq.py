import io
from typing import Any, Dict, Optional
import requests
from utils.logger.logger import Logger
from .notifier import Notifier


class PushChanQqNotifier(Notifier):
    """PushChan QQ (qq-push-bot) 消息推送通知器。

    支持通过 HTTP 接口将文本与图片消息推送到指定的 QQ 用户（私聊）或 QQ 群（群聊）。
    """

    DEFAULT_ENDPOINT = "https://pushchan.shingyu.cn"
    KNOWN_PATHS = (
        "/sendmessage",
        "/sendmarkdown",
        "/sendimage",
        "/sendvoice",
        "/sendfile",
        "/sendimagecard",
        "/sendcard",
    )

    def __init__(self, params: Dict[str, Any], logger: Logger):
        super().__init__(params, logger)

    def _get_supports_image(self) -> bool:
        return True

    def _resolve_endpoint(self) -> str:
        raw = str(
            self.params.get("endpoint")
            or self.params.get("api_url")
            or self.params.get("url")
            or self.DEFAULT_ENDPOINT
        ).strip()
        if not raw:
            raw = self.DEFAULT_ENDPOINT
        raw = raw.rstrip("/")
        lower = raw.lower()
        for suffix in self.KNOWN_PATHS:
            if lower.endswith(suffix):
                raw = raw[: -len(suffix)].rstrip("/")
                break
        return raw or self.DEFAULT_ENDPOINT

    def _resolve_group(self) -> bool:
        raw = self.params.get("group", False)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return bool(raw)
        if isinstance(raw, str):
            return raw.strip().lower() in ("true", "1", "yes", "group")
        return False

    @staticmethod
    def _check_response(response: requests.Response, action_name: str) -> None:
        try:
            data = response.json()
        except Exception:
            data = None

        if response.ok and (not isinstance(data, dict) or data.get("ok", True)):
            return

        detail = ""
        if isinstance(data, dict):
            detail = str(data.get("detail") or data.get("message") or "").strip()
        if not detail:
            detail = (getattr(response, "text", "") or "").strip() or f"HTTP {response.status_code}"
        raise RuntimeError(f"PushChan QQ {action_name}发送失败: {detail}")

    def send(self, title: str, content: str, image_io: Optional[io.BytesIO] = None):
        endpoint = self._resolve_endpoint()
        openid = str(self.params.get("openid") or self.params.get("touid") or "").strip()
        if not openid:
            raise ValueError("PushChan QQ 通知需要配置 openid")

        token = str(self.params.get("token") or "").strip()
        group = self._resolve_group()

        headers: Dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        message = title if not content else f"{title}\n{content}" if title else content

        if message:
            payload: Dict[str, Any] = {
                "content": message,
                "group": group,
                "openid": openid,
            }
            if token:
                payload["token"] = token
            resp = requests.post(
                f"{endpoint}/sendmessage",
                headers={**headers, "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            self._check_response(resp, "文本消息")

        if image_io is not None:
            image_io.seek(0)
            image_bytes = image_io.read()
            if image_bytes:
                form_data: Dict[str, str] = {
                    "openid": openid,
                    "group": "true" if group else "false",
                }
                if token:
                    form_data["token"] = token
                files = {
                    "file": ("screenshot.jpg", image_bytes, "image/jpeg"),
                }
                resp = requests.post(
                    f"{endpoint}/sendimage",
                    headers=headers,
                    data=form_data,
                    files=files,
                    timeout=60,
                )
                self._check_response(resp, "图片")
