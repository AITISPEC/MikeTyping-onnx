import ctypes
import time
from .config import PASTE_DELAY
from .logger import Logger

logger = Logger("Clipboard")


def paste_via_ctrlv():
    try:
        ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)
        time.sleep(PASTE_DELAY)
        ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
    except Exception as e:
        logger.error(f"paste_via_ctrlv failed: {e}")
