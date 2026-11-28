"""使用 Redmi 实机 HUD 片段，沿任务、截图、识别和 ADB 输入调用链注入故障。"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from PIL import Image
import numpy as np
import pytest

from module.automation import automation
from module.automation.adb_input import AdbInput
from module.config import cfg
from module.config.platform import get_ui_profile, pin_game_connection
from module.game import adb as adb_module
from module.game.adb import AdbGameController
from module.game.adb_transport import AdbError
from tasks.touch import power
from utils.pause import RunStopRequested, pause_guard


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "touch_auto_battle"


class BattleScene:
    def __init__(self):
        self.now = 0.0
        self.inputs = []
        self.captures = 0
        self.accepted_at = None
        self.ignored_taps = 0
        self.ack_delay = 0.5
        self.ack_error = False
        self.frame_error = None
        self.frame_fail_until = 0.0
        self.ocr_failures = 0
        self.auto_running = False
        self.auto_unreadable = False
        self.off_unreadable = True
        self.false_after_confirm = False
        self.disable_at = float("inf")
        self.moving = False
        self.no_commands = False
        self.lose_pause = False
        self.stop_at = float("inf")
        self.in_tap = False
        self.expire_in_tap = False
        self.stop_in_tap = False
        self.lookup_failure = False
        self.kind = "manual"
        self.end = None
        self.images = {}
        for name in ("manual", "auto", "auto-animation", "off-action"):
            with Image.open(FIXTURES / f"{name}.png") as image:
                self.images[name] = image.convert("RGB")

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    def check_stop(self):
        if self.now >= self.stop_at:
            raise RunStopRequested()

    def capture_frame(self, crop=(0, 0, 1, 1), **_kwargs):
        self.captures += 1
        self.now += 0.015
        if self.in_tap:
            if self.stop_in_tap:
                self.stop_at = self.now
            if self.lookup_failure:
                self.lookup_failure = False
                raise RuntimeError("一次截图失败，进入截图内部重试")
            if self.expire_in_tap:
                self.now += 60
        if self.frame_error and self.now < self.frame_fail_until:
            raise AdbError(self.frame_error, "注入取帧故障")
        enabled = (self.auto_running and self.now < self.disable_at) or (
            self.accepted_at is not None and self.now >= self.accepted_at + self.ack_delay
        )
        victory = enabled and self.now >= (self.accepted_at or 0) + self.ack_delay + (18 if self.moving else 3)
        self.kind = "auto-animation" if self.moving else "auto" if enabled else "manual"
        if self.no_commands:
            self.kind = "off-action"
        frame = self.images[self.kind].copy()
        if self.moving:
            # 原生自动战斗中指令也会短暂显示，但行动角色、血条会推进。
            progress = int(self.now // 2) % 2
            turn = self.images["manual" if progress else "auto"].crop((48, 65, 145, 112))
            frame.paste(turn, (48, 65))
            health = self.images["manual" if progress else "auto"].crop((430, 62, 843, 69))
            frame.paste(health, (430, 62))
        if self.lose_pause:
            frame.paste((0, 0, 0), (1205, 20, 1255, 60))
        if victory:
            frame = Image.new("RGB", (1280, 720))
            with Image.open(f"{power.IMAGES}/victory.png") as title:
                frame.paste(title.convert("RGB"), (520, 100))
        left, top = int(crop[0] * 1280), int(crop[1] * 720)
        width, height = int(crop[2] * 1280), int(crop[3] * 720)
        return frame.crop((left, top, left + width, top + height)), (left, top, width, height), 1

    def request(self, command, **params):
        assert command == "tap"
        self.check_stop()
        self.inputs.append((self.now, params["x"], params["y"]))
        if len(self.inputs) > self.ignored_taps and self.accepted_at is None:
            self.accepted_at = self.now
        if self.ack_error:
            self.ack_error = False
            raise AdbError("frame_clock_unavailable", "输入已送达，回执暂不可读")
        return {"delivered": True, "input_ns": int(self.now * 1e9)}, b""

    def recognize(self, pixels, **_kwargs):
        if pixels.shape[:2] != (175, 250):
            return []
        if self.ocr_failures:
            self.ocr_failures -= 1
            raise RuntimeError("一次文字识别失败")
        if self.kind not in ("manual", "auto-animation"):
            return []
        return [
            ([(40, 145), (90, 145), (90, 168), (40, 168)], ("单攻", 0.999)),
            ([(155, 56), (205, 56), (205, 80), (155, 80)], ("强化", 0.999)),
        ]


@pytest.fixture
def battle_scene(monkeypatch):
    scene = BattleScene()
    monkeypatch.setattr(power, "time", scene)
    monkeypatch.setattr(automation, "time", scene)
    monkeypatch.setattr(adb_module, "time", scene)
    monkeypatch.setattr(power.pause_ctl, "checkpoint", scene.check_stop)
    monkeypatch.setattr(power.pause_ctl, "check_stop", scene.check_stop)
    monkeypatch.setattr(power, "game_option_enabled", lambda *_: True)
    monkeypatch.setattr(power, "ENTRY_TIMEOUT", 20)
    monkeypatch.setattr(power, "BATTLE_TIMEOUT", 55)
    monkeypatch.setattr(automation.ocr, "recognize_multi_lines", scene.recognize)
    monkeypatch.setattr(power.log, "warning", Mock())

    controller = AdbGameController(SimpleNamespace(), logger=Mock())
    controller._service = SimpleNamespace(request=scene.request)
    controller._display_id = controller._game_display_id = 2
    controller._watching = True
    monkeypatch.setattr(controller, "_poll_events", lambda **_: None)
    monkeypatch.setattr(controller, "capture_frame", scene.capture_frame)
    monkeypatch.setattr("module.game.get_game_controller", lambda *_: controller)
    inputs = AdbInput(controller)
    auto = object.__new__(automation.Automation)
    auto.window_title = "offline-android-battle"
    auto.logger = Mock()
    auto.input_handler = inputs
    auto.mouse_click = pause_guard(inputs.mouse_click)
    auto.screenshot = None
    auto.img_cache = {}
    monkeypatch.setattr(power, "auto", auto)
    monkeypatch.setattr(auto, "_is_debug_enabled", lambda: False)

    original_tap = power._tap

    def tap(*args):
        scene.in_tap = True
        try:
            return original_tap(*args)
        finally:
            scene.in_tap = False

    monkeypatch.setattr(power, "_tap", tap)
    original_wait = power._wait_battle

    def wait(**kwargs):
        try:
            result = original_wait(**kwargs)
            scene.end = "victory"
            return result
        except BaseException as error:
            scene.end = f"{type(error).__name__}: {error}"
            raise

    monkeypatch.setattr(power, "_wait_battle", wait)
    classify = power.classify_auto_button

    def classify_with_fault(pixels, glyph):
        status = classify(pixels, glyph)
        if scene.false_after_confirm and scene.now >= 0.6:
            return False
        if scene.auto_unreadable or (status is False and scene.off_unreadable):
            return None
        return status

    monkeypatch.setattr(power, "classify_auto_button", classify_with_fault)
    profile = get_ui_profile(SimpleNamespace(ui_profile="touch_720"))
    with pin_game_connection(cfg, connection=("adb", profile)):
        yield scene


@pytest.mark.parametrize("repeated", [False, True])
def test_battle_flow_recovers_an_unreadable_button(battle_scene, repeated):
    power._wait_battle(repeated=repeated)
    assert len(battle_scene.inputs) == 1
    assert battle_scene.inputs[0][1:] == (1147, 40)
    assert 9 <= battle_scene.inputs[0][0] < 13


def test_battle_flow_keeps_the_fast_path_for_a_readable_off_button(battle_scene):
    battle_scene.off_unreadable = False
    power._wait_battle()
    assert len(battle_scene.inputs) == 1
    assert battle_scene.inputs[0][0] < 2


@pytest.mark.parametrize("fault", ["frame_timeout", "frame_clock_unavailable", "ocr", "input_receipt"])
def test_battle_flow_recovers_local_failures(battle_scene, fault):
    if fault in ("frame_timeout", "frame_clock_unavailable"):
        battle_scene.frame_error = fault
        battle_scene.frame_fail_until = 2
    elif fault == "ocr":
        battle_scene.ocr_failures = 1
    else:
        battle_scene.ack_error = True
    power._wait_battle()
    assert len(battle_scene.inputs) == 1


@pytest.mark.parametrize("delay", [0.5, 4, 8])
def test_battle_flow_waits_for_a_late_receipt(battle_scene, delay):
    battle_scene.ack_delay = delay
    power._wait_battle()
    assert len(battle_scene.inputs) == 1


def test_battle_flow_retries_a_confirmed_missed_tap(battle_scene):
    battle_scene.ignored_taps = 1
    power._wait_battle()
    assert len(battle_scene.inputs) == 2
    assert battle_scene.inputs[1][0] - battle_scene.inputs[0][0] >= 11


def test_battle_flow_reports_persistent_input_failure(battle_scene):
    battle_scene.ignored_taps = 100
    with pytest.raises(power.PowerError, match="已中断本场挑战"):
        power._wait_battle()
    assert len(battle_scene.inputs) == 3


def test_battle_flow_does_not_toggle_unknown_automatic_animations(battle_scene):
    battle_scene.auto_running = True
    battle_scene.auto_unreadable = True
    battle_scene.moving = True
    power._wait_battle()
    assert battle_scene.inputs == []


def test_battle_flow_does_not_toggle_a_confirmed_enabled_button(battle_scene):
    battle_scene.auto_running = True
    power._wait_battle()
    assert battle_scene.inputs == []


def test_battle_flow_rechecks_a_gray_frame_after_confirming_auto(battle_scene):
    battle_scene.auto_running = True
    battle_scene.false_after_confirm = True
    power._wait_battle()
    assert battle_scene.inputs == []


def test_battle_flow_can_restore_auto_after_an_earlier_confirmation(battle_scene):
    battle_scene.auto_running = True
    battle_scene.disable_at = 2
    power._wait_battle()
    assert len(battle_scene.inputs) == 1


def test_battle_flow_does_not_guess_without_manual_commands(battle_scene):
    battle_scene.no_commands = True
    with pytest.raises(power.PowerError, match="等待战斗结算超时"):
        power._wait_battle()
    assert battle_scene.inputs == []


@pytest.mark.parametrize("fault", ["deadline", "stop", "lookup_retry_deadline"])
def test_battle_flow_stops_before_dispatch_after_lookup(battle_scene, fault):
    battle_scene.off_unreadable = False
    if fault == "stop":
        battle_scene.stop_in_tap = True
        expected = RunStopRequested
    else:
        battle_scene.expire_in_tap = True
        battle_scene.lookup_failure = fault == "lookup_retry_deadline"
        expected = power.PowerError
    with pytest.raises(expected):
        power._wait_battle()
    assert battle_scene.inputs == []


@pytest.mark.parametrize("ignored", [0, 100])
def test_battle_flow_standalone_reports_the_real_result(battle_scene, monkeypatch, ignored):
    from tasks.touch import daily

    battle_scene.ignored_taps = ignored
    monkeypatch.setattr(daily, "support_demand", lambda: power.SupportDemand())
    monkeypatch.setattr(power, "_run", lambda *_args: power._wait_battle() or True)
    error = Mock()
    monkeypatch.setattr(power.log, "error", error)
    assert power.run_standalone() is (ignored == 0)
    if ignored:
        assert "已中断本场挑战" in error.call_args.args[0]


def test_battle_flow_reports_continuous_frame_failure(battle_scene):
    battle_scene.frame_error = "frame_timeout"
    battle_scene.frame_fail_until = 100
    with pytest.raises(AdbError, match="注入取帧故障"):
        power._wait_battle()
    assert battle_scene.inputs == []
    assert battle_scene.now < 17


def test_battle_flow_honors_stop_while_observing(battle_scene):
    battle_scene.stop_at = 4
    with pytest.raises(RunStopRequested):
        power._wait_battle()
    assert battle_scene.inputs == []


def test_battle_flow_can_use_the_speed_hud_when_pause_is_unreadable(battle_scene):
    battle_scene.lose_pause = True
    power._wait_battle()
    assert len(battle_scene.inputs) == 1


@pytest.mark.parametrize("sample,expected", [("manual", False), ("auto", True), ("off-action", False)])
def test_recorded_auto_button_states(sample, expected):
    with Image.open(FIXTURES / f"{sample}.png") as frame, Image.open(f"{power.IMAGES}/auto_glyph.png") as mask:
        pixels = np.asarray(frame.convert("RGB"))[27:52, 1128:1169]
        glyph = np.asarray(mask.convert("L")) > 0
    assert power.classify_auto_button(pixels, glyph) is expected


def test_recorded_special_turn_glow_does_not_look_like_progress():
    with Image.open(FIXTURES / "manual-special.png") as first, Image.open(FIXTURES / "manual-special-pulse.png") as second:
        assert power._same_turn(power._battle_progress(first), power._battle_progress(second))


def test_changed_action_values_are_progress_even_when_enemy_health_is_unchanged():
    with Image.open(FIXTURES / "manual-special.png") as source:
        first = source.convert("RGB")
    second = first.copy()
    for y in (130, 179, 228, 277):
        second.paste(first.crop((98, 326, 120, 342)), (98, y))
    assert not power._same_turn(power._battle_progress(first), power._battle_progress(second))
