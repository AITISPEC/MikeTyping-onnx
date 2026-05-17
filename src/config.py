from pathlib import Path
import sounddevice as sd
from pynput import keyboard as pynput_keyboard

# ========== БАЗОВЫЕ ПУТИ ==========
BASE_DIR = Path(__file__).absolute().parent.parent
MODELS_DIR = BASE_DIR / "models"

# ========== АУДИОПАРАМЕТРЫ ==========
CAPTURE_SAMPLE_RATE = 44100
CAPTURE_CHANNELS = 2
SAMPLE_RATE = 16000
BLOCK_SIZE = 1600
AUDIO_DTYPE = "float32"

# ========== ПАРАМЕТРЫ VAD ==========
ENABLE_VAD = False
VAD_MODEL = MODELS_DIR / "vad.onnx"
VAD_THRESHOLD = 0.5  # порог детекции (0.0-1.0)
VAD_MIN_SPEECH_MS = 250  # минимальная длительность речи в мс
VAD_MIN_SILENCE_MS = 100  # минимальная пауза для разделения фраз в мс
VAD_SPEECH_PAD_MS = 30  # паддинг вокруг речевых сегментов
VAD_PROVIDER = "CPUExecutionProvider"

# ========== ZIPFORMER ASR ==========
ZIPFORMER_RU_PATH = MODELS_DIR / "asr" / "ru"
ZIPFORMER_EN_PATH = MODELS_DIR / "asr" / "en"
ZIPFORMER_PROVIDER = "cpu"
ZIPFORMER_NUM_THREADS = 4
ZIPFORMER_DECODING_METHOD = "greedy_search"

# ========== ВЫВОД ТЕКСТА ==========
AUTO_SPACE = True
PASTE_DELAY = 0.05

# ========== ГОРЯЧАЯ КЛАВИША ==========
HOTKEY = pynput_keyboard.Key.scroll_lock
HOTKEY_DEBOUNCE_MS = 300
AUTO_SWITCH_BY_KEYBOARD_LAYOUT = True

DEBUG = False
