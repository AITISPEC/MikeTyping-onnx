import ctypes
import ctypes.wintypes
from .logger import Logger

_layout_logger = Logger("Layout")
_warned_unsupported = False

LAYOUT_RU = 0x419
LAYOUT_EN = 0x409


def get_current_layout_id():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd == 0:
            return LAYOUT_EN  # fallback
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        h_layout = user32.GetKeyboardLayout(thread_id)
        return h_layout & 0xFFFF
    except Exception as e:
        Logger.error(f"get loyout failed: {e}")
        return LAYOUT_EN  # fallback


def get_current_language():
    global _warned_unsupported
    lid = get_current_layout_id()
    if lid == LAYOUT_RU:
        return "ru"
    elif lid == LAYOUT_EN:
        return "en"
    else:
        if not _warned_unsupported:
            _layout_logger.warning(
                f"Обнаружена неподдерживаемая раскладка (ID: {lid:#x}). "
                "Поддерживаются только русская (0x419) и английская (0x409). "
                "Автоматическое переключение языка отключено."
            )
            _warned_unsupported = True
        return None
