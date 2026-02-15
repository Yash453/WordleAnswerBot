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


def load_word_bank():
    """Load and prepare the word bank from CSV."""
    w_bank = pandas.read_csv('word_data.csv')
    w_bank = w_bank[w_bank['words'].str.len() == LETTERS]
    w_bank['words'] = w_bank['words'].str.upper()
    return w_bank


def run_test_solver(w_bank, num_games=GAMES):
    """Run the automated solver test for num_games rounds."""
    print('TEST SOLVER SELECTED\n---------------------\n')
    results = []
    for _ in range(num_games):
        word = random.choice(w_bank['words'].tolist())
        game = Game(word, rows=ROWS, letters=LETTERS)
        bot = Bot(game)
        while game.is_end() == False:
            u_inp = bot.choose_action()
            if game.valid_guess(u_inp) == True:
                game.update_board(u_inp)
            else:
                print('ERROR: Word is not 5 Letters')
        r = game.game_result()
        results.append({'word': word, 'result': r[0], 'moves': r[1] + 1})
    results = pandas.DataFrame(results)
    print(results)
    print(f'Win Percent = {(len(results[results["result"]==True]) / len(results)) * 100}%\nAverage Moves = {results[results["result"]==True]["moves"].mean()}')
    return results


def run_solver_single(w_bank):
    """Run solver on a single random word. Returns (game, bot) for visualization."""
    word = random.choice(w_bank['words'].tolist())
    game = Game(word, rows=ROWS, letters=LETTERS)
    bot = Bot(game)
    while game.is_end() == False:
        u_inp = bot.choose_action()
        if game.valid_guess(u_inp) == True:
            game.update_board(u_inp)
    return game, bot


def run_play_game(w_bank):
    """Run a single interactive play game in the terminal."""
    print('PLAY GAME SELECTED\n---------------------')
    word = random.choice(w_bank['words'].tolist())
    game = Game(word, rows=ROWS, letters=LETTERS)
    bot = Bot(game)
    while game.is_end() == False:
        u_inp = input('\n* PLEASE GUESS A 5 LETTER WORD\n')
        if game.valid_guess(u_inp) == True:
            game.update_board(u_inp)
            print("* COLORS & GUESSES:")
            for c, b in zip(game.colors, game.board):
                colors_string = "".join(c)
                guess_string = "".join(b)
                if guess_string != colors_string:
                    print(colors_string, guess_string)
        else:
            print('ERROR: Word is not 5 Letters')
    r = game.game_result()
    if r[0] == True:
        if r[1] > 0:
            print(f'\nCONGRATS YOU WON IN {r[1] + 1} GUESSES!\n')
        else:
            print(f'\nCONGRATS YOU WON IN {r[1] + 1} GUESS!\n')
    else:
        print(f'\nSORRY YOU DID NOT WIN.\n')
    print(numpy.array(game.board), '\n')
    return game


def run_assist():
    """Run the assist mode in the terminal."""
    print('GAME ASSIST ACTIVATED\n---------------------')
    game = Game(None, rows=ROWS, letters=LETTERS)
    bot = Bot(game)
    for i in range(ROWS):
        guess = bot.choose_action()
        print(f'\nSuggested Word = {guess}\n')
        u_inp = input('What was the result returned? [ex. YBGGY]?\n')
        game.colors[i] = [s.upper() for s in str(u_inp)]
        game.board[i] = [s for s in str(guess).upper()]
        game.num_guesses += 1
        if all(s == 'G' for s in game.colors[i]):
            print(f'\nWord found: {guess}! Solved in {i + 1} guess(es)!\n')
            break
    return game, bot


def main_cli():
    """Original CLI entry point."""
    w_bank = load_word_bank()
    control = input('Which mode do you want to run? \n\n Test Solver = [T] \n\n Game Assist = [A] \n\n Play Game = [P] \n\n Wordle UI = [U]\n\n')
    control = control.upper()
    if 'U' in str(control):
        from wordle_ui import launch
        launch()
    elif 'T' in str(control):
        run_test_solver(w_bank)
    elif 'P' in str(control):
        run_play_game(w_bank)
    elif 'A' in str(control):
        run_assist()


if __name__ == '__main__':
    main_cli()