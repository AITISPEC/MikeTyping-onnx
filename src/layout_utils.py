import ctypes
import ctypes.wintypes

LAYOUT_RU = 0x419
LAYOUT_EN = 0x409


def get_current_layout_id():
	user32 = ctypes.windll.user32
	hwnd = user32.GetForegroundWindow()
	if hwnd == 0:
		return LAYOUT_EN  # fallback
	thread_id = user32.GetWindowThreadProcessId(hwnd, None)
	h_layout = user32.GetKeyboardLayout(thread_id)
	return h_layout & 0xFFFF


def get_current_language():
	lid = get_current_layout_id()
	if lid == LAYOUT_RU:
		return "ru"
	elif lid == LAYOUT_EN:
		return "en"
	else:
		return None
