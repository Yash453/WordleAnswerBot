# WordleAnswerBot
This program uses a combination of statistics and logical filtering to automatically solve the word puzzle game, Wordle.

## Running
- `python main.py` — choose Test Solver, Game Assist, Play Game, or the web UI (Flask, `wordle_ui.py`).
- `docs/index.html` — the same solver in JavaScript for GitHub Pages (no server needed).
- `python -m unittest discover -s tests` — run the tests.

## Entering colors in Assist mode
Assist mode (terminal and web UI) accepts the colors Wordle showed as a code (`GBYBB`, `g b y b b`), emoji squares
(`🟩⬛🟨⬛⬛`), or plain words (`C green, A yellow, rest grey`). Codes and emoji are read in code. Descriptions are read
by TypeSafe (`feedback_parser.py`, one question per tile) when `TYPESAFE_API_KEY` is set; tiles it can't pin down are
flagged for you to set by hand, and the web UI always lets you check the tiles before submitting. The GitHub Pages
version keeps the click-to-set tiles only, since it has no server to hold the API key.

## Word bank
`word_data.csv` holds every word the bot may guess:

| column | meaning |
| --- | --- |
| `words` | five-letter word |
| `answer` | 1 if the word is on the Wordle answer list (the solver and play modes pick answers from these) |
| `commonness` | 0–1 weight from TypeSafe judgments; the bot multiplies each word's letter-frequency score by it |
| `familiar`, `recognized` | the raw TypeSafe judgments behind `commonness` |

The bank adds dictionary words to the answer list so Assist mode can still find answers outside it, and
`commonness` keeps the bot from guessing obscure words. Across all 2,309 answers the bot wins 97.7% of games
(3.98 guesses on average), and 94.8% when the answer is a common word missing from the answer list.

To rebuild the bank (for example with a different dictionary), set `TYPESAFE_API_KEY` and run:

```
python scripts/score_commonness.py --dictionary /usr/share/dict/words
```

Judgments are cached in `.cache/`, so only new words are sent to TypeSafe.
