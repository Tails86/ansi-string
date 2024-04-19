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

import sys
from enum import Enum
import io
from typing import Any, Union, List

__version__ = '0.0.3'
PACKAGE_NAME = 'ansi-string'

IS_WINDOWS = sys.platform.lower().startswith('win')

if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes
        import msvcrt

        def _kernel32_check_bool(result, func, args):
            if not result:
                raise ctypes.WinError(ctypes.get_last_error())
            return args

        LPDWORD = ctypes.POINTER(wintypes.DWORD)
        ctypes.windll.kernel32.GetConsoleMode.errcheck = _kernel32_check_bool
        ctypes.windll.kernel32.GetConsoleMode.argtypes = (wintypes.HANDLE, LPDWORD)
        ctypes.windll.kernel32.SetConsoleMode.errcheck = _kernel32_check_bool
        ctypes.windll.kernel32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)

        def win_en_virtual_terminal(fd:io.IOBase) -> bool:
            try:
                fd_handle = msvcrt.get_osfhandle(fd.fileno())
                current_mode = wintypes.DWORD()
                ctypes.windll.kernel32.GetConsoleMode(fd_handle, ctypes.byref(current_mode))
                ctypes.windll.kernel32.SetConsoleMode(fd_handle, current_mode.value | 4)
                return True
            except:
                return False
    except:
        # On any import/definition error, exploit the known Windows bug instead
        import subprocess
        def win_en_virtual_terminal(fd) -> bool:
            # This looks weird, but a bug in Windows causes ANSI to be enabled after this is called
            subprocess.run('', shell=True)
            return True

def en_tty_ansi(fd:io.IOBase=sys.stdout) -> bool:
    '''
    Ensures that ANSI formatting directives are accepted by the given TTY.
    fd: The TTY to set (normally either sys.stdout or sys.stderr)
    '''
    if fd.isatty():
        if IS_WINDOWS:
            return win_en_virtual_terminal(fd)
        else:
            # Nothing to do otherwise
            return True
    else:
        return False

class AnsiFormat(Enum):
    '''
    Formatting which may be supplied to AnsiString.
    '''
    RESET='0'
    BOLD='1'
    FAINT='2'
    ITALIC='3'
    ITALICS=ITALIC # Alias
    UNDERLINE='4'
    SLOW_BLINK='5'
    RAPID_BLINK='6'
    SWAP_BG_FG='7'
    HIDE='8'
    CROSSED_OUT='9'
    DEFAULT_FONT='10'
    ALT_FONT_1='11'
    ALT_FONT_2='12'
    ALT_FONT_3='13'
    ALT_FONT_4='14'
    ALT_FONT_5='15'
    ALT_FONT_6='16'
    ALT_FONT_7='17'
    ALT_FONT_8='18'
    ALT_FONT_9='19'
    GOTHIC_FONT='20'
    DOUBLE_UNDERLINE='21'
    NO_BOLD_FAINT='22'
    NO_ITALIC='23'
    NO_UNDERLINE='24'
    NO_BLINK='25'
    PROPORTIONAL_SPACING='26'
    NO_SWAP_BG_FG='27'
    NO_HIDE='28'
    NO_CROSSED_OUT='29'
    NO_PROPORTIONAL_SPACING='50'
    FRAMED='51'
    ENCIRCLED='52'
    OVERLINED='53'
    NO_FRAMED_ENCIRCLED='54'
    NO_OVERLINED='55'
    SET_UNDERLINE_COLOR='58' # Must be proceeded by rgb values
    DEFAULT_UNDERLINE_COLOR='59'

    FG_BLACK='30'
    FG_RED='31'
    FG_GREEN='32'
    FG_YELLOW='33'
    FG_BLUE='34'
    FG_MAGENTA='35'
    FG_CYAN='36'
    FG_WHITE='37'
    FG_SET='38' # Must be proceeded by rgb values
    FG_DEFAULT='39'
    FG_ORANGE=FG_SET+';5;202'
    FG_PURPLE=FG_SET+';5;129'

    BG_BLACK='40'
    BG_RED='41'
    BG_GREEN='42'
    BG_YELLOW='43'
    BG_BLUE='44'
    BG_MAGENTA='45'
    BG_CYAN='46'
    BG_WHITE='47'
    BG_SET='48' # Must be proceeded by rgb values
    BG_DEFAULT='49'
    BG_ORANGE=BG_SET+';5;202'
    BG_PURPLE=BG_SET+';5;129'

