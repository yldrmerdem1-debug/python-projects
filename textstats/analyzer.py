from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import islice

WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")  # letters, with inner apostrophes: don't, o'clock
SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")
STOPWORDS = frozenset(
    "a an and are as at be but by for from has have he her his i in is it its of on or "
    "she that the their they this to was we were will with you".split()
)


def words(lines: Iterable[str]) -> Iterator[str]:
    """Lower-cased words, yielded one at a time so large files are never read into memory at once."""
    for line in lines:
        for match in WORD.finditer(line):
            yield match.group().lower()


@dataclass
class TextStats:
    word_count: int = 0
    sentence_count: int = 0
    frequencies: Counter[str] = field(default_factory=Counter)

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> TextStats:
        stats = cls()
        for line in lines:
            stats.sentence_count += len(SENTENCE_END.findall(line))
            line_words = list(words([line]))
            stats.word_count += len(line_words)
            stats.frequencies.update(line_words)
        return stats

    @classmethod
    def from_text(cls, text: str) -> TextStats:
        return cls.from_lines(text.splitlines())

    @property
    def unique_words(self) -> int:
        return len(self.frequencies)

    @property
    def average_sentence_length(self) -> float:
        # Text without final punctuation still counts as one sentence.
        sentences = self.sentence_count or (1 if self.word_count else 0)
        return round(self.word_count / sentences, 1) if sentences else 0.0

    def top(self, n: int = 10, skip_stopwords: bool = True) -> list[tuple[str, int]]:
        pairs = (
            (word, count)
            for word, count in self.frequencies.most_common()
            if not (skip_stopwords and word in STOPWORDS)
        )
        return list(islice(pairs, n))

    def reading_time_minutes(self, words_per_minute: int = 230) -> float:
        return round(self.word_count / words_per_minute, 1)
