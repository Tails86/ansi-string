# MIT License
#
# Copyright (c) 2024 James Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import math
from typing import Any, Union, List, Dict, Tuple
from .ansi_param import AnsiParam
from .ansi_format import AnsiFormat, AnsiSetting, ColorComponentType, ColourComponentType, ansi_sep, ansi_escape_format, ansi_escape_clear

__version__ = '1.0.4'
PACKAGE_NAME = 'ansi-string'

WHITESPACE_CHARS = ' \t\n\r\v\f'

class AnsiString:
    '''
    Represents an ANSI colorized/formatted string. All or part of the string may contain style and
    color formatting which may be used to print out to an ANSI-supported terminal such as those
    on Linux, Mac, and Windows 10+.
    '''

    # Change this to True for testing
    WITH_ASSERTIONS = False

    def __init__(
        self,
        s:str='',
        *setting_or_settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat, List['AnsiSetting'], 'AnsiSetting']
    ):
        '''
        Creates an AnsiString
        s: The underlying string
        setting_or_settings: setting(s) in any of the listed formats below
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

        A setting may also be any of the following, but it's not advised to specify settings these ways unless there is
        a specific reason to do so.
            - An AnsiSetting object
            - A string containing known ANSI directives (ex: `"01;31"` for BOLD and FG_RED)
                - The string will normally be parsed into separate settings unless the character "[" is the first
                  character of the string (ex: `"[38;5;214"`)
                - Never specify the reset directive (0) because this is implicitly handled internally
            - A single ANSI directive as an integer
        '''
        self._s = s
        # Key is the string index to make a color change at
        self._fmts:Dict[int,'_AnsiSettingPoint'] = {}

        # Unpack settings
        settings = []
        for sos in setting_or_settings:
            if not isinstance(sos, list) and not isinstance(sos, tuple):
                settings.append(sos)
            else:
                settings += sos

        if settings:
            self.apply_formatting(settings)

    def assign_str(self, s:str):
        '''
        Assigns the base string and adjusts the ANSI settings based on the new length.
        '''
        if len(s) > len(self._s):
            if len(self._s) in self._fmts:
                self._fmts[len(s)] = self._fmts.pop(len(self._s))
        elif len(s) < len(self._s):
            # This may erase some settings that will no longer apply
            self.clip(end=len(s), inplace=True)
        self._s = s

    @property
    def base_str(self) -> str:
        '''
        Returns the base string without any formatting set.
        '''
        return self._s

    def copy(self) -> 'AnsiString':
        return self[:]

    @staticmethod
    def _shift_settings_idx(settings_dict:Dict[int,'_AnsiSettingPoint'], num:int, keep_origin:bool):
        '''
        Not fully supported for when num is negative
        '''
        for key in sorted(settings_dict.keys(), reverse=(num > 0)):
            if not keep_origin or key != 0:
                new_key = max(key + num, 0)
                # new_key could be negative when num is negative - TODO: either handle or raise exception
                settings_dict[new_key] = settings_dict.pop(key)

    def _insert_settings(
        self,
        idx:int,
        apply:bool,
        settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat, List['AnsiSetting'], 'AnsiSetting'],
        topmost:bool=True
    ) -> List['AnsiSetting']:
        if idx not in self._fmts:
            self._fmts[idx] = _AnsiSettingPoint()
        return self._fmts[idx].insert_settings(apply, settings, topmost)

    def apply_formatting(
            self,
            setting_or_settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat, List['AnsiSetting'], 'AnsiSetting'],
            start:int=0,
            end:Union[int,None]=None,
            topmost:bool=True
    ):
        '''
        Sets the formatting for a given range of characters.
        Inputs: setting_or_settings - setting or list of settings to apply
                start - The string start index where setting(s) are to be applied
                end - The string index where the setting(s) should be removed
                topmost - When true, this setting is placed at the end of the set for the given
                          start_index meaning it takes precedent over others; when false, setting is
                          applied first
        '''
        start = self._slice_val_to_idx(start, 0)
        end = self._slice_val_to_idx(end, len(self._s))

        if not setting_or_settings or start >= len(self._s) or end <= start:
            # Ignore - nothing to apply
            return

        if not isinstance(setting_or_settings, list) and not isinstance(setting_or_settings, tuple):
            settings = [setting_or_settings]
        else:
            settings = list(setting_or_settings)

        # Settings are removed by reference (using "is" instead of "==") because this is easier than generating unique
        # IDs, so it is necessary to ensure the incoming settings have distinct references. It would be possible to do
        # so only if the setting is not already in self._fmts[*].add, but it doesn't add much more overhead to just make
        # a copy for every incoming AnsiSetting.
        for i in range(len(settings)):
            if isinstance(settings[i], AnsiSetting):
                settings[i] = AnsiSetting(str(settings[i]))

        # Apply settings
        inserted_settings = self._insert_settings(start, True, settings, topmost)

        # Remove settings
        self._insert_settings(end, False, inserted_settings, topmost)

    def apply_formatting_for_match(
            self,
            setting_or_settings:Union[List[str], str, List[AnsiFormat], AnsiFormat],
            match_object,
            group:int=0
    ):
        '''
        Apply formatting using a match object generated from re
        setting_or_settings - setting or list of settings to apply to matching strings
        match_object - the match object to use (result of re.search() or re.finditer())
        group - match the group to set
        '''
        s = match_object.start(group)
        e = match_object.end(group)
        self.apply_formatting(setting_or_settings, s, e)

    def format_matching(self, matchspec:str, *format, regex:bool=False, match_case=False):
        '''
        Apply formatting for anything matching the matchspec
        matchspec: the string to match
        format: 0 to many format specifiers
        regex: set to True to treat matchspec as a regex string
        match_case: set to True to make matching case-sensitive (false by default)
        '''
        if not regex:
            matchspec = re.escape(matchspec)

        for match in re.finditer(matchspec, self._s, re.IGNORECASE if not match_case else 0):
            self.apply_formatting_for_match(format, match)

    def clear_formatting(self):
        '''
        Clears all internal formatting.
        '''
        self._fmts = {}

    @staticmethod
    def _find_setting_reference(find:AnsiSetting, in_list:List[AnsiSetting]) -> int:
        for i, s in enumerate(in_list):
            if s is find:
                return i
        return -1

    @staticmethod
    def _find_settings_references(find_list:List[AnsiSetting], in_list:List[AnsiSetting]) -> List[Tuple]:
        matches = []
        for i, s in enumerate(find_list):
            for i2, s2 in enumerate(in_list):
                if s is s2:
                    matches.append((i, i2))
        return matches

    def _slice_val_to_idx(self, val:int, default:int) -> int:
        if val is None:
            return default
        elif val < 0:
            ret_val = len(self._s) + val
            if ret_val < 0:
                ret_val = 0
            return ret_val
        else:
            return val

    def __getitem__(self, val:Union[int, slice]) -> 'AnsiString':
        '''
        Returns a new AnsiString object which represents a substring of self.
        Note: the new copy may contain some references to settings in the origin. This is ok since the value of each
              setting is not internally modified after creation.
        '''
        if isinstance(val, int):
            st = val
            en = val + 1
        elif isinstance(val, slice):
            if val.step is not None and val.step != 1:
                raise ValueError('Step other than 1 not supported')
            st = self._slice_val_to_idx(val.start, 0)
            en = self._slice_val_to_idx(val.stop, len(self._s))
        else:
            raise TypeError('Invalid type for __getitem__')

        new_s = AnsiString(self._s[val])

        if not new_s._s:
            # Special case - string is now empty
            return new_s

        # String cannot be empty from this point on, so that will be assumed going forward

        previous_settings = None
        settings_initialized = False
        for idx, settings, current_settings in _AnsiSettingsIterator(self._fmts):
            if idx > len(self._s) or idx > en:
                # Complete
                break
            elif idx == en:
                if settings.rem:
                    new_s._fmts[idx - st] = _AnsiSettingPoint(rem=(settings.rem))
                # Complete
                break
            elif idx == st:
                if current_settings:
                    new_s._fmts[0] = _AnsiSettingPoint(add=list(current_settings))
                settings_initialized = True
            elif idx > st:
                if not settings_initialized and previous_settings:
                    new_s._fmts[0] = _AnsiSettingPoint(add=previous_settings)
                settings_initialized = True
                new_s._fmts[idx - st] = _AnsiSettingPoint(settings.add, settings.rem)

            # It's necessary to copy (i.e. call list()) since current_settings ref will change on next loop
            previous_settings = list(current_settings)

        if not settings_initialized and previous_settings:
            # Substring was between settings
            new_s._fmts[0] = _AnsiSettingPoint(add=previous_settings)

        # Because this class supports concatenation, it's necessary to remove all settings before ending
        if previous_settings:
            new_len = len(new_s._s)
            if new_len not in new_s._fmts:
                new_s._fmts[new_len] = _AnsiSettingPoint()
            settings_to_remove = [s for s in previous_settings if s not in new_s._fmts[new_len].rem]
            new_s._fmts[new_len].rem.extend(settings_to_remove)

        return new_s

    def __str__(self) -> str:
        '''
        Returns a string with ANSI-formatting applied
        '''
        return self.__format__(None)

    def _apply_string_format(self, string_format:str):
        match = re.search(r'^(.?)<([0-9]*)$', string_format)
        if match:
            # Left justify
            num = match.group(2)
            if num:
                self.ljust(int(num), match.group(1) or ' ', inplace=True)
            return

        match = re.search(r'^(.?)>([0-9]*)$', string_format)
        if match:
            # Right justify
            num = match.group(2)
            if num:
                self.rjust(int(num), match.group(1) or ' ', inplace=True)
            return

        match = re.search(r'^(.?)\^([0-9]*)$', string_format)
        if match:
            # Center
            num = match.group(2)
            if num:
                self.center(int(num), match.group(1) or ' ', inplace=True)
            return

        match = re.search(r'^[<>\^]?[+-]?[0-9]*$', string_format)
        if match:
            raise ValueError('Sign not allowed in string format specifier')

        match = re.search(r'^[<>\^]?[ ]?[0-9]*$', string_format)
        if match:
            raise ValueError('Space not allowed in string format specifier')

        raise ValueError('Invalid format specifier')


    def __format__(self, __format_spec:str) -> str:
        '''
        Returns an ANSI format string with both internal and given formatting spec set.
        __format_spec: must be in the format "[string_format][:ansi_format]" where string_format is the standard
                       string format specifier and ansi_format contains 0 or more ansi directives separated by
                       semicolons (;)
                       ex: ">10:bold;fg_red" to make output right justify with width of 10, bold and red formatting
        '''
        if not __format_spec and not self._fmts:
            # No formatting
            return self._s

        if __format_spec:
            # Make a copy
            obj = self.copy()

            format_parts = __format_spec.split(':', 1)

            if format_parts[0]:
                # Normal string formatting
                obj._apply_string_format(format_parts[0])

            if len(format_parts) > 1:
                # ANSI color/style formatting
                obj.apply_formatting(format_parts[1])
        else:
            # No changes - just copy the reference
            obj = self

        out_str = ''
        last_idx = 0
        clear_needed = False
        for idx, settings, current_settings in _AnsiSettingsIterator(obj._fmts):
            if idx >= len(obj):
                # Invalid
                break
            # Catch up output to current index
            out_str += obj._s[last_idx:idx]
            last_idx = idx

            settings_to_apply = [str(s) for s in current_settings]
            if settings.rem and settings_to_apply:
                # Settings were removed and there are settings to be applied -
                # need to reset before applying current settings
                settings_to_apply = [str(AnsiParam.RESET.value)] + settings_to_apply
            # Apply these settings
            out_str += ansi_escape_format.format(ansi_sep.join(settings_to_apply))
            # Save this flag in case this is the last loop
            clear_needed = bool(current_settings)

        # Final catch up
        out_str += obj._s[last_idx:]
        if clear_needed:
            # Clear settings
            out_str += ansi_escape_clear

        return out_str

    def __iter__(self) -> 'AnsiString':
        ''' Iterates over each character '''
        return iter(_AnsiCharIterator(self))

    def capitalize(self, inplace:bool=False) -> 'AnsiString':
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj._s = obj._s.capitalize()
        return obj

    def casefold(self, inplace:bool=False) -> 'AnsiString':
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj._s = obj._s.casefold()
        return obj

    def center(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiString':
        '''
        Center justification.
        inplace: True to execute in-place; False to return a copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()

        old_len = len(obj._s)
        num = width - old_len
        if num > 0:
            left_spaces = math.floor((num) / 2)
            right_spaces = num - left_spaces
            obj._s = fillchar * left_spaces + obj._s + fillchar * right_spaces
            # Move the removal settings from previous end to new end (formats the right fillchars with same as last char)
            if old_len in obj._fmts:
                obj._fmts[len(obj._s)] = obj._fmts.pop(old_len)
            # Shift all indices except for the origin (formats the left fillchars with same as first char)
            __class__._shift_settings_idx(obj._fmts, left_spaces, True)

        return obj

    def ljust(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiString':
        '''
        Left justification.
        inplace: True to execute in-place; False to return a copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()

        old_len = len(obj._s)
        num = width - old_len
        if num > 0:
            obj._s += fillchar * num
            # Move the removal settings from previous end to new end (formats the right fillchars with same as last char)
            if old_len in obj._fmts:
                obj._fmts[len(obj._s)] = obj._fmts.pop(old_len)

        return obj

    def rjust(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiString':
        '''
        Right justification.
        inplace: True to execute in-place; False to return a copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()

        old_len = len(obj._s)
        num = width - old_len
        if num > 0:
            obj._s = fillchar * num + obj._s
            # Shift all indices except for the origin (formats the left fillchars with same as first char)
            __class__._shift_settings_idx(obj._fmts, num, True)

        return obj

    def count(self, sub:str, start:int=None, end:int=None) -> int:
        return self._s.count(sub, start, end)

    def encode(self, encoding:str="utf-8", errors:str="strict") -> bytes:
        return str(self).encode(encoding, errors)

    def endswith(self, suffix:str, start:int=None, end:int=None) -> bool:
        return self._s.endswith(suffix, start, end)

    def expandtabs(self, tabsize:int=8, inplace:bool=False) -> 'AnsiString':
        return self.replace('\t', ' ' * tabsize, inplace=inplace)

    def find(self, sub:str, start:int=None, end:int=None) -> int:
        return self._s.find(sub, start, end)

    def index(self, sub:str, start:int=None, end:int=None) -> int:
        return self._s.index(sub, start, end)

    def isalnum(self) -> bool:
        return self._s.isalnum()

    def isalpha(self) -> bool:
        return self._s.isalpha()

    def isascii(self) -> bool:
        '''
        This is only available for Python >=3.7; exception will be raised in Python 3.6
        '''
        return self._s.isascii()

    def isdecimal(self) -> bool:
        return self._s.isdecimal()

    def isdigit(self) -> bool:
        return self._s.isdigit()

    def isidentifier(self) -> bool:
        return self._s.isidentifier()

    def islower(self) -> bool:
        return self._s.islower()

    def isnumeric(self) -> bool:
        return self._s.isnumeric()

    def isprintable(self) -> bool:
        return self._s.isprintable()

    def isspace(self) -> bool:
        return self._s.isspace()

    def istitle(self) -> bool:
        return self._s.istitle()

    def isupper(self) -> bool:
        return self._s.isupper()

    def __add__(self, value:Union[str,'AnsiString']) -> 'AnsiString':
        cpy = self.copy()
        cpy += value
        return cpy

    def __iadd__(self, value:Union[str,'AnsiString']) -> 'AnsiString':
        ''' Appends a string or AnsiString to this AnsiString '''
        if isinstance(value, str):
            self._s += value
        elif isinstance(value, AnsiString):
            shift = len(self._s)
            self._s += value._s
            find_settings = []
            replace_settings = []
            for key, settings in sorted(value._fmts.items()):
                key += shift
                if key in self._fmts:
                    if (
                        key == shift
                        and settings.add
                        and self._fmts[key].rem[:len(settings.add)] == settings.add
                    ):
                        # Special case - the string being added contains same formatting as end of my string.
                        # Because the settings work based on references instead of values, the settings not only
                        # need to be removed here but changed where they are removed in the added string.
                        find_settings = settings.add
                        replace_settings = self._fmts[key].rem[:len(settings.add)]
                        self._fmts[key].rem = self._fmts[key].rem[len(settings.add):]
                        settings.add = []
                        if not self._fmts[key] and not settings:
                            del self._fmts[key]
                            continue

                    self._fmts[key].add.extend(settings.add)
                    self._fmts[key].rem.extend(settings.rem)

                else:
                    self._fmts[key] = _AnsiSettingPoint(list(settings.add), list(settings.rem))

                    finds = __class__._find_settings_references(find_settings, settings.rem)
                    if finds:
                        for find_idx, add_idx in reversed(finds):
                            self._fmts[key].rem[add_idx] = replace_settings[find_idx]
                            # Note: find_idx will always be sorted in ascending order and this is iterating in reverse
                            del find_settings[find_idx]
                            del replace_settings[find_idx]

        else:
            raise TypeError(f'value is invalid type: {type(value)}')
        return self

    def __eq__(self, value:'AnsiString') -> bool:
        ''' == operator - returns True if exactly equal '''
        if not isinstance(value, AnsiString):
            return False
        return self._s == value._s and self._fmts == value._fmts

    def __contains__(self, value:Union[str,'AnsiString',Any]) -> bool:
        if isinstance(value, str):
            return value in self._s
        elif isinstance(value, AnsiString):
            return value._s in self._s
        return False

    def __len__(self) -> int:
        return len(self._s)

    @staticmethod
    def join(*args:Union[str,'AnsiString']) -> 'AnsiString':
        ''' Joins strings and AnsiStrings into a single AnsiString object '''
        if not args:
            return AnsiString()
        args = list(args)
        first_arg = args[0]
        if isinstance(first_arg, str):
            joint = AnsiString(first_arg)
        elif isinstance(first_arg, AnsiString):
            joint = first_arg.copy()
        else:
            raise TypeError(f'value is invalid type: {type(first_arg)}')
        for arg in args[1:]:
            joint += arg
        return joint

    def lower(self, inplace:bool=False) -> 'AnsiString':
        '''
        Convert to lowercase.
        inplace: True to execute in-place; False to return a copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj._s = obj._s.lower()
        return obj

    def upper(self, inplace:bool=False) -> 'AnsiString':
        '''
        Convert to uppercase.
        inplace: True to execute in-place; False to return a copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj._s = obj._s.upper()
        return obj

    def lstrip(self, chars:str=None, inplace:bool=False) -> 'AnsiString':
        '''
        Remove leading whitespace
        chars: If not None, remove characters in chars instead
        inplace: True to execute in-place; False to return a copy
        '''
        return self._strip(chars=chars, inplace=inplace, do_lstrip=True, do_rstrip=False)

    def clip(self, start:int=None, end:int=None, inplace:bool=False) -> 'AnsiString':
        '''
        Calls [] operator and optionally assigns in-place
        '''
        obj = self[start:end]
        if inplace:
            self._s = obj._s
            self._fmts = obj._fmts
            del obj
            return self
        else:
            return obj

    def rstrip(self, chars:str=None, inplace:bool=False) -> 'AnsiString':
        '''
        Remove trailing whitespace
        chars: If not None, remove characters in chars instead
        inplace: True to execute in-place; False to return a copy
        '''
        return self._strip(chars=chars, inplace=inplace, do_lstrip=False, do_rstrip=True)

    def strip(self, chars:str=None, inplace:bool=False) -> 'AnsiString':
        '''
        Remove leading and trailing whitespace
        chars: If not None, remove characters in chars instead
        inplace: True to execute in-place; False to return a copy
        '''
        return self._strip(chars=chars, inplace=inplace, do_lstrip=True, do_rstrip=True)

    def _strip(self, chars:str=None, inplace:bool=False, do_lstrip:bool=True, do_rstrip:bool=True) -> 'AnsiString':
        '''
        Remove leading and trailing whitespace
        chars: If not None, remove characters in chars instead
        inplace: True to execute in-place; False to return a copy
        '''
        if chars is None:
            chars = WHITESPACE_CHARS

        lcount = 0
        if do_lstrip:
            for char in self._s:
                if char in chars:
                    lcount += 1
                else:
                    break

        rcount = None
        if do_rstrip and lcount < len (self._s):
            rcount = 0
            for char in reversed(self._s):
                if char in chars:
                    rcount -= 1
                else:
                    break
            if rcount == 0:
                rcount = None

        if inplace and lcount == 0 and rcount is None:
            return self

        # This is always going to create a copy - no good way to modify settings while iterating over it
        return self.clip(lcount, rcount, inplace)

    def partition(self, sep:str) -> Tuple['AnsiString','AnsiString','AnsiString']:
        '''
        Partition the string into three parts using the given separator.

        This will search for the separator in the string. If the separator is found, returns a 3-tuple containing the
        part before the separator, the separator itself, and the part after it.

        If the separator is not found, returns a 3-tuple containing the original string and two empty strings.
        '''
        idx = self._s.find(sep)
        if idx >= 0:
            sep_len = len(sep)
            idx_end = idx + sep_len
            return (self[0:idx], self[idx:idx_end], self[idx_end:])
        else:
            return (self.copy(), AnsiString(), AnsiString())

    def rpartition(self, sep:str) -> Tuple['AnsiString','AnsiString','AnsiString']:
        '''
        Partition the string into three parts using the given separator, searching from right to left.

        This will search for the separator in the string. If the separator is found, returns a 3-tuple containing the
        part before the separator, the separator itself, and the part after it.

        If the separator is not found, returns a 3-tuple containing the original string and two empty strings.
        '''
        idx = self._s.rfind(sep)
        if idx >= 0:
            sep_len = len(sep)
            idx_end = idx + sep_len
            return (self[0:idx], self[idx:idx_end], self[idx_end:])
        else:
            return (self.copy(), AnsiString(), AnsiString())

    def _settings_at(self, idx:int) -> List[AnsiSetting]:
        if idx >= 0 and idx < len(self._s):
            previous_settings = []
            for sidx, _, current_settings in _AnsiSettingsIterator(self._fmts):
                if sidx > idx:
                    break
                previous_settings = list(current_settings)
            return previous_settings
        else:
            return []

    def settings_at(self, idx:int) -> str:
        '''
        Returns a string which represents the settings being used at the given index
        '''
        return ansi_sep.join([str(s) for s in self._settings_at(idx)])

    def removeprefix(self, prefix:str, inplace:bool=False) -> 'AnsiString':
        if not self._s.startswith(prefix):
            if inplace:
                return self
            else:
                return self.copy()
        else:
            return self.clip(start=len(prefix), inplace=inplace)

    def removesuffix(self, suffix:str, inplace:bool=False) -> 'AnsiString':
        if not self._s.endswith(suffix):
            if inplace:
                return self
            else:
                return self.copy()
        else:
            return self.clip(end=-len(suffix), inplace=inplace)

    def replace(self, old:str, new:Union[str,'AnsiString'], count:int=-1, inplace:bool=False) -> 'AnsiString':
        '''
        Does a find-and-replace - if new is a str, the string the is applied will take on the format settings of the
        first character of the old string in each replaced item.
        '''
        obj = self
        idx = obj._s.find(old)
        while (count < 0 or count > 0) and idx >= 0:
            if isinstance(new, str):
                replace = AnsiString(new, obj._settings_at(idx))
            else:
                replace = new
            obj = obj[:idx] + replace + obj[idx+len(old):]
            if count > 0:
                count -= 1
            idx = obj._s.find(old, idx + len(new))

        if inplace:
            self._s = obj._s
            self._fmts = obj._fmts
            return self
        else:
            return obj

    def rfind(self, sub:str, start:int=None, end:int=None) -> int:
        return self._s.rfind(sub, start, end)

    def rindex(self, sub:str, start:int=None, end:int=None) -> int:
        return self._s.rindex(sub, start, end)

    def _split(self, sep:Union[str,None]=None, maxsplit:int=-1, r:bool=False) -> List['AnsiString']:
        if r:
            str_splits = self._s.rsplit(sep, maxsplit)
        else:
            str_splits = self._s.split(sep, maxsplit)
        split_idx_len = []
        idx = 0
        for s in str_splits:
            idx = self._s.find(s, idx)
            split_idx_len.append((idx, len(s)))
            idx += len(s)

        ansi_str_splits = []
        for idx, length in split_idx_len:
            ansi_str_splits.append(self[idx:idx+length])

        return ansi_str_splits

    def split(self, sep:Union[str,None]=None, maxsplit:int=-1) -> List['AnsiString']:
        return self._split(sep, maxsplit, False)

    def rsplit(self, sep:Union[str,None]=None, maxsplit:int=-1) -> List['AnsiString']:
        return self._split(sep, maxsplit, True)

    def splitlines(self, keepends:bool=False) -> List['AnsiString']:
        str_splits = self._s.splitlines(keepends)
        split_idx_len = []
        idx = 0
        for s in str_splits:
            idx = self._s.find(s, idx)
            split_idx_len.append((idx, len(s)))
            idx += len(s)

        ansi_str_splits = []
        for idx, length in split_idx_len:
            ansi_str_splits.append(self[idx:idx+length])

        return ansi_str_splits

    def swapcase(self, inplace:bool=False) -> 'AnsiString':
        if inplace:
            obj = self
        else:
            obj = self.copy()

        obj._s = obj._s.swapcase()

        return obj

    def title(self, inplace:bool=False) -> 'AnsiString':
        if inplace:
            obj = self
        else:
            obj = self.copy()

        obj._s = obj._s.title()

        return obj

    def zfill(self, width:int, inplace:bool=False) -> 'AnsiString':
        return self.rjust(width, "0", inplace)


class _AnsiSettingPoint:
    '''
    This class is used internally to keep track of ANSI settings at a specific string index
    '''

    def __init__(
        self,
        add:Union[List['AnsiSetting'],None]=None,
        rem:Union[List['AnsiSetting'],None]=None
    ):
        self.add:List[AnsiSetting] = add or []
        self.rem:List[AnsiSetting] = rem or []

    def __eq__(self, value) -> bool:
        if isinstance(value, _AnsiSettingPoint):
            return value.add == self.add and value.rem == self.rem
        return False

    def __bool__(self) -> bool:
        return bool(self.add) or bool(self.rem)

    @staticmethod
    def _parse_rgb_string(s:str) -> AnsiSetting:
        component_dict = {
            'dul_': ColorComponentType.DOUBLE_UNDERLINE,
            'ul_': ColorComponentType.UNDERLINE,
            'bg_': ColorComponentType.BACKGROUND,
            'fg_': ColorComponentType.FOREGROUND
        }

        # rgb(), fg_rgb(), bg_rgb(), or ul_rgb() with 3 distinct values as decimal or hex
        match = re.search(r'^((?:fg_)?|(?:bg_)|(?:ul_)|(?:dul_))rgb\([\[\()]?\s*(0x)?([0-9a-fA-F]+)\s*,\s*(0x)?([0-9a-fA-F]+)\s*,\s*(0x)?([0-9a-fA-F]+)\s*[\)\]]?\)$', s)
        if match:
            try:
                r = int(match.group(3), 16 if match.group(2) else 10)
                g = int(match.group(5), 16 if match.group(4) else 10)
                b = int(match.group(7), 16 if match.group(6) else 10)
            except ValueError:
                raise ValueError('Invalid rgb value(s)')
            # Get RGB format and remove the leading '['
            return AnsiFormat.rgb(r, g, b, component_dict.get(match.group(1), ColorComponentType.FOREGROUND))

        # rgb(), fg_rgb(), bg_rgb(), or ul_rgb() with 1 value as decimal or hex
        match = re.search(r'^((?:fg_)?|(?:bg_)|(?:ul_)|(?:dul_))rgb\([\[\()]?\s*(0x)?([0-9a-fA-F]+)\s*[\)\]]?\)$', s)
        if match:
            try:
                rgb = int(match.group(3), 16 if match.group(2) else 10)
            except ValueError:
                raise ValueError('Invalid rgb value')
            # Get RGB format and remove the leading '['
            return AnsiFormat.rgb(rgb, component=component_dict.get(match.group(1), ColorComponentType.FOREGROUND))
        return None

    @staticmethod
    def _scrub_ansi_format_string(ansi_format:str) -> List[AnsiSetting]:
        if ansi_format.startswith("["):
            # Use the rest of the string as-is for settings
            return [AnsiSetting(ansi_format[1:])]
        else:
            # The format string contains names within AnsiFormat or integers, separated by semicolon
            formats = ansi_format.split(ansi_sep)
            format_settings = []
            for format in formats:
                ansi_fmt_enum = None
                try:
                    ansi_fmt_enum = AnsiFormat[format.upper()]
                except KeyError:
                    pass
                else:
                    format_settings.append(ansi_fmt_enum.setting)

                if ansi_fmt_enum is None:
                    rgb_format = __class__._parse_rgb_string(format)
                    if not rgb_format:
                        try:
                            int_value = int(format)
                            # 0 should never be used because it will mess with internal assumptions
                            # Negative values are invalid
                            if int_value < 0:
                                raise ValueError(f'Invalid value [{int_value}]; must be greater than or equal to 0')
                        except ValueError:
                            raise ValueError(
                                'AnsiString.__format__ failed to parse format ({}); invalid name: {}'
                                .format(ansi_format, format)
                            )
                        else:
                            # Value is an integer - use the format verbatim
                            format_settings.append(AnsiSetting(format))
                    else:
                        format_settings.append(rgb_format)
            return format_settings

    def insert_setting(self, apply:bool, setting:'AnsiSetting', topmost:bool=True):
        lst = self.add if apply else self.rem
        if topmost:
            lst.append(setting)
        else:
            lst.insert(0, setting)

    def insert_settings(
        self,
        apply:bool,
        settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat, List['AnsiSetting'], 'AnsiSetting'],
        topmost:bool=True
    ) -> List['AnsiSetting']:
        if not isinstance(settings, list) and not isinstance(settings, tuple):
            settings = [settings]

        settings_to_insert = []
        for setting in settings:
            if isinstance(setting, AnsiSetting):
                settings_to_insert.append(setting)
            elif isinstance(setting, str) or isinstance(setting, int):
                settings_to_insert.extend(__class__._scrub_ansi_format_string(str(setting)))
            elif hasattr(setting, "setting"):
                settings_to_insert.append(setting.setting)

        lst = self.add if apply else self.rem
        if topmost:
            lst.extend(settings_to_insert)
        else:
            lst[:0] = settings_to_insert

        return settings_to_insert

class _AnsiSettingsIterator:
    '''
    Internally-used class which helps iterate over settings
    '''
    def __init__(self, settings_dict:Dict[int,'_AnsiSettingPoint']):
        self.settings_dict:Dict[int,_AnsiSettingPoint] = settings_dict
        self.current_settings:List[AnsiSetting] = []
        self.dict_iter = iter(sorted(self.settings_dict))

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[int,'_AnsiSettingPoint',List['AnsiSetting']]:
        # Will raise StopIteration when complete
        idx = next(self.dict_iter)
        settings = self.settings_dict[idx]
        # Remove settings that it is time to remove
        for setting in settings.rem:
            # setting object will only be matched and removed if it is the same reference to one
            # previously added - will raise exception otherwise which should not happen if the
            # settings dictionary and this method were setup correctly.
            remove_idx = AnsiString._find_setting_reference(setting, self.current_settings)
            if remove_idx >= 0:
                del self.current_settings[remove_idx]
            elif AnsiString.WITH_ASSERTIONS:
                # This exception is really only useful in testing
                raise ValueError('could not remove setting: not in list')
        # Apply settings that it is time to add
        self.current_settings += settings.add
        return (idx, settings, self.current_settings)

class _AnsiCharIterator:
    '''
    Internally-used class which helps iterate over characters
    '''
    def __init__(self, s:'AnsiString'):
        self.current_idx:int = -1
        self.s:AnsiString = s

    def __iter__(self):
        return self

    def __next__(self) -> 'AnsiString':
        self.current_idx += 1
        if self.current_idx >= len(self.s):
            raise StopIteration
        return self.s[self.current_idx]