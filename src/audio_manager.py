import time
import queue
import numpy as np
import sounddevice as sd
import winsound
from pynput import keyboard
from scipy import signal
from .config import (
    HOTKEY,
    HOTKEY_DEBOUNCE_MS,
    CAPTURE_SAMPLE_RATE,
    CAPTURE_CHANNELS,
    BLOCK_SIZE,
    SAMPLE_RATE,
)
from .console_utils import status_active, status_waiting
from .logger import Logger

logger = Logger("AudioManager")
audio_queue = queue.Queue()
_recording_active = False
_vad = None
MAX_QUEUE_SIZE = 128

_last_toggle_time = 0
_TOGGLE_COOLDOWN_MS = HOTKEY_DEBOUNCE_MS


def set_vad(vad_instance):
    """Устанавливает экземпляр VAD из main.py"""
    global _vad
    _vad = vad_instance
    logger.debug("VAD instance set in audio_manager")


def is_recording_active():
    return _recording_active


def toggle_recording():
    global _recording_active, _last_toggle_time
    # Защита от дребезга
    current_time = time.time() * 1000  # в миллисекундах
    if current_time - _last_toggle_time < _TOGGLE_COOLDOWN_MS:
        logger.debug(
            f"Toggle ignored (cooldown): {current_time - _last_toggle_time:.0f}ms since last"
        )
        return
    _last_toggle_time = current_time

    _recording_active = not _recording_active
    winsound.Beep(1000, 200)
    if _recording_active:
        # Очищаем очередь аудио при старте записи
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except queue.Empty:
                break
        # Сбрасываем VAD, если он есть
        if _vad is not None:
            _vad.reset()
            logger.debug("VAD reset on recording start")
        status_active()
    else:
        print()
        status_waiting()


def audio_callback(indata, frames, time, status):
    try:
        if _recording_active:
            if audio_queue.qsize() < MAX_QUEUE_SIZE:
                audio_queue.put(indata.copy())
                logger.debug(f"callback: {frames} frames, shape {indata.shape}")
            else:
                logger.warning("Audio queue overflow! Dropping chunk.")
    except Exception as e:
        logger.error(f"audio_callback error: {e}")


def start_audio_stream():
    return sd.InputStream(
        samplerate=CAPTURE_SAMPLE_RATE,
        channels=CAPTURE_CHANNELS,
        callback=audio_callback,
        blocksize=BLOCK_SIZE,
    )


def get_audio_chunk(timeout=1.0):
    return audio_queue.get(timeout=timeout)


def setup_hotkey():
    try:

        def on_press(key):
            try:
                if key == HOTKEY:
                    toggle_recording()
            except Exception as e:
                logger.error(f"Hotkey press error: {e}")

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    except Exception as e:
        logger.error(f"Failed to setup hotkey: {e}")


def _stereo_to_mono(audio, channels=CAPTURE_CHANNELS):
    if channels == 2 and audio.ndim == 2:
        return np.mean(audio, axis=1)
    elif audio.ndim == 1:
        return audio
    else:
        return audio[:, 0] if audio.ndim == 2 else audio


def _resample_audio(audio, orig_sr=CAPTURE_SAMPLE_RATE, target_sr=SAMPLE_RATE):
    if orig_sr == target_sr:
        return audio

    num_samples = int(len(audio) * target_sr / orig_sr)

    resampled = signal.resample(audio, num_samples)
    return resampled.astype(np.float32)


def prepare_for_asr(audio_block):
    try:
        mono = _stereo_to_mono(audio_block)
        resampled = _resample_audio(mono)
        return resampled
    except Exception as e:
        logger.error(f"prepare_for_asr error: {e}")
        # возвращаем пустой массив, чтобы не ломать ASR
        return np.array([], dtype=np.float32)
