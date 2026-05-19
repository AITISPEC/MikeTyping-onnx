# src/show_tokens.py
from natasha import (
    Segmenter,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    MorphVocab,
    Doc,
)


def print_token_table(text):
    segmenter = Segmenter()
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)
    syntax_parser = NewsSyntaxParser(emb)
    morph_vocab = MorphVocab()

    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)

    for sent_idx, sent in enumerate(doc.sents):
        print(f"\n--- Предложение {sent_idx + 1} ---")
        print(
            f"{'№':<3} {'Текст':<12} {'Лемма':<12} {'Часть речи':<8} {'Роль':<10} {'Главное слово (id)':<18}"
        )
        print("-" * 70)
        for token_idx, token in enumerate(sent.tokens):
            token.lemmatize(morph_vocab)
            lemma = token.lemma if token.lemma else "?"
            head_info = token.head_id if hasattr(token, "head_id") else "?"
            print(
                f"{token_idx:<3} {token.text:<12} {lemma:<12} {token.pos:<8} {token.rel:<10} {head_info:<18}"
            )
        print()
