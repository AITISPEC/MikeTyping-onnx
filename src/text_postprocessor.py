# src/text_postprocessor.py
import re
from natasha import Segmenter, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc
from .logger import Logger

logger = Logger("TextPostprocessor")


class TextPostprocessor:
    def __init__(self):
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.syntax_parser = NewsSyntaxParser(self.emb)

    def process(self, text: str, is_final: bool = False) -> str:
        """Основной метод: приводит текст в порядок."""
        if not text or not text.strip():
            return text

        # 1. Анализируем текст
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)

        # 2. Собираем текст обратно
        result_parts = []
        for sent in doc.sents:
            for i, token in enumerate(sent.tokens):
                # Если это не первое слово и текущий токен НЕ знак препинания -> нужен пробел
                if i > 0 and not self._is_punctuation(token.text):
                    result_parts.append(" ")

                result_parts.append(token.text)

        raw_text = "".join(result_parts)

        # 3. Убираем лишние пробелы
        raw_text = re.sub(r"\s+", " ", raw_text).strip()

        # 4. Капитализация первого символа
        if raw_text:
            raw_text = raw_text[0].upper() + raw_text[1:]

        # 5. Точка в конце
        if is_final and raw_text and raw_text[-1] not in ".!?…":
            raw_text += "."

        return raw_text

    @staticmethod
    def _is_punctuation(text: str) -> bool:
        """Проверяет, является ли токен знаком препинания."""
        return text in (".", ",", "!", "?", ";", ":", "…", "(", ")", '"', "'")
