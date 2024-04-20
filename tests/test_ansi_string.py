#!/usr/bin/env python3

import os
import sys
import unittest
from io import BytesIO, StringIO
from unittest.mock import patch

THIS_FILE_PATH = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
PROJECT_DIR = os.path.abspath(os.path.join(THIS_FILE_PATH, '..'))
SOURCE_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'src'))

if os.path.isdir(SOURCE_DIR):
    sys.path.insert(0, SOURCE_DIR)
from ansi_string import en_tty_ansi, AnsiFormat, AnsiString, ColorComponentType, ColourComponentType

def _is_windows():
    return sys.platform.lower().startswith('win')

class FakeStdOut:
    def __init__(self) -> None:
        self.buffer = BytesIO()

class FakeStdIn:
    def __init__(self, loaded_str):
        if isinstance(loaded_str, str):
            loaded_str = loaded_str.encode()
        self.buffer = BytesIO(loaded_str)

class CliTests(unittest.TestCase):
    def test_en_tty_ansi(self):
        # Not a very useful test
        en_tty_ansi()

    def test_no_format(self):
        s = AnsiString('No format')
        self.assertEqual(str(s), 'No format')

    def test_using_AnsiFormat(self):
        s = AnsiString('This is bold', AnsiFormat.BOLD)
        self.assertEqual(str(s), '\x1b[1mThis is bold\x1b[m')

    def test_using_list_of_AnsiFormat(self):
        s = AnsiString('This is bold and red', [AnsiFormat.BOLD, AnsiFormat.RED])
        self.assertEqual(str(s), '\x1b[1;31mThis is bold and red\x1b[m')

    def test_using_list_of_various(self):
        s = AnsiString('Lots of formatting!', ['[1', AnsiFormat.UL_RED, 'rgb(0x12A03F);bg_white'])
        self.assertEqual(str(s), '\x1b[1;4;58;5;9;38;2;18;160;63;47mLots of formatting!\x1b[m')

    def test_custom_formatting(self):
        s = AnsiString('This string contains custom formatting', '[38;2;175;95;95')
        self.assertEqual(str(s), '\x1b[38;2;175;95;95mThis string contains custom formatting\x1b[m')

    def test_ranges(self):
        s = AnsiString('This string contains multiple color settings across different ranges')
        s.apply_formatting(AnsiFormat.BOLD, 5, 11)
        s.apply_formatting(AnsiFormat.BG_BLUE, 21, 29)
        s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
        self.assertEqual(
            str(s),
            'This \x1b[1mstring\x1b[m contains \x1b[44;38;5;214;3mmultiple\x1b[0;38;5;214;3m color\x1b[m settings '
            'across different ranges'
        )

    def test_format_right_only(self):
        s = AnsiString('This has no ANSI formatting')
        self.assertEqual(
            f'{s:#>90}',
            '###############################################################This has no ANSI formatting'
        )

    def test_format_right_justify_and_int(self):
        s = AnsiString('This string will be formatted bold and red, right justify')
        self.assertEqual(
            f'{s:>90:01;31}',
            '\x1b[01;31m                                 This string will be formatted bold and red, right justify\x1b[m'
        )

    def test_format_left_justify_and_strings(self):
        s = AnsiString('This string will be formatted bold and red', 'bold')
        self.assertEqual(
            '{:+<90:fg_red}'.format(s),
            '\x1b[1;31mThis string will be formatted bold and red++++++++++++++++++++++++++++++++++++++++++++++++\x1b[m'
        )

    def test_format_center_and_verbatim_string(self):
        s = AnsiString('This string will be formatted bold and red')
        self.assertEqual(
            '{:*^90:[this is not parsed}'.format(s),
            '\x1b[this is not parsedm************************This string will be formatted bold and red************************\x1b[m'
        )

    def test_no_format_and_rgb_functions(self):
        s = AnsiString('Manually adjust colors of foreground, background, and underline')
        self.assertEqual(
            f'{s::rgb(0x8A2BE2);bg_rgb(100, 232, 170);ul_rgb(0xFF, 0x63, 0x47)}',
            '\x1b[38;2;138;43;226;48;2;100;232;170;4;58;2;255;99;71mManually adjust colors of foreground, background, and underline\x1b[m'
        )

    def test_no_format_and_rgb_functions2(self):
        s = AnsiString('Manually adjust colors of foreground, background, and underline')
        fg_color = 0x8A2BE2
        bg_colors = [100, 232, 170]
        ul_colors = [0xFF, 0x63, 0x47]
        self.assertEqual(
            f'{s::rgb({fg_color});bg_rgb({bg_colors});ul_rgb({ul_colors})}',
            '\x1b[38;2;138;43;226;48;2;100;232;170;4;58;2;255;99;71mManually adjust colors of foreground, background, and underline\x1b[m'
        )

    def test_add(self):
        s = AnsiString('bold', 'bold') + AnsiString('red', 'red')
        self.assertEqual(
            str(s),
            '\x1b[1mbold\x1b[0;31mred\x1b[m'
        )

    def test_iadd(self):
        s = AnsiString('part bold')
        s.apply_formatting(AnsiFormat.BOLD, 0, 3)
        s += AnsiString('red', 'red')
        self.assertEqual(
            str(s),
            '\x1b[1mpar\x1b[mt bold\x1b[31mred\x1b[m'
        )

    def test_eq(self):
        s=AnsiString('red', 'red')
        self.assertEqual(s, AnsiString('red', AnsiFormat.FG_RED))

    def test_neq(self):
        s=AnsiString('red', 'red')
        self.assertNotEqual(s, AnsiString('red', AnsiFormat.BG_RED))

    def test_ljust(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s.ljust(90, 'X')
        self.assertEqual(
            str(s),
            '\x1b[1;31mThis string will be formatted bold and redXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\x1b[m'
        )

if __name__ == '__main__':
    unittest.main()
