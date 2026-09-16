# -*- coding: utf-8 -*-
"""
@author: Yash
"""

from collections import Counter


def score_guess(guess, answer):
    """Return Wordle colors ('G', 'Y', 'B') for guess against answer.

    Greens are assigned first; each remaining answer letter can then turn at most
    one misplaced guess letter yellow, left to right, so repeated letters are
    colored the same way Wordle colors them.
    """
    colors = ['B'] * len(guess)
    unmatched = Counter()
    for x, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            colors[x] = 'G'
        else:
            unmatched[a] += 1
    for x, g in enumerate(guess):
        if colors[x] != 'G' and unmatched[g] > 0:
            colors[x] = 'Y'
            unmatched[g] -= 1
    return colors


class Game:
    def __init__(self, answer, rows=6, letters=5):
        self.num_guesses = 0
        self.answer = answer
        self.rows = rows
        self.letters = letters
        self.board = [['' for _ in range(letters)] for _ in range(rows)]
        self.colors = [['' for _ in range(letters)] for _ in range(rows)]

    def is_end(self):
        if self.board[-1] != ['' for _ in range(self.letters)]:
            return True
        else:
            r = self.game_result()
            if r[0] == True:
                return True
            else:
                return False

    def game_result(self):
        win = (False, 99)
        for i, r in enumerate(self.board):
            if self.answer == ''.join(r):
                win = (True, i)
                break
        return win

    def update_board(self, input_word):
        word = str(input_word).upper()
        self.board[self.num_guesses] = list(word)
        self.colors[self.num_guesses] = score_guess(word, self.answer)
        self.num_guesses += 1

    def valid_guess(self, input_word):
        word = str(input_word).upper()
        return len(word) == self.letters and all('A' <= s <= 'Z' for s in word)
