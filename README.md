# ansi_string

ANSI String Formatter in Python for CLI Color and Style Formatting

**Table of Contents**
* [Introduction](#introduction)
* [Contribution](#contribution)
* [Installation](#installation)
* [Examples](#examples)
* [Usage](#usage)

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

These examples assume that ANSI formatting is enabled on the terminal. Refer to [Enabling ANSI Formatting](#enabling-ansi-formatting) to ensure this is enabled.

### Example 1

Code:
```py
from ansi_string import AnsiString
s = AnsiString('This string is red and bold', AnsiFormat.BOLD, AnsiFormat.RED)
print(s)
```
Output:
![Example 1 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out1.png)

### Example 2

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
![Example 2 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out2.png)

### Example 3

Code:
```py
from ansi_string import AnsiString
s = AnsiString('This string will be formatted bold and red, right justify')
# An AnsiString format string uses the format: [string_format[:ansi_format]]
# For ansi_format, use any name within AnsiFormat and separate directives with semicolons
print('{:>90:bold;red}'.format(s))
```
Output:
![Example 3 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out3.png)

### Example 4

Code:
```py
from ansi_string import AnsiString
s = AnsiString('This string will be formatted bold and red')
# Use double colon to skip specification of string_format
print('{::bold;red}'.format(s))
```
Output:
![Example 4 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out4.png)

### Example 5

Code:
```py
from ansi_string import AnsiString
s1 = 'This is a normal string'
s2 = AnsiString('This is an ANSI string')
# AnsiString may also be used in an F-String
print(f'String 1: "{s1}" String 2: "{s2::bold;purple}"')
```
Output:
![Example 5 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out5.png)

### Example 6

Code:
```py
from ansi_string import AnsiString
s = AnsiString('Manually adjust colors of foreground, background, and underline')
print(f'{s::rgb(0x8A2BE2);bg_rgb(100, 232, 170);ul_rgb(0xFF, 0x63, 0x47)}')
```
Output:
![Example 6 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out6.png)

### Example 7

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
![Example 7 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out7.png)

### Example 8

Code:
```py
from ansi_string import AnsiString, AnsiFormat
import itertools
colors = [AnsiFormat.RED, AnsiFormat.ORANGE, AnsiFormat.YELLOW, AnsiFormat.GREEN, AnsiFormat.BLUE, AnsiFormat.INDIGO, AnsiFormat.VIOLET]
s = AnsiString('IMAGINATION', AnsiFormat.BOLD)
for i, color in zip(range(len(s)), itertools.cycle(colors)):
    s.apply_formatting(color, i, i+1)
print(s)
```
Output:
![Example 8 Output](https://raw.githubusercontent.com/Tails86/ansi-string/30f950ed81aef46e9d4ca993740f3dc8caedfdc3/docs/out8.png)

## Usage

## Enabling ANSI Formatting

Windows requires ANSI formatting to be enabled before it can be used. This can be locally enabled by calling the following before printing.
```py
en_tty_ansi()
```

If this also needs to be enabled for stderr, stderr may also be passed to this method.
```py
import sys
en_tty_ansi(sys.stderr)
```

For Windows, this returns True if the given IO is a TTY (i.e. not piped to a file) and enabling ANSI was successful. For all other operating systems, this will return True if and only if the given IO is a TTY (i.e. isatty()); no other action is taken.

## AnsiString and AnsiStr Classes

This library contains both `AnsiString` and `AnsiStr`. An `AnsiString` is mutable while an `AnsiStr` is immutable, and any formatting changes to `AnsiStr` will create a new `AnsiStr` object rather than applying in-place. The only advantage of `AnsiStr` over `AnsiString` is that `isinstance(AnsiStr(), str)` will return `True`. This may be useful when the string object needs to be passable to functions and methods which explicitly checks if the given object is a string.

### Construction

The `AnsiString` and `AnsiStr` classes contain the following `__init__` method.

```py
def __init__(self, s:Union[str,'AnsiString','AnsiStr']='', *settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple]): ...
```

The first argument, `s`, is a string to be formatted. If this string contains ANSI directives, they will be parsed and added into the internal format dictionary. The next 0 to N arguments are formatting setting directives that can be applied to the entire string. These arguments can be in the form of any of the following.

- The following setting types are guaranteed to be valid, optimizable, and won't throw any exception
    - An AnsiFormat enum (ex: `AnsiFormat.BOLD`)
    - The result of calling `AnsiFormat.rgb()`, `AnsiFormat.fg_rgb()`, `AnsiFormat.bg_rgb()`, `AnsiFormat.ul_rgb()`, or `AnsiFormat.dul_rgb()`
    - The result of calling `AnsiFormat.color256()`, `AnsiFormat.fg_color256()`, `AnsiFormat.bg_color256()`, `AnsiFormat.ul_color256()`, `AnsiFormat.dul_color256()`, or `*colour256()` counterparts
- The following setting types are parsed and may throw and exception if they are invalid
    - A string color or formatting name (i.e. any name of the AnsiFormat enum in lower or upper case)
    - An `rgb(...)` function directive as a string (ex: `"rgb(255, 255, 255)"`)
        - `rgb(...)` or `fg_rgb(...)` to adjust text color
        - `bg_rgb(...)` to adjust background color
        - `ul_rgb(...)` to enable underline and set the underline color
        - `dul_rgb(...)` to enable double underline and set the underline color
        - Value given may be either a 24-bit integer or 3 x 8-bit integers, separated by commas
        - Each given value within the parenthesis is treated as hexadecimal if the value starts with "0x"; it is otherwise treated as a decimal value
    - A `color256(...)` function directive as a string (ex: `"color256(255)"`)
        - `color256(...)` or `fg_color256(...)` to adjust text color
        - `bg_color256(...)` to adjust background color
        - `ul_color256(...)` to enable underline and set the underline color
        - `dul_color256(...)` to enable double underline and set the underline color
        - Value given must be an 8-bit integer
        - Value within the parenthesis is treated as hexadecimal if the value starts with "0x"; it is otherwise treated as a decimal value
        - Alternative spelling, "colour" may also be used
    - A string containing known ANSI directives (ex: `"01;31"` for BOLD and FG_RED)
        - Only non-negative integers are valid; all other values will cause a ValueError exception
    - Integer values which will be parsed in a similar way to above string ANSI directives
- The following setting types will be used verbatim as the ANSI graphics code and no exceptions will be thrown (handle with care)
    - An `AnsiSetting` object generated using a string
        - It is advised to check `AnsiSetting.valid` to ensure settings don't terminate the escape sequence
    - A string which starts with the character `"["` plus ANSI directives (ex: `"[38;5;214"`)
        - This will internally wrap the substring after the `"["` character into an `AnsiSetting` (ex: `"[38;5;214"` is equivalent to `AnsiSetting("38;5;214")`)

Hint: After creation, `is_formatting_parsable()` can be called to determine if all settings are parsable. Call `simplify()` in order to force invalid or redundant values to be thrown out.

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

### Apply Formatting

The method `apply_formatting()` is provided to apply formatting to a set range of characters.

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

### Format String

A format string may be used to format an `AnsiString` or `AnsiStr` before printing. The format specification string must be in the format `"[string_format[:ansi_format]]"` where `string_format` is an extension of the standard string format specifier and `ansi_format` contains 0 or more ANSI directives separated by semicolons (;). The ANSI directives may be any of the same string values that can be passed to the `AnsiString` constructor. If no `string_format` is desired, then it can be set to an empty string.

Examples:

```py
ansi_str = AnsiString("This is an ANSI string")
# Right justify with width of 100, formatted with underline and colored red.
# By default, all fill characters will take on the first character's formatting.
print("{:>100:underline;red}".format(ansi_str))

# The character after the first colon is the fill character. The following minus
# sign means that the fill character won't take on the first character's
# formatting like it did above.
print("{: ->100:underline;red}".format(ansi_str))

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

### Formatting and Unformatting Matching

The methods `format_matching()` and `unformat_matching()` are provided to apply or remove formatting based on a match specification.

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

### Other Notable Formatting Methods

- `is_formatting_valid()`: check if all formatting is valid in the sense that it won't print garbage on the terminal
- `is_formatting_parsable()`: check if the formatting is valid AND parsable into internally-known directives
- `simplify()`: simplify formatting settings by removing invalid and redundant codes
- `clear_formatting()`: clear all formatting applied
- `assign_str()`: assign the internal string and adjust formatting as necessary
- `base_str`: read-only property which returns the unformatted base string
- `ansi_settings_at()`: retrieve the settings applied over a single character
- `settings_at()`: similar to `ansi_settings_at()`, but a single string of directives is returned
- `find_settings()`: find start and end index of one or more settings
- `to_str()`: convert to a str with ANSI directives applied; this contains extra output formatting attributes over `__str__()`

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

## ParsedAnsiControlSequenceString Class

The `ParsedAnsiControlSequenceString` class may be used to parse any ANSI control sequence string. Check the `sequences` attribute after creation for the parsed sequences. This is used internally to parse graphic control sequences from an incoming ANSI string into an `AnsiString`.

## Other Library Functionality

### Parsing

- `parse_graphic_sequence()`: parses graphic sequence string into a list of `AnsiSettings`
- `settings_to_dict()`: converts a list of `AnsiSettings` into a dictionary which keys off of an effect type

### Cursor and Clear ANSI Control Sequence Generation

The following functions are provided to create strings which perform cursor or clear actions on the terminal when printed to the terminal. Take note that when calling `print()` with these, the `end` character should be set to an empty string `''` to ensure the cursor is not advanced after performing the operation.

- `cursor_up_str()`
- `cursor_down_str()`
- `cursor_forward_str()`
- `cursor_backward_str()`
- `cursor_back_str()`
- `cursor_next_line_str()`
- `cursor_previous_line_str()`
- `cursor_horizontal_absolute_str()`
- `cursor_position_str()`
- `erase_in_display_str()`
- `erase_in_line_str()`
- `scroll_up_str()`
- `scroll_down_str()`

#### Example

```py
from ansi_string import cursor_up_str
# Move cursor up 5 lines
print(cursor_up_str(5), end='')
```
