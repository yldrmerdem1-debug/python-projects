import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from textstats import TextStats, words
from textstats.__main__ import main

TEXT = """The crash came on a Tuesday. Nobody saw it coming!
Banks closed, and the banks that stayed open ran out of cash.
Was it greed? It was fear."""


class WordsTest(unittest.TestCase):
    def test_lowercases_skips_numbers_and_keeps_apostrophes(self):
        self.assertEqual(list(words(["Don't panic, 42 times!"])), ["don't", "panic", "times"])

    def test_is_lazy(self):
        stream = words(["one two"])
        self.assertEqual(next(stream), "one")


class TextStatsTest(unittest.TestCase):
    def setUp(self):
        self.stats = TextStats.from_text(TEXT)

    def test_counts(self):
        self.assertEqual(self.stats.word_count, 28)
        self.assertEqual(self.stats.sentence_count, 5)
        self.assertEqual(self.stats.average_sentence_length, 5.6)

    def test_top_words_skip_stopwords_by_default(self):
        self.assertEqual(self.stats.top(2), [("banks", 2), ("crash", 1)])
        self.assertEqual(self.stats.top(1, skip_stopwords=False), [("it", 3)])

    def test_text_without_final_punctuation_is_one_sentence(self):
        stats = TextStats.from_text("no full stop here")
        self.assertEqual(stats.sentence_count, 0)
        self.assertEqual(stats.average_sentence_length, 4.0)

    def test_empty_text(self):
        stats = TextStats.from_text("")
        self.assertEqual((stats.word_count, stats.average_sentence_length, stats.top()), (0, 0.0, []))


class CommandLineTest(unittest.TestCase):
    def test_reports_file_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "article.txt"
            path.write_text(TEXT, encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main([str(path), "--top", "3"])
        self.assertEqual(code, 0)
        report = out.getvalue()
        self.assertIn("words:          28", report)
        self.assertIn("banks", report)


if __name__ == "__main__":
    unittest.main()
