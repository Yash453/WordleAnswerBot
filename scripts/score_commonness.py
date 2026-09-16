# -*- coding: utf-8 -*-
"""
Build the solver's word bank with a TypeSafe "commonness" weight for every word.

Wordle answers are familiar everyday words, but players (and the Assist mode) can
face answers outside the original answer list. This script widens the bank with a
dictionary's five-letter words, then asks TypeSafe two judgments per word:

  familiar    Score 0-3: how familiar the word is to a typical adult
  recognized  Noul:      would most adults recognize it

commonness = (familiar / 3 + recognized) / 2, in [0, 1]. The solver multiplies each
word's letter-frequency score by it, so obscure words are still candidates but
rarely guessed. Tested over all answers: 96.9% wins with the expanded bank versus
89.8% without the weight, and 93.9% versus 0% on common words missing from the
original answer list.

usage:
    TYPESAFE_API_KEY=... python scripts/score_commonness.py [--dictionary /usr/share/dict/words]

Answers already in word_data.csv (answer=1) stay marked as answers. Judgments are
cached in .cache/commonness.jsonl, so re-running only scores new words.
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from typesafe_client import TypeSafeError, system_one  # noqa: E402

LETTERS = 5
CSV_PATH = os.path.join(ROOT, "word_data.csv")
JSON_PATH = os.path.join(ROOT, "docs", "words.json")
CACHE_PATH = os.path.join(ROOT, ".cache", "commonness.jsonl")

QUESTIONS = {
    "familiar": {
        "type": "score",
        "instructions": "How familiar is the English word in `word` to a typical adult native English speaker today?",
        "criteria": [
            {"what": "Not a word most people have ever seen: archaic, technical, dialect, or a rare variant spelling", "examples": ["ZOEAE", "ULNAE", "KNURL"]},
            {"what": "A real word that many adults would recognize but rarely use", "examples": ["TAPIR", "GLEBE", "VOTIVE"]},
            {"what": "A word most adults know and understand, though not used every day", "examples": ["PLAID", "CRAVE", "ELOPE"]},
            {"what": "An everyday word nearly everyone uses or hears regularly", "examples": ["HOUSE", "WATER", "LAUGH"]},
        ],
    },
    "recognized": {
        "type": "noul",
        "instructions": "Would most adult native English speakers recognize the word in `word` as a word they know?",
    },
}


def load_answers():
    bank = pandas.read_csv(CSV_PATH, dtype={"words": str}, keep_default_na=False)
    if "answer" in bank:
        bank = bank[bank["answer"] == 1]
    return {w.upper() for w in bank["words"] if len(w) == LETTERS}


def load_dictionary(path):
    with open(path) as f:
        return {w.strip().upper() for w in f
                if len(w.strip()) == LETTERS and w.strip().isalpha() and w.strip().isascii() and w.strip().islower()}


def load_cache():
    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            for line in f:
                record = json.loads(line)
                cache[record["word"]] = record
    return cache


def score_word(word):
    answers = system_one({"word": word}, QUESTIONS)
    return {"word": word, "familiar": answers["familiar"]["score"], "recognized": answers["recognized"]["noul"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dictionary", default="/usr/share/dict/words",
                        help="newline-separated word list to add (lowercase entries only; capitalized names are skipped)")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    answers = load_answers()
    words = sorted(answers | load_dictionary(args.dictionary))
    cache = load_cache()
    todo = [w for w in words if w not in cache]
    print(f"{len(words)} words ({len(answers)} answers); {len(todo)} need scoring")

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    failures = []
    with open(CACHE_PATH, "a") as out, ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(score_word, w): w for w in todo}
        for n, future in enumerate(as_completed(futures), 1):
            try:
                record = future.result()
            except TypeSafeError as e:
                failures.append((futures[future], str(e)))
                continue
            cache[record["word"]] = record
            out.write(json.dumps(record) + "\n")
            if n % 500 == 0:
                out.flush()
                print(f"  {n}/{len(todo)}")
    if failures:
        print(f"{len(failures)} words failed (re-run to retry), e.g. {failures[0]}")
        sys.exit(1)

    rows = []
    for w in words:
        c = cache[w]
        commonness = (c["familiar"] / 3 + c["recognized"]) / 2
        rows.append({"words": w.lower(), "answer": int(w in answers), "commonness": round(commonness, 3),
                     "familiar": round(c["familiar"], 2), "recognized": round(c["recognized"], 2)})
    pandas.DataFrame(rows).to_csv(CSV_PATH, index=False, lineterminator="\r\n")

    with open(JSON_PATH, "w") as f:
        json.dump({"answers": sorted(answers), "words": {r["words"].upper(): r["commonness"] for r in rows}},
                  f, separators=(",", ":"))
    print(f"wrote {CSV_PATH} and {JSON_PATH}")


if __name__ == "__main__":
    main()
