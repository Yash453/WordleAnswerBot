import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedback_parser  # noqa: E402
from feedback_parser import parse_exact, parse_feedback  # noqa: E402


def tile(choice, confidence=0.9):
    return {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": {choice: confidence}}


class ParseExactTest(unittest.TestCase):
    def test_codes(self):
        for text in ['GBYBB', 'gbybb', 'g b y b b', 'G-B-Y-B-B', 'gb ybb']:
            self.assertEqual(parse_exact(text), list('GBYBB'), text)

    def test_emoji(self):
        self.assertEqual(parse_exact('🟩⬛🟨⬛⬛'), list('GBYBB'))
        self.assertEqual(parse_exact('🟩 ⬜ 🟨 ⬜ ⬜'), list('GBYBB'))

    def test_color_words(self):
        self.assertEqual(parse_exact('green gray yellow black grey'), list('GBYBB'))

    def test_rejects_descriptions_and_wrong_lengths(self):
        for text in ['C is green', 'GBYB', 'GBYBBG', '🟩⬛🟨', 'all grey', 'green yellow']:
            self.assertIsNone(parse_exact(text), text)


class ParseFeedbackTest(unittest.TestCase):
    def test_exact_format_skips_typesafe(self):
        with mock.patch.object(feedback_parser, 'system_one') as system_one:
            result = parse_feedback('crane', 'GBYBB')
        system_one.assert_not_called()
        self.assertEqual((result['colors'], result['source'], result['unclear']), (list('GBYBB'), 'code', []))

    def test_description_without_key_asks_for_code(self):
        with mock.patch.object(feedback_parser, 'is_configured', return_value=False):
            result = parse_feedback('CRANE', 'C is green, rest grey')
        self.assertIsNotNone(result['error'])
        self.assertEqual(result['unclear'], [1, 2, 3, 4, 5])

    def test_confident_answers_are_trusted(self):
        answers = {f'tile_{i}': tile(c) for i, c in enumerate('GBYBB')}
        with mock.patch.object(feedback_parser, 'is_configured', return_value=True), \
                mock.patch.object(feedback_parser, 'system_one', return_value=answers) as system_one:
            result = parse_feedback('CRANE', 'C green, A yellow, rest grey')
        state, questions = system_one.call_args[0]
        self.assertEqual(state['feedback'], 'C green, A yellow, rest grey')
        self.assertEqual(sorted(questions), [f'tile_{i}' for i in range(5)])
        self.assertEqual((result['colors'], result['unclear'], result['source']), (list('GBYBB'), [], 'typesafe'))

    def test_unspecified_and_low_confidence_tiles_are_unclear(self):
        answers = {'tile_0': tile('G'), 'tile_1': tile('unspecified'), 'tile_2': tile('Y', 0.3),
                   'tile_3': tile('B'), 'tile_4': tile('B')}
        with mock.patch.object(feedback_parser, 'is_configured', return_value=True), \
                mock.patch.object(feedback_parser, 'system_one', return_value=answers):
            result = parse_feedback('CRANE', 'C is green, A maybe yellow')
        self.assertEqual(result['colors'], ['G', None, 'Y', 'B', 'B'])
        self.assertEqual(result['unclear'], [2, 3])

    def test_service_failure_is_reported(self):
        with mock.patch.object(feedback_parser, 'is_configured', return_value=True), \
                mock.patch.object(feedback_parser, 'system_one', side_effect=feedback_parser.TypeSafeError('boom')):
            result = parse_feedback('CRANE', 'C is green')
        self.assertIsNone(result['source'])
        self.assertIn('boom', result['error'])

    def test_repeated_letter_hint_only_on_repeats(self):
        questions = feedback_parser.tile_questions('SPEED')
        self.assertIn('more than once', questions['tile_2']['instructions'])
        self.assertNotIn('more than once', questions['tile_0']['instructions'])


if __name__ == '__main__':
    unittest.main()
