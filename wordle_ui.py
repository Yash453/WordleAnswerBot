# -*- coding: utf-8 -*-
"""
Wordle Solver & Assist – Web UI (Flask)
@author: Yash
"""

import os
import random

from flask import Flask, request, jsonify, send_from_directory
import pandas

from prediction_bot import Bot
from wordle_game import Game

# ── Constants ───────────────────────────────────────────────────────────
ROWS = 6
LETTERS = 5
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "word_data.csv")


def load_word_bank():
    w_bank = pandas.read_csv(CSV_PATH)
    w_bank = w_bank[w_bank["words"].str.len() == LETTERS]
    w_bank["words"] = w_bank["words"].str.upper()
    return w_bank


# ── Flask App ───────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static")

# In-memory session state (single-user local tool)
_assist_state = {}


def _reset_assist():
    """Create a fresh assist session."""
    game = Game(None, rows=ROWS, letters=LETTERS)
    bot = Bot(game, filename=CSV_PATH)
    _assist_state.clear()
    _assist_state["game"] = game
    _assist_state["bot"] = bot
    _assist_state["current_row"] = 0
    _assist_state["finished"] = False


# ── Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── Assist endpoints ────────────────────────────────────────────────────

@app.route("/assist/start", methods=["POST"])
def assist_start():
    """Reset assist state and return first suggestion."""
    _reset_assist()
    try:
        suggestion = _assist_state["bot"].choose_action()
    except Exception:
        suggestion = None
    return jsonify({"suggestion": suggestion, "row": 0})


@app.route("/assist/submit", methods=["POST"])
def assist_submit():
    """Submit a guess + color feedback, get next suggestion."""
    data = request.get_json()
    guess = str(data.get("guess", "")).upper()
    colors = [c.upper() for c in data.get("colors", [])]

    if len(guess) != LETTERS or len(colors) != LETTERS:
        return jsonify({"error": "Guess and colors must each have 5 entries."}), 400
    if not all(c in ("G", "Y", "B") for c in colors):
        return jsonify({"error": "Colors must be G, Y, or B."}), 400

    game = _assist_state["game"]
    bot = _assist_state["bot"]
    row = _assist_state["current_row"]

    if _assist_state["finished"] or row >= ROWS:
        return jsonify({"error": "Game is already finished."}), 400

    # Update game state for bot.parse_board()
    game.board[row] = list(guess)
    game.colors[row] = list(colors)
    game.num_guesses += 1
    _assist_state["current_row"] = row + 1

    # Check if solved
    if all(c == "G" for c in colors):
        _assist_state["finished"] = True
        return jsonify({
            "solved": True,
            "row": row,
            "message": f"Solved in {row + 1} guess(es)! Word: {guess}",
            "suggestion": None,
        })

    if row + 1 >= ROWS:
        _assist_state["finished"] = True
        return jsonify({
            "solved": False,
            "row": row,
            "message": "All 6 guesses used.",
            "suggestion": None,
        })

    # Get next suggestion
    try:
        suggestion = bot.choose_action()
    except Exception:
        suggestion = None
        _assist_state["finished"] = True

    return jsonify({
        "solved": False,
        "row": row,
        "suggestion": suggestion,
        "message": None,
    })


# ── Solver endpoints ────────────────────────────────────────────────────

@app.route("/solver/run", methods=["POST"])
def solver_run():
    """Run a single solver game and return the full board for animation."""
    w_bank = load_word_bank()
    word = random.choice(w_bank["words"].tolist())

    game = Game(word, rows=ROWS, letters=LETTERS)
    bot = Bot(game, filename=CSV_PATH)

    while not game.is_end():
        guess = bot.choose_action()
        if game.valid_guess(guess):
            game.update_board(guess)

    result = game.game_result()
    won = result[0]
    moves = (result[1] + 1) if won else game.num_guesses

    rows_data = []
    for i in range(game.num_guesses):
        rows_data.append({
            "letters": game.board[i],
            "colors": game.colors[i],
        })

    return jsonify({
        "word": word,
        "won": won,
        "moves": moves,
        "rows": rows_data,
    })


# ── Launch helper ───────────────────────────────────────────────────────

def launch(port=5111, open_browser=True):
    """Start the Flask dev server and optionally open a browser."""
    import webbrowser
    import threading
    url = f"http://127.0.0.1:{port}"
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    print(f"\n  Wordle UI running at {url}\n  Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    launch()
