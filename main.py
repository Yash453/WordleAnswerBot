# -*- coding: utf-8 -*-
"""
@author: Yash
"""

import random
import numpy
import pandas

from prediction_bot import Bot
from wordle_game import Game

ROWS = 6
LETTERS = 5
GAMES = 100

w_bank = pandas.read_csv('word_data.csv')
w_bank = w_bank[w_bank['words'].str.len()==LETTERS]
w_bank['words'] = w_bank['words'].str.upper() #Convert all words to uppercase

control = input('Which mode do you want to run? \n\n Test Solver = [T] \n\n Game Assist = [A] \n\n Play Game = [P]\n\n')
control = control.upper()
if 'T' in str(control) or 'P' in str(control):
    if 'P' in str(control):
        print('PLAY GAME SELECTED\n---------------------')
    else:
        print('TEST SOLVER SELECTED\n---------------------\n')
    results = []
    if 'P' in str(control):
        GAMES = 1
    for _ in range(GAMES):
        word = random.choice(w_bank['words'].tolist())
        game = Game(
            word,
            rows=ROWS,
            letters=LETTERS
        )
        bot = Bot(game)
        while game.is_end() == False:
            if 'P' in str(control):
                u_inp = input('\n* PLEASE GUESS A 5 LETTER WORD\n')
            else:
                u_inp = bot.choose_action()
            if game.valid_guess(u_inp) == True:
                game.update_board(u_inp)
                if 'P' in str(control):
                    print("* COLORS & GUESSES:")
                    for c,b in zip(game.colors,game.board):
                        colors_string="".join(c)
                        guess_string="".join(b)
                        if guess_string != colors_string:  # simple hack to not print blank lines: color string is never a legit word. so if both are equal then its an empty line (we haven't played it yet).
                           print(colors_string, guess_string)
            else:
                print('ERROR: Word is not 5 Letters')
        r = game.game_result()
        if 'P' in str(control):
            if r[0] == True:
                if r[1] > 0:
                    print(f'\nCONGRATS YOU WON IN {r[1] + 1} GUESSES!\n')
                else:
                    print(f'\nCONGRATS YOU WON IN {r[1] + 1} GUESS!\n')
            else:
                print(f'\nSORRY YOU DID NOT WIN.\n')
            print(numpy.array(game.board),'\n')
        results.append({'word':word,'result':r[0],'moves':r[1]+1})

    results = pandas.DataFrame(results)
    print(results)
    print(f'Win Percent = {(len(results[results["result"]==True]) / len(results)) * 100}%\nAverage Moves = {results[results["result"]==True]["moves"].mean()}')
elif 'A' in str(control):
    print('GAME ASSIST ACTIVATED\n---------------------')
    game = Game(
        None,
        rows=ROWS,
        letters=LETTERS
    )
    bot = Bot(game)
    for i in range(ROWS):
        guess = bot.choose_action()
        print(f'\nSuggested Word = {guess}\n')
        u_inp = input('What was the result returned? [ex. ybggy]?\n')
        game.colours[i] = [s for s in str(u_inp)]
        game.board[i] = [s for s in str(guess).upper()]
        game.g_count += 1
        for x, s in enumerate(game.colors[i]):
            if s == 'Y':
                if guess[x] in bot.yellow_letters:
                    bot.y_letters[guess[x]].append(x)
                else:
                    bot.y_letters[guess[x]] = [x]
            elif s == 'B':
                if guess[x] in bot.green_letters:
                    bot.g_letters.append(guess[x])
            elif s == 'G':
                bot.prediction[x] = guess[x]