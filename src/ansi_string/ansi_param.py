from enum import Enum, IntEnum, auto as enum_auto
from typing import Dict, Tuple

class AnsiParamEffect(Enum):
    '''
    Contains the different effect groups.
    Only 1 of each group may be set at a time except for RESET which is stateless (resets state of all others).
    '''
    RESET=enum_auto()
    BOLDNESS=enum_auto()
    ITALICS=enum_auto()
    UNDERLINE=enum_auto()
    OVERLINE=enum_auto()
    BLINKING=enum_auto()
    SWAP_BG_FG=enum_auto()
    VISIBILITY=enum_auto()
    CROSSED_OUT=enum_auto()
    FONT_TYPE=enum_auto()
    SPACING=enum_auto()
    BOXING=enum_auto()
    FG_COLOR=enum_auto()
    FG_COLOUR=FG_COLOR
    BG_COLOR=enum_auto()
    BG_COLOUR=BG_COLOR
    UL_COLOR=enum_auto()
    UL_COLOUR=UL_COLOR

class AnsiParamEffectFn(Enum):
    RESET_ALL=enum_auto()
    APPLY_SETTING=enum_auto()
    CLEAR_SETTING=enum_auto()

# The dictionary lookup from code to effect type
# (Separate dict is used so that the key of AnsiParam is not affected)
_ANSI_CODE_TO_EFFECT:Dict[int, Tuple[AnsiParamEffect, bool]] = {
    0: (AnsiParamEffect.RESET, AnsiParamEffectFn.RESET_ALL),
    1: (AnsiParamEffect.BOLDNESS, AnsiParamEffectFn.APPLY_SETTING),
    2: (AnsiParamEffect.BOLDNESS, AnsiParamEffectFn.APPLY_SETTING),
    3: (AnsiParamEffect.ITALICS, AnsiParamEffectFn.APPLY_SETTING),
    4: (AnsiParamEffect.UNDERLINE, AnsiParamEffectFn.APPLY_SETTING),
    5: (AnsiParamEffect.BLINKING, AnsiParamEffectFn.APPLY_SETTING),
    6: (AnsiParamEffect.BLINKING, AnsiParamEffectFn.APPLY_SETTING),
    7: (AnsiParamEffect.SWAP_BG_FG, AnsiParamEffectFn.APPLY_SETTING),
    8: (AnsiParamEffect.VISIBILITY, AnsiParamEffectFn.APPLY_SETTING),
    9: (AnsiParamEffect.CROSSED_OUT, AnsiParamEffectFn.APPLY_SETTING),
    10: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    11: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    12: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    13: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    14: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    15: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    16: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    17: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    18: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    19: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    20: (AnsiParamEffect.FONT_TYPE, AnsiParamEffectFn.APPLY_SETTING),
    21: (AnsiParamEffect.UNDERLINE, AnsiParamEffectFn.APPLY_SETTING),
    22: (AnsiParamEffect.BOLDNESS, AnsiParamEffectFn.CLEAR_SETTING),
    23: (AnsiParamEffect.ITALICS, AnsiParamEffectFn.CLEAR_SETTING),
    24: (AnsiParamEffect.UNDERLINE, AnsiParamEffectFn.CLEAR_SETTING),
    25: (AnsiParamEffect.BLINKING, AnsiParamEffectFn.CLEAR_SETTING),
    26: (AnsiParamEffect.SPACING, AnsiParamEffectFn.APPLY_SETTING),
    27: (AnsiParamEffect.SWAP_BG_FG, AnsiParamEffectFn.CLEAR_SETTING),
    28: (AnsiParamEffect.VISIBILITY, AnsiParamEffectFn.CLEAR_SETTING),
    29: (AnsiParamEffect.CROSSED_OUT, AnsiParamEffectFn.CLEAR_SETTING),

    30: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    31: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    32: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    33: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    34: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    35: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    36: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    37: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    38: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    39: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.CLEAR_SETTING),

    40: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    41: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    42: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    43: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    44: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    45: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    46: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    47: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    48: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    49: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.CLEAR_SETTING),

    50: (AnsiParamEffect.SPACING, AnsiParamEffectFn.CLEAR_SETTING),
    51: (AnsiParamEffect.BOXING, AnsiParamEffectFn.APPLY_SETTING),
    52: (AnsiParamEffect.BOXING, AnsiParamEffectFn.APPLY_SETTING),
    53: (AnsiParamEffect.OVERLINE, AnsiParamEffectFn.APPLY_SETTING),
    54: (AnsiParamEffect.BOXING, AnsiParamEffectFn.CLEAR_SETTING),
    55: (AnsiParamEffect.OVERLINE, AnsiParamEffectFn.CLEAR_SETTING),
    58: (AnsiParamEffect.UL_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    59: (AnsiParamEffect.UL_COLOR, AnsiParamEffectFn.CLEAR_SETTING),

    90: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    91: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    92: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    93: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    94: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    95: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    96: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    97: (AnsiParamEffect.FG_COLOR, AnsiParamEffectFn.APPLY_SETTING),

    100: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    101: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    102: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    103: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    104: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    105: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    106: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING),
    107: (AnsiParamEffect.BG_COLOR, AnsiParamEffectFn.APPLY_SETTING)
}

