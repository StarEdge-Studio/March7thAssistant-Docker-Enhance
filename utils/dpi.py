import ctypes


PROCESS_PER_MONITOR_DPI_AWARE = 2
E_ACCESSDENIED = 0x80070005
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

_dpi_awareness_configured = False


def configure_dpi_awareness(force: bool = False) -> bool:
    global _dpi_awareness_configured

    if _dpi_awareness_configured and not force:
        return True

    try:
        user32 = ctypes.windll.user32
    except (AttributeError, OSError):
        user32 = None

    if user32 is not None:
        try:
            if user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2):
                _dpi_awareness_configured = True
                return True
        except (AttributeError, OSError, TypeError, ValueError):
            pass

    try:
        shcore = ctypes.windll.shcore
    except (AttributeError, OSError):
        shcore = None

    if shcore is not None:
        try:
            result = shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
            if result in (0, E_ACCESSDENIED, ctypes.c_long(E_ACCESSDENIED).value):
                _dpi_awareness_configured = True
                return True
        except (AttributeError, OSError, TypeError, ValueError):
            pass

    if user32 is not None:
        try:
            if user32.SetProcessDPIAware():
                _dpi_awareness_configured = True
                return True
        except (AttributeError, OSError, TypeError, ValueError):
            pass

    return False
