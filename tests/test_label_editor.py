import unittest

from canvas_renderer import parse_rich
from label_editor import encode_runs


class LabelEditorTest(unittest.TestCase):
    def test_word_style_runs_round_trip(self):
        for runs in ([['10',0],['6',1]], [['H',0],['2',-1],['O',0]], [['Fe',0],['2+',1]], [['sample_a^{x}\\',0],['a}_^\\b',1]]):
            self.assertEqual(parse_rich(encode_runs(runs)), [tuple(r) for r in runs])

    def test_untrusted_component_values_rejected(self):
        for value in (None, 'text', [[5,0]], [['x',2]], [{}]):
            with self.assertRaises(ValueError):
                encode_runs(value)
