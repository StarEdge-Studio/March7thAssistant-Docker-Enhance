import types

from utils import dpi


def _set_fake_windll(monkeypatch, *, user32=None, shcore=None):
    fake_windll = types.SimpleNamespace()
    if user32 is not None:
        fake_windll.user32 = user32
    if shcore is not None:
        fake_windll.shcore = shcore
    monkeypatch.setattr(dpi.ctypes, "windll", fake_windll, raising=False)
    monkeypatch.setattr(dpi, "_dpi_awareness_configured", False)


def test_configure_dpi_awareness_prefers_per_monitor_v2(monkeypatch):
    calls = []

    fake_user32 = types.SimpleNamespace(
        SetProcessDpiAwarenessContext=lambda value: calls.append(("context", value)) or 1,
        SetProcessDPIAware=lambda: calls.append(("legacy", None)) or 1,
    )
    fake_shcore = types.SimpleNamespace(
        SetProcessDpiAwareness=lambda value: calls.append(("shcore", value)) or 0,
    )

    _set_fake_windll(monkeypatch, user32=fake_user32, shcore=fake_shcore)

    assert dpi.configure_dpi_awareness(force=True) is True
    assert calls == [("context", dpi.DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)]


def test_configure_dpi_awareness_falls_back_to_shcore(monkeypatch):
    calls = []

    fake_user32 = types.SimpleNamespace(
        SetProcessDpiAwarenessContext=lambda value: calls.append(("context", value)) or 0,
        SetProcessDPIAware=lambda: calls.append(("legacy", None)) or 1,
    )
    fake_shcore = types.SimpleNamespace(
        SetProcessDpiAwareness=lambda value: calls.append(("shcore", value)) or 0,
    )

    _set_fake_windll(monkeypatch, user32=fake_user32, shcore=fake_shcore)

    assert dpi.configure_dpi_awareness(force=True) is True
    assert calls == [
        ("context", dpi.DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2),
        ("shcore", dpi.PROCESS_PER_MONITOR_DPI_AWARE),
    ]


def test_configure_dpi_awareness_falls_back_to_legacy_api(monkeypatch):
    calls = []

    fake_user32 = types.SimpleNamespace(
        SetProcessDPIAware=lambda: calls.append(("legacy", None)) or 1,
    )

    _set_fake_windll(monkeypatch, user32=fake_user32)

    assert dpi.configure_dpi_awareness(force=True) is True
    assert calls == [("legacy", None)]
