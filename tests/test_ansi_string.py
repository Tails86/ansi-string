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

    def test_center(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s2 = s.center(90, 'X')
        self.assertEqual(
            str(s2),
            '\x1b[1;31mXXXXXXXXXXXXXXXXXXXXXXXXThis string will be formatted bold and redXXXXXXXXXXXXXXXXXXXXXXXX\x1b[m'
        )
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31mThis string will be formatted bold and red\x1b[m'
        )

    def test_center_inplace(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s2 = s.center(89, 'X', inplace=True)
        self.assertEqual(
            str(s2),
            '\x1b[1;31mXXXXXXXXXXXXXXXXXXXXXXXThis string will be formatted bold and redXXXXXXXXXXXXXXXXXXXXXXXX\x1b[m'
        )
        self.assertIs(s, s2)

    def test_ljust(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s2 = s.ljust(90, 'X')
        self.assertEqual(
            str(s2),
            '\x1b[1;31mThis string will be formatted bold and redXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\x1b[m'
        )
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31mThis string will be formatted bold and red\x1b[m'
        )

    def test_ljust_inplace(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s2 = s.ljust(90, 'X', inplace=True)
        self.assertEqual(
            str(s2),
            '\x1b[1;31mThis string will be formatted bold and redXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\x1b[m'
        )
        self.assertIs(s, s2)

    def test_rjust(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s2 = s.rjust(90, '0')
        self.assertEqual(
            str(s2),
            '\x1b[1;31m000000000000000000000000000000000000000000000000This string will be formatted bold and red\x1b[m'
        )
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31mThis string will be formatted bold and red\x1b[m'
        )

    def test_rjust_inplace(self):
        s = AnsiString('This string will be formatted bold and red', 'bold;red')
        s2 = s.rjust(90, '0', inplace=True)
        self.assertEqual(
            str(s2),
            '\x1b[1;31m000000000000000000000000000000000000000000000000This string will be formatted bold and red\x1b[m'
        )
        self.assertIs(s, s2)

    def test_strip(self):
        s = AnsiString('    T\t\r\n \v\f', 'bold;red')
        s2 = s.strip()
        self.assertEqual(str(s2), '\x1b[1;31mT\x1b[m')
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31m    T\t\r\n \x0b\x0c\x1b[m'
        )

    def test_strip_inplace(self):
        s = AnsiString('    T\t\r\n \v\f', 'bold;red')
        s2 = s.strip(inplace=True)
        self.assertEqual(str(s2), '\x1b[1;31mT\x1b[m')
        self.assertIs(s, s2)

    def test_strip_all(self):
        s = AnsiString('    ', 'bold;red')
        s2 = s.strip()
        self.assertEqual(str(s2), '')

    def test_lstrip(self):
        s = AnsiString('    T\t\r\n \v\f', 'bold;red')
        s2 = s.lstrip()
        self.assertEqual(str(s2), '\x1b[1;31mT\t\r\n \v\f\x1b[m')
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31m    T\t\r\n \x0b\x0c\x1b[m'
        )

    def test_lstrip_inplace(self):
        s = AnsiString('    T\t\r\n \v\f', 'bold;red')
        s2 = s.lstrip(inplace=True)
        self.assertEqual(str(s2), '\x1b[1;31mT\t\r\n \v\f\x1b[m')
        self.assertIs(s, s2)

    def test_lstrip_all(self):
        s = AnsiString(' \t   ', 'bold;red')
        s2 = s.lstrip()
        self.assertEqual(str(s2), '')

    def test_rstrip(self):
        s = AnsiString('    T\t\r\n \v\f', 'bold;red')
        s2 = s.rstrip()
        self.assertEqual(str(s2), '\x1b[1;31m    T\x1b[m')
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31m    T\t\r\n \x0b\x0c\x1b[m'
        )

    def test_rstrip_inplace(self):
        s = AnsiString('    T\t\r\n \v\f', 'bold;red')
        s2 = s.rstrip(inplace=True)
        self.assertEqual(str(s2), '\x1b[1;31m    T\x1b[m')
        self.assertIs(s, s2)

    def test_rstrip_all(self):
        s = AnsiString(' \n   ', 'bold;red')
        s2 = s.rstrip()
        self.assertEqual(str(s2), '')

    def test_partition_found(self):
        s = AnsiString('This string will be formatted italic and purple', ['purple', 'italic'])
        s_orig = s
        out = s.partition('will')
        self.assertEqual(
            [str(s) for s in out],
            ['\x1b[38;5;90;3mThis string \x1b[m', '\x1b[38;5;90;3mwill\x1b[m', '\x1b[38;5;90;3m be formatted italic and purple\x1b[m']
        )
        self.assertIs(s, s_orig)

    def test_partition_not_found(self):
        s = AnsiString('This string will be formatted italic and purple', ['purple', 'italic'])
        s_orig = s
        out = s.partition('bella')
        self.assertEqual(
            [str(s) for s in out],
            ['\x1b[38;5;90;3mThis string will be formatted italic and purple\x1b[m', '', '']
        )
        self.assertIs(s, s_orig)


    def test_get_item_edge_case(self):
        # There used to be a bug where if a single character was retrieved right before the index where a new format was
        # applied, it add a remove setting for something that didn't exist yet
        s=AnsiString('This string will be formatted italic and purple', ['purple', 'italic'])
        s.apply_formatting('bold', 5, 11)
        self.assertEqual(str(s[4]), '\x1b[38;5;90;3m \x1b[m')
        self.assertEqual(str(s[5]), '\x1b[38;5;90;3;1ms\x1b[m')

    def test_settings_at(self):
        s=AnsiString('This string will be formatted italic and purple', ['purple', 'italic'])
        s.apply_formatting('bold', 5, 11)
        self.assertEqual(s.settings_at(4), '38;5;90;3')
        self.assertEqual(s.settings_at(5), '38;5;90;3;1')

    def test_settings_at_no_format(self):
        s=AnsiString('String without format')
        self.assertEqual(s.settings_at(3), '')

    def test_settings_at_out_of_range_high(self):
        s=AnsiString('String without format', 'red')
        self.assertEqual(s.settings_at(21), '')

    def test_settings_at_out_of_range_low(self):
        s=AnsiString('String without format', 'orange')
        self.assertEqual(s.settings_at(-1), '')

    def test_iterate(self):
        s = AnsiString('one ', 'bg_yellow') + AnsiString('two ', AnsiFormat.UNDERLINE) + AnsiString('three', '1')
        s2 = AnsiString()
        # Recreate the original string by iterating the characters
        for c in s:
            s2 += c
        # This will look the same, even though each character now has formatting
        self.assertEqual(
            str(s2),
            '\x1b[43mo\x1b[0;43mn\x1b[0;43me\x1b[0;43m \x1b[0;4mt\x1b[0;4mw\x1b[0;4mo\x1b[0;4m \x1b[0;1mt\x1b[0;1mh'
            '\x1b[0;1mr\x1b[0;1me\x1b[0;1me\x1b[m'
        )
        self.assertIsNot(s, s2)

    def test_apply_string_equal_length(self):
        s = AnsiString('a', 'red') + AnsiString('b', 'green') + AnsiString('c', 'blue')
        s.assign_str('xyz')
        self.assertEqual(str(s), '\x1b[31mx\x1b[0;32my\x1b[0;34mz\x1b[m')

    def test_apply_larger_string(self):
        s = AnsiString('a', 'red') + AnsiString('b', 'green') + AnsiString('c', 'blue')
        s.assign_str('xxxxxx')
        self.assertEqual(str(s), '\x1b[31mx\x1b[0;32mx\x1b[0;34mxxxx\x1b[m')

    def test_apply_shorter_string(self):
        s = AnsiString('a', 'red') + AnsiString('b', 'green') + AnsiString('c', 'blue')
        s.assign_str('x')
        self.assertEqual(str(s), '\x1b[31mx\x1b[m')

    def test_remove_prefix_inplace(self):
        s = AnsiString('blah blah', AnsiFormat.ALT_FONT_4)
        s.apply_formatting(AnsiFormat.ANTIQUE_WHITE, 1, 2)
        s.apply_formatting(AnsiFormat.AQUA, 2, 3)
        s.apply_formatting(AnsiFormat.BEIGE, 3, 4)
        s.apply_formatting(AnsiFormat.BG_DARK_GRAY, 4, 5)
        s2 = s.removeprefix('blah', inplace=True)
        self.assertEqual(str(s), '\x1b[14;48;2;169;169;169m \x1b[0;14mblah\x1b[m')
        self.assertIs(s, s2)

    def test_remove_prefix_not_found(self):
        s = AnsiString('blah blah', AnsiFormat.ALT_FONT_4)
        s2 = s.removeprefix('nah')
        self.assertEqual(str(s), '\x1b[14mblah blah\x1b[m')
        self.assertIsNot(s, s2)

    def test_remove_suffix_inplace(self):
        s = AnsiString('blah blah', AnsiFormat.ALT_FONT_4, 'blue')
        s2 = s.removesuffix('blah', inplace=True)
        self.assertEqual(str(s), '\x1b[14;34mblah \x1b[m')
        self.assertIs(s, s2)

    def test_remove_suffix_not_found(self):
        s = AnsiString('blah blah', AnsiFormat.ALT_FONT_4)
        s2 = s.removesuffix('nah')
        self.assertEqual(str(s), '\x1b[14mblah blah\x1b[m')
        self.assertIsNot(s, s2)

    def test_cat_edge_case(self):
        a = AnsiString('a', 'red')
        b = AnsiString('b', 'red')
        c = a + b
        self.assertEqual(str(c), '\x1b[31ma\x1b[0;31mb\x1b[m')


if __name__ == '__main__':
    unittest.main()
