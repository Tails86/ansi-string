# ansi-string

ANSI String Formatter in Python for CLI Color and Style Formatting

## Introduction

This code was originally written for [greplica](https://pypi.org/project/greplica/), but I felt it deserved its own, separate library.

The main goals for this project are:
- To provide a simple way to construct a string-like object with embedded ANSI formatting without requiring the developer to know how ANSI formatting works
- Provide a way to further format the object using format string
- Allow for concatenation of the object

## Contribution

Feel free to open a bug report or make a merge request on [github](https://github.com/Tails86/ansi-string/issues).

## Installation
This project is uploaded to PyPI at https://pypi.org/project/ansi-string

To install, ensure you are connected to the internet and execute: `python3 -m pip install ansi-string --upgrade`

## Examples

### AnsiString

#### Example 1
Code:
```py
from ansi_string import AnsiString
s = AnsiString('This string is red and bold', AnsiFormat.BOLD, AnsiFormat.RED)
print(s)
```
Output:
![Example 1 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out1.png)

#### Example 2

Code:
```py
from ansi_string import AnsiString, AnsiFormat
s = AnsiString.join('This ', AnsiString('string', AnsiFormat.BOLD))
s += AnsiString(' contains ') + AnsiString('multiple', AnsiFormat.BG_BLUE)
s += ' color settings across different ranges'
s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
# Blue and orange will conflict - blue applied on bottom, so orange will show for [21:35]
s.apply_formatting(AnsiFormat.FG_BLUE, 21, 44, topmost=False)
print(s)
```
Output:
![Example 2 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out2.png)

#### Example 3

Code:
```py
from ansi_string import AnsiString
s = AnsiString('This string will be formatted bold and red, right justify')
# An AnsiString format string uses the format: [string_format[:ansi_format]]
# For ansi_format, use any name within AnsiFormat and separate directives with semicolons
print('{:>90:bold;red}'.format(s))
```
Output:
![Example 3 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out3.png)

#### Example 4

Code:
```py
from ansi_string import AnsiString
s = AnsiString('This string will be formatted bold and red')
# Use double colon to skip specification of string_format
print('{::bold;red}'.format(s))
```
Output:
![Example 4 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out4.png)

#### Example 5

Code:
```py
from ansi_string import AnsiString
s1 = 'This is a normal string'
s2 = AnsiString('This is an ANSI string')
# AnsiString may also be used in an F-String
print(f'String 1: "{s1}" String 2: "{s2::bold;purple}"')
```
Output:
![Example 5 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out5.png)

#### Example 6

Code:
```py
from ansi_string import AnsiString
s = AnsiString('Manually adjust colors of foreground, background, and underline')
print(f'{s::rgb(0x8A2BE2);bg_rgb(100, 232, 170);ul_rgb(0xFF, 0x63, 0x47)}')
```
Output:
![Example 6 Output](https://raw.githubusercontent.com/Tails86/ansi-string/76fd7fe127ab65c2b0ff5215f1b1ce9e253d50e9/docs/out6.png)

#### Example 7

Code:
```py
from ansi_string import AnsiString, AnsiFormat
s = AnsiString(
    'This example shows how to format and unformat matching',
    AnsiFormat.dul_rgb(0xFF, 0x80, 0x00),
    AnsiFormat.ITALIC
)
s.format_matching('[a-z]*mat', AnsiFormat.RED, match_case=True, regex=True)
s.unformat_matching('unformat') # don't specify any format to remove all formatting in matching range
print(s)
```
Output:
![Example 7 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out7.png)

#### More Examples

Refer to the [AnsiString test file](https://github.com/Tails86/ansi-string/blob/main/tests/test_ansi_string.py) for more examples on how to use the AnsiString class.

### AnsiStr

AnsiStr is an immutable version of AnsiString. The advantage of this object is that isinstance(AnsiStr(), str) returns True. The disadvantage is that all formatting functionality return a new object rather than formatting in-place.

#### Example 1
Code:
```py
from ansi_string import AnsiStr
s = AnsiStr('This string is red and bold', AnsiFormat.BOLD, AnsiFormat.RED)
print(s)
```
Output:
![Example 1 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out1.png)

#### Example 2

Code:
```py
from ansi_string import AnsiStr, AnsiFormat
s = AnsiStr.join('This ', AnsiStr('string', AnsiFormat.BOLD))
s += AnsiStr(' contains ') + AnsiStr('multiple', AnsiFormat.BG_BLUE)
s += ' color settings across different ranges'
# Since AnsiStr is immutable, apply_formatting() returns a new object rather than formatting in-place
s = s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
# Blue and orange will conflict - blue applied on bottom, so orange will show for [21:35]
s = s.apply_formatting(AnsiFormat.FG_BLUE, 21, 44, topmost=False)
print(s)
```
Output:
![Example 2 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out2.png)

#### Example 3

Code:
```py
from ansi_string import AnsiStr
s = AnsiStr('This string will be formatted bold and red, right justify')
# An AnsiStr format string uses the format: [string_format[:ansi_format]]
# For ansi_format, use any name within AnsiFormat and separate directives with semicolons
print('{:>90:bold;red}'.format(s))
```
Output:
![Example 3 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out3.png)

#### Example 4

Code:
```py
from ansi_string import AnsiStr
s = AnsiStr('This string will be formatted bold and red')
# Use double colon to skip specification of string_format
print('{::bold;red}'.format(s))
```
Output:
![Example 4 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out4.png)

#### Example 5

Code:
```py
from ansi_string import AnsiStr
s1 = 'This is a normal string'
s2 = AnsiStr('This is an ANSI string')
# AnsiStr may also be used in an F-String
print(f'String 1: "{s1}" String 2: "{s2::bold;purple}"')
```
Output:
![Example 5 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out5.png)

#### Example 6

Code:
```py
from ansi_string import AnsiStr
s = AnsiStr('Manually adjust colors of foreground, background, and underline')
print(f'{s::rgb(0x8A2BE2);bg_rgb(100, 232, 170);ul_rgb(0xFF, 0x63, 0x47)}')
```
Output:
![Example 6 Output](https://raw.githubusercontent.com/Tails86/ansi-string/76fd7fe127ab65c2b0ff5215f1b1ce9e253d50e9/docs/out6.png)

#### Example 7

Code:
```py
from ansi_string import AnsiStr, AnsiFormat
s = AnsiStr(
    'This example shows how to format and unformat matching',
    AnsiFormat.dul_rgb(0xFF, 0x80, 0x00),
    AnsiFormat.ITALIC
)
# Since AnsiStr is immutable, these calls return a new object rather than formatting in-place
s = s.format_matching('[a-z]*mat', AnsiFormat.RED, match_case=True, regex=True)
s = s.unformat_matching('unformat') # don't specify any format to remove all formatting in matching range
print(s)
```
Output:
![Example 7 Output](https://raw.githubusercontent.com/Tails86/ansi-string/32d5b2fed1c1ac061a5382b80faa65bbf794290c/docs/out7.png)

#### More Examples

Refer to the [AnsiStr test file](https://github.com/Tails86/ansi-string/blob/main/tests/test_ansi_str.py) for examples on how to use AnsiStr.

## Usage

To begin, import `AnsiString` and/or `AnsiStr` from the ansi_string module.

```py
from ansi_string import en_tty_ansi, AnsiFormat, AnsiString, AnsiStr
```

### Enabling ANSI Formatting

Windows requires ANSI formatting to be enabled before it can be used. This can either be set in the environment or by simply calling the following before printing so that ANSI is enabled locally.
```py
en_tty_ansi()
```

If this also needs to be enabled for stderr, stderr may also be passed to this method.
```py
import sys
en_tty_ansi(sys.stderr)
```

For Windows, this returns True if the given IO is a TTY (i.e. not piped to a file) and enabling ANSI was successful. For all other operating systems, this will return True if and only if the given IO is a TTY (i.e. isatty()); no other action is taken.

### Construction

The AnsiString and AnsiStr classes contains the following `__init__` method.

```py
    def __init__(self, s:str='', *setting_or_settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat]): ...
```

The first argument, `s`, is a string to be formatted. The next 0 to N arguments are formatting setting directives that can be applied to the entire string. These arguments can be in the form of any of the following.

- An AnsiFormat enum (ex: `AnsiFormat.BOLD`)
- The result of calling `AnsiFormat.rgb()`, `AnsiFormat.fg_rgb()`, `AnsiFormat.bg_rgb()`,
    `AnsiFormat.ul_rgb()`, or `AnsiFormat.dul_rgb()`
- A string color or formatting name (i.e. any name of the AnsiFormat enum in lower or upper case)
- An `rgb(...)` function directive as a string (ex: `"rgb(255, 255, 255)"`)
    - `rgb(...)` or `fg_rgb(...)` to adjust text color
    - `bg_rgb(...)` to adjust background color
    - `ul_rgb(...)` to enable underline and set the underline color
    - `dul_rgb(...)` to enable double underline and set the underline color
    - Value given may be either a 24-bit integer or 3 x 8-bit integers, separated by commas
    - Each given value within the parenthesis is treated as hexadecimal if the value starts with "0x",
        otherwise it is treated as a decimal value
- A string containing known ANSI directives (ex: `"01;31"` for BOLD and FG_RED)
    - This string will be parsed, and all invalid values, including RESET (0), will be thrown out
- Integer values which will be parsed in a similar way to strings

A setting may also be any of the following, but these are not advised because they will be used verbatim,
and optimization of codes on string output will not occur.
- An AnsiSetting object
- A string which starts with the character `"["` plus ANSI directives (ex: `"[38;5;214"`)

Examples:

```py
# Set foreground to light_sea_green using string directive
# Set background to chocolate using AnsiFormat directive
# Underline in gray using ul_rgb() directive
# Enable italics using explicit string directive ("3")
# Enable bold using explicit integer directive (1)
s = AnsiString("This is an ANSI string", "light_sea_green", AnsiFormat.BG_CHOCOLATE, "ul_rgb(0x808080)", "3", 1)
print(s)
```

### Concatenation

- The static methods `AnsiString.join()` and `AnsiStr.join()` are provided to join together 0 to many `AnsiStr`, `AnsiString`, and `str` values into a single `AnsiString` or `AnsiStr`.
- The `+` operator may be used to join an `AnsiString` or `AnsiStr` with another `AnsiStr`, `AnsiString`, or `str` into a new object
    - The `+` operator may not be used if the left-hand-side value is a `str` and the right-hand-side values is an `AnsiString` or `AnsiStr`
- The `+=` operator may be used to append an `AnsiStr`, `AnsiString`, or `str` to an `AnsiString` or `AnsiStr`

Examples:

```py
s = AnsiString.join("This ", AnsiStr("string", AnsiFormat.BOLD))
s += AnsiStr(" contains ") + AnsiStr("multiple", AnsiFormat.BG_BLUE)
s += AnsiString(" color ", AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC) + "settings accross different ranges"
print(s)
```

### Formatting

#### apply_formatting

The method `AnsiString.apply_formatting()` is provided to append formatting to a previously constructed `AnsiString`. The method `AnsiStr.apply_formatting()` works similarly except it returns a new object since `AnsiStr` is immutable.

Example:

```py
s = AnsiString("This string contains multiple color settings across different ranges")
s.apply_formatting(AnsiFormat.BOLD, 5, 11)
s.apply_formatting(AnsiFormat.BG_BLUE, 21, 29)
s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
print(s)

# This will result in the same printout using AnsiStr instead of AnsiString
s = AnsiStr("This string contains multiple color settings across different ranges")
s = s.apply_formatting(AnsiFormat.BOLD, 5, 11)
s = s.apply_formatting(AnsiFormat.BG_BLUE, 21, 29)
s = s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
print(s)
```

#### Format String

A format string may be used to format an AnsiString before printing. The format specification string must be in the format `"[string_format][:ansi_format]"` where `string_format` is the standard string format specifier and `ansi_format` contains 0 or more ANSI directives separated by semicolons (;). The ANSI directives may be any of the same string values that can be passed to the `AnsiString` constructor. If no `string_format` is desired, then it can be set to an empty string. This same functionality is available in `AnsiStr`.

Examples:

```py
ansi_str = AnsiString("This is an ANSI string")
# Right justify with width of 100, formatted bold and red
print("{:>100:bold;red}".format(ansi_str))
# No justification settings, formatted bold and red
print("{::bold;red}".format(ansi_str))
# No justification settings, formatted bold and red
print("{::bold;rgb(255, 0, 0)}".format(ansi_str))
# No justification settings, formatted bold and red
print(f"{ansi_str::bold;red}")
# Format text, background, and underline with custom colors
fg_color = 0x8A2BE2
bg_colors = [100, 232, 170]
ul_colors = [0xFF, 0x63, 0x47]
print(f"{ansi_str::rgb({fg_color});bg_rgb({bg_colors});ul_rgb({ul_colors})}")
```

#### format_matching and unformat_matching

The methods `AnsiString.format_matching()` and `AnsiString.unformat_matching()` are provided to apply or remove formatting of an `AnsiString` based on a match specification. The methods `AnsiStr.format_matching()` and `AnsiStr.unformat_matching()` work similarly except they return a new object since `AnsiStr` is immutable.

Example:

```py
s = AnsiString("Here is a strING that I will match formatting", AnsiFormat.BOLD)
# This will make the word "formatting" cyan with a pink background
s.format_matching("[A-Za-z]+ing", "cyan", AnsiFormat.BG_PINK, regex=True, match_case=True)
# This will remove BOLD from "strING" and "formatting"
s.unformat_matching("[A-Za-z]+ing", AnsiFormat.BOLD, regex=True)
print(s)

# This will result in the same printout using AnsiStr instead of AnsiString
s = AnsiStr("Here is a strING that I will match formatting", AnsiFormat.BOLD)
# This will make the word "formatting" cyan with a pink background
s = s.format_matching("[A-Za-z]+ing", "cyan", AnsiFormat.BG_PINK, regex=True, match_case=True)
# This will remove BOLD from "strING" and "formatting"
s = s.unformat_matching("[A-Za-z]+ing", AnsiFormat.BOLD, regex=True)
print(s)
```

#### clear_formatting

Calling the method `AnsiString.clear_formatting()` will clear all formatting applied. The method `AnsiStr.clear_formatting()` works similarly except it returns a new object since `AnsiStr` is immutable.

### String Assignment

The method `AnsiString.assign_str()` may be used to assign the internal string and adjust formatting as necessary. There is no associated function available in `AnsiStr`.

### Base String Retrieval

The attributes `AnsiString.base_str` and `AnsiStr.base_str` may be used to retrieve the unformatted base string.

### Format Status

The methods `AnsiString.ansi_settings_at()` and `AnsiString.settings_at()` may be used to retrieve the settings applied over a single character. The same methods exist in `AnsiStr`.

### Other String Methods

Many other methods that are found in the `str` class such as `replace()` are available in `AnsiString` and `AnsiStr` which manipulate the string while applying formatting where necessary.

- capitalize
- casefold
- center
- count
- encode
- endswith
- expandtabs
- find
- index
- isalnum
- isalpha
- isascii
- isdecimal
- isdigit
- isidentifier
- islower
- isnumeric
- isprintable
- isspace
- istitle
- isupper
- ljust
- lower
- lstrip
- partition
- removeprefix
- removesuffix
- replace
- rfind
- rindex
- rjust
- rpartition
- rsplit
- rstrip
- split
- splitlines
- strip
- swapcase
- title
- upper
- zfill

## Other Functions

The following functions are provided to perform cursor or clear actions on the terminal.

- cursor_up_str
- cursor_down_str
- cursor_forward_str
- cursor_backward_str
- cursor_back_str
- cursor_next_line_str
- cursor_previous_line_str
- cursor_horizontal_absolute_str
- cursor_position_str
- erase_in_display_str
- erase_in_line_str
- scroll_up_str
- scroll_down_str

### Example

```py
from ansi_string import cursor_up_str
# Move cursor up 5 lines
print(cursor_up_str(5), end='')
```
