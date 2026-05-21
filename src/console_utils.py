import os
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

TEXT_COLORS = {
	"black": Fore.BLACK,
	"red": Fore.RED,
	"green": Fore.GREEN,
	"yellow": Fore.YELLOW,
	"blue": Fore.BLUE,
	"magenta": Fore.MAGENTA,
	"cyan": Fore.CYAN,
	"white": Fore.WHITE,
	"bright_black": Fore.LIGHTBLACK_EX,
	"bright_red": Fore.LIGHTRED_EX,
	"bright_green": Fore.LIGHTGREEN_EX,
	"bright_yellow": Fore.LIGHTYELLOW_EX,
	"bright_blue": Fore.LIGHTBLUE_EX,
	"bright_magenta": Fore.LIGHTMAGENTA_EX,
	"bright_cyan": Fore.LIGHTCYAN_EX,
	"bright_white": Fore.LIGHTWHITE_EX,
}

STYLES = {
	"bold": Style.BRIGHT,
	"dim": Style.DIM,
	"normal": Style.NORMAL,
}


def cprint(text, color=None, style=None, end="\n", flush=False):
	parts = []
	if style and style in STYLES:
		parts.append(STYLES[style])
	if color and color in TEXT_COLORS:
		parts.append(TEXT_COLORS[color])
	prefix = "".join(parts)
	if prefix:
		print(prefix + text + Style.RESET_ALL, end=end, flush=flush)
	else:
		print(text, end=end, flush=flush)


def success(text, end="\n", flush=False):
	cprint(text, color="green", style="bold", end=end, flush=flush)


def error(text, end="\n", flush=False):
	cprint(text, color="red", style="bold", end=end, flush=flush)


def warning(text, end="\n", flush=False):
	cprint(text, color="yellow", style="bold", end=end, flush=flush)


def info(text, end="\n", flush=False):
	cprint(text, color="cyan", end=end, flush=flush)


def status_active():
	cprint("[СТАТУС] АКТИВНА 🎙️", color="green", style="bold")


def status_waiting():
	cprint("[СТАТУС] ОЖИДАНИЕ ⏸️", color="yellow", style="bold")


def header(title, char="=", length=60, color="bright_cyan", style="bold"):
	line = char * length
	cprint(line, color=color, style=style)
	if len(title) < length - 4:
		title_spaced = f"  {title}  "
		cprint(title_spaced.center(length), color=color, style=style)
	else:
		cprint(title, color=color, style=style)
	cprint(line, color=color, style=style)


def section(title, char="-", length=40, color="bright_blue", style="bold"):
	line = char * length
	cprint(line, color=color, style=style)
	cprint(title, color=color, style=style)
	cprint(line, color=color, style=style)


def print_device_info(device_index, device_name, is_input=True):
	prefix = "🎤 Вход" if is_input else "🔊 Выход"
	cprint(f"{prefix} [{device_index}] - {device_name}", color="magenta")


def print_recognized_text(text, timestamp):
	cprint(f"\n[{timestamp}]", color="bright_black", end=" ")
	cprint(text, color="white", style="bold")


def clear_screen():
	"""Надёжно очищает экран в любой ОС (Windows, Linux, macOS)"""
	os.system("cls" if os.name == "nt" else "clear")


def show_error_dialog(title, message):
	import ctypes

	ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
	import sys

	sys.exit(1)
