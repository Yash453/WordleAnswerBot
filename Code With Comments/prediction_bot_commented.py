# -*- coding: utf-8 -*-
"""
@author: Yash
"""

import random
import numpy
import pandas

class Bot:
    def __init__(self, game, filename='word_data.csv'):
        self.vowels = ['A','E','I','O','U','Y']
        
        '''
        - Creates a wordbank used the .read_csv() function in pandas
        
        - This is then used to capitalize all the words to standardize word formatting
          for when letters are being compared to each other (to prevent any mistakes
          due to capitalization errors)
        
        - The number of vowels that exist in a given word are also stored into a word bank element 
        '''
        wordbank = pandas.read_csv(filename)
        wordbank['words'] = wordbank['words'].str.upper() #Convert all words to uppercase
        wordbank['vowel_count'] = wordbank['words'].apply(lambda x: ''.join(set(x))).str.count('|'.join(self.vowels)) #Count amount of vowels in words
        self.wordbank = wordbank
        
        
        self.game = game
        #self.prediction represents the green letters that we know exist for certain
        self.prediction = ['' for _ in range(game.letters)]
        self.yellow_letters = {}
        self.green_letters = []

    def calc_letter_probs(self):
        '''
        Iterates through each letter in the word and "normalizes" the probability of that
        letter in the word. This essentially means that it tries to see how often that letter
        occurs in that given position amongst the remaining words that are left.
        
        These values are then mapped into the according letter index/column of that word to be
        compared to and considered for the word score calculations
        '''
        for x in range(self.game.letters):
            counts = self.wordbank['words'].str[x].value_counts(normalize=True).to_dict()
            self.wordbank[f'p-{x}'] = self.wordbank['words'].str[x].map(counts)

    '''
    Parses through the board to keep track of the green, yellow, and black
    letters that are in the guesses to be used to formulate the next set of letters
    that should be used when guessing
    '''
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
            #print("Self prediction:")
            #print(self.prediction)
            #print("yellow letters: ")
            #print(self.yellow_letters)

    def choose_action(self):
        #Parses to keep track of the green, yellow, and black letters at the algorithms disposal to use for calculations
        self.parse_board()
        
        '''
        If there is a green letter, make sure that remaining words left contain that green letter as well
        '''
        if len(self.green_letters) > 0:
            self.wordbank = self.wordbank[~self.wordbank['words'].str.contains('|'.join(self.green_letters))]
            self.green_letters = []
        '''
        Using a regex string, words that contain a yellow letter are found and filtered for the remaining
        usable words in the wordbank
        '''
        if len(self.yellow_letters) > 0:
            yellow_string = '^' + ''.join(fr'(?=.*{l})' for l in self.yellow_letters)
            self.wordbank = self.wordbank[self.wordbank['words'].str.contains(yellow_string)]
            for s, p in self.yellow_letters.items():
                for i in p:
                    self.wordbank = self.wordbank[self.wordbank['words'].str[i]!=s] #makes sure that yellow letter is not at the same position in this new guess
            self.yellow_letters = {}
        for i, s in enumerate(self.prediction):
            if s != '':
                self.wordbank = self.wordbank[self.wordbank['words'].str[i]==s] #last filter to make sure that remaining words reflect the green letter we already know
        self.wordbank['w-score'] = [0] * len(self.wordbank) #sets the w-score to 0 for all words in order to recalculate the scores
        '''
        Word scores are recalculated and added into the w-score based on the letter probability and the vowel count of the word
        '''
        if len(self.wordbank) > 5:
            self.calc_letter_probs() #Recalculate letter position probability
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.wordbank['w-score'] += self.wordbank[f'p-{x}']
        if True not in [True for s in self.prediction if s in self.vowels]:
            self.wordbank['w-score'] += self.wordbank['vowel_count'] / self.game.letters
        
        '''
        The word with the highest scores are kept in the wordbank using the .max() function
        
        In the case that multiple words have the highest score, a random word amongst them
        is chosen be the next guess (theoretically, it should not make a significant difference
                                     as these words would likely have either similar beginnings
                                     or ending such as would or could meaning the guesses end
                                     up becoming 50/50 guesses since they cannot be filtered
                                     any further without simply guessing the word itself)
        '''
        mv_bank = self.wordbank[self.wordbank['w-score']==self.wordbank['w-score'].max()]
        result = random.choice(mv_bank['words'].tolist())
        #print("Result:")
        #print(result)
        return result