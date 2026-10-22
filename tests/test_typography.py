import unittest

import canvas_renderer as cr


class TypographyRegressionTest(unittest.TestCase):
    def test_incomplete_markup_is_literal(self):
        self.assertEqual(cr.parse_rich('Fe^{2+'), [('Fe^{2+', 0)])

    def test_accented_multiline_scripts_are_not_clipped(self):
        for size in (12, 24, 48):
            for angle in (0, 90, 270):
                image = cr._label_image('É^{Åg}\nH_{2}O', size, 'Arial', (0,0,0), angle)
                box = image.getbbox()
                self.assertIsNotNone(box)
                self.assertGreater(box[0], 0)
                self.assertGreater(box[1], 0)
                self.assertLess(box[2], image.width)
                self.assertLess(box[3], image.height)

    def test_plain_text_uses_font_advance(self):
        font, _ = cr._script_fonts(30, 'Arial')
        self.assertAlmostEqual(cr.rich_text_width('AV fi',30,'Arial'), font.getlength('AV fi'), delta=1)
