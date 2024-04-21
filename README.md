# ansi-string

ANSI String Formatter in Python for CLI Color and Style Formatting

## Introduction

This code was originally written for [greplica](https://pypi.org/project/greplica/), but I felt it deserved its own, separate library. The main goals for this project are:
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

## Usage

To begin, import AnsiString from the ansi_string module.

```py
from ansi_string import en_tty_ansi, AnsiFormat, AnsiString
```

### Construction

The AnsiString class contains the following `__init__` method. The first argument, `s`, is a string to be formatted. The next 0 to N arguments are formatting directives that can be applied to the entire string. These arguments can be in the form of any of the following:
- A string color name for a formatting directive (i.e. any name of the AnsiFormat enum in lower or upper case)
- An AnsiFormat directive (ex: `AnsiFormat.BOLD`)
- An rgb() function directive as a string (ex: `"rgb(255, 255, 255)"`)
    - rgb() or fg_rgb() to adjust text color
    - bg_rgb() to adjust background color
    - ul_rgb() to enable underline and set the underline color
    - Value given may be either a 24-bit value or 3 x 8-bit values, separated by commas
    - Each given value within the parenthesis is treated as a hexadecimal value if it starts with "0x", otherwise it will be treated as a decimal value
- A string containing known ANSI directives (ex: `"01;31"` for BOLD and FG_RED)
    - The string will normally be parsed and verified unless the character "[" is the first character of the string
- A single ANSI directive as an integer

```py
class AnsiString:
    def __init__(self, s:str='', *setting_or_settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat]): ...
```

### Concatenation

- The static method `AnsiString.join()` is provided to join together 0 to many `str` ans `AnsiString` values into a single `AnsiString`.
- The `+` operator may be used to join an `AnsiString` with another `AnsiString` or `str` into a new `AnsiString`
    - The `+` operator may not be used if the left-hand-side value is a `str` and the right-hand-side values is an `AnsiString`
- The `+=` operator may be used to append an `AnsiString` or `str` to an `AnsiString`

### Formatting

The method `AnsiString.apply_formatting()` is provided to append formatting to a previously constructed `AnsiString`.

A format string may be used to format an AnsiString before printing (ex: `"{:>10:bold;red}".format(ansi_str)`). The format specification string must be in the format `"[string_format][:ansi_format]"` where `string_format` is the standard string format specifier and `ansi_format` contains 0 or more ANSI directives separated by semicolons (;). The ANSI directives may be any of the same string values that can be passed to the `AnsiString` constructor. If no `string_format` is desired, then it can be set to an empty string (ex: `"{::bold;red}".format(ansi_str)`). This can also be set as a F-String (ex: `f"{ansi_str::bold;red}"`).
