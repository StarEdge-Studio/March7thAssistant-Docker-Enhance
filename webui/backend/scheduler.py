import os
import time
import json
import subprocess
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta
import ruamel.yaml

from .account_manager import account_manager, DATA_DIR, PROFILES_DIR

SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
LOGS_DIR = os.path.join(DATA_DIR, 'run_logs')
INTERNET_CHECK_URL = 'https://www.mihoyo.com/'
INTERNET_CHECK_TIMEOUT_SECONDS = 10
INTERNET_RETRY_DELAY_SECONDS = 2 * 60 * 60
INTERNET_MAX_RETRIES = 3
INTERNET_CHECK_ACCOUNT_ID = '__webui_internet_check__'
os.makedirs(LOGS_DIR, exist_ok=True)

class Scheduler:
    def __init__(self):
        self.running = False
        self.current_process = None
        self.current_account_id = None
        self.current_account_name = None
        self.waiting_for_retry = False
        self.internet_retry_count = 0
        self.next_retry_time = None
        self.run_history = []
        self._load_settings()
        self._load_history()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                'scheduled_time': '04:00',
                'auto_run': True
            }
            self._save_settings()

    def _save_settings(self):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self._save_settings()

    def get_settings(self):
        return self.settings

    def get_status(self):
        return {
            "running": self.running,
            "current_account_id": self.current_account_id,
            "current_account_name": self.current_account_name,
            "waiting_for_retry": self.waiting_for_retry,
            "internet_retry_count": self.internet_retry_count,
            "internet_max_retries": INTERNET_MAX_RETRIES,
            "next_retry_time": self.next_retry_time.isoformat() if self.next_retry_time else None
        }

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.run_history = json.load(f)
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                self.run_history = []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.run_history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def _loop(self):
        last_run_date = None
        while True:
            time.sleep(10)
            if not self.settings.get('auto_run'):
                continue

            now = datetime.now()
            current_time_str = now.strftime('%H:%M')
            current_date_str = now.strftime('%Y-%m-%d')

            if current_time_str == self.settings.get('scheduled_time') and last_run_date != current_date_str:
                if not self.running:
                    last_run_date = current_date_str
                    self.start_run()

    def start_run(self):
        if self.running:
            return False

        self.running = True
        threading.Thread(target=self._execute_all_accounts, daemon=True).start()
        return True

    def stop_run(self):
        if not self.running:
            return False

        self.running = False
        self.waiting_for_retry = False
        self.next_retry_time = None

        if self.current_process:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()

        # 清理可能残留的由小助手启动的浏览器进程
        try:
            self._kill_all_m7a_processes()
        except Exception as e:
            print(f"清理残留浏览器进程失败: {e}")

        return True

    @staticmethod
    def _kill_all_m7a_processes():
        """通过 psutil 直接查找并终止所有带有 M7A 标记的浏览器和 chromedriver 进程"""
        import psutil
        BROWSER_TAG = "--march-7th-assistant-sr-cloud-game"
        target_names = {
            'chrome', 'chrome.exe', 'chromium', 'chromium-browser',
            'msedge', 'msedge.exe', 'chromedriver', 'chromedriver.exe',
            'msedgedriver', 'msedgedriver.exe',
            'google-chrome', 'google-chrome-stable',
        }
        killed = []
        for proc in psutil.process_iter(['pid', 'name']):
            name = proc.info.get('name', '')
            if not name or name.lower() not in target_names:
                continue
            try:
                cmdline = proc.cmdline()
                if BROWSER_TAG in cmdline or name.lower().startswith(('chromedriver', 'msedgedriver')):
                    proc.terminate()
                    killed.append(proc)
            except psutil.Error:
                continue
        if killed:
            gone, alive = psutil.wait_procs(killed, timeout=5)
            for p in alive:
                try:
                    p.kill()
                except psutil.Error:
                    pass
            if alive:
                psutil.wait_procs(alive, timeout=3)

    def _reset_internet_retry_state(self):
        self.waiting_for_retry = False
        self.internet_retry_count = 0
        self.next_retry_time = None

    def _check_internet_connection(self):
        request = urllib.request.Request(
            INTERNET_CHECK_URL,
            headers={
                'User-Agent': 'March7thAssistant-WebUI/1.0'
            }
        )

        try:
            with urllib.request.urlopen(request, timeout=INTERNET_CHECK_TIMEOUT_SECONDS) as response:
                status_code = getattr(response, 'status', 200)
                response.read(1)
            if status_code < 500:
                return True, f"HTTP {status_code}"
            return False, f"HTTP {status_code}"
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return True, f"HTTP {e.code}"
            return False, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, str(e)

    def _write_webui_log(self, log_file, message):
        log_path = os.path.join(LOGS_DIR, log_file)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {message}\n")

    def _create_internet_check_result(self, history_entry, run_id):
        result = {
            'account_id': INTERNET_CHECK_ACCOUNT_ID,
            'account_name': '互联网连接检查',
            'success': False,
            'log_file': f"log_{run_id}_internet_check.txt",
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        history_entry['accounts'].append(result)
        self.current_account_id = INTERNET_CHECK_ACCOUNT_ID
        self.current_account_name = '互联网连接检查'
        return result

    def _wait_for_retry_or_stop(self):
        retry_until = time.monotonic() + INTERNET_RETRY_DELAY_SECONDS
        while self.running and time.monotonic() < retry_until:
            time.sleep(min(10, max(0, retry_until - time.monotonic())))
        return self.running

    def _ensure_internet_available(self, history_entry, run_id):
        check_result = None

        for attempt in range(INTERNET_MAX_RETRIES + 1):
            if not self.running:
                return False

            if attempt > 0:
                self.current_account_id = INTERNET_CHECK_ACCOUNT_ID
                self.current_account_name = f"互联网连接检查（第 {attempt}/{INTERNET_MAX_RETRIES} 次重试）"
                self._save_history()

            success, detail = self._check_internet_connection()
            if success:
                self._reset_internet_retry_state()
                if check_result:
                    self._write_webui_log(check_result['log_file'], f"[WebUI] 互联网连接检查通过：{INTERNET_CHECK_URL} ({detail})")
                    check_result['success'] = True
                    check_result['end_time'] = datetime.now().isoformat()
                    self._save_history()
                return True

            if check_result is None:
                check_result = self._create_internet_check_result(history_entry, run_id)

            self._write_webui_log(check_result['log_file'], f"[WebUI] 互联网连接检查失败：{INTERNET_CHECK_URL} ({detail})")

            if attempt >= INTERNET_MAX_RETRIES:
                self._write_webui_log(check_result['log_file'], f"[WebUI] 已重试 {INTERNET_MAX_RETRIES} 次，互联网连接仍不可用，本次 WebUI 执行退出")
                check_result['success'] = False
                check_result['end_time'] = datetime.now().isoformat()
                self._save_history()
                return False

            self.internet_retry_count = attempt + 1
            self.waiting_for_retry = True
            self.next_retry_time = datetime.now() + timedelta(seconds=INTERNET_RETRY_DELAY_SECONDS)
            self.current_account_id = INTERNET_CHECK_ACCOUNT_ID
            self.current_account_name = f"网络不可用，等待第 {self.internet_retry_count}/{INTERNET_MAX_RETRIES} 次重试"
            self._write_webui_log(check_result['log_file'], f"[WebUI] 将延迟 2 小时后重试，预计重试时间：{self.next_retry_time.isoformat(timespec='seconds')}")
            self._save_history()

            if not self._wait_for_retry_or_stop():
                self._write_webui_log(check_result['log_file'], "[WebUI] 等待重试期间收到停止信号，本次 WebUI 执行退出")
                check_result['success'] = False
                check_result['end_time'] = datetime.now().isoformat()
                self._save_history()
                return False

            self.waiting_for_retry = False
            self.next_retry_time = None

    def _execute_all_accounts(self):
        accounts = [a for a in account_manager.get_accounts() if a.get('enabled')]
        
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        history_entry = {
            'run_id': run_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'accounts': []
        }
        self.run_history.insert(0, history_entry)
        if len(self.run_history) > 50:  # 稍微增加一点上限
            self.run_history.pop()
        self._save_history()  # 启动时保存一次

        try:
            if accounts and not self._ensure_internet_available(history_entry, run_id):
                return

            for account in accounts:
                if not self.running:
                    break
                
                acc_result = {
                    'account_id': account['id'],
                    'account_name': account['name'],
                    'success': False,
                    'log_file': f"log_{run_id}_{account['id']}.txt",
                    'start_time': None,
                    'end_time': None
                }
                history_entry['accounts'].append(acc_result)
                self._run_single_account(account, acc_result)
                self._save_history()  # 每次账号运行结束后立即保存状态，以便前端及时更新
        finally:
            history_entry['end_time'] = datetime.now().isoformat()
            self._save_history()  # 运行结束后保存
            self.running = False
            self.current_account_id = None
            self.current_account_name = None
            self._reset_internet_retry_state()

    def _run_single_account(self, account, acc_result):
        acc_result['start_time'] = datetime.now().isoformat()
        self.current_account_id = account['id']
        self.current_account_name = account['name']
        account_profile_dir = os.path.join(PROFILES_DIR, account['id'])
        os.makedirs(account_profile_dir, exist_ok=True)

        # 准备独立的配置
        base_config_path = os.path.join(DATA_DIR, 'config.yaml')
        if not os.path.exists(base_config_path):
            base_config_path = os.path.join(os.getcwd(), 'config.yaml')
        temp_config_path = os.path.join(DATA_DIR, f"config_{account['id']}.yaml")
        
        yaml = ruamel.yaml.YAML()
        if os.path.exists(base_config_path):
            with open(base_config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.load(f) or {}
        else:
            config_data = {}

        # 叠加 account 覆盖配置
        if account.get('config_override'):
            try:
                override_data = yaml.load(account['config_override']) or {}
                # 简单递归更新
                def deep_update(d, u):
                    for k, v in u.items():
                        if isinstance(v, dict):
                            d[k] = deep_update(d.get(k, {}), v)
                        else:
                            d[k] = v
                    return d
                deep_update(config_data, override_data)
            except Exception as e:
                print(f"解析账号配置覆盖失败: {e}")

        # 强制接管控制权：必须让子进程在执行完本账号后退出，以便调度器继续执行下一个账号
        config_data['after_finish'] = "Exit"
        # 强制启用浏览器持久化，确保 user-data-dir 生效（登录信息才能被复用）
        config_data['browser_persistent_enable'] = True

        # 保存临时配置
        with open(temp_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        # 环境变量
        env = os.environ.copy()
        env['MARCH7TH_CONFIG_PATH'] = temp_config_path
        env['MARCH7TH_USER_PROFILE_DIR'] = account_profile_dir
        # Cloud game mode default to true for WebUI execution if not specified
        if 'MARCH7TH_CLOUD_GAME_ENABLE' not in env:
            env['MARCH7TH_CLOUD_GAME_ENABLE'] = 'true'
        # 强制子进程使用 UTF-8 编码输出，防止 Windows 下日志乱码
        env['PYTHONIOENCODING'] = 'utf-8'
        # 再次确保退出模式生效，防止环境变量覆盖
        env['MARCH7TH_AFTER_FINISH'] = 'Exit'

        log_path = os.path.join(LOGS_DIR, acc_result['log_file'])
        
        try:
            with open(log_path, 'w', encoding='utf-8') as log_file:
                # 检查是否开启了调试模式
                if self.settings.get('debug_mode'):
                    import time
                    
                    def get_ts():
                        return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]

                    log_file.write(f"+-------------------------------------------------------------------------------------------------------------------+\n")
                    log_file.write(f"|                                               [DEBUG] 模拟开始运行                                                |\n")
                    log_file.write(f"+-------------------------------------------------------------------------------------------------------------------+\n")
                    log_file.flush()
                    
                    mock_flow = [
                        (f"{get_ts()} | INFO | 正在启动 chrome 浏览器", 2),
                        (f"{get_ts()} | INFO | 云游戏剩余时长：462 分钟", 1),
                        (f"{get_ts()} | INFO | 进入云游戏成功", 3),
                        (f"+-------------------------------------------------------------------------------------------------------------------+\n|                                                 开始获取培养目标                                                  |\n+-------------------------------------------------------------------------------------------------------------------+", 0),
                        (f"{get_ts()} | INFO | 识别到副本: ('拟造花萼（赤）', '「世界尽头」酒馆')", 3),
                        (f"{get_ts()} | INFO | 识别到副本: ('历战余响', '铁骸的锈冢')", 2),
                        (f"{get_ts()} | INFO | 沉浸器: 2/12", 2),
                        (f"------------------------------------------------ 准备合成 4 个沉浸器 ------------------------------------------------", 3),
                        (f"{get_ts()} | INFO | 开拓力: 162/300", 2),
                        (f"+-------------------------------------------------------------------------------------------------------------------+\n|                                                   开始每日实训                                                    |\n+-------------------------------------------------------------------------------------------------------------------+", 0),
                        (f"{get_ts()} | INFO | 每日实训已完成", 3),
                        (f"{get_ts()} | INFO | 准备发送 wechatworkapp 通知（级别：全部，图片：是）", 2),
                        (f"{get_ts()} | INFO | wechatworkapp 通知发送完成", 1),
                        (f"{get_ts()} | INFO | 关闭浏览器成功", 2),
                        (f"------------------------------------------------------- 完成 --------------------------------------------------------", 0)
                    ]
                    
                    for line, delay in mock_flow:
                        if not self.running: break
                        log_file.write(f"{line}\n")
                        log_file.flush()
                        if delay > 0:
                            time.sleep(delay)
                    
                    acc_result['success'] = True
                else:
                    # 运行真实的 main.py
                    import sys
                    self.current_process = subprocess.Popen(
                        [sys.executable, 'main.py'],
                        cwd=os.getcwd(),
                        env=env,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8'
                    )
                    self.current_process.wait()
                    acc_result['success'] = (self.current_process.returncode == 0)
        except Exception as e:
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n[WebUI] 执行异常: {e}\n")
            acc_result['success'] = False
        finally:
            acc_result['end_time'] = datetime.now().isoformat()
            # 运行结束，尝试将特定配置回写到账号覆盖配置中
            if os.path.exists(temp_config_path):
                try:
                    with open(temp_config_path, 'r', encoding='utf-8') as f:
                        final_config = yaml.load(f) or {}

                    default_config_path = os.path.join(os.getcwd(), 'assets', 'config', 'config.example.yaml')
                    if os.path.exists(default_config_path):
                        with open(default_config_path, 'r', encoding='utf-8') as f:
                            default_config = yaml.load(f) or {}
                    else:
                        default_config = {}
                    
                    # 定义需要持久化回写的项
                    keys_to_check = [
                        'last_run_timestamp', 
                        'echo_of_war_timestamp', 
                        'asset_self_molding_resin_timestamp',
                        'asset_ember_special_pass_timestamp',
                        'asset_ember_regular_pass_timestamp',
                        'asset_ember_tracks_of_destiny_timestamp',
                        'currencywars_timestamp',
                        'weekly_divergent_timestamp',
                        'universe_timestamp',
                        'divergent_universe_daily_completed_count',
                        'divergent_universe_daily_completed_timestamp',
                        'divergent_universe_weekly_completed_count',
                        'divergent_universe_weekly_completed_timestamp',
                        'already_used_codes',
                        'power_plan'
                    ]
                    # # 自动加入所有以 _timestamp 结尾的键
                    # for k in final_config.keys():
                    #     if k.endswith('_timestamp') and k not in keys_to_check:
                    #         keys_to_check.append(k)
                    
                    # 获取现有的覆盖配置
                    current_override = yaml.load(account.get('config_override') or '') or {}
                    
                    changed_keys = []
                    for key in keys_to_check:
                        if key not in final_config:
                            continue

                        final_value = final_config[key]
                        if key in default_config and final_value == default_config[key]:
                            continue

                        if current_override.get(key) != final_value:
                            current_override[key] = final_value
                            changed_keys.append(key)
                    
                    if changed_keys:
                        from io import StringIO
                        if current_override:
                            stream = StringIO()
                            yaml.dump(current_override, stream)
                            config_override = stream.getvalue()
                        else:
                            config_override = ''
                        account_manager.update_account(account['id'], {'config_override': config_override})
                        
                        # 记录到运行日志中
                        with open(log_path, 'a', encoding='utf-8') as log_file:
                            log_file.write(f"\n[WebUI] 账号运行数据已回写: {', '.join(changed_keys)}\n")
                except Exception as e:
                    print(f"回写账号特定配置失败: {e}")
                    try:
                        with open(log_path, 'a', encoding='utf-8') as log_file:
                            log_file.write(f"\n[WebUI] 回写账号配置失败: {e}\n")
                    except:
                        pass

            self.current_process = None
            # 清理该账号运行可能残留的浏览器进程
            try:
                self._kill_all_m7a_processes()
            except Exception:
                pass
            if os.path.exists(temp_config_path):
                try:
                    os.remove(temp_config_path)
                except:
                    pass

scheduler = Scheduler()
