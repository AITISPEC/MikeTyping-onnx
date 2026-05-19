import sherpa_onnx
import numpy as np
from pathlib import Path
import os
from .config import (
    ZIPFORMER_PROVIDER,
    ZIPFORMER_NUM_THREADS,
    ZIPFORMER_DECODING_METHOD,
)
from .logger import Logger

logger = Logger("ASR")


def _check_model_files(model_path: Path):
    """Проверка наличия всех файлов модели"""
    required = ["encoder.onnx", "decoder.onnx", "joiner.onnx", "tokens.txt"]
    missing = [f for f in required if not (model_path / f).is_file()]
    if missing:
        raise FileNotFoundError(f"Отсутствуют файлы: {', '.join(missing)}")


class ZipformerASR:
    def __init__(
        self,
        model_path: Path,
        lang: str = "ru",
        provider: str = ZIPFORMER_PROVIDER,
        num_threads: int = ZIPFORMER_NUM_THREADS,
        decoding_method: str = ZIPFORMER_DECODING_METHOD,
        use_hotwords: bool = False,
        hotwords_file: Path = None,
        hotwords_score: float = 1.0,
        bpe_vocab: Path = None,
    ):
        self.lang = lang
        model_path = Path(model_path).resolve()

        _check_model_files(model_path)

        encoder_path = os.path.normpath(os.fspath(model_path / "encoder.onnx"))
        decoder_path = os.path.normpath(os.fspath(model_path / "decoder.onnx"))
        joiner_path = os.path.normpath(os.fspath(model_path / "joiner.onnx"))
        tokens_path = os.path.normpath(os.fspath(model_path / "tokens.txt"))

        logger.info("Loading " + lang.upper() + " ASR model from " + str(model_path))

        if lang == "en":
            use_hotwords = False
            hotwords_file = None
            bpe_vocab = None
            if decoding_method == "modified_beam_search":
                decoding_method = "greedy_search"

        kwargs = {
            "encoder": encoder_path,
            "decoder": decoder_path,
            "joiner": joiner_path,
            "tokens": tokens_path,
            "decoding_method": decoding_method,
            "num_threads": num_threads,
            "sample_rate": 16000,
            "feature_dim": 80,
            "provider": provider,
        }

        # Загрузка BPE
        if use_hotwords and hotwords_file and hotwords_file.is_file():
            kwargs["hotwords_file"] = str(hotwords_file)
            kwargs["hotwords_score"] = hotwords_score
            if bpe_vocab and bpe_vocab.is_file():
                kwargs["bpe_vocab"] = str(bpe_vocab)
                kwargs["modeling_unit"] = "bpe"
                kwargs["decoding_method"] = "modified_beam_search"

                logger.info(
                    f"Hotwords enabled: {hotwords_file}, score={hotwords_score}"
                )
            else:
                logger.warning("bpe_vocab not found, hotwords disabled")

        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(**kwargs)
        self.stream = None
        self.reset()
        logger.info(lang.upper() + " ASR model loaded")

    def reset(self):
        try:
            if self.stream is not None:
                del self.stream
            self.stream = self.recognizer.create_stream()
            logger.debug("ASR stream reset")
        except Exception as e:
            logger.error(f"reset error: {e}")
            self.stream = None  # чтобы дальше не крашилось

    def _ensure_float32(self, audio: np.ndarray) -> np.ndarray:
        if audio.dtype == np.int16:
            return audio.astype(np.float32) / 32768.0
        if audio.dtype == np.int32:
            return audio.astype(np.float32) / 2147483648.0
        return audio.astype(np.float32) if audio.dtype != np.float32 else audio

    def process_chunk(self, audio_chunk: np.ndarray) -> str:
        if audio_chunk.size == 0:
            return ""
        logger.debug(
            "Process chunk: size="
            + str(audio_chunk.size)
            + ", max="
            + str(np.max(np.abs(audio_chunk)))
        )
        try:
            self.stream.accept_waveform(16000, self._ensure_float32(audio_chunk))
            iter_count = 0
            while self.recognizer.is_ready(self.stream) and iter_count < 100:
                self.recognizer.decode_stream(self.stream)
                iter_count += 1
            result = self.recognizer.get_result(self.stream)
            if result:
                logger.info("ASR output: '" + result + "'")
            return result if result else ""
        except Exception as e:
            logger.error("process_chunk error: " + str(e))
            self.reset()
            return ""

    def finalize(self) -> str:
        try:
            self.stream.input_finished()
            iter_count = 0
            while self.recognizer.is_ready(self.stream) and iter_count < 100:
                self.recognizer.decode_stream(self.stream)
                iter_count += 1
            result = self.recognizer.get_result(self.stream)
            text = result if result else ""
            logger.debug("Finalize result: '" + text + "'")
            self.reset()
            return text
        except Exception as e:
            logger.error("finalize error: " + str(e))
            self.reset()
            return ""
