import io
import json
import os
import shutil
import threading
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional
from ruamel.yaml import YAML

DATA_DIR = os.path.abspath(os.environ.get("WEBUI_DATA_DIR", "webui/data"))
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
CONFIGS_DIR = os.path.join(DATA_DIR, "configs")
RUNTIME_DIR = os.path.join(DATA_DIR, "runtime")
EXAMPLE_CONFIG_PATH = os.path.abspath("assets/config/config.example.yaml")

DOCKER_DEFAULT_OVERRIDES = {
    "cloud_game_enable": True,
    "browser_persistent_enable": True,
    "browser_headless_enable": True,
    "browser_headless_restart_on_not_logged_in": False,
    "after_finish": "Exit",
    "auto_update": False,
    "check_prerelease_enable": False,
}

# 禁止写回用户配置的容器运行期固定键
PROTECTED_RUNTIME_KEYS = {
    "cloud_game_enable",
    "browser_persistent_enable",
    "browser_headless_enable",
    "browser_headless_restart_on_not_logged_in",
    "after_finish",
    "auto_update",
}


def _create_yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    return y


def _to_plain_data(obj: Any) -> Any:
    """将 ruamel.yaml 的 CommentedMap/CommentedSeq 递归转换为标准 Python dict/list。"""
    if isinstance(obj, dict):
        return {str(k): _to_plain_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain_data(item) for item in obj]
    return obj


def _deep_merge_ruamel(target: Any, source: Dict[str, Any]) -> Any:
    """将 source 字典递归合并到 ruamel CommentedMap 中，保留原有的注释结构。"""
    if not isinstance(source, dict) or not isinstance(target, dict):
        return deepcopy(source)
    for k, v in source.items():
        if k in target and isinstance(target[k], dict) and isinstance(v, dict):
            _deep_merge_ruamel(target[k], v)
        else:
            target[k] = deepcopy(v)
    return target


class AccountManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._ensure_dirs()
        self.accounts: List[Dict[str, Any]] = self._load_accounts()
        self._ensure_all_account_files()

    def _ensure_dirs(self) -> None:
        for d in (DATA_DIR, PROFILES_DIR, CONFIGS_DIR, RUNTIME_DIR):
            os.makedirs(d, exist_ok=True)
        if not os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load_accounts(self) -> List[Dict[str, Any]]:
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            changed = False
            for idx, acc in enumerate(data):
                if "secret_key" not in acc or not acc["secret_key"]:
                    acc["secret_key"] = uuid.uuid4().hex
                    changed = True
                if "username" not in acc or acc["username"] is None:
                    acc["username"] = ""
                    changed = True
                if "enabled" not in acc:
                    acc["enabled"] = True
                    changed = True
                if "order" not in acc:
                    acc["order"] = idx
                    changed = True
                if "is_logged_in" not in acc:
                    acc["is_logged_in"] = False
                    changed = True
                if "last_run_at" not in acc:
                    acc["last_run_at"] = None
                if "last_run_status" not in acc:
                    acc["last_run_status"] = None
            data.sort(key=lambda x: x.get("order", 0))
            if changed:
                self._save_accounts_unlocked(data)
            return data
        except Exception:
            return []

    def _save_accounts_unlocked(self, accounts_list: Optional[List[Dict[str, Any]]] = None) -> None:
        target = accounts_list if accounts_list is not None else self.accounts
        tmp_file = ACCOUNTS_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(target, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, ACCOUNTS_FILE)

    def save_accounts(self) -> None:
        with self._lock:
            self._save_accounts_unlocked()

    def get_profile_dir(self, account_id: str) -> str:
        return os.path.abspath(os.path.join(PROFILES_DIR, account_id))

    def get_config_file_path(self, account_id: str) -> str:
        return os.path.abspath(os.path.join(CONFIGS_DIR, f"{account_id}.yaml"))

    def get_runtime_config_path(self, account_id: str) -> str:
        return os.path.abspath(os.path.join(RUNTIME_DIR, f"{account_id}_runtime.yaml"))

    def _init_profile_dir(self, account_id: str) -> None:
        """初始化账号的浏览器 Profile 目录及合法的 JSON 模板文件，防止首次启动报错。"""
        profile_dir = self.get_profile_dir(account_id)
        default_dir = os.path.join(profile_dir, "Default")
        os.makedirs(default_dir, exist_ok=True)
        for json_path in (
            os.path.join(profile_dir, "Local State"),
            os.path.join(default_dir, "Preferences"),
        ):
            if not os.path.exists(json_path) or os.path.getsize(json_path) == 0:
                try:
                    with open(json_path, "w", encoding="utf-8") as f:
                        f.write("{}")
                except Exception:
                    pass

    def _load_example_commented_map(self) -> Any:
        y = _create_yaml()
        if os.path.exists(EXAMPLE_CONFIG_PATH):
            with open(EXAMPLE_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = y.load(f)
            if isinstance(data, dict):
                _deep_merge_ruamel(data, DOCKER_DEFAULT_OVERRIDES)
                return data
        return deepcopy(DOCKER_DEFAULT_OVERRIDES)

    def _ensure_account_config_file(self, account_id: str) -> None:
        cfg_path = self.get_config_file_path(account_id)
        if not os.path.exists(cfg_path) or os.path.getsize(cfg_path) == 0:
            base_map = self._load_example_commented_map()
            y = _create_yaml()
            with open(cfg_path, "w", encoding="utf-8") as f:
                y.dump(base_map, f)

    def _ensure_all_account_files(self) -> None:
        with self._lock:
            for acc in self.accounts:
                acc_id = acc["id"]
                self._init_profile_dir(acc_id)
                self._ensure_account_config_file(acc_id)

    def check_profile_logged_in(self, account_id: str) -> bool:
        """检查 Profile 目录中是否存在有效登录痕迹。"""
        profile_dir = self.get_profile_dir(account_id)
        if not os.path.exists(profile_dir):
            return False

        cookie_paths = [
            os.path.join(profile_dir, "Default", "Cookies"),
            os.path.join(profile_dir, "Default", "Network", "Cookies"),
        ]
        for cp in cookie_paths:
            try:
                if os.path.exists(cp) and os.path.getsize(cp) > 4096:
                    return True
            except OSError:
                pass

        leveldb_dir = os.path.join(profile_dir, "Default", "Local Storage", "leveldb")
        if os.path.exists(leveldb_dir):
            try:
                for fn in os.listdir(leveldb_dir):
                    if fn.endswith((".ldb", ".log")):
                        fp = os.path.join(leveldb_dir, fn)
                        if os.path.isfile(fp) and os.path.getsize(fp) > 512:
                            return True
            except OSError:
                pass
        return False

    def get_accounts(self) -> List[Dict[str, Any]]:
        with self._lock:
            changed = False
            for acc in self.accounts:
                if self.check_profile_logged_in(acc["id"]) and not acc.get("is_logged_in"):
                    acc["is_logged_in"] = True
                    changed = True
            if changed:
                self._save_accounts_unlocked()
            return [deepcopy(a) for a in sorted(self.accounts, key=lambda x: x.get("order", 0))]

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for acc in self.accounts:
                if acc["id"] == account_id:
                    if self.check_profile_logged_in(acc["id"]) and not acc.get("is_logged_in"):
                        acc["is_logged_in"] = True
                        self._save_accounts_unlocked()
                    return deepcopy(acc)
            return None

    def get_accounts_by_username(self, username: str) -> List[Dict[str, Any]]:
        """根据 OIDC username 查找绑定的账号列表。"""
        if not username:
            return []
        target = username.strip().lower()
        if not target:
            return []
        with self._lock:
            matched = []
            for acc in sorted(self.accounts, key=lambda x: x.get("order", 0)):
                bound = (acc.get("username") or "").strip().lower()
                if bound and bound == target:
                    if self.check_profile_logged_in(acc["id"]) and not acc.get("is_logged_in"):
                        acc["is_logged_in"] = True
                    matched.append(deepcopy(acc))
            return matched

    def get_account_by_secret_key(self, secret_key: str) -> Optional[Dict[str, Any]]:
        """根据 Token 模式的 secret_key 查找对应账号。"""
        if not secret_key:
            return None
        key = secret_key.strip()
        with self._lock:
            for acc in self.accounts:
                if acc.get("secret_key") == key:
                    return deepcopy(acc)
            return None

    def add_account(self, name: str, username: str = "") -> Dict[str, Any]:
        with self._lock:
            account_id = f"acc_{uuid.uuid4().hex[:8]}"
            new_acc = {
                "id": account_id,
                "name": (name or "").strip() or "未命名账号",
                "username": (username or "").strip(),
                "secret_key": uuid.uuid4().hex,
                "enabled": True,
                "order": len(self.accounts),
                "is_logged_in": False,
                "last_run_at": None,
                "last_run_status": None,
            }
            self.accounts.append(new_acc)
            self._init_profile_dir(account_id)
            self._ensure_account_config_file(account_id)
            self._save_accounts_unlocked()
            return deepcopy(new_acc)

    def update_account(self, account_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        allowed_fields = {
            "name",
            "username",
            "enabled",
            "order",
            "is_logged_in",
            "last_run_at",
            "last_run_status",
        }
        with self._lock:
            for acc in self.accounts:
                if acc["id"] == account_id:
                    for k, v in kwargs.items():
                        if k in allowed_fields and v is not None:
                            if k in ("name", "username") and isinstance(v, str):
                                acc[k] = v.strip()
                            else:
                                acc[k] = v
                    self._save_accounts_unlocked()
                    return deepcopy(acc)
            return None

    def regenerate_secret_key(self, account_id: str) -> Optional[str]:
        with self._lock:
            for acc in self.accounts:
                if acc["id"] == account_id:
                    acc["secret_key"] = uuid.uuid4().hex
                    self._save_accounts_unlocked()
                    return acc["secret_key"]
            return None

    def delete_account(self, account_id: str) -> bool:
        with self._lock:
            idx_to_remove = None
            for idx, acc in enumerate(self.accounts):
                if acc["id"] == account_id:
                    idx_to_remove = idx
                    break
            if idx_to_remove is None:
                return False

            self.accounts.pop(idx_to_remove)
            for idx, acc in enumerate(self.accounts):
                acc["order"] = idx
            self._save_accounts_unlocked()

            profile_dir = self.get_profile_dir(account_id)
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir, ignore_errors=True)

            for fpath in (self.get_config_file_path(account_id), self.get_runtime_config_path(account_id)):
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass
            return True

    def reorder_accounts(self, account_ids: List[str]) -> bool:
        with self._lock:
            id_map = {acc["id"]: acc for acc in self.accounts}
            new_list = []
            for idx, aid in enumerate(account_ids):
                if aid in id_map:
                    acc = id_map.pop(aid)
                    acc["order"] = idx
                    new_list.append(acc)
            for acc in id_map.values():
                acc["order"] = len(new_list)
                new_list.append(acc)
            self.accounts = new_list
            self._save_accounts_unlocked()
            return True

    # ==================== 独立配置读写与合并 ====================

    def _load_merged_commented_config(self, account_id: str) -> Any:
        """
        加载 example 配置作为基底，并将账号自己的配置文件合并在其之上。
        返回带完整注释的 ruamel CommentedMap。
        """
        self._ensure_account_config_file(account_id)
        base_map = self._load_example_commented_map()
        cfg_path = self.get_config_file_path(account_id)
        y = _create_yaml()
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                user_data = y.load(f)
            if isinstance(user_data, dict):
                _deep_merge_ruamel(base_map, _to_plain_data(user_data))
        except Exception:
            pass
        return base_map

    def get_account_config(self, account_id: str) -> Dict[str, Any]:
        """获取账号的完整合并配置（同时返回给简单模式用的 JSON dict 和给高级模式用的带注释 YAML 文本）。"""
        with self._lock:
            merged_map = self._load_merged_commented_config(account_id)
            y = _create_yaml()
            buf = io.StringIO()
            y.dump(merged_map, buf)
            raw_yaml = buf.getvalue()
            plain_dict = _to_plain_data(merged_map)
            return {
                "config": plain_dict,
                "raw_yaml": raw_yaml,
            }

    def save_account_config_dict(self, account_id: str, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """从简单模式保存账号配置，将其合并到带注释的模板并持久化到账号独立 YAML。"""
        if not isinstance(new_config, dict):
            raise ValueError("配置必须是 JSON 对象")
        with self._lock:
            merged_map = self._load_merged_commented_config(account_id)
            _deep_merge_ruamel(merged_map, new_config)
            cfg_path = self.get_config_file_path(account_id)
            y = _create_yaml()
            tmp_path = cfg_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                y.dump(merged_map, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, cfg_path)
            return self.get_account_config(account_id)

    def save_account_config_raw(self, account_id: str, raw_yaml: str) -> Dict[str, Any]:
        """从高级模式保存 YAML 文本，校验合法性后与 example 配置合并补全并写入账号独立配置文件。"""
        y = _create_yaml()
        try:
            parsed = y.load(raw_yaml)
        except Exception as e:
            raise ValueError(f"YAML 语法错误: {e}") from e

        if not isinstance(parsed, dict):
            raise ValueError("YAML 根节点必须是键值对映射 (Mapping)")

        with self._lock:
            # 将用户编辑的 YAML 与 example 基底合并，既保留用户的修改和注释，又确保不丢失上游新增字段
            base_map = self._load_example_commented_map()
            _deep_merge_ruamel(base_map, _to_plain_data(parsed))
            # 如果用户保留了完整注释，优先在用户的 CommentedMap 上补齐缺失键
            for k, v in base_map.items():
                if k not in parsed:
                    parsed[k] = deepcopy(v)
            cfg_path = self.get_config_file_path(account_id)
            tmp_path = cfg_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                y.dump(parsed, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, cfg_path)
            return self.get_account_config(account_id)

    def reset_account_config(self, account_id: str) -> Dict[str, Any]:
        """重置账号配置为默认配置。"""
        with self._lock:
            base_map = self._load_example_commented_map()
            cfg_path = self.get_config_file_path(account_id)
            y = _create_yaml()
            with open(cfg_path, "w", encoding="utf-8") as f:
                y.dump(base_map, f)
            return self.get_account_config(account_id)

    def prepare_runtime_config(self, account_id: str) -> tuple[str, Dict[str, Any]]:
        """
        生成运行期配置文件（与 assets/config/config.example.yaml 合并，并注入 Docker 必需项）。
        返回 (runtime_config_path, before_snapshot_dict)。
        """
        with self._lock:
            self._init_profile_dir(account_id)
            merged_map = self._load_merged_commented_config(account_id)
            for k, v in DOCKER_DEFAULT_OVERRIDES.items():
                merged_map[k] = v
            runtime_path = self.get_runtime_config_path(account_id)
            y = _create_yaml()
            tmp_path = runtime_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                y.dump(merged_map, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, runtime_path)
            return runtime_path, _to_plain_data(merged_map)

    def sync_runtime_state_back(
        self, account_id: str, before_snapshot: Dict[str, Any], runtime_config_path: str
    ) -> None:
        """
        将小助手运行期间自动更新的状态字段（如 *_timestamp、power_plan、already_used_codes 等）
        同步写回账号的独立配置文件。
        """
        if not os.path.exists(runtime_config_path):
            return
        y = _create_yaml()
        try:
            with open(runtime_config_path, "r", encoding="utf-8") as f:
                after_map = y.load(f)
            if not isinstance(after_map, dict):
                return
            after_plain = _to_plain_data(after_map)
        except Exception:
            return

        changed_fields: Dict[str, Any] = {}
        for k, after_val in after_plain.items():
            if k in PROTECTED_RUNTIME_KEYS:
                continue
            before_val = before_snapshot.get(k)
            if after_val != before_val:
                changed_fields[k] = after_val

        if changed_fields:
            with self._lock:
                merged_map = self._load_merged_commented_config(account_id)
                _deep_merge_ruamel(merged_map, changed_fields)
                cfg_path = self.get_config_file_path(account_id)
                tmp_path = cfg_path + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    y.dump(merged_map, f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, cfg_path)


account_manager = AccountManager()
