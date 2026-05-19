from pathlib import Path
from pynput import keyboard as pynput_keyboard

# ========== БАЗОВЫЕ ПУТИ ==========
BASE_DIR = Path(__file__).absolute().parent.parent
MODELS_DIR = BASE_DIR / "models"
RU_MODEL = MODELS_DIR / "asr" / "ru"
EN_MODEL = MODELS_DIR / "asr" / "en"

# ========== АУДИОПАРАМЕТРЫ ==========
CAPTURE_SAMPLE_RATE = 44100
CAPTURE_CHANNELS = 2
SAMPLE_RATE = 16000
BLOCK_SIZE = 3528
AUDIO_DTYPE = "float32"

# ========== ПАРАМЕТРЫ VAD ==========
ENABLE_VAD = False
VAD_MODEL = RU_MODEL / "vad.onnx"
VAD_THRESHOLD = 0.00075  # порог детекции (0.0-1.0)
VAD_MIN_SPEECH_MS = 250  # минимальная длительность речи в мс
VAD_MIN_SILENCE_MS = 100  # минимальная пауза для разделения фраз в мс
VAD_SPEECH_PAD_MS = 30  # паддинг вокруг речевых сегментов
VAD_PROVIDER = "CPUExecutionProvider"

# ========== ZIPFORMER ASR ==========
ZIPFORMER_RU_PATH = RU_MODEL
ZIPFORMER_EN_PATH = EN_MODEL
ZIPFORMER_PROVIDER = "cpu"
ZIPFORMER_NUM_THREADS = 4
ZIPFORMER_DECODING_METHOD = "greedy_search"

# ========== ВЫВОД ТЕКСТА ==========
AUTO_SPACE = True
PASTE_DELAY = 0.05

# ========== HOTWORDS (контекстное усиление) ==========
USE_HOTWORDS = True
HOTWORDS_SCORE = 1.5  # вес (1.0–3.0)
HOTWORDS_RU_FILE = RU_MODEL / "hotwords.txt"
BPE_VOCAB_RU_FILE = RU_MODEL / "bpe.vocab"

# ========== ПОСТОБРАБОТКА ТЕКСТА ==========
USE_TEXT_POSTPROCESSING = True  # включает лемматизацию, капитализацию и точку в конце

# ========== ГОРЯЧАЯ КЛАВИША ==========
HOTKEY = pynput_keyboard.Key.scroll_lock
HOTKEY_DEBOUNCE_MS = 300
AUTO_SWITCH_BY_KEYBOARD_LAYOUT = True

DEBUG = False
LOGS_DIR = BASE_DIR / "logs"
