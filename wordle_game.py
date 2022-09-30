# -*- coding: utf-8 -*-
"""
@author: Yash
"""

from copy import deepcopy

class Game:
    def __init__(self, answer, rows=6, letters=5):
        self.num_guesses = 0
        self.answer = answer
        self.word_hash_table = {}
        
        self.alph = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

        if answer is not None:
            for x, letter in enumerate(answer):
                if letter in self.word_hash_table:
                    self.word_hash_table[letter]['count'] += 1
                    self.word_hash_table[letter]['pos'].append(x)
                else:
                    self.word_hash_table[letter] = {'count':1, 'pos':[x]}
        
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
        word_hash_table = deepcopy(self.word_hash_table)
        temp_hash_table = {}
        for x, l in enumerate(str(input_word).upper()):
            self.board[self.num_guesses][x] = l
            if l in temp_hash_table:
                temp_hash_table[l].append(x)
            else:
                temp_hash_table[l] = [x]
        colors = {'G':[],'Y':[],'B':[]}
        for l in temp_hash_table:
            if l in word_hash_table:
                green_temp = []
                for p in temp_hash_table[l]:
                    if p in word_hash_table[l]['pos']:
                        green_temp.append(p)
                for p in green_temp:
                    temp_hash_table[l].remove(p)
                colors['G'] += green_temp
                if len(green_temp) < word_hash_table[l]['count']:
                    yellow_temp = []
                    for p in temp_hash_table[l]:
                        yellow_temp.append(p)
                        if len(yellow_temp) == word_hash_table[l]['count']:
                            break
                    for p in yellow_temp:
                        temp_hash_table[l].remove(p)
                    colors['Y'] += yellow_temp
                for p in temp_hash_table[l]:
                    colors['B'].append(p)
            else:
                colors['B'] += temp_hash_table[l]
                temp_hash_table[l] = []
        for c in colors:
            for p in colors[c]:
                self.colors[self.num_guesses][p] = c
        self.num_guesses += 1

    def valid_guess(self, input_word):
        if len(input_word) == 5 and False not in [False for s in str(input_word).upper() if s not in self.alph]:
            return True
        else:
            return False