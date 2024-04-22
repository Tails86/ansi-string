# ansi-string

ANSI String Formatter in Python for CLI Color and Style Formatting

## Introduction

This code was originally written for [greplica](https://pypi.org/project/greplica/), but I felt it deserved its own, separate library.

The main goals for this project are:
- To provide a simple way to construct an object with ANSI formatting without requiring the developer to know how ANSI formatting works
- Provide a way to further format the object using format string
- Allow for concatenation of the object

## Contribution

Feel free to open a bug report or make a merge request on [github](https://github.com/Tails86/ansi-string/issues).

## Installation
This project is uploaded to PyPI at https://pypi.org/project/ansi-string

To install, ensure you are connected to the internet and execute: `python3 -m pip install ansi-string --upgrade`

## Examples

![Examples](https://raw.githubusercontent.com/Tails86/ansi-string/0e2c943f25ccc219256204511fd308652a8075c0/docs/examples.jpg)

Refer to the [test file](https://github.com/Tails86/ansi-string/blob/main/tests/test_ansi_string.py) for more examples on how to use the AnsiString class.

## Usage

To begin, import AnsiString from the ansi_string module.

```py
from ansi_string import en_tty_ansi, AnsiFormat, AnsiString
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

For Windows, this returns True if the given IO is a TTY (i.e. not piped to a file) and enabling ANSI was successful. For all other operating systems, this will return True if and only if the given IO is a TTY; no other action is taken.

### Construction

The AnsiString class contains the following `__init__` method.

```py
class AnsiString:
    def __init__(self, s:str='', *setting_or_settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat]): ...
```

The first argument, `s`, is a string to be formatted. The next 0 to N arguments are formatting directives that can be applied to the entire string. These arguments can be in the form of any of the following:
- A string color name for a formatting directive (i.e. any name of the AnsiFormat enum in lower or upper case)
- An AnsiFormat directive (ex: `AnsiFormat.BOLD`)
- An `rgb(...)` function directive as a string (ex: `"rgb(255, 255, 255)"`)
    - `rgb(...)` or `fg_rgb(...)` to adjust text color
    - `bg_rgb(...)` to adjust background color
    - `ul_rgb(...)` to enable underline and set the underline color
    - Value given may be either a 24-bit integer or 3 x 8-bit integers, separated by commas
    - Each given value within the parenthesis is treated as hexadecimal if the value starts with "0x", otherwise it is treated as a decimal value
- A string containing known ANSI directives (ex: `"01;31"` for BOLD and FG_RED)
    - The string will normally be parsed into their individual values and verified unless the character "[" is the first character of the string (ex: `"[01;31"`)
- A single ANSI directive as an integer

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

- The static method `AnsiString.join()` is provided to join together 0 to many `str` and `AnsiString` values into a single `AnsiString`.
- The `+` operator may be used to join an `AnsiString` with another `AnsiString` or `str` into a new `AnsiString`
    - The `+` operator may not be used if the left-hand-side value is a `str` and the right-hand-side values is an `AnsiString`
- The `+=` operator may be used to append an `AnsiString` or `str` to an `AnsiString`

Examples:
```py
s = AnsiString.join("This ", AnsiString("string", AnsiFormat.BOLD))
s += AnsiString(" contains ") + AnsiString("multiple", AnsiFormat.BG_BLUE)
s += AnsiString(" color ", AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC) + "settings accross different ranges"
print(s)
```

### Formatting

The method `AnsiString.apply_formatting()` is provided to append formatting to a previously constructed `AnsiString`.
Example:
```py
s = AnsiString("This string contains multiple color settings across different ranges")
s.apply_formatting(AnsiFormat.BOLD, 5, 11)
s.apply_formatting(AnsiFormat.BG_BLUE, 21, 29)
s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 35)
print(s)
```

A format string may be used to format an AnsiString before printing. The format specification string must be in the format `"[string_format][:ansi_format]"` where `string_format` is the standard string format specifier and `ansi_format` contains 0 or more ANSI directives separated by semicolons (;). The ANSI directives may be any of the same string values that can be passed to the `AnsiString` constructor. If no `string_format` is desired, then it can be set to an empty string.
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

The method `AnsiString.format_matching()` is provided to apply formatting to an `AnsiString` based on a match specification.
Example:
```py
s = AnsiString("Here is a strING that I will match formatting")
# This will make the word "formatting" cyan with a pink background
s.format_matching("[A-Za-z]+ing", "cyan", AnsiFormat.BG_PINK, regex=True, match_case=True)
print(s)
```

### Other String Manipulation Methods

Many other methods that are found in the `str` class such as `replace()` are available in `AnsiString` which manipulate the string while applying formatting where necessary.
