# -*- coding: utf-8 -*-
"""
@author: Yash
"""

import random
import numpy
import pandas

from wordle_game import score_guess

class Bot:
    def __init__(self, game, filename='word_data.csv'):
        self.vowels = ['A','E','I','O','U','Y']
        wordbank = pandas.read_csv(filename, dtype={'words': str}, keep_default_na=False) #Keep words like FALSE and NULL as text
        wordbank = wordbank[wordbank['words'].str.len()==game.letters].copy()
        wordbank['words'] = wordbank['words'].str.upper() #Convert all words to uppercase
        wordbank['vowel_count'] = wordbank['words'].apply(lambda x: ''.join(set(x))).str.count('|'.join(self.vowels)) #Count amount of vowels in words
        self.wordbank = wordbank
        self.game = game
        self.prediction = ['' for _ in range(game.letters)]
        self.rows_seen = 0

    def calc_letter_probs(self):
        for x in range(self.game.letters):
            counts = self.wordbank['words'].str[x].value_counts(normalize=True).to_dict()
            self.wordbank[f'p-{x}'] = self.wordbank['words'].str[x].map(counts)

    def parse_board(self):
        #Keep only words that would have produced exactly the colors shown for every new row
        while self.rows_seen < self.game.num_guesses:
            guess = ''.join(self.game.board[self.rows_seen])
            colors = list(self.game.colors[self.rows_seen])
            for x, c in enumerate(colors):
                if c == 'G':
                    self.prediction[x] = guess[x]
            consistent = self.wordbank['words'].map(lambda w: score_guess(guess, w) == colors)
            self.wordbank = self.wordbank[consistent].copy()
            self.rows_seen += 1

    def choose_action(self):
        """Return the best remaining word, or None if no word fits the feedback so far."""
        self.parse_board()
        if len(self.wordbank) == 0:
            return None
        self.wordbank['w-score'] = [0] * len(self.wordbank)
        if len(self.wordbank) > 5 or 'p-0' not in self.wordbank:
            self.calc_letter_probs() #Recalculate letter position probability
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.wordbank['w-score'] += self.wordbank[f'p-{x}']
        if True not in [True for s in self.prediction if s in self.vowels]:
            self.wordbank['w-score'] += self.wordbank['vowel_count'] / self.game.letters
        mv_bank = self.wordbank[self.wordbank['w-score']==self.wordbank['w-score'].max()]
        result = random.choice(mv_bank['words'].tolist())
        return result
