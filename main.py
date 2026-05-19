import sys

try:
    import pymorphy3

    # Подменяем модуль в кэше Python, чтобы Natasha думала, что импортирует pymorphy2
    sys.modules["pymorphy2"] = pymorphy3
except ImportError:
    pass

import os
import time
import queue
import threading
import pyperclip
import numpy as np
import sounddevice as sd
import winsound

from src.config import (
    HOTKEY,
    AUTO_SPACE,
    AUTO_SWITCH_BY_KEYBOARD_LAYOUT,
    ZIPFORMER_RU_PATH,
    ZIPFORMER_EN_PATH,
    ENABLE_VAD,
    VAD_MODEL,
    VAD_THRESHOLD,
    USE_HOTWORDS,
    HOTWORDS_RU_FILE,
    HOTWORDS_SCORE,
    BPE_VOCAB_RU_FILE,
    DEBUG,
)

from src.config import USE_TEXT_POSTPROCESSING
from src.clipboard_utils import paste_via_ctrlv
from src.asr_manager import ZipformerASR
from src import audio_manager
import src.layout_utils as layout_utils
from src.console_utils import (
    header,
    info,
    error,
    print_device_info,
    print_recognized_text,
    cprint,
    clear_screen,
)
from src.logger import Logger

logger = Logger("Main")
clear_screen()

# VAD (если включён)
if ENABLE_VAD:
    try:
        from src.vad_ov import SileroVAD
    except ImportError:
        error("Модуль VAD не найден, VAD отключён")
        ENABLE_VAD = False


def print_diagnostics():
    header("ДИАГНОСТИКА АУДИО", length=50)
    try:
        cprint(f"Индексы устройств: {sd.default.device}", color="yellow")
        default_input = sd.default.device[0]
        input_info = sd.query_devices(default_input)
        print_device_info(default_input, input_info["name"], is_input=True)
        default_output = sd.default.device[1]
        output_info = sd.query_devices(default_output)
        print_device_info(default_output, output_info["name"], is_input=False)
    except Exception as e:
        error(f"Ошибка: {e}")
    print()