class AnsiString:
    '''
    Represents an ANSI colorized/formatted string. All or part of the string may contain style and
    color formatting which may be used to print out to an ANSI-supported terminal such as those
    on Linux, Mac, and Windows 10+.

    Example 1:
    s = AnsiString('This string is red and bold string', [AnsiFormat.BOLD, AnsiFormat.FG_RED])
    print(s)

    Example 2:
    s = AnsiString('This string contains custom formatting', '38;2;175;95;95')
    print(s)

    Example 3:
    s = AnsiString('This string contains multiple color settings across different ranges')
    s.apply_formatting(AnsiFormat.BOLD, 5, 6)
    s.apply_formatting(AnsiFormat.BG_BLUE, 21, 8)
    s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 14)
    print(s)

    Example 4:
    s = AnsiString('This string will be formatted bold and red')
    print('{:01;31}'.format(s))

    Example 5:
    s = AnsiString('This string will be formatted bold and red')
    # Use any name within AnsiFormat (can be lower or upper case representation of the name)
    print('{:bold;fg_red}'.format(s))

    Example 6:
    s = AnsiString('This string will be formatted bold and red')
    # The character '[' tells the format method to do no parsing/checking and use verbatim as codes
    print('{:[01;31}'.format(s))
    '''

    # The escape sequence that needs to be formatted with command str
    ANSI_ESCAPE_FORMAT = '\x1b[{}m'
    # The escape sequence which will clear all previous formatting (empty command is same as 0)
    ANSI_ESCAPE_CLEAR = ANSI_ESCAPE_FORMAT.format('')

    # Number of elements in each value of _color_settings dict
    SETTINGS_ITEM_LIST_LEN = 2
    # Index of _color_settings value list which contains settings to apply
    SETTINGS_APPLY_IDX = 0
    # Index of _color_settings value list which contains settings to remove
    SETTINGS_REMOVE_IDX = 1

    class Settings:
        '''
        Internal use only - mainly used to create a unique objects which may contain same strings
        '''
        def __init__(self, setting_or_settings:Union[List[str], str, List[AnsiFormat], AnsiFormat]):
            if not isinstance(setting_or_settings, list):
                settings = [setting_or_settings]
            else:
                settings = setting_or_settings

            for i, item in enumerate(settings):
                if isinstance(item, str):
                    # Use string verbatim
                    pass
                elif hasattr(item, 'value') and isinstance(item.value, str):
                    # Likely an enumeration - use the value
                    settings[i] = item.value
                else:
                    raise TypeError('Unsupported type for setting_or_settings: {}'.format(type(setting_or_settings)))

            self._str = ';'.join(settings)

        def __str__(self):
            return self._str

    def __init__(self, s:str='', setting_or_settings:Union[List[str], str, List[AnsiFormat], AnsiFormat]=None):
        self._s = s
        # Key is the string index to make a color change at
        # Each value element is a list of 2 lists
        #   index 0: the settings to apply at this string index
        #   index 1: the settings to remove at this string index
        self._color_settings = {}
        if setting_or_settings:
            self.apply_formatting(setting_or_settings)

    def assign_str(self, s):
        '''
        Assigns the base string.
        '''
        self._s = s

    @property
    def base_str(self) -> str:
        '''
        Returns the base string without any formatting set.
        '''
        return self._s

    @staticmethod
    def _insert_settings_to_dict(settings_dict:dict, idx:int, apply:bool, settings:Settings, topmost:bool=True):
        if idx not in settings_dict:
            settings_dict[idx] = [[] for _ in range(__class__.SETTINGS_ITEM_LIST_LEN)]
        list_idx = __class__.SETTINGS_APPLY_IDX if apply else __class__.SETTINGS_REMOVE_IDX
        if topmost:
            settings_dict[idx][list_idx].append(settings)
        else:
            settings_dict[idx][list_idx].insert(0, settings)

    def _insert_settings(self, idx:int, apply:bool, settings:Settings, topmost:bool=True):
        __class__._insert_settings_to_dict(self._color_settings, idx, apply, settings, topmost)

    def apply_formatting(
            self,
            setting_or_settings:Union[List[str], str, List[AnsiFormat], AnsiFormat],
            start_idx=0,
            length=None,
            topmost=True
    ):
        '''
        Sets the formatting for a given range of characters.
        Inputs: setting_or_settings - Can either be a single item or list of items;
                                      each item can either be a string or AnsiFormat type
                start_idx - The string start index where setting(s) are to be applied
                length - Number of characters to apply settings or None to apply until end of string
                topmost - When true, this setting is placed at the end of the set for the given
                        start_index meaning it is applied last; when false, setting is applied first

        Note: The desired effect may not be achieved if the same setting is applied over an
              overlapping range of characters.
        '''
        if not setting_or_settings:
            # Ignore - nothing to apply
            return
        elif length is not None and length <= 0:
            # Ignore - nothing to apply
            return

        settings = __class__.Settings(setting_or_settings)

        # Apply settings
        self._insert_settings(start_idx, True, settings, topmost)

        if length is not None:
            # Remove settings
            self._insert_settings(start_idx + length, False, settings, topmost)

    def apply_formatting_for_match(
            self,
            setting_or_settings:Union[List[str], str, List[AnsiFormat], AnsiFormat],
            match_object,
            group:int=0
    ):
        '''
        Apply formatting using a match object generated from re
        '''
        s = match_object.start(group)
        e = match_object.end(group)
        self.apply_formatting(setting_or_settings, s, e - s)

    def clear_formatting(self):
        '''
        Clears all internal formatting.
        '''
        self._color_settings = {}

    class SettingsIterator:
        def __init__(self, settings_dict:dict):
            self.settings_dict = settings_dict
            self.current_settings = []
            self.dict_iter = iter(sorted(self.settings_dict))

        def __iter__(self):
            return self

        def __next__(self) -> tuple:
            # Will raise StopIteration when complete
            idx = next(self.dict_iter)
            settings = self.settings_dict[idx]
            # Remove settings that it is time to remove
            for setting in settings[AnsiString.SETTINGS_REMOVE_IDX]:
                # setting object will only be matched and removed if it is the same reference to one
                # previously added - will raise exception otherwise which should not happen if the
                # settings dictionary and this method were setup correctly.
                self.current_settings.remove(setting)
            # Apply settings that it is time to add
            self.current_settings += settings[AnsiString.SETTINGS_APPLY_IDX]
            return (idx, settings, self.current_settings)

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

    def __getitem__(self, val:Union[int, slice]):
        ''' Returns a AnsiString object which represents a substring of self '''
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

        if st == 0 and en == len(self._s):
            # No need to make substring
            return self

        new_s = AnsiString(self._s[val])
        last_settings = []
        settings_initialized = False
        for idx, settings, current_settings in __class__.SettingsIterator(self._color_settings):
            if idx >= len(self._s) or idx >= en:
                # Complete
                break
            if idx == st:
                new_s._color_settings[0] = [list(current_settings), []]
                settings_initialized = True
            elif idx > st:
                if not settings_initialized:
                    new_s._color_settings[0] = [last_settings, []]
                    settings_initialized = True
                new_s._color_settings[idx - st] = [list(settings[0]), list(settings[1])]
            last_settings = list(current_settings)
        return new_s

    def __str__(self) -> str:
        '''
        Returns an ANSI format string with only internal formatting set.
        '''
        return self.__format__(None)

    def __format__(self, __format_spec:str) -> str:
        '''
        Returns an ANSI format string with both internal and given formatting spec set.
        '''
        if not __format_spec and not self._color_settings:
            # No formatting
            return self._s

        out_str = ''
        last_idx = 0

        settings_dict = self._color_settings
        if __format_spec:
            # Make a local copy and add this temporary format spec
            settings_dict = dict(self._color_settings)

            if __format_spec.startswith("["):
                # Use the rest of the string as-is for settings
                format_settings = __class__.Settings(__format_spec[1:])
            else:
                # The format string contains names within AnsiFormat or integers, separated by semicolon
                formats = __format_spec.split(';')
                format_settings_strs = []
                for format in formats:
                    try:
                        ansi_format = AnsiFormat[format.upper()]
                    except KeyError:
                        try:
                            _ = int(format)
                        except ValueError:
                            raise ValueError(
                                'AnsiString.__format__ failed to parse format ({}); invalid name: {}'
                                .format(__format_spec, format)
                            )
                        else:
                            # Value is an integer - use the format verbatim
                            format_settings_strs.append(format)
                    else:
                        format_settings_strs.append(ansi_format.value)
                format_settings = __class__.Settings(';'.join(format_settings_strs))

            __class__._insert_settings_to_dict(settings_dict, 0, True, format_settings, True)

        clear_needed = False
        for idx, settings, current_settings in __class__.SettingsIterator(settings_dict):
            if idx >= len(self._s):
                # Invalid
                break
            # Catch up output to current index
            out_str += self._s[last_idx:idx]
            last_idx = idx

            settings_to_apply = [str(s) for s in current_settings]
            if settings[__class__.SETTINGS_REMOVE_IDX] and settings_to_apply:
                # Settings were removed and there are settings to be applied -
                # need to reset before applying current settings
                settings_to_apply = [AnsiFormat.RESET.value] + settings_to_apply
            # Apply these settings
            out_str += __class__.ANSI_ESCAPE_FORMAT.format(';'.join(settings_to_apply))
            # Save this flag in case this is the last loop
            clear_needed = bool(current_settings)

        # Final catch up
        out_str += self._s[last_idx:]
        if clear_needed:
            # Clear settings
            out_str += __class__.ANSI_ESCAPE_CLEAR

        return out_str
