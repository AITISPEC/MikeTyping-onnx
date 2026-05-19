import numpy as np
import onnxruntime as ort
from .logger import Logger

logger = Logger("VAD")


class SileroVAD:
    def __init__(
        self,
        model_path: str,
        threshold: float = 0.5,
        sample_rate: int = 16000,
    ):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = 512  # 512 samples for 16kHz

        # Load ONNX model
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"], sess_options=opts
        )

        # Log model inputs for debugging
        for inp in self.session.get_inputs():
            logger.info(f"Model input: {inp.name} {inp.shape}")

        # Validate and detect state size from model inputs
        state_shape = None
        for inp in self.session.get_inputs():
            if inp.name == "state":
                state_shape = inp.shape
                break
        if state_shape is None:
            raise ValueError("Model does not have 'state' input")

        # Typical shape: (2, 1, 64) or (2, 1, 128)
        if len(state_shape) != 3:
            raise ValueError(f"Unexpected state shape: {state_shape}")
        self.state_dim = int(state_shape[2])
        logger.info(f"State dimension: {self.state_dim}")

        self.reset()

    def reset(self):
        """Reset VAD internal state"""
        self._state = np.zeros((2, 1, self.state_dim), dtype=np.float32)
        logger.debug("VAD state reset")

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """Convert to float32 and normalize to [-1, 1]"""
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype == np.int32:
            audio = audio.astype(np.float32) / 2147483648.0
        elif audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Peak normalization if outside [-1,1]
        max_val = np.max(np.abs(audio))
        if max_val > 1e-6 and max_val > 1.0:
            audio = audio / max_val
        return audio

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Возвращает True, если в аудиофрагменте обнаружена речь.
        audio_chunk: 1D array at 16kHz, dtype int16/float32.
        """
        try:
            if audio_chunk.size == 0:
                logger.debug("Empty audio chunk")
                return False

            # Кэшировать нормализацию
            if not hasattr(self, "_cached_normalization"):
                self._cached_normalization = {}

            audio = self._normalize(audio_chunk)
            flat = audio.ravel()
            speech_prob = 0.0
        except Exception as e:
            logger.error(f"is_speech error: {e}")
            return False

        logger.debug(
            f"Input chunk: size={len(flat)}, max={np.max(np.abs(flat)):.6f}, mean={np.mean(np.abs(flat)):.6f}"
        )

        for i in range(0, len(flat), self.chunk_size):
            chunk = flat[i : i + self.chunk_size]
            if len(chunk) < self.chunk_size:
                chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)))

            ort_inputs = {
                "input": chunk.reshape(1, -1).astype(np.float32),
                "state": self._state,
                "sr": np.array(self.sample_rate, dtype=np.int64),
            }
            outputs = self.session.run(None, ort_inputs)
            prob = float(outputs[0].flat[0])
            self._state = outputs[1]  # update hidden state
            speech_prob = max(speech_prob, prob)

        logger.debug(
            f"Max speech probability: {speech_prob:.4f} (threshold={self.threshold})"
        )
        return speech_prob >= self.threshold
