# -*- coding: utf-8 -*-
"""
Turn a player's description of Wordle's tile colors into G/Y/B codes.

Exact formats (GBYBB, "g b y b b", emoji squares, "green grey yellow grey grey")
are parsed in code. Anything else ("C is green, A yellow, rest grey") goes to
TypeSafe as one Choice per tile. Tiles the model marks unspecified, or answers
with confidence below MIN_CONFIDENCE, are reported as unclear so the player can
set them by hand instead of the bot acting on a guess.

On a 56-case test set: code alone read 9/48 clear inputs; code + TypeSafe read
43/48 with none wrong, sent 5 back for review, and flagged all 8 ambiguous inputs.
"""

import re

from typesafe_client import TypeSafeError, is_configured, system_one

LETTERS = 5
MIN_CONFIDENCE = 0.5

EMOJI = {"🟩": "G", "🟨": "Y", "⬛": "B", "⬜": "B"}
COLOR_WORDS = {"green": "G", "yellow": "Y", "grey": "B", "gray": "B", "black": "B", "white": "B"}

TILE_CRITERIA = {
    "G": {
        "what": "Green: the letter is in the answer at exactly this position",
        "examples": ["'O is correct' / 'the T is spot on'", "a code like YGBBG where this position's code is G", "'🟩' at this position", "'nailed it' (every tile green)"],
    },
    "Y": {
        "what": "Yellow: the letter is in the answer but at a different position",
        "examples": ["'L is yellow'", "'O is in there but somewhere else'", "'the I is misplaced'", "'🟨' at this position"],
    },
    "B": {
        "what": "Grey/black: the letter is not in the answer",
        "examples": ["'U is grey'", "'no other letters are in it' when this tile is not otherwise mentioned", "'zero hits'", "'⬛' or '⬜' at this position"],
    },
    "unspecified": {
        "what": "The feedback says nothing that determines this tile, and has no catch-all phrase covering the remaining tiles",
        "examples": ["'T is yellow' says nothing about the other letters", "'not sure'", "'like before'"],
    },
}


def parse_exact(text):
    """Parse unambiguous formats in code; returns a list of colors or None."""
    t = text.strip()
    squares = [EMOJI[ch] for ch in t if ch in EMOJI]
    if len(squares) == LETTERS and not re.sub(r"[\s🟩🟨⬛⬜]", "", t):
        return squares
    compact = re.sub(r"[\s,;:/|.\-]", "", t).upper()
    if re.fullmatch(f"[GYB]{{{LETTERS}}}", compact):
        return list(compact)
    tokens = re.findall(r"[a-z]+", t.lower())
    if len(tokens) == LETTERS and all(tok in COLOR_WORDS for tok in tokens):
        return [COLOR_WORDS[tok] for tok in tokens]
    return None


def tile_questions(guess):
    ordinal_hint = " (this letter appears more than once in the guess; use position words like first/second/other to tell them apart)"
    return {
        f"tile_{i}": {
            "type": "choice",
            "instructions": (
                f"`feedback` is how a player described the colors Wordle showed for their guess {guess}. "
                f"Tiles are numbered 1-5 left to right; codes like GBYBB or emoji squares list tiles in that order. "
                f"What color was tile {i + 1}, the letter {guess[i]}"
                + (ordinal_hint if guess.count(guess[i]) > 1 else "")
                + "?"
            ),
            "criteria": TILE_CRITERIA,
        }
        for i in range(LETTERS)
    }


def parse_feedback(guess, text):
    """Read tile colors for `guess` from free-form `text`.

    Returns a dict:
      colors       list of 'G'/'Y'/'B', with None for tiles that could not be read
      unclear      1-based positions the player should check (empty when colors are complete and trusted)
      source       'code', 'typesafe', or None
      error        message when nothing could be read, else None
    """
    guess = str(guess).upper()
    exact = parse_exact(text)
    if exact:
        return {"colors": exact, "unclear": [], "source": "code", "error": None}
    if not is_configured():
        return {"colors": [None] * LETTERS, "unclear": list(range(1, LETTERS + 1)), "source": None,
                "error": "Use a code like GBYBB or emoji squares (set TYPESAFE_API_KEY to describe colors in words)."}

    state = {
        "guess": guess,
        "tiles": [{"position": i + 1, "letter": ch} for i, ch in enumerate(guess)],
        "feedback": text,
    }
    try:
        answers = system_one(state, tile_questions(guess))
    except TypeSafeError as e:
        return {"colors": [None] * LETTERS, "unclear": list(range(1, LETTERS + 1)), "source": None,
                "error": f"Couldn't read the colors right now ({e}). Try a code like GBYBB."}

    colors, unclear = [], []
    for i in range(LETTERS):
        answer = answers[f"tile_{i}"]
        choice = answer["choice"]
        colors.append(None if choice == "unspecified" else choice)
        if choice == "unspecified" or answer["confidence"] < MIN_CONFIDENCE:
            unclear.append(i + 1)
    return {"colors": colors, "unclear": unclear, "source": "typesafe", "error": None}
