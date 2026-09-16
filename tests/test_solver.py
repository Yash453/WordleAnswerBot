import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from prediction_bot import Bot  # noqa: E402
from wordle_game import Game, score_guess  # noqa: E402

CSV_PATH = os.path.join(ROOT, 'word_data.csv')


def colors(guess, answer):
    return ''.join(score_guess(guess, answer))


class ScoreGuessTest(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(colors('CRANE', 'CRANE'), 'GGGGG')

    def test_no_overlap(self):
        self.assertEqual(colors('BUILT', 'CRANE'), 'BBBBB')

    def test_green_uses_up_repeated_letter(self):
        # SPEED has two Es; the green E leaves only one to mark yellow
        self.assertEqual(colors('EXEXE', 'SPEED'), 'YBGBB')

    def test_extra_repeats_are_grey(self):
        self.assertEqual(colors('EERIE', 'SPEED'), 'YYBBB')

    def test_repeated_letter_yellow_and_green(self):
        self.assertEqual(colors('BABES', 'ABBEY'), 'YYGGB')

    def test_single_answer_letter_marks_one_yellow_or_green(self):
        self.assertEqual(colors('LLAMA', 'ALOFT'), 'BGYBB')


class BotTest(unittest.TestCase):
    def play(self, game, guess):
        game.update_board(guess)

    def test_grey_repeat_caps_letter_count(self):
        # EERIE vs THOSE is BBBBG: exactly one E, so two-E words like THEME must go
        game = Game('THOSE')
        bot = Bot(game, filename=CSV_PATH)
        self.play(game, 'EERIE')
        bot.choose_action()
        words = set(bot.wordbank['words'])
        self.assertIn('THOSE', words)
        self.assertNotIn('THEME', words)

    def test_answer_survives_grey_repeat_next_to_green(self):
        game = Game('THEME')
        bot = Bot(game, filename=CSV_PATH)
        self.play(game, 'EARLY')
        self.play(game, 'GEESE')
        bot.choose_action()
        self.assertIn('THEME', set(bot.wordbank['words']))

    def test_inconsistent_feedback_returns_none(self):
        game = Game(None)
        bot = Bot(game, filename=CSV_PATH)
        game.board[0], game.colors[0] = list('CRANE'), list('GGGGB')
        game.board[1], game.colors[1] = list('CRANE'), list('BBBBB')
        game.num_guesses = 2
        self.assertIsNone(bot.choose_action())

    def test_keeps_words_like_false(self):
        bot = Bot(Game('FALSE'), filename=CSV_PATH)
        self.assertIn('FALSE', set(bot.wordbank['words']))

    def test_answer_never_filtered_out(self):
        rng = random.Random(0)
        answers = Bot(Game(None), filename=CSV_PATH).wordbank['words'].tolist()
        for answer in rng.sample(answers, 40):
            random.seed(answer)
            game = Game(answer)
            bot = Bot(game, filename=CSV_PATH)
            while not game.is_end():
                guess = bot.choose_action()
                self.assertIsNotNone(guess, answer)
                self.assertIn(answer, set(bot.wordbank['words']))
                game.update_board(guess)


if __name__ == '__main__':
    unittest.main()
