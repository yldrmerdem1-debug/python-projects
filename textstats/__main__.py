"""Command line: python -m textstats article.txt --top 15"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import TextStats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="textstats", description="Word and sentence statistics for a text file.")
    parser.add_argument("file", nargs="?", help="text file to analyse (reads standard input when omitted)")
    parser.add_argument("--top", type=int, default=10, help="how many frequent words to list (default 10)")
    parser.add_argument("--all-words", action="store_true", help="keep common words like 'the' in the list")
    args = parser.parse_args(argv)

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            parser.error(f"no such file: {path}")
        with path.open(encoding="utf-8") as handle:
            stats = TextStats.from_lines(handle)
    else:
        stats = TextStats.from_lines(sys.stdin)

    print(f"words:          {stats.word_count}")
    print(f"sentences:      {stats.sentence_count}")
    print(f"unique words:   {stats.unique_words}")
    print(f"avg sentence:   {stats.average_sentence_length} words")
    print(f"reading time:   {stats.reading_time_minutes()} min")
    print("top words:")
    for word, count in stats.top(args.top, skip_stopwords=not args.all_words):
        print(f"  {word:<15}{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