def main():
    print_diagnostics()
    info("Загрузка Zipformer ASR (русская модель)...")
    try:
        asr_ru = ZipformerASR(
            ZIPFORMER_RU_PATH,
            "ru",
            use_hotwords=USE_HOTWORDS,
            hotwords_file=HOTWORDS_RU_FILE if USE_HOTWORDS else None,
            hotwords_score=HOTWORDS_SCORE,
            bpe_vocab=BPE_VOCAB_RU_FILE if USE_HOTWORDS else None,
        )
    except Exception as e:
        error(f"Не удалось загрузить русскую модель: {e}")
        return

    info("Загрузка Zipformer ASR (английская модель)...")
    try:
        asr_en = ZipformerASR(
            ZIPFORMER_EN_PATH,
            "en",
            use_hotwords=False,
        )
    except Exception as e:
        error(f"Не удалось загрузить английскую модель: {e}")
        return

    current_asr = asr_ru
    current_lang = "ru"
    asr_lock = threading.Lock()
    info("Модели загружены.")

    vad = None
    if ENABLE_VAD:
        try:
            vad = SileroVAD(VAD_MODEL, threshold=VAD_THRESHOLD)
            info("VAD загружен (onnxruntime)")
            audio_manager.set_vad(vad)
        except Exception as e:
            error(f"Ошибка VAD: {e}. VAD отключён")

    punctuator = None
    text_postprocessor = None
    if USE_TEXT_POSTPROCESSING:
        try:
            from src.text_postprocessor import TextPostprocessor
            from src.show_tokens import print_token_table as ptt
            from src.punctuator import Punctuator

            punctuator = Punctuator()
            text_postprocessor = TextPostprocessor()
            info("Модуль постобработки текста загружен")
        except Exception as e:
            error(f"Не удалось загрузить модуль постобработки: {e}")

    audio_manager.setup_hotkey()
    cprint(
        f"\n🎤 Нажмите {HOTKEY} для старта/паузы. Ctrl+C выход.\n", color="bright_white"
    )

    last_full_text = ""
    prev_recording_active = False

    winsound.Beep(800, 200)
    time.sleep(0.1)
    winsound.Beep(1200, 300)

    # Путь к папке logs рядом с файлом main.py
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)  # Создаем папку, если её нет

    # Создаем файл-маркер готовности
    open(os.path.join(log_dir, "asr_ready.tmp"), "w").close()

    logger.info("Entering main loop")
    try:
        with audio_manager.start_audio_stream():
            while True:
                recording_active = audio_manager.is_recording_active()

                if not prev_recording_active and recording_active:
                    last_full_text = ""
                    logger.debug("Recording started, state reset")

                # Финализация при остановке записи – только здесь вставляем текст
                if prev_recording_active and not recording_active:
                    with asr_lock:
                        final_text = current_asr.finalize()
                    if final_text and final_text.strip():
                        final = final_text.strip()
                        if final:
                            try:
                                # Применяем постобработку, если она включена
                                if text_postprocessor and current_lang == "ru":
                                    final = punctuator.fix(final)
                                    original = final
                                    final = text_postprocessor.process(
                                        final, is_final=True
                                    )
                                    logger.debug(
                                        f"Постобработка: '{original}' -> '{final}'"
                                    )
                                    if DEBUG and final != "":
                                        ptt(final)
                            except Exception as e:
                                logger.error(f"Text processing ERROR: '{e}'")

                            final_with_space = final + (" " if AUTO_SPACE else "")
                            pyperclip.copy(final_with_space)
                            paste_via_ctrlv()
                            print_recognized_text(final, time.strftime("%H:%M:%S"))
                            logger.info(f"Final pasted: '{final}'")
                    last_full_text = ""

                prev_recording_active = recording_active

                if recording_active:
                    # Автоопределение языка по раскладке
                    if AUTO_SWITCH_BY_KEYBOARD_LAYOUT:
                        detected_lang = layout_utils.get_current_language()
                        if detected_lang == "ru" and current_lang != "ru":
                            with asr_lock:
                                current_asr = asr_ru
                                current_lang = "ru"
                                current_asr.reset()
                                last_full_text = ""
                            cprint("   [ЯЗЫК: РУССКИЙ]", color="bright_green")
                        elif detected_lang == "en" and current_lang != "en":
                            with asr_lock:
                                current_asr = asr_en
                                current_lang = "en"
                                current_asr.reset()
                                last_full_text = ""
                            cprint("   [ЯЗЫК: ENGLISH]", color="bright_cyan")

                    try:
                        raw_block = audio_manager.get_audio_chunk(timeout=1.0)
                    except queue.Empty:
                        continue

                    prepared = audio_manager.prepare_for_asr(raw_block)

                    # Шумоподавление и TE полностью удалены

                    if ENABLE_VAD and vad is not None and current_lang == "ru":
                        if not vad.is_speech(prepared):
                            logger.debug("VAD decision: False, skipping")
                            continue
                        else:
                            logger.debug("VAD decision: True")
                    else:
                        max_val = np.max(np.abs(prepared))
                        if max_val > 1e-6:
                            prepared = prepared / max_val

                    with asr_lock:
                        new_text = current_asr.process_chunk(prepared)

                    # Показываем промежуточный результат, но не вставляем
                    if new_text and new_text != last_full_text:
                        processed_interim = new_text
                        if text_postprocessor:
                            processed_interim = text_postprocessor.process(new_text)
                        cprint(
                            f"\r   [РАСПОЗНАЁТСЯ] {processed_interim}",
                            color="bright_black",
                            end="",
                            flush=True,
                        )
                        logger.debug(f"Interim result: '{processed_interim}'")
                        last_full_text = new_text

                    time.sleep(0.01)
                else:
                    cprint("\r" + " " * 80 + "\r", end="", flush=True)
                    time.sleep(0.05)

    except KeyboardInterrupt:
        with asr_lock:
            current_asr.finalize()
        print("\nВыход.")
        logger.info("Application terminated")


if __name__ == "__main__":
    main()
