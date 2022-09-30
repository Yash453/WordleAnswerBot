# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 00:54:04 2022

@author: Yash
"""

import random
import numpy
import pandas

class Bot:
    def __init__(self, game, filename='data/words.csv'):
        self.vowels = ['A','E','I','O','U','Y']
        wordbank = pandas.read_csv(filename)
        wordbank = wordbank[wordbank['words'].str.len()==game.letters]
        wordbank['words'] = wordbank['words'].str.upper() #Convert all words to uppercase
        wordbank['vowel_count'] = wordbank['words'].apply(lambda x: ''.join(set(x))).str.count('|'.join(self.vowels)) #Count amount of vowels in words
        self.wordbank = wordbank
        self.game = game
        self.prediction = ['' for _ in range(game.letters)]
        self.yellow_letters = {}
        self.green_letters = []

    def calc_letter_probs(self):
        for x in range(self.game.letters):
            counts = self.wordbank['words'].str[x].value_counts(normalize=True).to_dict()
            self.wordbank[f'p-{x}'] = self.wordbank['words'].str[x].map(counts)

    def parse_board(self):
        if self.game.num_guesses > 0:
            g_hold = []
            for x, c in enumerate(self.game.colors[self.game.num_guesses - 1]):
                letter = self.game.board[self.game.num_guesses - 1][x]
                if c == 'Y':
                    if letter not in self.yellow_letters:
                        self.yellow_letters[letter] = [x]
                    else:
                        if x not in self.yellow_letters[letter]:
                            self.yellow_letters[letter].append(x)
                elif c == 'G':
                    self.prediction[x] = letter
                else:
                    if letter in self.prediction:
                        if letter not in self.yellow_letters:
                            self.yellow_letters[letter] = [x]
                        else:
                            self.yellow_letters[letter].append(x)
                    elif letter not in self.green_letters:
                        self.green_letters.append(letter)
            self.green_letters = [l for l in self.green_letters if l not in self.yellow_letters and l not in self.prediction]

    def choose_action(self):
        self.parse_board()
        if len(self.green_letters) > 0:
            self.wordbank = self.wordbank[~self.wordbank['words'].str.contains('|'.join(self.green_letters))]
            self.green_letters = []
        if len(self.yellow_letters) > 0:
            yellow_string = '^' + ''.join(fr'(?=.*{l})' for l in self.yellow_letters)
            self.wordbank = self.wordbank[self.wordbank['words'].str.contains(yellow_string)]
            for s, p in self.yellow_letters.items():
                for i in p:
                    self.wordbank = self.wordbank[self.wordbank['words'].str[i]!=s]
            self.yellow_letters = {}
        for i, s in enumerate(self.prediction):
            if s != '':
                self.wordbank = self.wordbank[self.wordbank['words'].str[i]==s]
        self.wordbank['w-score'] = [0] * len(self.wordbank)
        if len(self.wordbank) > 5:
            self.calc_letter_probs() #Recalculate letter position probability
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.wordbank['w-score'] += self.wordbank[f'p-{x}']
        if True not in [True for s in self.prediction if s in self.vowels]:
            self.wordbank['w-score'] += self.wordbank['vowel_count'] / self.game.letters
        mv_bank = self.wordbank[self.wordbank['w-score']==self.wordbank['w-score'].max()]
        result = random.choice(mv_bank['words'].tolist())
        return result