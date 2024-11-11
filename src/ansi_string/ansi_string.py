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
import collections
from typing import Any, Union, List, Dict, Tuple
from .ansi_param import AnsiParam
from .ansi_format import AnsiFormat, AnsiSetting, ColorComponentType, ColourComponentType, ansi_sep, ansi_escape_format, ansi_escape_clear

__version__ = '1.0.7'
PACKAGE_NAME = 'ansi-string'

# Constant: all characters considered to be whitespaces
WHITESPACE_CHARS = ' \t\n\r\v\f'

class AnsiString(collections.UserString):
    '''
    Represents an ANSI colorized/formatted string. All or part of the string may contain style and
    color formatting which may be used to print out to an ANSI-supported terminal such as those
    on Linux, Mac, and Windows 10+.
    '''

    # Change this to True for testing
    WITH_ASSERTIONS = False

    def __init__(
        self,
        s:Union[str,'AnsiString','AnsiStr']='',
        *settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple]
    ):
        '''
        Creates an AnsiString
        Parameters:
        s - The underlying string or an AnsiString to copy from
        settings - setting(s) in any of the listed formats below
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
        incoming_fmts = None
        if isinstance(s, AnsiString):
            incoming_fmts = s._fmts
            super().__init__(s.data)
        elif isinstance(s, AnsiStr):
            incoming_fmts = s._ansi_string._fmts
            super().__init__(s._ansi_string.data)
        elif isinstance(s, str):
            super().__init__(s)
        else:
            raise TypeError('Invalid type for s')

        # Key is the string index to make a color change at
        self._fmts:Dict[int,'_AnsiSettingPoint'] = {}

        if incoming_fmts is not None:
            for k, v in incoming_fmts.items():
                self._fmts[k] = _AnsiSettingPoint(list(v.add), list(v.rem))

        # Unpack settings
        ansi_settings = []
        for s in settings:
            if not isinstance(s, list) and not isinstance(s, tuple):
                ansi_settings.append(s)
            else:
                ansi_settings += s

        if ansi_settings:
            self.apply_formatting(ansi_settings)

    def assign_str(self, s:str):
        '''
        Assigns the base string and adjusts the ANSI settings based on the new length.
        Parameters:
            s - the new string to set
        '''
        if len(s) > len(self.data):
            if len(self.data) in self._fmts:
                self._fmts[len(s)] = self._fmts.pop(len(self.data))
        elif len(s) < len(self.data):
            # This may erase some settings that will no longer apply
            self.clip(end=len(s), inplace=True)
        self.data = s

    @property
    def base_str(self) -> str:
        ''' Returns the base string without any formatting set. '''
        return self.data

    def copy(self) -> 'AnsiString':
        ''' Creates a new AnsiString which is a copy of the original '''
        return AnsiString(self)

    def _shift_settings_idx(self, num:int, keep_origin:bool):
        '''
        Shifts format settings to the right by the given index
        Parameters:
            num - positive number of elements to shift right
            keep_origin - true to keep format at index 0; false to shift as well
        '''
        if num < 0:
            raise ValueError('num cannot be negative')

        for key in sorted(self._fmts.keys(), reverse=True):
            if not keep_origin or key != 0:
                new_key = max(key + num, 0)
                self._fmts[new_key] = self._fmts.pop(key)

    def apply_formatting(
            self,
            settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple],
            start:int=0,
            end:Union[int,None]=None,
            topmost:bool=True
    ):
        '''
        Sets the formatting for a given range of characters.
        Parameters:
            settings - setting or list of settings to apply
            start - The string start index where setting(s) are to be applied
            end - The string index where the setting(s) should be removed
            topmost - When true, the settings placed at the end of the set for the given
                      start_index, meaning it takes precedent over others; the opposite when False
        '''
        start = self._slice_val_to_idx(start, 0)
        end = self._slice_val_to_idx(end, len(self.data))

        if not settings or start >= len(self.data) or end <= start:
            # Ignore - nothing to apply
            return

        ansi_settings = _AnsiSettingPoint._scrub_ansi_settings(settings, make_unique=True)

        # Apply settings
        if start not in self._fmts:
            self._fmts[start] = _AnsiSettingPoint()
        self._fmts[start].insert_settings(True, ansi_settings, topmost)

        # Remove settings
        if end not in self._fmts:
            self._fmts[end] = _AnsiSettingPoint()
        self._fmts[end].insert_settings(False, ansi_settings, topmost)

    def remove_formatting(
            self,
            settings:Union[None, AnsiFormat, AnsiSetting, str, int, list, tuple]=None,
            start:int=0,
            end:Union[int,None]=None
    ):
        '''
        Remove the given formatting settings from the given range
        Parameters:
            settings - setting or list of settings to apply (remove all if None specified)
            start - The string start index where setting(s) are to be applied
            end - The string index where the setting(s) should be removed
        '''
        start = self._slice_val_to_idx(start, 0)
        end = self._slice_val_to_idx(end, len(self.data))

        if (settings is not None and not settings) or start >= len(self.data) or end <= start:
            # Ignore - nothing to apply
            return

        if start not in self._fmts:
            self._fmts[start] = _AnsiSettingPoint()

        if end not in self._fmts:
            self._fmts[end] = _AnsiSettingPoint()

        if not settings:
            ansi_settings = None
        else:
            ansi_settings = _AnsiSettingPoint._scrub_ansi_settings(settings)

        removed_settings = []
        for idx, settings_point, current_settings in _AnsiSettingsIterator(self._fmts):
            if idx < start:
                continue
            elif idx > end:
                break

            if idx == start:
                for s in current_settings:
                    if ansi_settings is None or s in ansi_settings:
                        add_idx = __class__._find_setting_reference(s, settings_point.add)
                        if add_idx < 0:
                            settings_point.rem.append(s)
                            removed_settings.append(s)
                        else:
                            del settings_point.add[add_idx]
                            removed_settings.append(s)
            else:
                for i in reversed(range(len(settings_point.rem))):
                    s = settings_point.rem[i]
                    rem_idx = __class__._find_setting_reference(s, removed_settings)
                    if rem_idx >= 0:
                        del removed_settings[rem_idx]
                        del settings_point.rem[i]

                if idx == end:
                    if end != len(self.data):
                        settings_point.add += removed_settings
                else:
                    for i in reversed(range(len(settings_point.add))):
                        if ansi_settings is None or settings_point.add[i] in ansi_settings:
                            removed_settings.append(settings_point.add[i])
                            del settings_point.add[i]

        # Clean up now empty entries
        for idx in list(self._fmts.keys()):
            if not self._fmts[idx]:
                del self._fmts[idx]

    def apply_formatting_for_match(
            self,
            settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple],
            match_object,
            group:int=0
    ):
        '''
        Apply formatting using a match object generated from re
        Parameters:
            settings - setting or list of settings to apply to matching strings
            match_object - the match object to use (result of re.search() or re.finditer())
            group - match the group to set
        '''
        s = match_object.start(group)
        e = match_object.end(group)
        self.apply_formatting(settings, s, e)

    def format_matching(
        self,
        matchspec:str,
        *format:Union[AnsiFormat, AnsiSetting, str, int, list, tuple],
        regex:bool=False,
        match_case=False,
        count=-1
    ):
        '''
        Apply formatting for anything matching the matchspec
        Parameters:
            matchspec - the string to match
            format - 0 to many format specifiers
            regex - set to True to treat matchspec as a regex string
            match_case - set to True to make matching case-sensitive (false by default)
            count - the number of matches to format or -1 to match all
        '''
        if not regex:
            matchspec = re.escape(matchspec)

        for match in re.finditer(matchspec, self.data, re.IGNORECASE if not match_case else 0):
            if count < 0 or count > 0:
                self.apply_formatting_for_match(format, match)
                if count > 0:
                    count -= 1
            else:
                break

    def unformat_matching(
        self,
        matchspec:str,
        *format:Union[None, AnsiFormat, AnsiSetting, str, int, list, tuple],
        regex:bool=False,
        match_case=False,
        count=-1
    ):
        '''
        Remove the given formatting for anything matching the matchspec
        Parameters:
            matchspec - the string to match
            format - 0 to many format specifiers (remove all if None specified)
            regex - set to True to treat matchspec as a regex string
            match_case - set to True to make matching case-sensitive (false by default)
            count - the number of matches to unformat or -1 to match all
        '''
        if not regex:
            matchspec = re.escape(matchspec)

        if not format or None in format:
            format = None

        for match in re.finditer(matchspec, self.data, re.IGNORECASE if not match_case else 0):
            if count < 0 or count > 0:
                self.remove_formatting(format, match.start(0), match.end(0))
                if count > 0:
                    count -= 1
            else:
                break

    def clear_formatting(self):
        ''' Clears all internal formatting. '''
        self._fmts = {}

    @staticmethod
    def _find_setting_reference(find:AnsiSetting, in_list:List[AnsiSetting]) -> int:
        '''
        Parses a list of AnsiSettings for a given AnsiSetting reference
        Parameters:
            find - the setting reference to search for
            in_list - the setting list to search
        Returns: -1 if setting not found or integer >=0 if found
        '''
        for i, s in enumerate(in_list):
            if s is find:
                return i
        return -1

    @staticmethod
    def _find_settings_references(find_list:List[AnsiSetting], in_list:List[AnsiSetting]) -> List[Tuple[int, int]]:
        '''
        Parses a list of AniSettings for any AnsiSetting references in a find list
        Parameters:
            find_list - a list of AnsiSetting reference to search for
            in_list - the list to search in
        Returns:
            A list of integer pairs, ordered by elements found from find_list. First element in each pair is a find_list
            index, and second element is an in_list index.
        '''
        matches = []
        for i, s in enumerate(find_list):
            for i2, s2 in enumerate(in_list):
                if s is s2:
                    matches.append((i, i2))
        return matches

    def _slice_val_to_idx(self, val:int, default:int) -> int:
        '''
        Converts a slice start or stop value to a real index into my string
        Parameters:
            val - start or stop value
            default - the default value to use when val is None
        Returns: a real index into my string
        '''
        if val is None:
            return default
        elif val < 0:
            ret_val = len(self.data) + val
            if ret_val < 0:
                ret_val = 0
            return ret_val
        else:
            return val

    def __getitem__(self, val:Union[int, slice]) -> 'AnsiString':
        '''
        Returns a new AnsiString object which represents a substring of self.
        Parameters:
            val - an index or slice to retrieve (step value must be None or 1 when slice is given)
        Returns: a new AnsiString which represents the given range in val

        Note: the new copy may contain some references to AnsiSettings in the origin. This is ok since AnsiSettings
              are not internally modified after creation.
        '''
        if isinstance(val, int):
            st = val
            en = val + 1
        elif isinstance(val, slice):
            if val.step is not None and val.step != 1:
                raise ValueError('Step other than 1 not supported')
            st = self._slice_val_to_idx(val.start, 0)
            en = self._slice_val_to_idx(val.stop, len(self.data))
        else:
            raise TypeError('Invalid type for __getitem__')

        new_s = AnsiString(self.data[val])

        if not new_s.data:
            # Special case - string is now empty
            return new_s

        # String cannot be empty from this point on, so that will be assumed going forward

        previous_settings = None
        settings_initialized = False
        for idx, settings, current_settings in _AnsiSettingsIterator(self._fmts):
            if idx > len(self.data) or idx > en:
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
            new_len = len(new_s.data)
            if new_len not in new_s._fmts:
                new_s._fmts[new_len] = _AnsiSettingPoint()
            settings_to_remove = [s for s in previous_settings if s not in new_s._fmts[new_len].rem]
            new_s._fmts[new_len].rem.extend(settings_to_remove)

        return new_s

    def __str__(self) -> str:
        ''' Returns a string with ANSI-formatting applied '''
        return self.__format__(None)

    def __repr__(self) -> str:
        ''' Returns repr of a string with ANSI-formatting applied '''
        return self.__format__(None).__repr__()

    def _apply_string_format(self, string_format:str):
        '''
        Applies string formatting, given from the format spec (justification settings)
        Parameters:
            string_format - the string format to apply
        '''
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
        Parameters:
            __format_spec - must be in the format "[string_format][:ansi_format]" where string_format is the standard
                            string format specifier and ansi_format contains 0 or more ansi directives separated by
                            semicolons (;)
                            ex: ">10:bold;red" to make output right justify with width of 10, bold and red formatting
        '''
        if not __format_spec and not self._fmts:
            # No formatting
            return self.data

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
            out_str += obj.data[last_idx:idx]
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
        out_str += obj.data[last_idx:]
        if clear_needed:
            # Clear settings
            out_str += ansi_escape_clear

        return out_str

    def __iter__(self) -> 'AnsiString':
        ''' Iterates over each character of this AnsiString '''
        return iter(_AnsiCharIterator(self))

    def capitalize(self, inplace:bool=False) -> 'AnsiString':
        '''
        Return a capitalized version of the string.
        More specifically, make the first character have upper case and the rest lower case.
        Parameters:
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj.data = obj.data.capitalize()
        return obj

    def casefold(self, inplace:bool=False) -> 'AnsiString':
        '''
        Return a version of the string suitable for caseless comparisons.
        Parameters:
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj.data = obj.data.casefold()
        return obj

    def center(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiString':
        '''
        Center justification.
        Parameters:
            width - the number of characters to center over
            fillchar - the character used to fill empty spaces
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if len(fillchar) != 1:
            raise ValueError('fillchar must be exactly 1 character in length')

        if inplace:
            obj = self
        else:
            obj = self.copy()

        old_len = len(obj.data)
        num = width - old_len
        if num > 0:
            left_spaces = math.floor((num) / 2)
            right_spaces = num - left_spaces
            obj.data = fillchar * left_spaces + obj.data + fillchar * right_spaces
            # Move the removal settings from previous end to new end (formats the right fillchars with same as last char)
            if old_len in obj._fmts:
                obj._fmts[len(obj.data)] = obj._fmts.pop(old_len)
            # Shift all indices except for the origin (formats the left fillchars with same as first char)
            obj._shift_settings_idx(left_spaces, True)

        return obj

    def ljust(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiString':
        '''
        Left justification.
        Parameters:
            width - the number of characters to left justify over
            fillchar - the character used to fill empty spaces
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if len(fillchar) != 1:
            raise ValueError('fillchar must be exactly 1 character in length')

        if inplace:
            obj = self
        else:
            obj = self.copy()

        old_len = len(obj.data)
        num = width - old_len
        if num > 0:
            obj.data += fillchar * num
            # Move the removal settings from previous end to new end (formats the right fillchars with same as last char)
            if old_len in obj._fmts:
                obj._fmts[len(obj.data)] = obj._fmts.pop(old_len)

        return obj

    def rjust(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiString':
        '''
        Right justification.
        Parameters:
            width - the number of characters to right justify over
            fillchar - the character used to fill empty spaces
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if len(fillchar) != 1:
            raise ValueError('fillchar must be exactly 1 character in length')

        if inplace:
            obj = self
        else:
            obj = self.copy()

        old_len = len(obj.data)
        num = width - old_len
        if num > 0:
            obj.data = fillchar * num + obj.data
            # Shift all indices except for the origin (formats the left fillchars with same as first char)
            obj._shift_settings_idx(num, True)

        return obj

    def __add__(self, value:Union[str,'AnsiString','AnsiStr']) -> 'AnsiString':
        '''
        Appends a str or AnsiString to an AnsiString
        Note: an appended str will take on the formatting of the last character in the AnsiString
        Parameters:
            value - the right-hand-side value as str or AnsiString
        Returns: a new AnsiString
        '''
        cpy = self.copy()
        cpy += value
        return cpy

    def __iadd__(self, value:Union[str,'AnsiString','AnsiStr']) -> 'AnsiString':
        '''
        Appends a string or AnsiString to this AnsiString
        Parameters:
            value - the right-hand-side value as str or AnsiString
        Returns: self
        '''
        if isinstance(value, AnsiString):
            incoming_str = value.data
            incoming_fmts = value._fmts
        elif isinstance(value, AnsiStr):
            incoming_str = value._ansi_string.data
            incoming_fmts = value._ansi_string._fmts
        elif isinstance(value, str):
            incoming_str = value
            incoming_fmts = {}
        else:
            raise TypeError(f'value is invalid type: {type(value)}')

        shift = len(self.data)
        self.data += incoming_str
        find_settings = []
        replace_settings = []
        for key, settings in sorted(incoming_fmts.items()):
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

        return self

    def __eq__(self, value:'AnsiString') -> bool:
        '''
        == operator - returns True if exactly equal
        Note: this may return False even if the two strings look the same. To be exactly equal means the format settings
              are the same, arranged in the same order, and any duplicate entries match between the two.
        '''
        if not isinstance(value, AnsiString):
            return False
        return self.data == value.data and self._fmts == value._fmts

    def __contains__(self, value:Union[str,'AnsiString','AnsiStr',Any]) -> bool:
        ''' Returns True iff the str or the underlying str of an AnsiString is in this AnsiString '''
        if isinstance(value, AnsiString):
            return value.data in self.data
        elif isinstance(value, AnsiStr):
            return value._ansi_string.data in self.data
        elif isinstance(value, str):
            return value in self.data
        return False

    def __len__(self) -> int:
        ''' Returns the length of the underlying string '''
        return len(self.data)

    @staticmethod
    def join(*args:Union[str,'AnsiString','AnsiStr']) -> 'AnsiString':
        ''' Joins strings and AnsiStrings into a single AnsiString object '''
        if not args:
            return AnsiString()
        args = list(args)
        first_arg = args[0]
        if isinstance(first_arg, AnsiString):
            joint = first_arg.copy()
        elif isinstance(first_arg, AnsiStr):
            joint = first_arg._ansi_string.copy()
        elif isinstance(first_arg, str):
            joint = AnsiString(first_arg)
        else:
            raise TypeError(f'value is invalid type: {type(first_arg)}')
        for arg in args[1:]:
            joint += arg
        return joint

    def lower(self, inplace:bool=False) -> 'AnsiString':
        '''
        Convert to lowercase.
        Parameters:
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj.data = obj.data.lower()
        return obj

    def upper(self, inplace:bool=False) -> 'AnsiString':
        '''
        Convert to uppercase.
        Parameters:
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()
        obj.data = obj.data.upper()
        return obj

    def lstrip(self, chars:str=None, inplace:bool=False) -> 'AnsiString':
        '''
        Remove leading whitespace
        Parameters:
            chars - If not None, remove characters in chars instead
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        return self._strip(chars=chars, inplace=inplace, do_lstrip=True, do_rstrip=False)

    def clip(self, start:int=None, end:int=None, inplace:bool=False) -> 'AnsiString':
        '''
        Calls [] operator and optionally assigns in-place
        Parameters:
            start - start index
            end - end index
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        obj = self[start:end]
        if inplace:
            self.data = obj.data
            self._fmts = obj._fmts
            del obj
            return self
        else:
            return obj

    def rstrip(self, chars:str=None, inplace:bool=False) -> 'AnsiString':
        '''
        Remove trailing whitespace
        Parameters:
            chars - If not None, remove characters in chars instead
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        return self._strip(chars=chars, inplace=inplace, do_lstrip=False, do_rstrip=True)

    def strip(self, chars:str=None, inplace:bool=False) -> 'AnsiString':
        '''
        Remove leading and trailing whitespace
        Parameters:
            chars - If not None, remove characters in chars instead
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        return self._strip(chars=chars, inplace=inplace, do_lstrip=True, do_rstrip=True)

    def _strip(self, chars:str=None, inplace:bool=False, do_lstrip:bool=True, do_rstrip:bool=True) -> 'AnsiString':
        '''
        Remove leading and trailing whitespace
        Parameters:
            chars - If not None, remove characters in chars instead
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
            do_lstrip - True to do left strip
            do_rstrip - Trie to do right strip
        '''
        if chars is None:
            chars = WHITESPACE_CHARS

        lcount = 0
        if do_lstrip:
            for char in self.data:
                if char in chars:
                    lcount += 1
                else:
                    break

        rcount = None
        if do_rstrip and lcount < len (self.data):
            rcount = 0
            for char in reversed(self.data):
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
        idx = self.data.find(sep)
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
        idx = self.data.rfind(sep)
        if idx >= 0:
            sep_len = len(sep)
            idx_end = idx + sep_len
            return (self[0:idx], self[idx:idx_end], self[idx_end:])
        else:
            return (self.copy(), AnsiString(), AnsiString())

    def ansi_settings_at(self, idx:int) -> List[AnsiSetting]:
        '''
        Returns a list of AnsiSettings at the given index
        Parameters:
            idx - the index to get settings of
        '''
        if idx >= 0 and idx < len(self.data):
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
        Parameters:
            idx - the index to get settings of
        '''
        return ansi_sep.join([str(s) for s in self.ansi_settings_at(idx)])

    def removeprefix(self, prefix:str, inplace:bool=False) -> 'AnsiString':
        '''
        Return a str with the given prefix string removed if present.

        If the string starts with the prefix string, return string[len(prefix):]. Otherwise, return the original string.

        Parameters:
            prefix - the prefix to remove
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if not self.data.startswith(prefix):
            if inplace:
                return self
            else:
                return self.copy()
        else:
            return self.clip(start=len(prefix), inplace=inplace)

    def removesuffix(self, suffix:str, inplace:bool=False) -> 'AnsiString':
        '''
        Return a str with the given suffix string removed if present.

        If the string ends with the suffix string and that suffix is not empty, return string[:-len(suffix)]. Otherwise,
        return the original string.

        Parameters:
            suffix - the suffix to remove
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        if not self.data.endswith(suffix):
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
        Parameters:
            old - the string to search for
            new - the string to replace; if this is a str type, the formatting of the replacement will match the
                  formatting of the first character of the old string
            count - the number of occurrences to replace or -1 to replace all occurrences
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        obj = self
        idx = obj.data.find(old)
        while (count < 0 or count > 0) and idx >= 0:
            if isinstance(new, str):
                replace = AnsiString(new, obj.ansi_settings_at(idx))
            else:
                replace = new
            obj = obj[:idx] + replace + obj[idx+len(old):]
            if count > 0:
                count -= 1
            idx = obj.data.find(old, idx + len(new))

        if inplace:
            self.data = obj.data
            self._fmts = obj._fmts
            return self
        else:
            return obj

    def count(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        Return the number of non-overlapping occurrences of substring sub in
        string S[start:end]. Optional arguments start and end are interpreted as in slice notation.
        '''
        return self.data.count(sub, start, end)

    def encode(self, encoding:str="utf-8", errors:str="strict") -> bytes:
        '''
        Encode the string using the codec registered for encoding.

        encoding
        The encoding in which to encode the string.
        errors
        The error handling scheme to use for encoding errors. The default is 'strict' meaning that encoding errors raise
        a UnicodeEncodeError. Other possible values are 'ignore', 'replace' and 'xmlcharrefreplace' as well as any other
        name registered with codecs.register_error that can handle UnicodeEncodeErrors.
        '''
        return str(self).encode(encoding, errors)

    def endswith(self, suffix:str, start:int=None, end:int=None) -> bool:
        '''
        Return True if S ends with the specified suffix, False otherwise. With optional start, test S beginning at that
        position. With optional end, stop comparing S at that position. suffix can also be a tuple of strings to try.
        '''
        return self.data.endswith(suffix, start, end)

    def expandtabs(self, tabsize:int=8, inplace:bool=False) -> 'AnsiString':
        '''
        Replaces all tab characters with the given number of spaces
        Parameters:
            tabsize - number of spaces to replace each tab with
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        return self.replace('\t', ' ' * tabsize, inplace=inplace)

    def find(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].
        Optional arguments start and end are interpreted as in slice notation.

        Return -1 on failure.
        '''
        return self.data.find(sub, start, end)

    def index(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].
        Optional arguments start and end are interpreted as in slice notation.

        Raises ValueError when the substring is not found.
        '''
        return self.data.index(sub, start, end)

    def isalnum(self) -> bool:
        '''
        Return True if the string is an alpha-numeric string, False otherwise.

        A string is alpha-numeric if all characters in the string are alpha-numeric and there is at least one character
        in the string
        '''
        return self.data.isalnum()

    def isalpha(self) -> bool:
        '''
        Return True if the string is an alphabetic string, False otherwise.

        A string is alphabetic if all characters in the string are alphabetic and there is at least one character in the
        string.
        '''
        return self.data.isalpha()

    def isascii(self) -> bool:
        '''
        This is only available for Python >=3.7; exception will be raised in Python 3.6

        Return True if all characters in the string are ASCII, False otherwise.

        ASCII characters have code points in the range U+0000-U+007F. Empty string is ASCII too.
        '''
        return self.data.isascii()

    def isdecimal(self) -> bool:
        '''
        Return True if the string is a decimal string, False otherwise.

        A string is a decimal string if all characters in the string are decimal and there is at least one character in
        the string.
        '''
        return self.data.isdecimal()

    def isdigit(self) -> bool:
        '''
        Return True if the string is a digit string, False otherwise.

        A string is a digit string if all characters in the string are digits and there is at least one character in the
        string.
        '''
        return self.data.isdigit()

    def isidentifier(self) -> bool:
        '''
        Return True if the string is a valid Python identifier, False otherwise.

        Call keyword.iskeyword(s) to test whether string s is a reserved identifier, such as "def" or "class".
        '''
        return self.data.isidentifier()

    def islower(self) -> bool:
        '''
        Return True if the string is a lowercase string, False otherwise.

        A string is lowercase if all cased characters in the string are lowercase and there is at least one cased
        character in the string.
        '''
        return self.data.islower()

    def isnumeric(self) -> bool:
        '''
        Return True if the string is a numeric string, False otherwise.

        A string is numeric if all characters in the string are numeric and there is at least one character in the
        string.
        '''
        return self.data.isnumeric()

    def isprintable(self) -> bool:
        '''
        Return True if the string is printable, False otherwise.

        A string is printable if all of its characters are considered printable in repr() or if it is empty.
        '''
        return self.data.isprintable()

    def isspace(self) -> bool:
        '''
        Return True if the string is a whitespace string, False otherwise.

        A string is whitespace if all characters in the string are whitespace and there is at least one character in the string.
        '''
        return self.data.isspace()

    def istitle(self) -> bool:
        '''
        Return True if the string is a title-cased string, False otherwise.

        In a title-cased string, upper- and title-case characters may only follow uncased characters and lowercase
        characters only cased ones.
        '''
        return self.data.istitle()

    def isupper(self) -> bool:
        '''
        Return True if the string is an uppercase string, False otherwise.

        A string is uppercase if all cased characters in the string are uppercase and there is at least one cased
        character in the string.
        '''
        return self.data.isupper()

    def rfind(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        S.rfind(sub[, start[, end]]) -> int

        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice
        notation.

        Return -1 on failure.
        '''
        return self.data.rfind(sub, start, end)

    def rindex(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        S.rindex(sub[, start[, end]]) -> int

        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice
        notation.

        Raises ValueError when the substring is not found.
        '''
        return self.data.rindex(sub, start, end)

    def _split(self, sep:Union[str,None]=None, maxsplit:int=-1, r:bool=False) -> List['AnsiString']:
        '''
        Return a list of substrings in the string, using sep as the separator string.
        Parameters:
            sep - the separator string (use whitespace characters if None)
            maxsplit - maximum number of splits to make or -1 for no limit
            r - True to search from right; False to search from left
        '''
        if r:
            str_splits = self.data.rsplit(sep, maxsplit)
        else:
            str_splits = self.data.split(sep, maxsplit)
        split_idx_len = []
        idx = 0
        for s in str_splits:
            idx = self.data.find(s, idx)
            split_idx_len.append((idx, len(s)))
            idx += len(s)

        ansi_str_splits = []
        for idx, length in split_idx_len:
            ansi_str_splits.append(self[idx:idx+length])

        return ansi_str_splits

    def split(self, sep:Union[str,None]=None, maxsplit:int=-1) -> List['AnsiString']:
        '''
        Return a list of the substrings in the string, using sep as the separator string.

        sep
            The separator used to split the string.

            When set to None (the default value), will split on any whitespace character (including \n \r \t \f and
            spaces) and will discard empty strings from the result.
        maxsplit
            Maximum number of splits (starting from the left). -1 (the default value) means no limit.

        Note, str.split() is mainly useful for data that has been intentionally delimited. With natural text that
        includes punctuation, consider using the regular expression module.
        '''
        return self._split(sep, maxsplit, False)

    def rsplit(self, sep:Union[str,None]=None, maxsplit:int=-1) -> List['AnsiString']:
        '''
        Return a list of the substrings in the string, using sep as the separator string.

        sep
            The separator used to split the string.

            When set to None (the default value), will split on any whitespace character (including \n \r \t \f and
            spaces) and will discard empty strings from the result.
        maxsplit
            Maximum number of splits (starting from the left). -1 (the default value) means no limit.

        Splitting starts at the end of the string and works to the front.
        '''
        return self._split(sep, maxsplit, True)

    def splitlines(self, keepends:bool=False) -> List['AnsiString']:
        '''
        Return a list of the lines in the string, breaking at line boundaries.

        Line breaks are not included in the resulting list unless keepends is given and true.
        '''
        str_splits = self.data.splitlines(keepends)
        split_idx_len = []
        idx = 0
        for s in str_splits:
            idx = self.data.find(s, idx)
            split_idx_len.append((idx, len(s)))
            idx += len(s)

        ansi_str_splits = []
        for idx, length in split_idx_len:
            ansi_str_splits.append(self[idx:idx+length])

        return ansi_str_splits

    def swapcase(self, inplace:bool=False) -> 'AnsiString':
        ''' Convert uppercase characters to lowercase and lowercase characters to uppercase. '''
        if inplace:
            obj = self
        else:
            obj = self.copy()

        obj.data = obj.data.swapcase()

        return obj

    def title(self, inplace:bool=False) -> 'AnsiString':
        '''
        Return a version of the string where each word is titlecased.

        More specifically, words start with uppercased characters and all remaining cased characters have lower case.
        '''
        if inplace:
            obj = self
        else:
            obj = self.copy()

        obj.data = obj.data.title()

        return obj

    def zfill(self, width:int, inplace:bool=False) -> 'AnsiString':
        '''
        Pad a numeric string with zeros on the left, to fill a field of the given width.

        The string is never truncated.
        '''
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
    def _scrub_ansi_format_int(ansi_format:int) -> AnsiSetting:
        if ansi_format < 0:
            raise ValueError(f'Invalid value [{ansi_format}]; must be greater than or equal to 0')
        return AnsiSetting(ansi_format)

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
                        except ValueError:
                            raise ValueError(
                                'AnsiString.__format__ failed to parse format ({}); invalid name: {}'
                                .format(ansi_format, format)
                            )
                        else:
                            # Value is an integer - use the format verbatim
                            format_settings.append(__class__._scrub_ansi_format_int(int_value))
                    else:
                        format_settings.append(rgb_format)
            return format_settings

    @staticmethod
    def _scrub_ansi_settings(
        settings:Union[List[str], str, List[int], int, List[AnsiFormat], AnsiFormat, List['AnsiSetting'], 'AnsiSetting'],
        make_unique=False
    ) -> List[AnsiSetting]:
        if not isinstance(settings, list) and not isinstance(settings, tuple):
            settings = [settings]

        settings_out = []
        for setting in settings:
            if isinstance(setting, AnsiSetting):
                if make_unique:
                    setting = AnsiSetting(setting)
                settings_out.append(setting)
            elif isinstance(setting, str):
                settings_out.extend(__class__._scrub_ansi_format_string(setting))
            elif isinstance(setting, int):
                settings_out.append(__class__._scrub_ansi_format_int(setting))
            elif hasattr(setting, "setting"):
                settings_out.append(setting.setting)
        return settings_out

    def insert_settings(self, apply:bool, settings:Union[List[AnsiSetting], AnsiSetting], topmost:bool=True):
        if not isinstance(settings, list) and not isinstance(settings, tuple):
            settings = [settings]

        lst = self.add if apply else self.rem
        if topmost:
            lst.extend(settings)
        else:
            lst[:0] = settings

class _AnsiSettingsIterator:
    '''
    Internally-used class which helps iterate over settings
    '''
    def __init__(self, settings_dict:Dict[int,_AnsiSettingPoint]):
        self.settings_dict:Dict[int,_AnsiSettingPoint] = settings_dict
        self.current_settings:List[AnsiSetting] = []
        self.dict_iter = iter(sorted(self.settings_dict))

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[int,_AnsiSettingPoint,List[AnsiSetting]]:
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

class AnsiStr(str):
    '''
    Immutable version of AnsiString. The advantage of this object is that isinstance(AnsiStr(), str) returns True.
    This is currently experimental and not completely tested.
    '''
    def __new__(
        cls,
        s:Union[str,'AnsiString','AnsiStr']='',
        *settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple]
    ):
        if isinstance(s, AnsiString):
            if settings:
                ansi_string = AnsiString(s, *settings)
            else:
                ansi_string = s
        elif isinstance(s, AnsiStr):
            if settings:
                ansi_string = AnsiString(s._ansi_string, *settings)
            else:
                ansi_string = s._ansi_string
        elif isinstance(s, str):
            ansi_string = AnsiString(s, *settings)
        else:
            raise TypeError('Invalid type for s')
        instance = super().__new__(cls, str(ansi_string))
        instance._ansi_string = ansi_string
        return instance

    @property
    def base_str(self) -> str:
        ''' Returns the base string without any formatting set. '''
        return self._ansi_string.base_str

    def __len__(self) -> int:
        ''' Returns the length of the underlying string '''
        return self._ansi_string.__len__()

    def __add__(self, value:Union[str,'AnsiString','AnsiStr']) -> 'AnsiStr':
        '''
        Appends a str or AnsiString to an AnsiStr
        Note: an appended str will take on the formatting of the last character in the AnsiString
        Parameters:
            value - the right-hand-side value as str or AnsiString
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        if isinstance(value, AnsiStr):
            cpy += value._ansi_string
        else:
            cpy += value
        return AnsiStr(cpy)

    def __iadd__(self, value:Union[str,'AnsiString','AnsiStr']) -> 'AnsiStr':
        '''
        Appends a string or AnsiString to this AnsiString
        Parameters:
            value - the right-hand-side value as str or AnsiString
        Returns: a new AnsiStr
        '''
        # Can't add in place - always return a new instance
        return (self + value)

    def __format__(self, __format_spec:str) -> str:
        '''
        Returns an ANSI format string with both internal and given formatting spec set.
        Parameters:
            __format_spec - must be in the format "[string_format][:ansi_format]" where string_format is the standard
                            string format specifier and ansi_format contains 0 or more ansi directives separated by
                            semicolons (;)
                            ex: ">10:bold;red" to make output right justify with width of 10, bold and red formatting
        '''
        return self._ansi_string.__format__(__format_spec)

    def __getitem__(self, val:Union[int, slice]) -> 'AnsiStr':
        '''
        Returns a new AnsiStr object which represents a substring of self.
        Parameters:
            val - an index or slice to retrieve (step value must be None or 1 when slice is given)
        Returns: a new AnsiStr which represents the given range in val

        Note: the new copy may contain some references to AnsiSettings in the origin. This is ok since AnsiSettings
              are not internally modified after creation.
        '''
        return AnsiStr(self._ansi_string.__getitem__(val))

    def apply_formatting(
            self,
            settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple],
            start:int=0,
            end:Union[int,None]=None,
            topmost:bool=True
    ) -> 'AnsiStr':
        '''
        Apply formatting using a match object generated from re into a new AnsiStr
        Parameters:
            settings - setting or list of settings to apply to matching strings
            match_object - the match object to use (result of re.search() or re.finditer())
            group - match the group to set
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.apply_formatting(settings, start, end, topmost)
        return AnsiStr(cpy)

    def remove_formatting(
            self,
            settings:Union[None, AnsiFormat, AnsiSetting, str, int, list, tuple]=None,
            start:int=0,
            end:Union[int,None]=None
    ) -> 'AnsiStr':
        '''
        Remove the given formatting settings from the given range into a new AnsiStr
        Parameters:
            settings - setting or list of settings to apply (remove all if None specified)
            start - The string start index where setting(s) are to be applied
            end - The string index where the setting(s) should be removed
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.remove_formatting(settings, start, end)
        return AnsiStr(cpy)

    def apply_formatting_for_match(
            self,
            settings:Union[AnsiFormat, AnsiSetting, str, int, list, tuple],
            match_object,
            group:int=0
    ) -> 'AnsiStr':
        '''
        Apply formatting using a match object generated from re into a new AnsiStr
        Parameters:
            settings - setting or list of settings to apply to matching strings
            match_object - the match object to use (result of re.search() or re.finditer())
            group - match the group to set
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.apply_formatting_for_match(settings, match_object, group)
        return AnsiStr(cpy)

    def format_matching(
        self,
        matchspec:str,
        *format:Union[AnsiFormat, AnsiSetting, str, int, list, tuple],
        regex:bool=False,
        match_case=False,
        count=-1
    ) -> 'AnsiStr':
        '''
        Apply formatting for anything matching the matchspec into a new AnsiStr
        Parameters:
            matchspec - the string to match
            format - 0 to many format specifiers
            regex - set to True to treat matchspec as a regex string
            match_case - set to True to make matching case-sensitive (false by default)
            count - the number of matches to format or -1 to match all
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.format_matching(matchspec, *format, regex=regex, match_case=match_case, count=count)
        return AnsiStr(cpy)

    def unformat_matching(
        self,
        matchspec:str,
        *format:Union[None, AnsiFormat, AnsiSetting, str, int, list, tuple],
        regex:bool=False,
        match_case=False,
        count=-1
    ) -> 'AnsiStr':
        '''
        Remove the given formatting for anything matching the matchspec into a new AnsiStr
        Parameters:
            matchspec - the string to match
            format - 0 to many format specifiers (remove all if None specified)
            regex - set to True to treat matchspec as a regex string
            match_case - set to True to make matching case-sensitive (false by default)
            count - the number of matches to unformat or -1 to match all
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.unformat_matching(matchspec, *format, regex=regex, match_case=match_case, count=count)
        return AnsiStr(cpy)

    def __iter__(self) -> 'AnsiStr':
        ''' Iterates over each character of this AnsiStr '''
        return iter(_AnsiStrCharIterator(self))

    def center(self, width:int, fillchar:str=' ') -> 'AnsiStr':
        '''
        Center justification.
        Parameters:
            width - the number of characters to center over
            fillchar - the character used to fill empty spaces
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.center(width, fillchar, inplace=True)
        return AnsiStr(cpy)

    def ljust(self, width:int, fillchar:str=' ') -> 'AnsiStr':
        '''
        Left justification.
        Parameters:
            width - the number of characters to left justify over
            fillchar - the character used to fill empty spaces
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.ljust(width, fillchar, inplace=True)
        return AnsiStr(cpy)

    def rjust(self, width:int, fillchar:str=' ', inplace:bool=False) -> 'AnsiStr':
        '''
        Right justification.
        Parameters:
            width - the number of characters to right justify over
            fillchar - the character used to fill empty spaces
        Returns: a new AnsiStr
        '''
        cpy = self._ansi_string.copy()
        cpy.rjust(width, fillchar, inplace=True)
        return AnsiStr(cpy)

    def __eq__(self, value:'AnsiStr') -> bool:
        '''
        == operator - returns True if exactly equal
        Note: this may return False even if the two strings look the same. To be exactly equal means the format settings
              are the same, arranged in the same order, and any duplicate entries match between the two.
        '''
        if not isinstance(value, AnsiStr):
            return False
        return str(self) == str(value)

    def __contains__(self, value:Union[str,'AnsiString','AnsiStr',Any]) -> bool:
        ''' Returns True iff the str or the underlying str of an AnsiString is in this AnsiString '''
        return self._ansi_string.__contains__(value)

    @staticmethod
    def join(*args:Union[str,'AnsiString','AnsiStr']) -> 'AnsiStr':
        ''' Joins strings and AnsiStrings into a single AnsiStr object '''
        return AnsiStr(AnsiString.join(*args))

    def lower(self) -> 'AnsiStr':
        '''
        Convert to lowercase into a new AnsiStr.
        '''
        cpy = self._ansi_string.copy()
        cpy.lower(inplace=True)
        return AnsiStr(cpy)

    def upper(self) -> 'AnsiStr':
        '''
        Convert to uppercase into a new AnsiStr.
        '''
        cpy = self._ansi_string.copy()
        cpy.upper(inplace=True)
        return AnsiStr(cpy)

    def lstrip(self, chars:str=None) -> 'AnsiStr':
        '''
        Remove leading whitespace into a new AnsiStr
        Parameters:
            chars - If not None, remove characters in chars instead
        '''
        cpy = self._ansi_string.copy()
        cpy.lstrip(chars, inplace=True)
        return AnsiStr(cpy)

    def clip(self, start:int=None, end:int=None) -> 'AnsiStr':
        '''
        Calls [] operator into a new AnsiStr
        Parameters:
            start - start index
            end - end index
        '''
        cpy = self._ansi_string.copy()
        cpy.clip(start, end, inplace=True)
        return AnsiStr(cpy)

    def rstrip(self, chars:str=None) -> 'AnsiStr':
        '''
        Remove trailing whitespace
        Parameters:
            chars - If not None, remove characters in chars instead
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        cpy = self._ansi_string.copy()
        cpy.rstrip(chars, inplace=True)
        return AnsiStr(cpy)

    def strip(self, chars:str=None) -> 'AnsiStr':
        '''
        Remove leading and trailing whitespace
        Parameters:
            chars - If not None, remove characters in chars instead
        '''
        cpy = self._ansi_string.copy()
        cpy.strip(chars, inplace=True)
        return AnsiStr(cpy)

    def partition(self, sep:str) -> Tuple['AnsiStr','AnsiStr','AnsiStr']:
        '''
        Partition the string into three parts using the given separator.

        This will search for the separator in the string. If the separator is found, returns a 3-tuple containing the
        part before the separator, the separator itself, and the part after it.

        If the separator is not found, returns a 3-tuple containing the original string and two empty strings.
        '''
        return [AnsiStr(x) for x in self._ansi_string.partition(sep)]

    def rpartition(self, sep:str) -> Tuple['AnsiStr','AnsiStr','AnsiStr']:
        '''
        Partition the string into three parts using the given separator, searching from right to left.

        This will search for the separator in the string. If the separator is found, returns a 3-tuple containing the
        part before the separator, the separator itself, and the part after it.

        If the separator is not found, returns a 3-tuple containing the original string and two empty strings.
        '''
        return [AnsiStr(x) for x in self._ansi_string.rpartition(sep)]

    def ansi_settings_at(self, idx:int) -> List[AnsiSetting]:
        '''
        Returns a list of AnsiSettings at the given index
        Parameters:
            idx - the index to get settings of
        '''
        return self._ansi_string.ansi_settings_at(idx)

    def settings_at(self, idx:int) -> str:
        '''
        Returns a string which represents the settings being used at the given index
        Parameters:
            idx - the index to get settings of
        '''
        return self._ansi_string.settings_at(idx)

    def removeprefix(self, prefix:str) -> 'AnsiStr':
        '''
        Return a str with the given prefix string removed if present.

        If the string starts with the prefix string, return string[len(prefix):]. Otherwise, return the original string.

        Parameters:
            prefix - the prefix to remove
        '''
        cpy = self._ansi_string.copy()
        cpy.removeprefix(prefix, inplace=True)
        return AnsiStr(cpy)

    def removesuffix(self, suffix:str) -> 'AnsiString':
        '''
        Return a str with the given suffix string removed if present.

        If the string ends with the suffix string and that suffix is not empty, return string[:-len(suffix)]. Otherwise,
        return the original string.

        Parameters:
            suffix - the suffix to remove
        '''
        cpy = self._ansi_string.copy()
        cpy.removesuffix(suffix, inplace=True)
        return AnsiStr(cpy)

    def replace(self, old:str, new:Union[str,'AnsiString'], count:int=-1) -> 'AnsiString':
        '''
        Does a find-and-replace - if new is a str, the string the is applied will take on the format settings of the
        first character of the old string in each replaced item.
        Parameters:
            old - the string to search for
            new - the string to replace; if this is a str type, the formatting of the replacement will match the
                  formatting of the first character of the old string
            count - the number of occurrences to replace or -1 to replace all occurrences
        '''
        cpy = self._ansi_string.copy()
        cpy.replace(old, new, count, inplace=True)
        return AnsiStr(cpy)

    def count(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        Return the number of non-overlapping occurrences of substring sub in
        string S[start:end]. Optional arguments start and end are interpreted as in slice notation.
        '''
        return self._ansi_string.count(sub, start, end)

    def encode(self, encoding:str="utf-8", errors:str="strict") -> bytes:
        '''
        Encode the string using the codec registered for encoding.

        encoding
        The encoding in which to encode the string.
        errors
        The error handling scheme to use for encoding errors. The default is 'strict' meaning that encoding errors raise
        a UnicodeEncodeError. Other possible values are 'ignore', 'replace' and 'xmlcharrefreplace' as well as any other
        name registered with codecs.register_error that can handle UnicodeEncodeErrors.
        '''
        return self._ansi_string.encode(encoding, errors)

    def endswith(self, suffix:str, start:int=None, end:int=None) -> bool:
        '''
        Return True if S ends with the specified suffix, False otherwise. With optional start, test S beginning at that
        position. With optional end, stop comparing S at that position. suffix can also be a tuple of strings to try.
        '''
        return self._ansi_string.endswith(suffix, start, end)

    def expandtabs(self, tabsize:int=8, inplace:bool=False) -> 'AnsiStr':
        '''
        Replaces all tab characters with the given number of spaces
        Parameters:
            tabsize - number of spaces to replace each tab with
            inplace - when True, do the conversion in-place and return self;
                      when False, do the conversion on a copy and return the copy
        '''
        return self.replace('\t', ' ' * tabsize, inplace=inplace)

    def find(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].
        Optional arguments start and end are interpreted as in slice notation.

        Return -1 on failure.
        '''
        return self._ansi_string.find(sub, start, end)

    def index(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].
        Optional arguments start and end are interpreted as in slice notation.

        Raises ValueError when the substring is not found.
        '''
        return self._ansi_string.index(sub, start, end)

    def isalnum(self) -> bool:
        '''
        Return True if the string is an alpha-numeric string, False otherwise.

        A string is alpha-numeric if all characters in the string are alpha-numeric and there is at least one character
        in the string
        '''
        return self._ansi_string.isalnum()

    def isalpha(self) -> bool:
        '''
        Return True if the string is an alphabetic string, False otherwise.

        A string is alphabetic if all characters in the string are alphabetic and there is at least one character in the
        string.
        '''
        return self._ansi_string.isalpha()

    def isascii(self) -> bool:
        '''
        This is only available for Python >=3.7; exception will be raised in Python 3.6

        Return True if all characters in the string are ASCII, False otherwise.

        ASCII characters have code points in the range U+0000-U+007F. Empty string is ASCII too.
        '''
        return self._ansi_string.isascii()

    def isdecimal(self) -> bool:
        '''
        Return True if the string is a decimal string, False otherwise.

        A string is a decimal string if all characters in the string are decimal and there is at least one character in
        the string.
        '''
        return self._ansi_string.isdecimal()

    def isdigit(self) -> bool:
        '''
        Return True if the string is a digit string, False otherwise.

        A string is a digit string if all characters in the string are digits and there is at least one character in the
        string.
        '''
        return self._ansi_string.isdigit()

    def isidentifier(self) -> bool:
        '''
        Return True if the string is a valid Python identifier, False otherwise.

        Call keyword.iskeyword(s) to test whether string s is a reserved identifier, such as "def" or "class".
        '''
        return self._ansi_string.isidentifier()

    def islower(self) -> bool:
        '''
        Return True if the string is a lowercase string, False otherwise.

        A string is lowercase if all cased characters in the string are lowercase and there is at least one cased
        character in the string.
        '''
        return self._ansi_string.islower()

    def isnumeric(self) -> bool:
        '''
        Return True if the string is a numeric string, False otherwise.

        A string is numeric if all characters in the string are numeric and there is at least one character in the
        string.
        '''
        return self._ansi_string.isnumeric()

    def isprintable(self) -> bool:
        '''
        Return True if the string is printable, False otherwise.

        A string is printable if all of its characters are considered printable in repr() or if it is empty.
        '''
        return self._ansi_string.isprintable()

    def isspace(self) -> bool:
        '''
        Return True if the string is a whitespace string, False otherwise.

        A string is whitespace if all characters in the string are whitespace and there is at least one character in the string.
        '''
        return self._ansi_string.isspace()

    def istitle(self) -> bool:
        '''
        Return True if the string is a title-cased string, False otherwise.

        In a title-cased string, upper- and title-case characters may only follow uncased characters and lowercase
        characters only cased ones.
        '''
        return self._ansi_string.istitle()

    def isupper(self) -> bool:
        '''
        Return True if the string is an uppercase string, False otherwise.

        A string is uppercase if all cased characters in the string are uppercase and there is at least one cased
        character in the string.
        '''
        return self._ansi_string.isupper()

    def rfind(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        S.rfind(sub[, start[, end]]) -> int

        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice
        notation.

        Return -1 on failure.
        '''
        return self._ansi_string.rfind(sub, start, end)

    def rindex(self, sub:str, start:int=None, end:int=None) -> int:
        '''
        S.rindex(sub[, start[, end]]) -> int

        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice
        notation.

        Raises ValueError when the substring is not found.
        '''
        return self._ansi_string.rindex(sub, start, end)

    def split(self, sep:Union[str,None]=None, maxsplit:int=-1) -> List['AnsiStr']:
        '''
        Return a list of the substrings in the string, using sep as the separator string.

        sep
            The separator used to split the string.

            When set to None (the default value), will split on any whitespace character (including \n \r \t \f and
            spaces) and will discard empty strings from the result.
        maxsplit
            Maximum number of splits (starting from the left). -1 (the default value) means no limit.

        Note, str.split() is mainly useful for data that has been intentionally delimited. With natural text that
        includes punctuation, consider using the regular expression module.
        '''
        return [AnsiStr(x) for x in self._ansi_string.split(sep, maxsplit)]

    def rsplit(self, sep:Union[str,None]=None, maxsplit:int=-1) -> List['AnsiStr']:
        '''
        Return a list of the substrings in the string, using sep as the separator string.

        sep
            The separator used to split the string.

            When set to None (the default value), will split on any whitespace character (including \n \r \t \f and
            spaces) and will discard empty strings from the result.
        maxsplit
            Maximum number of splits (starting from the left). -1 (the default value) means no limit.

        Splitting starts at the end of the string and works to the front.
        '''
        return [AnsiStr(x) for x in self._ansi_string.rsplit(sep, maxsplit)]

    def splitlines(self, keepends:bool=False) -> List['AnsiStr']:
        '''
        Return a list of the lines in the string, breaking at line boundaries.

        Line breaks are not included in the resulting list unless keepends is given and true.
        '''
        return [AnsiStr(x) for x in self._ansi_string.splitlines(keepends)]

    def swapcase(self) -> 'AnsiStr':
        ''' Convert uppercase characters to lowercase and lowercase characters to uppercase. '''
        cpy = self._ansi_string.copy()
        cpy.swapcase(inplace=True)
        return AnsiStr(cpy)

    def title(self) -> 'AnsiStr':
        '''
        Return a version of the string where each word is titlecased.

        More specifically, words start with uppercased characters and all remaining cased characters have lower case.
        '''
        cpy = self._ansi_string.copy()
        cpy.title(inplace=True)
        return AnsiStr(cpy)

    def zfill(self, width:int) -> 'AnsiString':
        '''
        Pad a numeric string with zeros on the left, to fill a field of the given width.

        The string is never truncated.
        '''
        cpy = self._ansi_string.copy()
        cpy.zfill(width, inplace=True)
        return AnsiStr(cpy)

class _AnsiStrCharIterator:
    '''
    Internally-used class which helps iterate over characters
    '''
    def __init__(self, s:'AnsiStr'):
        self.current_idx:int = -1
        self.s:AnsiStr = s

    def __iter__(self):
        return self

    def __next__(self) -> 'AnsiStr':
        self.current_idx += 1
        if self.current_idx >= len(self.s):
            raise StopIteration
        return self.s[self.current_idx]