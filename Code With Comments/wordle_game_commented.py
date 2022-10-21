# -*- coding: utf-8 -*-
"""
@author: Yash
"""

from copy import deepcopy

class Game:
    def __init__(self, answer, rows=6, letters=5):
        self.num_guesses = 0
        self.answer = answer
        self.word_hash_table = {} #keeps track of different attributes of answer including vowel count and letter positions
        
        self.alph = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        '''
        answer is None check is meant for game assist option
        iterates through the answer and creates a dictionary/hash_table to represent
        letter counts and positions
        '''
        if answer is not None:
            for x, letter in enumerate(answer):
                if letter in self.word_hash_table:
                    self.word_hash_table[letter]['count'] += 1
                    self.word_hash_table[letter]['pos'].append(x)
                else:
                    self.word_hash_table[letter] = {'count':1, 'pos':[x]}
        
        self.rows = rows
        self.letters = letters
        
        '''
        creates 6 lists of 5 blank strings
        essentially, 6 rows of ['', '', '', '', '']
        '''
        self.board = [['' for _ in range(letters)] for _ in range(rows)]
        
        '''
        similar to the 2d list from above except this will be used to keep track of
        the various colors of each letter
        '''
        self.colors = [['' for _ in range(letters)] for _ in range(rows)]

    def is_end(self):
        '''
        checks to see if there is an entry in the sixth row on the board
        means that the entry is != to ['', '', '', '', ''] - which is an empty row
        '''
        if self.board[-1] != ['' for _ in range(self.letters)]:
            return True
        
        else: 
            r = self.game_result()
            if r[0] == True:
                return True
            else:
                return False
        '''otherwise we have reached the end of the game and should determine if the board has been solved or not'''


    def game_result(self):
        '''
        tuple win = (win_status, guess number)
        if the board is solved, win_status = true and the guess number will reflect that
        the default value 10 can be any number above 6 to represent that the board was not guessed within the possible 6 guesses
        '''
        win = (False, 10)
        
        '''iterate through the board to determine if any of the rows = the answer'''
        for i, r in enumerate(self.board):
            '''converts the list r to a string to be compared to the answer string'''
            if self.answer == ''.join(r):
                win = (True, i)
                break
        return win
    
    
    
    def update_board(self, input_word):
        '''
        copys the hash_table into a temporary one
        '''
        word_hash_table = deepcopy(self.word_hash_table)
        temp_hash_table = {}
        
        '''
        for loop updates the board based on the word that was just inputted/guessed
        by the user
        '''
        for x, l in enumerate(str(input_word).upper()):
            self.board[self.num_guesses][x] = l
            if l in temp_hash_table:
                temp_hash_table[l].append(x)
            else:
                temp_hash_table[l] = [x]
        '''
        These nested for loops are intended to go through each letter in the
        hash table and keep track of the position and counts of letters of
        a word in addition to seeing if it is a "green", "yellow", or "gray"
        letter based on the guess
        '''
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