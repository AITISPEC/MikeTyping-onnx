from natasha import (
    Segmenter,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    MorphVocab,
    Doc,
)
from .logger import Logger

logger = Logger("Punctuator")


class Punctuator:
    def __init__(self):
        try:
            self.segmenter = Segmenter()
            self.emb = NewsEmbedding()
            self.morph_tagger = NewsMorphTagger(self.emb)
            self.syntax_parser = NewsSyntaxParser(self.emb)
            self.morph_vocab = MorphVocab()  # Обязательно для лемматизации
            logger.info("Punctuator инициализирован (Natasha загружена)")
        except Exception as e:
            logger.error(f"Ошибка инициализации Punctuator: {e}")
            raise

    def fix(self, text: str) -> str:
        """Вставляет пропущенные запятые, сохраняя исходные пробелы автора."""
        if not text or not text.strip():
            logger.debug("fix получил пустой текст")
            return text

        logger.debug(f"Исходный текст: {text}")

        try:
            doc = Doc(text)
            doc.segment(self.segmenter)
            doc.tag_morph(self.morph_tagger)
            doc.parse_syntax(self.syntax_parser)

            # Собираем индексы токенов (внутри каждого предложения),
            # ПОСЛЕ которых нужно поставить запятую
            commas_after_tokens = set()

            for sent_idx, sent in enumerate(doc.sents):
                logger.debug(
                    f"Обработка предложения {sent_idx + 1}, токенов: {len(sent.tokens)}"
                )

                # Сначала лемматизируем все токены в предложении
                for token in sent.tokens:
                    token.lemmatize(self.morph_vocab)

                for i in range(len(sent.tokens) - 1):
                    token = sent.tokens[i]
                    next_token = sent.tokens[i + 1]

                    # Пропускаем, если после текущего слова уже стоит какой-то знак препинания
                    if next_token.pos == "PUNCT":
                        continue

                    # --- ПРАВИЛО 1: Относительные и подчинительные союзы ---
                    # Перед "который", "что", "чтобы", "если", "когда", "хотя"
                    if next_token.lemma in [
                        "который",
                        "что",
                        "чтобы",
                        "если",
                        "когда",
                        "хотя",
                        "чей",
                        "какой",
                    ]:
                        # Защита: не ставим запятую, если это одиночный союз в роли дополнения без зависимых
                        if next_token.rel in [
                            "nsubj",
                            "nmod",
                            "mark",
                            "advmod",
                            "obj",
                            "back",
                        ]:
                            logger.debug(
                                f"  -> Маркер правила 1 перед: '{next_token.text}'"
                            )
                            commas_after_tokens.add(token.id)
                            continue

                    # --- ПРАВИЛО 2: Противительные союзы ---
                    # Перед "а", "но", "однако", "зато"
                    if next_token.lemma in ["а", "но", "однако", "зато"]:
                        logger.debug(
                            f"  -> Маркер правила 2 перед: '{next_token.text}'"
                        )
                        commas_after_tokens.add(token.id)
                        continue

                    # --- ПРАВИЛО 3: Однородные члены (Перечисление без союзов) ---
                    # Одинаковая роль, одинаковый родитель, оба — значимые части речи
                    if (
                        token.rel == next_token.rel
                        and token.head_id == next_token.head_id
                    ):
                        if (
                            token.pos in ["NOUN", "ADJ", "VERB"]
                            and next_token.lemma != "и"
                        ):
                            logger.debug(
                                f"  -> Маркер правила 3 (однородные): '{token.text}' и '{next_token.text}'"
                            )
                            commas_after_tokens.add(token.id)
                            continue

            # --- СБОРКА ТЕКСТА ПО СИМВОЛЬНЫМ ИНДЕКСАМ ---
            result_parts = []
            last_idx = 0

            # Проходим по всем токенам всего документа
            for sent in doc.sents:
                for token in sent.tokens:
                    # Добавляем кусок оригинального текста (включая авторские пробелы) от конца прошлого токена до начала текущего
                    result_parts.append(text[last_idx : token.start])
                    # Добавляем сам токен
                    result_parts.append(token.text)

                    # Если после этого токена скрипт нашел синтаксическое правило для запятой
                    if token.id in commas_after_tokens:
                        result_parts.append(",")

                    last_idx = token.stop

            # Дописываем хвостик текста, если он остался (например, пробелы в конце строки)
            result_parts.append(text[last_idx:])

            result = "".join(result_parts)
            logger.info(f"Результат punctuator: {result}")
            return result

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            logger.error(f"Ошибка в punctuator.fix: {e}\n{error_details}")
            return text
