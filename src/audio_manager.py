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

# Глобальные переменные для реально используемых параметров
ACTUAL_SAMPLE_RATE = None
ACTUAL_CHANNELS = None


def set_vad(vad_instance):
	global _vad
	_vad = vad_instance
	logger.debug("VAD instance set")


def is_recording_active():
	return _recording_active


def toggle_recording():
	global _recording_active, _last_toggle_time
	current_time = time.time() * 1000
	if current_time - _last_toggle_time < _TOGGLE_COOLDOWN_MS:
		logger.debug(f"Toggle ignored (cooldown)")
		return
	_last_toggle_time = current_time
	_recording_active = not _recording_active
	winsound.Beep(1000, 200)
	if _recording_active:
		while not audio_queue.empty():
			try:
				audio_queue.get_nowait()
			except queue.Empty:
				break
		if _vad is not None:
			_vad.reset()
		status_active()
	else:
		print()
		status_waiting()


def audio_callback(indata, frames, time, status):
	try:
		if _recording_active and audio_queue.qsize() < MAX_QUEUE_SIZE:
			audio_queue.put(indata.copy())
			logger.debug(f"callback: {frames} frames, shape {indata.shape}")
		elif _recording_active:
			logger.warning("Audio queue overflow!")
	except Exception as e:
		logger.error(f"audio_callback error: {e}")


def start_audio_stream():
	global ACTUAL_SAMPLE_RATE, ACTUAL_CHANNELS

	# 1. Получаем список всех устройств
	all_devices = sd.query_devices()
	input_devices = []
	for i, dev in enumerate(all_devices):
		if dev["max_input_channels"] > 0:
			input_devices.append((i, dev))

	if not input_devices:
		error_msg = (
			"Не найдено ни одного микрофона.\n"
		)
		logger.error(error_msg)
		raise RuntimeError(error_msg)

	# 2. Выбираем первое устройство (можно улучшить: выбрать то, что поддерживает 16000)
	# Для удобства отсортируем: сначала те, у кого есть 16000 Гц в supported_samplerates
	def device_score(dev):
		supported = dev[1].get("supported_samplerates", [])
		return 1 if 16000 in supported else 0

	input_devices.sort(key=device_score, reverse=True)

	device_index, device_info = input_devices[0]
	device_name = device_info["name"]
	max_channels = device_info.get("max_input_channels", 1)
	default_sr = int(device_info.get("default_samplerate", 16000))
	supported_srs = device_info.get("supported_samplerates", [])

	logger.info(f"Выбрано устройство ввода: [{device_index}] {device_name}")
	logger.info(f"  max_input_channels: {max_channels}")
	logger.info(f"  default_samplerate: {default_sr}")
	logger.info(
		f"  supported_samplerates: {supported_srs[:10]}{'...' if len(supported_srs) > 10 else ''}"
	)

	# 3. Определяем количество каналов
	desired_channels = CAPTURE_CHANNELS
	actual_channels = min(desired_channels, max_channels)
	if actual_channels == 0:
		actual_channels = 1
	if actual_channels != desired_channels:
		logger.warning(
			f"Устройство поддерживает только {max_channels} канал(ов). Используем {actual_channels}"
		)

	# 4. Определяем частоту
	desired_sr = SAMPLE_RATE  # 16000
	if desired_sr in supported_srs:
		actual_sr = desired_sr
		logger.info(f"Устройство поддерживает {desired_sr} Гц, используем эту частоту")
	else:
		actual_sr = default_sr
		logger.warning(
			f"Устройство НЕ поддерживает {desired_sr} Гц. Используем default_samplerate = {actual_sr} Гц"
		)
		if actual_sr == 0:
			actual_sr = 16000
			logger.warning("default_samplerate = 0, принудительно 16000 Гц")

	ACTUAL_CHANNELS = actual_channels
	ACTUAL_SAMPLE_RATE = actual_sr

	# 5. Открываем поток
	try:
		stream = sd.InputStream(
			samplerate=actual_sr,
			channels=actual_channels,
			callback=audio_callback,
			blocksize=BLOCK_SIZE,
			device=device_index,  # используем найденный индекс, а не default
		)
		logger.info(
			f"Поток успешно открыт: {actual_channels} канал(ов), {actual_sr} Гц"
		)
		return stream
	except Exception as e:
		logger.error(f"Не удалось открыть поток: {e}")
		raise


def get_audio_chunk(timeout=1.0):
	return audio_queue.get(timeout=timeout)


def setup_hotkey():
	try:
		def on_press(key):
			try:
				if key == HOTKEY:
					toggle_recording()
			except Exception as e:
				logger.error(f"Hotkey error: {e}")

		listener = keyboard.Listener(on_press=on_press)
		listener.daemon = True
		listener.start()
	except Exception as e:
		logger.error(f"Failed to setup hotkey: {e}")


def _stereo_to_mono(audio, channels):
	if channels == 2 and audio.ndim == 2:
		return np.mean(audio, axis=1)
	elif audio.ndim == 1:
		return audio
	else:
		return audio[:, 0] if audio.ndim == 2 else audio


def _resample_audio(audio, orig_sr, target_sr=SAMPLE_RATE):
	if orig_sr == target_sr:
		return audio
	num_samples = int(len(audio) * target_sr / orig_sr)
	resampled = signal.resample(audio, num_samples)
	return resampled.astype(np.float32)


def prepare_for_asr(audio_block):
	try:
		channels = ACTUAL_CHANNELS if ACTUAL_CHANNELS is not None else CAPTURE_CHANNELS
		sample_rate = (
			ACTUAL_SAMPLE_RATE
			if ACTUAL_SAMPLE_RATE is not None
			else CAPTURE_SAMPLE_RATE
		)

		mono = _stereo_to_mono(audio_block, channels)
		if sample_rate != SAMPLE_RATE:
			mono = _resample_audio(mono, sample_rate, SAMPLE_RATE)
			logger.debug(f"Resampled from {sample_rate} to {SAMPLE_RATE}")
		return mono.astype(np.float32)
	except Exception as e:
		logger.error(f"prepare_for_asr error: {e}")
		return np.array([], dtype=np.float32)


def get_available_input_devices():
	"""Возвращает список кортежей (индекс, имя_устройства, max_channels) доступных устройств ввода"""
	devices = []
	all_devices = sd.query_devices()
	for i, dev in enumerate(all_devices):
		if dev["max_input_channels"] > 0:
			devices.append((i, dev["name"], dev["max_input_channels"]))
	return devices