class AnsiParam(IntEnum):
    '''
    Contains raw ANSI control parameters
    '''

    RESET=0
    BOLD=1
    FAINT=2
    ITALIC=3
    UNDERLINE=4
    SLOW_BLINK=5
    RAPID_BLINK=6
    SWAP_BG_FG=7
    HIDE=8
    CROSSED_OUT=9
    DEFAULT_FONT=10
    ALT_FONT_1=11
    ALT_FONT_2=12
    ALT_FONT_3=13
    ALT_FONT_4=14
    ALT_FONT_5=15
    ALT_FONT_6=16
    ALT_FONT_7=17
    ALT_FONT_8=18
    ALT_FONT_9=19
    GOTHIC_FONT=20
    DOUBLE_UNDERLINE=21
    NO_BOLD_FAINT=22
    NO_ITALIC=23
    NO_UNDERLINE=24
    NO_BLINK=25
    PROPORTIONAL_SPACING=26
    NO_SWAP_BG_FG=27
    NO_HIDE=28
    NO_CROSSED_OUT=29

    FG_BLACK=30
    FG_RED=31
    FG_GREEN=32
    FG_YELLOW=33
    FG_BLUE=34
    FG_MAGENTA=35
    FG_CYAN=36
    FG_WHITE=37
    FG_SET=38
    FG_DEFAULT=39

    BG_BLACK=40
    BG_RED=41
    BG_GREEN=42
    BG_YELLOW=43
    BG_BLUE=44
    BG_MAGENTA=45
    BG_CYAN=46
    BG_WHITE=47
    BG_SET=48
    BG_DEFAULT=49

    NO_PROPORTIONAL_SPACING=50
    FRAMED=51
    ENCIRCLED=52
    OVERLINED=53
    NO_FRAMED_ENCIRCLED=54
    NO_OVERLINED=55
    SET_UNDERLINE_COLOR=58
    SET_UNDERLINE_COLOUR=SET_UNDERLINE_COLOR # Alias for my British English friends
    DEFAULT_UNDERLINE_COLOR=59
    DEFAULT_UNDERLINE_COLOUR=DEFAULT_UNDERLINE_COLOR # Alias for my British English friends

    FG_BRIGHT_BLACK=90
    FG_BRIGHT_RED=91
    FG_BRIGHT_GREEN=92
    FG_BRIGHT_YELLOW=93
    FG_BRIGHT_BLUE=94
    FG_BRIGHT_MAGENTA=95
    FG_BRIGHT_CYAN=96
    FG_BRIGHT_WHITE=97

    BG_BRIGHT_BLACK=100
    BG_BRIGHT_RED=101
    BG_BRIGHT_GREEN=102
    BG_BRIGHT_YELLOW=103
    BG_BRIGHT_BLUE=104
    BG_BRIGHT_MAGENTA=105
    BG_BRIGHT_CYAN=106
    BG_BRIGHT_WHITE=107

    def __init__(self, code):
        self.code:int = code
        effect_settings = _ANSI_CODE_TO_EFFECT[code]
        self.effect_type:AnsiParamEffect = effect_settings[0]
        self.effect_fn:AnsiParamEffectFn = effect_settings[1]

# This dictionary has no use after AnsiParam is fully defined
# Lookup can be achieved through AnsiParam(<int>).effect_type
del _ANSI_CODE_TO_EFFECT

# Links an effect type with the parameter that will clear that effect
EFFECT_CLEAR_DICT:Dict[AnsiParamEffect, AnsiParam] = {
    AnsiParamEffect.RESET: AnsiParam.RESET,
    AnsiParamEffect.BOLDNESS: AnsiParam.NO_BOLD_FAINT,
    AnsiParamEffect.ITALICS: AnsiParam.NO_ITALIC,
    AnsiParamEffect.UNDERLINE: AnsiParam.NO_UNDERLINE,
    AnsiParamEffect.OVERLINE: AnsiParam.NO_OVERLINED,
    AnsiParamEffect.BLINKING: AnsiParam.NO_BLINK,
    AnsiParamEffect.SWAP_BG_FG: AnsiParam.NO_SWAP_BG_FG,
    AnsiParamEffect.VISIBILITY: AnsiParam.NO_HIDE,
    AnsiParamEffect.CROSSED_OUT: AnsiParam.NO_CROSSED_OUT,
    AnsiParamEffect.FONT_TYPE: AnsiParam.DEFAULT_FONT,
    AnsiParamEffect.SPACING: AnsiParam.NO_PROPORTIONAL_SPACING,
    AnsiParamEffect.BOXING: AnsiParam.NO_FRAMED_ENCIRCLED,
    AnsiParamEffect.FG_COLOR: AnsiParam.FG_DEFAULT,
    AnsiParamEffect.BG_COLOR: AnsiParam.BG_DEFAULT,
    AnsiParamEffect.UL_COLOR: AnsiParam.DEFAULT_UNDERLINE_COLOR
}
