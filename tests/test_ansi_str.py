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
from ansi_string import en_tty_ansi, AnsiFormat, AnsiString, AnsiStr, ColorComponentType, ColourComponentType

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

class AnsiStrTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        AnsiString.WITH_ASSERTIONS = True

    def test_verify_assertions_enabled(self):
        # Sanity check
        self.assertTrue(AnsiString.WITH_ASSERTIONS)

    def test_en_tty_ansi(self):
        # Not a very useful test
        en_tty_ansi()

    def test_no_format(self):
        s = AnsiStr('No format')
        self.assertEqual(str(s), 'No format')

    def test_from_ansi_string(self):
        s = AnsiStr('\x1b[32mabc\x1b[m')
        self.assertEqual(str(s), '\x1b[32mabc\x1b[m')
        self.assertEqual(s.base_str, 'abc')

    def test_using_AnsiFormat(self):
        s = AnsiStr('This is bold', AnsiFormat.BOLD)
        self.assertEqual(str(s), '\x1b[1mThis is bold\x1b[m')

    def test_using_list_of_AnsiFormat(self):
        s = AnsiStr('This is bold and red', [AnsiFormat.BOLD, AnsiFormat.RED])
        self.assertEqual(str(s), '\x1b[1;31mThis is bold and red\x1b[m')

    def test_using_list_of_various(self):
        s = AnsiStr('Lots of formatting!', ['[1', AnsiFormat.UL_RED, 'rgb(0x12A03F);bg_white'])
        self.assertEqual(str(s), '\x1b[1;4;58;5;9;38;2;18;160;63;47mLots of formatting!\x1b[m')

    def test_custom_formatting(self):
        s = AnsiStr('This string contains custom formatting', '[38;2;175;95;95')
        self.assertEqual(str(s), '\x1b[38;2;175;95;95mThis string contains custom formatting\x1b[m')

    def test_ranges(self):
        s = AnsiStr('This string contains multiple color settings across different ranges')
        s = s.apply_formatting(AnsiFormat.BOLD, 5, 11)
        s = s.apply_formatting(AnsiFormat.BG_BLUE, 21, 29)
        s = s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
        self.assertEqual(
            str(s),
            'This \x1b[1mstring\x1b[m contains \x1b[44;38;5;214;3mmultiple\x1b[0;38;5;214;3m color\x1b[m settings '
            'across different ranges'
        )

    def test_format_right_only(self):
        s = AnsiStr('This has no ANSI formatting')
        self.assertEqual(
            f'{s:#>90}',
            '###############################################################This has no ANSI formatting'
        )

    def test_format_right_justify_and_int(self):
        s = AnsiStr('This string will be formatted bold and red, right justify')
        self.assertEqual(
            f'{s:>90:01;31}',
            '\x1b[1;31m                                 This string will be formatted bold and red, right justify\x1b[m'
        )

    def test_format_left_justify_and_strings(self):
        s = AnsiStr('This string will be formatted bold and red', 'bold')
        self.assertEqual(
            '{:+<90:fg_red}'.format(s),
            '\x1b[1;31mThis string will be formatted bold and red++++++++++++++++++++++++++++++++++++++++++++++++\x1b[m'
        )

    def test_format_center_and_verbatim_string(self):
        s = AnsiStr('This string will be formatted bold and red')
        self.assertEqual(
            '{:*^90:[this is not parsed}'.format(s),
            '\x1b[this is not parsedm************************This string will be formatted bold and red************************\x1b[m'
        )

    def test_no_format_and_rgb_functions(self):
        s = AnsiStr('Manually adjust colors of foreground, background, and underline')
        self.assertEqual(
            f'{s::rgb(0x8A2BE2);bg_rgb(100, 232, 170);ul_rgb(0xFF, 0x63, 0x47)}',
            '\x1b[38;2;138;43;226;48;2;100;232;170;4;58;2;255;99;71mManually adjust colors of foreground, background, and underline\x1b[m'
        )

    def test_no_format_and_rgb_functions2(self):
        s = AnsiStr('Manually adjust colors of foreground, background, and underline')
        fg_color = 0x8A2BE2
        bg_colors = (100, 232, 170)
        ul_colors = [0xFF, 0x63, 0x47]
        self.assertEqual(
            f'{s::rgb({fg_color});bg_rgb({bg_colors});ul_rgb({ul_colors})}',
            '\x1b[38;2;138;43;226;48;2;100;232;170;4;58;2;255;99;71mManually adjust colors of foreground, background, and underline\x1b[m'
        )

    def test_add(self):
        s = AnsiStr('bold', 'bold') + AnsiStr('red', 'red')
        self.assertEqual(
            str(s),
            '\x1b[1mbold\x1b[0;31mred\x1b[m'
        )

    def test_add_ansistring(self):
        s = AnsiStr('bold', 'bold') + AnsiString('red', 'red')
        self.assertEqual(
            str(s),
            '\x1b[1mbold\x1b[0;31mred\x1b[m'
        )

    def test_iadd(self):
        s = AnsiStr('part bold')
        s = s.apply_formatting(AnsiFormat.BOLD, 0, 3)
        s += AnsiStr('red', 'red')
        self.assertEqual(
            str(s),
            '\x1b[1mpar\x1b[mt bold\x1b[31mred\x1b[m'
        )

    def test_iadd_ansistring(self):
        s = AnsiStr('part bold')
        s = s.apply_formatting(AnsiFormat.BOLD, 0, 3)
        s += AnsiString('red', 'red')
        self.assertEqual(
            str(s),
            '\x1b[1mpar\x1b[mt bold\x1b[31mred\x1b[m'
        )

    def test_eq(self):
        s=AnsiStr('red', 'red')
        self.assertEqual(s, AnsiStr('red', AnsiFormat.FG_RED))

    def test_neq(self):
        s=AnsiStr('red', 'red')
        self.assertNotEqual(s, AnsiStr('red', AnsiFormat.BG_RED))

    def test_center(self):
        s = AnsiStr('This string will be formatted bold and red', 'bold;red')
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

    def test_ljust(self):
        s = AnsiStr('This string will be formatted bold and red', 'bold;red')
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

    def test_rjust(self):
        s = AnsiStr('This string will be formatted bold and red', 'bold;red')
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

    def test_strip(self):
        s = AnsiStr('    T\t\r\n \v\f', 'bold;red')
        s2 = s.strip()
        self.assertEqual(str(s2), '\x1b[1;31mT\x1b[m')
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31m    T\t\r\n \x0b\x0c\x1b[m'
        )

    def test_strip_all(self):
        s = AnsiStr('    ', 'bold;red')
        s2 = s.strip()
        self.assertEqual(str(s2), '')

    def test_strip_no_right(self):
        s = AnsiStr('    b', 'bold;red')
        s2 = s.strip()
        self.assertEqual(str(s2), '\x1b[1;31mb\x1b[m')

    def test_strip_no_change(self):
        s = AnsiStr('b', 'bold;red')
        s2 = s.strip()
        self.assertEqual(str(s2), '\x1b[1;31mb\x1b[m')

    def test_lstrip(self):
        s = AnsiStr('    T\t\r\n \v\f', 'bold;red')
        s2 = s.lstrip()
        self.assertEqual(str(s2), '\x1b[1;31mT\t\r\n \v\f\x1b[m')
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31m    T\t\r\n \x0b\x0c\x1b[m'
        )

    def test_lstrip_all(self):
        s = AnsiStr(' \t   ', 'bold;red')
        s2 = s.lstrip()
        self.assertEqual(str(s2), '')

    def test_rstrip(self):
        s = AnsiStr('    T\t\r\n \v\f', 'bold;red')
        s2 = s.rstrip()
        self.assertEqual(str(s2), '\x1b[1;31m    T\x1b[m')
        self.assertIsNot(s, s2)
        self.assertEqual(
            str(s),
            '\x1b[1;31m    T\t\r\n \x0b\x0c\x1b[m'
        )

    def test_rstrip_all(self):
        s = AnsiStr(' \n   ', 'bold;red')
        s2 = s.rstrip()
        self.assertEqual(str(s2), '')

    def test_partition_found(self):
        s = AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s_orig = s
        out = s.partition('will')
        self.assertEqual(
            [str(s) for s in out],
            ['\x1b[38;5;90;3mThis string \x1b[m', '\x1b[38;5;90;3mwill\x1b[m', '\x1b[38;5;90;3m be formatted italic and purple\x1b[m']
        )
        self.assertIs(s, s_orig)

    def test_partition_not_found(self):
        s = AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s_orig = s
        out = s.partition('bella')
        self.assertEqual(
            [str(s) for s in out],
            ['\x1b[38;5;90;3mThis string will be formatted italic and purple\x1b[m', '', '']
        )
        self.assertIs(s, s_orig)

    def test_rpartition_found(self):
        s = AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s_orig = s
        out = s.rpartition('l')
        self.assertEqual(
            [str(s) for s in out],
            ['\x1b[38;5;90;3mThis string will be formatted italic and purp\x1b[m', '\x1b[38;5;90;3ml\x1b[m', '\x1b[38;5;90;3me\x1b[m']
        )
        self.assertIs(s, s_orig)

    def test_rpartition_not_found(self):
        s = AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s_orig = s
        out = s.rpartition('x')
        self.assertEqual(
            [str(s) for s in out],
            ['\x1b[38;5;90;3mThis string will be formatted italic and purple\x1b[m', '', '']
        )
        self.assertIs(s, s_orig)


    def test_get_item_edge_case(self):
        # There used to be a bug where if a single character was retrieved right before the index where a new format was
        # applied, it add a remove setting for something that didn't exist yet
        s=AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s = s.apply_formatting('bold', 5, 11)
        self.assertEqual(str(s[4]), '\x1b[38;5;90;3m \x1b[m')
        self.assertEqual(str(s[5]), '\x1b[38;5;90;3;1ms\x1b[m')

    def test_settings_at(self):
        s=AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s = s.apply_formatting('bold', 5, 11)
        self.assertEqual(s.settings_at(4), '38;5;90;3')
        self.assertEqual(s.settings_at(5), '38;5;90;3;1')

    def test_settings_at_no_format(self):
        s=AnsiStr('dsfoi sdfsdfksjdbf')
        s = s.apply_formatting('red', 4)
        self.assertEqual(s.settings_at(3), '')

    def test_settings_at_out_of_range_high(self):
        s=AnsiStr('aradfghsdfgsdfgdsfgdf', 'red')
        self.assertEqual(s.settings_at(21), '')

    def test_settings_at_out_of_range_low(self):
        s=AnsiStr('gvcsxghfwraedtygxc', 'orange')
        self.assertEqual(s.settings_at(-1), '')

    def test_iterate(self):
        s = AnsiStr('one ', 'bg_yellow') + AnsiStr('two ', AnsiFormat.UNDERLINE) + AnsiStr('three', '1')
        s2 = AnsiStr()
        # Recreate the original string by iterating the characters
        for c in s:
            s2 += c
        # This will look the same, even though each character now has formatting
        self.assertEqual(str(s2), str(s))
        self.assertIsNot(s, s2)

    def test_remove_prefix_not_found(self):
        s = AnsiStr('blah blah', AnsiFormat.ALT_FONT_4)
        s2 = s.removeprefix('nah')
        self.assertEqual(str(s), '\x1b[14mblah blah\x1b[m')
        self.assertIsNot(s, s2)

    def test_remove_suffix_not_found(self):
        s = AnsiStr('blah blah', AnsiFormat.ALT_FONT_4)
        s2 = s.removesuffix('nah')
        self.assertEqual(str(s), '\x1b[14mblah blah\x1b[m')
        self.assertIsNot(s, s2)

    def test_cat_edge_case(self):
        a = AnsiStr('a', 'red')
        b = AnsiStr('b', 'red')
        # Two string with same formatting should merge formatting properly
        c = a + b
        self.assertEqual(str(c), '\x1b[31mab\x1b[m')

    def test_cat_edge_case2(self):
        # The beginning of the RHS string contains the same formatting of the LHS string, but ends before last char
        a = AnsiStr('abc', 'red', 'bold')
        b = AnsiStr('xyz')
        b = b.apply_formatting('red', end=-2)
        b = b.apply_formatting('bold', end=-1)
        c = a + b
        self.assertEqual(str(c), '\x1b[31;1mabcx\x1b[0;1my\x1b[mz')

    def test_replace(self):
        s=AnsiStr('This string will be formatted italic and purple', ['purple', 'italic'])
        s2 = s.replace('formatted', AnsiStr('formatted', 'bg_red'))
        self.assertEqual(str(s2), '\x1b[38;5;90;3mThis string will be \x1b[0;41mformatted\x1b[0;38;5;90;3m italic and purple\x1b[m')
        self.assertEqual(str(s), '\x1b[38;5;90;3mThis string will be formatted italic and purple\x1b[m')

    def test_split_whitespace(self):
        s = AnsiStr('\t this  \t\nstring contains\tmany\r\n\f\vspaces ', 'red', 'bold')
        splits = s.split()
        self.assertEqual(
            [str(s) for s in splits],
            ['\x1b[31;1mthis\x1b[m','\x1b[31;1mstring\x1b[m','\x1b[31;1mcontains\x1b[m','\x1b[31;1mmany\x1b[m','\x1b[31;1mspaces\x1b[m']
        )

    def test_split_colon(self):
        s = AnsiStr(':::this string: contains : colons:::', 'red', 'bold')
        splits = s.split(':')
        self.assertEqual(
            [str(s) for s in splits],
            ['', '', '', '\x1b[31;1mthis string\x1b[m', '\x1b[31;1m contains \x1b[m', '\x1b[31;1m colons\x1b[m', '', '', '']
        )

    def test_rsplit(self):
        s = AnsiStr(':::this string: contains : colons', 'red', 'bold')
        splits = s.rsplit(':', 1)
        self.assertEqual(
            [str(s) for s in splits],
            ['\x1b[31;1m:::this string: contains \x1b[m', '\x1b[31;1m colons\x1b[m']
        )

    def test_splitlines(self):
        s = AnsiStr('\nthis string\ncontains\nmany lines\n\n\n', 'red', 'bold')
        splits = s.splitlines()
        self.assertEqual(
            [str(s) for s in splits],
            ['', '\x1b[31;1mthis string\x1b[m', '\x1b[31;1mcontains\x1b[m', '\x1b[31;1mmany lines\x1b[m', '', '']
        )

    def test_title(self):
        s = AnsiStr('make this String a title for some book', 'red', 'bold')
        s2 = s.title()
        self.assertEqual(str(s2), '\x1b[31;1mMake This String A Title For Some Book\x1b[m')
        self.assertEqual(str(s), '\x1b[31;1mmake this String a title for some book\x1b[m')

    def test_capitalize(self):
        s = AnsiStr('make this String a title for some book', 'red', 'bold')
        s2 = s.capitalize()
        self.assertEqual(str(s2), '\x1b[31;1mMake this string a title for some book\x1b[m')
        self.assertEqual(str(s), '\x1b[31;1mmake this String a title for some book\x1b[m')

    def test_cat_edge_case3(self):
        # There was a bug when copy() was used and the string didn't start with any formatting
        s = AnsiStr.join('This ', AnsiStr('string', AnsiFormat.ORANGE), ' contains ')
        s = s + AnsiStr('multiple', AnsiFormat.BG_BLUE)
        self.assertEqual(str(s), 'This \x1b[38;5;214mstring\x1b[m contains \x1b[44mmultiple\x1b[m')

    def test_format_matching(self):
        s = AnsiStr('Here is a string that I will match formatting')
        s = s.format_matching('InG', 'cyan', AnsiFormat.BG_PINK)
        self.assertEqual(
            str(s),
            'Here is a str\x1b[36;48;2;255;192;203ming\x1b[m that I will match formatt\x1b[36;48;2;255;192;203ming\x1b[m'
        )

    def test_format_matching_w_count1(self):
        s = AnsiStr('Here is a string that I will match formatting')
        s = s.format_matching('InG', 'cyan', AnsiFormat.BG_PINK, count=1)
        self.assertEqual(
            str(s),
            'Here is a str\x1b[36;48;2;255;192;203ming\x1b[m that I will match formatting'
        )

    def test_format_matching_ensure_escape(self):
        s = AnsiStr('Here is a (string) that I will match formatting')
        s = s.format_matching('(string)', 'cyan', AnsiFormat.BG_PINK)
        self.assertEqual(
            str(s),
            'Here is a \x1b[36;48;2;255;192;203m(string)\x1b[m that I will match formatting'
        )

    def test_format_matching_case_sensitive(self):
        s = AnsiStr('Here is a strING that I will match formatting')
        s = s.format_matching('ing', 'cyan', AnsiFormat.BG_PINK, match_case=True)
        self.assertEqual(
            str(s),
            'Here is a strING that I will match formatt\x1b[36;48;2;255;192;203ming\x1b[m'
        )

    def test_format_matching_regex_match_case(self):
        s = AnsiStr('Here is a strING that I will match formatting')
        s = s.format_matching('[A-Za-z]+ing', 'cyan', AnsiFormat.BG_PINK, regex=True, match_case=True)
        self.assertEqual(
            str(s),
            'Here is a strING that I will match \x1b[36;48;2;255;192;203mformatting\x1b[m'
        )

    def test_setting_eq_str(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertEqual(s.settings_at(0), '48;2;222;184;135')

    def test_rfind(self):
        s = AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0))
        result = s.rfind('ll')
        self.assertEqual(result, 8)

    def test_find(self):
        s = AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0))
        result = s.find('ll')
        self.assertEqual(result, 2)

    def test_index(self):
        s = AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0))
        result = s.index('ll')
        self.assertEqual(result, 2)

    def test_rindex(self):
        s = AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0))
        result = s.rindex('ll')
        self.assertEqual(result, 8)

    def test_upper(self):
        s = AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0))
        s2 = s.upper()
        self.assertEqual(
            str(s2),
            '\x1b[38;2;0;0;0mHELLO HELLO\x1b[m'
        )
        self.assertIsNot(s, s2)

    def test_lower(self):
        s = AnsiStr('HELLO HELLO', AnsiFormat.rgb(0, 0, 0))
        s2 = s.lower()
        self.assertEqual(
            str(s2),
            '\x1b[38;2;0;0;0mhello hello\x1b[m'
        )
        self.assertIsNot(s, s2)

    def test_join_no_args(self):
        s = AnsiStr.join()
        self.assertEqual(str(s), '')

    def test_join_AnsiString_first_arg(self):
        s = AnsiStr.join(AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0)))
        self.assertEqual(str(s), '\x1b[38;2;0;0;0mhello hello\x1b[m')

    def test_in_w_str_true(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertIn('is', s)

    def test_in_w_str_false(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertNotIn('the', s)

    def test_in_w_AnsiString_true(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertIn(AnsiStr('is'), s)

    def test_in_w_AnsiString_false(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertNotIn(AnsiStr('the'), s)

    def test_eq_int(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertNotEqual(s, 1)

    def test_is_upper_true(self):
        s = AnsiStr('HELLO HELLO', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isupper())

    def test_is_upper_false(self):
        s = AnsiStr('hELLO HELLO', AnsiFormat.rgb(0, 0, 0))
        self.assertFalse(s.isupper())

    def test_is_lower_true(self):
        s = AnsiStr('hello hello', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.islower())

    def test_is_lower_false(self):
        s = AnsiStr('Hello', AnsiFormat.rgb(0, 0, 0))
        self.assertFalse(s.islower())

    def test_is_title_true(self):
        s = AnsiStr('Hello Hello', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.istitle())

    def test_is_title_false(self):
        s = AnsiStr('Hello hello', AnsiFormat.rgb(0, 0, 0))
        self.assertFalse(s.istitle())

    def test_is_space_true(self):
        s = AnsiStr(' ', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isspace())

    def test_is_printable_true(self):
        s = AnsiStr(' dsfasdf', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isprintable())

    def test_is_numeric_true(self):
        s = AnsiStr('1', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isnumeric())

    def test_is_digit_true(self):
        s = AnsiStr('1', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isdigit())

    def test_is_decimal_true(self):
        s = AnsiStr('1', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isdecimal())

    def test_is_identifier_true(self):
        s = AnsiStr('AnsiStr', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isidentifier())

    # Removed this test to be compatible with Python 3.6
    # def test_is_ascii_true(self):
    #     s = AnsiStr('1', AnsiFormat.rgb(0, 0, 0))
    #     self.assertTrue(s.isascii())

    def test_is_alpha_true(self):
        s = AnsiStr('a', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isalpha())

    def test_is_alnum_true(self):
        s = AnsiStr('1', AnsiFormat.rgb(0, 0, 0))
        self.assertTrue(s.isalnum())

    def test_expand_tabs(self):
        s = AnsiStr('\ta\tb\n\tc', AnsiFormat.rgb(0, 0, 0))
        s = s.expandtabs(4)
        self.assertEqual(str(s), '\x1b[38;2;0;0;0m    a    b\n    c\x1b[m')

    def test_endswith(self):
        s = AnsiStr('This is an ansi string', 'BG_BURLY_WOOD')
        self.assertTrue(s.endswith('string'))

    def test_encode(self):
        s = AnsiStr('Hello Hello', 'bold')
        self.assertEqual(s.encode(), b'\x1b[1mHello Hello\x1b[m')

    def test_count(self):
        s = AnsiStr('Hello Hello mmm', 'bold')
        self.assertEqual(s.count('m'), 3)

    def test_base_str(self):
        s = AnsiStr('Hello Hello', 'bold')
        self.assertEqual(s.base_str, 'Hello Hello')

    def test_remove_settings(self):
        s = AnsiStr('Hello Hello', 'bold', AnsiFormat.RED)
        s = s.remove_formatting(AnsiFormat.BOLD, 2, 4)
        self.assertEqual(str(s), '\x1b[1;31mHe\x1b[0;31mll\x1b[31;1mo Hello\x1b[m')

    def test_remove_settings_end(self):
        s = AnsiStr('Hello Hello', 'bold', AnsiFormat.RED)
        s = s.remove_formatting(AnsiFormat.BOLD, 2)
        self.assertEqual(str(s), '\x1b[1;31mHe\x1b[0;31mllo Hello\x1b[m')

    def test_remove_settings_begin(self):
        s = AnsiStr('Hello Hello', 'bold', AnsiFormat.RED)
        s = s.remove_formatting(AnsiFormat.BOLD, end=2)
        self.assertEqual(str(s), '\x1b[31mHe\x1b[31;1mllo Hello\x1b[m')

    def test_remove_settings_entire_range(self):
        s = AnsiStr('Hello Hello', 'bold', AnsiFormat.RED)
        s = s.remove_formatting(AnsiFormat.BOLD)
        self.assertEqual(str(s), '\x1b[31mHello Hello\x1b[m')

    def test_remove_settings_entire_range_overlap(self):
        s = AnsiStr('Hello Hello', AnsiFormat.RED)
        s = s.apply_formatting(AnsiFormat.BOLD, 1, 3)
        s = s.remove_formatting(AnsiFormat.BOLD)
        self.assertEqual(str(s), '\x1b[31mHello Hello\x1b[m')

    def test_remove_settings_none(self):
        s = AnsiStr('Hello Hello', AnsiFormat.RED)
        s = s.remove_formatting(AnsiFormat.BOLD)
        self.assertEqual(str(s), '\x1b[31mHello Hello\x1b[m')

    def test_remove_settings_multiple(self):
        s = AnsiStr('Hello Hello', AnsiFormat.RED)
        s = s.apply_formatting(AnsiFormat.RED, 1, -1)
        s = s.remove_formatting(AnsiFormat.RED, 1, -1)
        self.assertEqual(str(s), '\x1b[31mH\x1b[mello Hell\x1b[31mo\x1b[m')

    def test_remove_settings_outside_range(self):
        s = AnsiStr('Hello Hello')
        s = s.apply_formatting(AnsiFormat.RED, 0, 3)
        s = s.remove_formatting(AnsiFormat.RED, start=-1)
        self.assertEqual(str(s), '\x1b[31mHel\x1b[mlo Hello')

    def test_remove_settings_all(self):
        s = AnsiStr('Hello Hello', AnsiFormat.RED)
        s = s.apply_formatting(AnsiFormat.BOLD, 1, 3)
        s = s.apply_formatting(AnsiFormat.BOLD, start=-1)
        s = s.apply_formatting(AnsiFormat.RED, 0, 3)
        s = s.remove_formatting(start=2)
        self.assertEqual(str(s), '\x1b[31mH\x1b[31;1me\x1b[mllo Hello')

    def test_unformat_matching(self):
        s = AnsiStr('Here is a string that I will unformat matching', AnsiFormat.CYAN, AnsiFormat.BOLD)
        s = s.apply_formatting([AnsiFormat.BG_PINK], 38)
        s = s.unformat_matching('ing', 'cyan', AnsiFormat.BG_PINK)
        self.assertEqual(
            str(s),
            '\x1b[36;1mHere is a str\x1b[0;1ming\x1b[1;36m that I will unformat \x1b[1;36;48;2;255;192;203mmatch\x1b[0;1ming\x1b[m'
        )

    def test_unformat_matching_w_count1(self):
        s = AnsiStr('Here is a string that I will unformat matching', AnsiFormat.CYAN, AnsiFormat.BOLD)
        s = s.apply_formatting([AnsiFormat.BG_PINK], 38)
        s = s.unformat_matching('ing', 'cyan', AnsiFormat.BG_PINK, count=1)
        self.assertEqual(
            str(s),
            '\x1b[36;1mHere is a str\x1b[0;1ming\x1b[1;36m that I will unformat \x1b[1;36;48;2;255;192;203mmatching\x1b[m'
        )


    # Exceptions tests

    def test_AnsiFormat_rgb_r_not_set(self):
        with self.assertRaises(ValueError):
            AnsiFormat.rgb(None)

    def test_AnsiFormat_rgb_g_without_b(self):
        with self.assertRaises(ValueError):
            AnsiFormat.rgb(100, 100)

    def test_AnsiFormat_rgb_b_without_g(self):
        with self.assertRaises(ValueError):
            AnsiFormat.rgb(100, b=100)

    def test_invalid_rgb_values1(self):
        with self.assertRaises(ValueError):
            AnsiStr('!', 'rgb(F)')

    def test_invalid_rgb_values3(self):
        with self.assertRaises(ValueError):
            AnsiStr('!', 'rgb(0,0,F)')

    def test_invalid_int(self):
        with self.assertRaises(ValueError):
            AnsiStr('!', -1)

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            AnsiStr('!', 'no setting')

    def test_getitem_invalid_step_size(self):
        s = AnsiStr('!')
        with self.assertRaises(ValueError):
            s = s[0:1:2]

    def test_getitem_invalid_type(self):
        s = AnsiStr('!')
        with self.assertRaises(TypeError):
            s = s[""]

    def test_string_format_sign_not_allowed(self):
        s = AnsiStr('!')
        with self.assertRaises(ValueError):
            '{:^+10}'.format(s)

    def test_string_format_space_not_allowed(self):
        s = AnsiStr('!')
        with self.assertRaises(ValueError):
            '{:^ 10}'.format(s)

    def test_string_format_invalid(self):
        s = AnsiStr('!')
        with self.assertRaises(ValueError):
            '{:djhfjd}'.format(s)

    def test_cat_invalid_type(self):
        s = AnsiStr('!')
        with self.assertRaises(TypeError):
            s += 1

    def test_join_first_arg_invalid_type(self):
        with self.assertRaises(TypeError):
            AnsiStr.join(1)

    def test_simplify(self):
        s = AnsiStr('abc', 'green')
        s = s.apply_formatting('red')
        # String should automatically be simplified
        self.assertEqual(str(s), '\x1b[31mabc\x1b[m')

if __name__ == '__main__':
    unittest.main()
