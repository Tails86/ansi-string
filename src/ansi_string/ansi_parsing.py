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

# This file contains types and functions which help parse an existing ANSI-formatted string

from typing import Any, Union, List, Dict, Tuple
from .ansi_format import (
    ansi_sep, ansi_graphic_rendition_code_end, ansi_graphic_rendition_code_terminator, ansi_control_sequence_introducer,
    ansi_term_ord_range, AnsiSetting, _AnsiControlFn
)
from .ansi_param import AnsiParam, AnsiParamEffect, AnsiParamEffectFn

class AnsiControlSequence:
    '''
    Contains a control sequence definition.
    '''
    def __init__(self, sequence:str, terminator:str):
        self.sequence = sequence
        self.terminator = terminator

    def is_terminator_valid(self) -> bool:
        return (
            len(self.terminator) == 1 and
            ord(self.terminator) >= ansi_term_ord_range[0] and
            ord(self.terminator) <= ansi_term_ord_range[1]
        )

    def is_graphic(self) -> bool:
        return self.terminator == ansi_graphic_rendition_code_terminator

class ParsedAnsiControlSequenceString:
    '''
    Contains a string parsed as an ANSI control sequence string.
    '''
    def __init__(self, s:str, allow_empty_terminator:str=True, acceptable_terminators:str=None):
        '''
        Initializer
        Parameters:
            s - input string
            allow_empty_terminator - allow a string that is not terminated to be counted as a control sequence
            acceptable_terminators - acceptable string of terminators (default: all acceptable)
        '''
        self._s = ''
        # Dictionary mapping index to a list of applied control sequences for that index
        self.sequences:Dict[int,List[AnsiControlSequence]] = {}
        i = 0
        while i < len(s):
            if s[i:i+len(ansi_control_sequence_introducer)] == ansi_control_sequence_introducer:
                # This is the start of a Control Sequence Introducer command
                i += len(ansi_control_sequence_introducer)
                current_seq = ''
                while i < len(s) and (ord(s[i]) < ansi_term_ord_range[0] or ord(s[i]) > ansi_term_ord_range[1]):
                    current_seq += s[i]
                    i += 1
                terminator = ''
                if i < len(s):
                    terminator = s[i]
                    i += 1
                if (terminator or allow_empty_terminator) and (acceptable_terminators is None or terminator in acceptable_terminators):
                    current_csi = AnsiControlSequence(current_seq, terminator)
                    idx = len(self._s)
                    if idx in self.sequences:
                        self.sequences[idx].append(current_csi)
                    else:
                        self.sequences[idx] = [current_csi]
                else:
                    # Put it all back into string
                    self._s += (ansi_control_sequence_introducer + current_seq + terminator)
            else:
                self._s += s[i]
                i += 1

    def __str__(self) -> str:
        '''
        Returns the formatted string
        '''
        return self.formatted_str()

    def __repr__(self) -> str:
        '''
        Returns the formatted string
        '''
        return self.formatted_str()

    @property
    def formatted_str(self) -> str:
        '''
        Returns the formatted string
        '''
        out_str = ''
        last_terminator = ''
        last_idx = 0
        for key, value_list in self.sequences.items():
            for value in value_list:
                out_str += self._s[last_idx:key] + last_terminator
                out_str += ansi_control_sequence_introducer + value.sequence
                last_terminator = value.terminator
                last_idx = key
        out_str += self._s[last_idx:] + last_terminator
        return out_str

    @property
    def unformatted_str(self) -> str:
        '''
        Returns the unformatted string
        '''
        return self._s

def parse_graphic_sequence(
    sequence:Union[str,List[Union[int,str]]],
    add_erroneous:bool=False
) -> List[AnsiSetting]:
    '''
    Parses an ANSI graphic sequence into a list of AnsiSettings.
    Parameters:
        sequence - the sequence to parse as semicolon-separated string or list of elements
        add_erroneous - Set to True to add items whose function could not be determined
    Returns a list of AnsiSettings. These settings will be guaranteed to be valid and parsable if
    add_erroneous is set to False.
    '''
    if not sequence:
        return [AnsiSetting(AnsiParam.RESET.value)]
    output = []
    if isinstance(sequence, str):
        items = [item.strip() for item in sequence.split(ansi_sep)]
    else:
        items = sequence
    # Attempt to make each value an integer
    for idx, value in enumerate(items):
        try:
            items[idx] = int(value)
        except ValueError:
            pass

    left_in_set = 0
    current_set = []
    for idx, value in enumerate(items):
        if isinstance(value, int):
            if not current_set:
                left_in_set = 1
                # Check all know multi-code functions for expected items in set
                fn_set = False
                fn_found = False
                for fn in _AnsiControlFn:
                    if items[idx : idx+len(fn.setup_seq)] == fn.setup_seq:
                        left_in_set = fn.total_seq_count
                        fn_set = True
                    elif value == fn.setup_seq[0]:
                        fn_found = True
                if fn_found and not fn_set and not add_erroneous:
                    # Skip this value - it's a function code that doesn't supply a valid setup sequence
                    continue
            if value:
                current_set.append(value)
            else:
                current_set.append(items[idx])
            left_in_set -= 1
            if left_in_set <= 0:
                output.append(AnsiSetting(current_set))
                current_set = []
        elif add_erroneous:
            output.append(AnsiSetting(value))
    if current_set and add_erroneous:
        # Dangling set of values
        output.append(AnsiSetting(current_set))
    return output

def settings_to_dict(
    settings:List[AnsiSetting],
    old_settings_dict:Dict[AnsiParamEffect, AnsiSetting] = {}
) -> Dict[AnsiParamEffect, AnsiSetting]:
    '''
    Converts a list of settings into a dictionary which keys off of an effect type.
    Parameters:
        settings - the list of settings to parse
        old_settings_dict - the dictionary to update from
    '''
    settings_dict:Dict[AnsiParamEffect, AnsiSetting] = dict(old_settings_dict)
    for setting in settings:
        initial_param = setting.get_initial_param()
        if initial_param is not None:
            effect = initial_param.effect_type
            effect_fn = initial_param.effect_fn
            if effect_fn == AnsiParamEffectFn.APPLY_SETTING:
                settings_dict[effect] = setting
            elif effect_fn == AnsiParamEffectFn.CLEAR_SETTING:
                if effect in settings_dict:
                    del settings_dict[effect]
            else:
                # AnsiParamEffectFn.RESET_ALL assumed
                settings_dict = {}
    return settings_dict
