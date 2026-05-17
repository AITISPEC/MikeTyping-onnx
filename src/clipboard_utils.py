import ctypes
from ctypes import wintypes
import time
from .config import PASTE_DELAY


def paste_via_ctrlv():
	ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
	ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)  # V down
	time.sleep(PASTE_DELAY)
	ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)  # V up
	ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
