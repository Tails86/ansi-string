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
import re
import copy
import math
from enum import Enum, EnumMeta, auto as enum_auto
import io
from typing import Any, Union, List

__version__ = '0.1.0'
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

class ColorComponentType(Enum):
    UNDERLINE=enum_auto(),
    FOREGROUND=enum_auto(),
    BACKGROUND=enum_auto()

ColourComponentType = ColorComponentType  # Alias for my British English friends

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
    SET_UNDERLINE_COLOR='58'
    SET_UNDERLINE_COLOUR=SET_UNDERLINE_COLOR # Alias for my British English friends
    SET_UNDERLINE_COLOR_256=f'{SET_UNDERLINE_COLOR};5'
    SET_UNDERLINE_COLOUR_256=SET_UNDERLINE_COLOR_256 # Alias for my British English friends
    SET_UNDERLINE_COLOR_24_BIT=f'{SET_UNDERLINE_COLOR};2'
    SET_UNDERLINE_COLOUR_24_BIT=SET_UNDERLINE_COLOR_24_BIT # Alias for my British English friends
    SET_UNDERLINE_COLOR_RGB=SET_UNDERLINE_COLOR_24_BIT
    SET_UNDERLINE_COLOUR_RGB=SET_UNDERLINE_COLOR_RGB # Alias for my British English friends

    DEFAULT_UNDERLINE_COLOR='59'
    DEFAULT_UNDERLINE_COLOUR=DEFAULT_UNDERLINE_COLOR # Alias for my British English friends

    FG_BLACK='30'
    FG_RED='31'
    FG_GREEN='32'
    FG_YELLOW='33'
    FG_BLUE='34'
    FG_MAGENTA='35'
    FG_CYAN='36'
    FG_WHITE='37'
    FG_SET_256='38;5' # Must be proceeded by ;value [0,255] corresponding to color
    FG_SET_24_BIT='38;2' # Must be proceeded by ;R;G;B values [0,255]
    FG_SET_RGB=FG_SET_24_BIT # Alias
    FG_DEFAULT='39'

    # Alias FG_XXX to XXX
    BLACK=FG_BLACK
    RED=FG_RED
    GREEN=FG_GREEN
    YELLOW=FG_YELLOW
    BLUE=FG_BLUE
    MAGENTA=FG_MAGENTA
    CYAN=FG_CYAN
    WHITE=FG_WHITE

    BG_BLACK='40'
    BG_RED='41'
    BG_GREEN='42'
    BG_YELLOW='43'
    BG_BLUE='44'
    BG_MAGENTA='45'
    BG_CYAN='46'
    BG_WHITE='47'
    BG_SET_256='48;5' # Must be proceeded by ;value [0,255] corresponding to color
    BG_SET_24_BIT='48;2' # Must be proceeded by ;R;G;B values [0,255]
    BG_SET_RGB=BG_SET_24_BIT # Alias
    BG_DEFAULT='49'

    # Extended color set (names match html names)
    FG_INDIAN_RED=f'{FG_SET_RGB};205;92;92'
    FG_LIGHT_CORAL=f'{FG_SET_RGB};240;128;128'
    FG_SALMON=f'{FG_SET_RGB};250;128;114'
    FG_DARK_SALMON=f'{FG_SET_RGB};233;150;122'
    FG_LIGHT_SALMON=f'{FG_SET_RGB};255;160;122'
    FG_CRIMSON=f'{FG_SET_RGB};220;20;60'
    FG_FIRE_BRICK=f'{FG_SET_RGB};178;34;34'
    FG_DARK_RED=f'{FG_SET_RGB};139;0;0'
    FG_PINK=f'{FG_SET_RGB};255;192;203'
    FG_LIGHT_PINK=f'{FG_SET_RGB};255;182;193'
    FG_HOT_PINK=f'{FG_SET_RGB};255;105;180'
    FG_DEEP_PINK=f'{FG_SET_RGB};255;20;147'
    FG_MEDIUM_VIOLET_RED=f'{FG_SET_RGB};199;21;133'
    FG_PALE_VIOLET_RED=f'{FG_SET_RGB};219;112;147'
    FG_ORANGE=f'{FG_SET_256};214'
    FG_CORAL=f'{FG_SET_RGB};255;127;80'
    FG_TOMATO=f'{FG_SET_RGB};255;99;71'
    FG_ORANGE_RED=f'{FG_SET_256};202'
    FG_DARK_ORANGE=f'{FG_SET_RGB};255;140;0'
    FG_GOLD=f'{FG_SET_RGB};255;215;0'
    FG_LIGHT_YELLOW=f'{FG_SET_RGB};255;255;224'
    FG_LEMON_CHIFFON=f'{FG_SET_RGB};255;250;205'
    FG_LIGHT_GOLDENROD_YELLOW=f'{FG_SET_RGB};250;250;210'
    FG_PAPAYA_WHIP=f'{FG_SET_RGB};255;239;213'
    FG_MOCCASIN=f'{FG_SET_RGB};255;228;181'
    FG_PEACH_PUFF=f'{FG_SET_RGB};255;218;185'
    FG_PALE_GOLDENROD=f'{FG_SET_RGB};238;232;170'
    FG_KHAKI=f'{FG_SET_RGB};240;230;140'
    FG_DARK_KHAKI=f'{FG_SET_RGB};189;183;107'
    FG_PURPLE=f'{FG_SET_256};90'
    FG_LAVENDER=f'{FG_SET_RGB};230;230;250'
    FG_THISTLE=f'{FG_SET_RGB};216;191;216'
    FG_PLUM=f'{FG_SET_RGB};221;160;221'
    FG_VIOLET=f'{FG_SET_RGB};238;130;238'
    FG_ORCHID=f'{FG_SET_RGB};218;112;214'
    FG_FUCHSIA=f'{FG_SET_RGB};255;0;255'
    FG_MEDIUM_ORCHID=f'{FG_SET_RGB};186;85;211'
    FG_MEDIUM_PURPLE=f'{FG_SET_RGB};147;112;219'
    FG_REBECCA_PURPLE=f'{FG_SET_RGB};102;51;153'
    FG_BLUE_VIOLET=f'{FG_SET_RGB};138;43;226'
    FG_DARK_VIOLET=f'{FG_SET_RGB};148;0;211'
    FG_DARK_ORCHID=f'{FG_SET_RGB};153;50;204'
    FG_DARK_MAGENTA=f'{FG_SET_RGB};139;0;139'
    FG_INDIGO=f'{FG_SET_RGB};75;0;130'
    FG_SLATE_BLUE=f'{FG_SET_RGB};106;90;205'
    FG_DARK_SLATE_BLUE=f'{FG_SET_RGB};72;61;139'
    FG_MEDIUM_SLATE_BLUE=f'{FG_SET_RGB};123;104;238'
    FG_GREEN_YELLOW=f'{FG_SET_RGB};173;255;47'
    FG_CHARTREUSE=f'{FG_SET_RGB};127;255;0'
    FG_LAWN_GREEN=f'{FG_SET_RGB};124;252;0'
    FG_LIME=f'{FG_SET_RGB};0;255;0'
    FG_LIME_GREEN=f'{FG_SET_RGB};50;205;50'
    FG_PALE_GREEN=f'{FG_SET_RGB};152;251;152'
    FG_LIGHT_GREEN=f'{FG_SET_RGB};144;238;144'
    FG_MEDIUM_SPRING_GREEN=f'{FG_SET_RGB};0;250;154'
    FG_SPRING_GREEN=f'{FG_SET_RGB};0;255;127'
    FG_MEDIUM_SEA_GREEN=f'{FG_SET_RGB};60;179;113'
    FG_SEA_GREEN=f'{FG_SET_RGB};46;139;87'
    FG_FOREST_GREEN=f'{FG_SET_RGB};34;139;34'
    FG_DARK_GREEN=f'{FG_SET_RGB};0;100;0'
    FG_YELLOW_GREEN=f'{FG_SET_RGB};154;205;50'
    FG_OLIVE_DRAB=f'{FG_SET_RGB};107;142;35'
    FG_OLIVE=f'{FG_SET_RGB};128;128;0'
    FG_DARK_OLIVE_GREEN=f'{FG_SET_RGB};85;107;47'
    FG_MEDIUM_AQUAMARINE=f'{FG_SET_RGB};102;205;170'
    FG_DARK_SEA_GREEN=f'{FG_SET_RGB};143;188;139'
    FG_LIGHT_SEA_GREEN=f'{FG_SET_RGB};32;178;170'
    FG_DARK_CYAN=f'{FG_SET_RGB};0;139;139'
    FG_TEAL=f'{FG_SET_RGB};0;128;128'
    FG_AQUA=f'{FG_SET_RGB};0;255;255'
    FG_LIGHT_CYAN=f'{FG_SET_RGB};224;255;255'
    FG_PALE_TURQUOISE=f'{FG_SET_RGB};175;238;238'
    FG_AQUAMARINE=f'{FG_SET_RGB};127;255;212'
    FG_TURQUOISE=f'{FG_SET_RGB};64;224;208'
    FG_MEDIUM_TURQUOISE=f'{FG_SET_RGB};72;209;204'
    FG_DARK_TURQUOISE=f'{FG_SET_RGB};0;206;209'
    FG_CADET_BLUE=f'{FG_SET_RGB};95;158;160'
    FG_STEEL_BLUE=f'{FG_SET_RGB};70;130;180'
    FG_LIGHT_STEEL_BLUE=f'{FG_SET_RGB};176;196;222'
    FG_POWDER_BLUE=f'{FG_SET_RGB};176;224;230'
    FG_LIGHT_BLUE=f'{FG_SET_RGB};173;216;230'
    FG_SKY_BLUE=f'{FG_SET_RGB};135;206;235'
    FG_LIGHT_SKY_BLUE=f'{FG_SET_RGB};135;206;250'
    FG_DEEP_SKY_BLUE=f'{FG_SET_RGB};0;191;255'
    FG_DODGER_BLUE=f'{FG_SET_RGB};30;144;255'
    FG_CORNFLOWER_BLUE=f'{FG_SET_RGB};100;149;237'
    FG_ROYAL_BLUE=f'{FG_SET_RGB};65;105;225'
    FG_MEDIUM_BLUE=f'{FG_SET_RGB};0;0;205'
    FG_DARK_BLUE=f'{FG_SET_RGB};0;0;139'
    FG_NAVY=f'{FG_SET_RGB};0;0;128'
    FG_MIDNIGHT_BLUE=f'{FG_SET_RGB};25;25;112'
    FG_CORNSILK=f'{FG_SET_RGB};255;248;220'
    FG_BLANCHED_ALMOND=f'{FG_SET_RGB};255;235;205'
    FG_BISQUE=f'{FG_SET_RGB};255;228;196'
    FG_NAVAJO_WHITE=f'{FG_SET_RGB};255;222;173'
    FG_WHEAT=f'{FG_SET_RGB};245;222;179'
    FG_BURLY_WOOD=f'{FG_SET_RGB};222;184;135'
    FG_TAN=f'{FG_SET_RGB};210;180;140'
    FG_ROSY_BROWN=f'{FG_SET_RGB};188;143;143'
    FG_SANDY_BROWN=f'{FG_SET_RGB};244;164;96'
    FG_GOLDENROD=f'{FG_SET_RGB};218;165;32'
    FG_DARK_GOLDENROD=f'{FG_SET_RGB};184;134;11'
    FG_PERU=f'{FG_SET_RGB};205;133;63'
    FG_CHOCOLATE=f'{FG_SET_RGB};210;105;30'
    FG_SADDLE_BROWN=f'{FG_SET_RGB};139;69;19'
    FG_SIENNA=f'{FG_SET_RGB};160;82;45'
    FG_BROWN=f'{FG_SET_RGB};165;42;42'
    FG_MAROON=f'{FG_SET_RGB};128;0;0'
    FG_SNOW=f'{FG_SET_RGB};255;250;250'
    FG_HONEY_DEW=f'{FG_SET_RGB};240;255;240'
    FG_MINT_CREAM=f'{FG_SET_RGB};245;255;250'
    FG_AZURE=f'{FG_SET_RGB};240;255;255'
    FG_ALICE_BLUE=f'{FG_SET_RGB};240;248;255'
    FG_GHOST_WHITE=f'{FG_SET_RGB};248;248;255'
    FG_WHITE_SMOKE=f'{FG_SET_RGB};245;245;245'
    FG_SEA_SHELL=f'{FG_SET_RGB};255;245;238'
    FG_BEIGE=f'{FG_SET_RGB};245;245;220'
    FG_OLD_LACE=f'{FG_SET_RGB};253;245;230'
    FG_FLORAL_WHITE=f'{FG_SET_RGB};255;250;240'
    FG_IVORY=f'{FG_SET_RGB};255;255;240'
    FG_ANTIQUE_WHITE=f'{FG_SET_RGB};250;235;215'
    FG_LINEN=f'{FG_SET_RGB};250;240;230'
    FG_LAVENDER_BLUSH=f'{FG_SET_RGB};255;240;245'
    FG_MISTY_ROSE=f'{FG_SET_RGB};255;228;225'
    FG_GAINSBORO=f'{FG_SET_RGB};220;220;220'
    FG_LIGHT_GRAY=f'{FG_SET_RGB};211;211;211'
    FG_LIGHT_GREY=FG_LIGHT_GRAY # Alias for my British English friends
    FG_SILVER=f'{FG_SET_RGB};192;192;192'
    FG_DARK_GRAY=f'{FG_SET_RGB};169;169;169'
    FG_DARK_GREY=FG_DARK_GRAY # Alias for my British English friends
    FG_GRAY=f'{FG_SET_256};244'
    FG_GREY=FG_GRAY # Alias for my British English friends
    FG_DIM_GRAY=f'{FG_SET_RGB};105;105;105'
    FG_LIGHT_SLATE_GRAY=f'{FG_SET_RGB};119;136;153'
    FG_SLATE_GRAY=f'{FG_SET_RGB};112;128;144'
    FG_DARK_SLATE_GRAY=f'{FG_SET_RGB};47;79;79'

    # Alias FG_XXX to XXX
    INDIAN_RED=FG_INDIAN_RED
    LIGHT_CORAL=FG_LIGHT_CORAL
    SALMON=FG_SALMON
    DARK_SALMON=FG_DARK_SALMON
    LIGHT_SALMON=FG_LIGHT_SALMON
    CRIMSON=FG_CRIMSON
    FIRE_BRICK=FG_FIRE_BRICK
    DARK_RED=FG_DARK_RED
    PINK=FG_PINK
    LIGHT_PINK=FG_LIGHT_PINK
    HOT_PINK=FG_HOT_PINK
    DEEP_PINK=FG_DEEP_PINK
    MEDIUM_VIOLET_RED=FG_MEDIUM_VIOLET_RED
    PALE_VIOLET_RED=FG_PALE_VIOLET_RED
    ORANGE=FG_ORANGE
    CORAL=FG_CORAL
    TOMATO=FG_TOMATO
    ORANGE_RED=FG_ORANGE_RED
    DARK_ORANGE=FG_DARK_ORANGE
    GOLD=FG_GOLD
    LIGHT_YELLOW=FG_LIGHT_YELLOW
    LEMON_CHIFFON=FG_LEMON_CHIFFON
    LIGHT_GOLDENROD_YELLOW=FG_LIGHT_GOLDENROD_YELLOW
    PAPAYA_WHIP=FG_PAPAYA_WHIP
    MOCCASIN=FG_MOCCASIN
    PEACH_PUFF=FG_PEACH_PUFF
    PALE_GOLDENROD=FG_PALE_GOLDENROD
    KHAKI=FG_KHAKI
    DARK_KHAKI=FG_DARK_KHAKI
    PURPLE=FG_PURPLE
    LAVENDER=FG_LAVENDER
    THISTLE=FG_THISTLE
    PLUM=FG_PLUM
    VIOLET=FG_VIOLET
    ORCHID=FG_ORCHID
    FUCHSIA=FG_FUCHSIA
    MEDIUM_ORCHID=FG_MEDIUM_ORCHID
    MEDIUM_PURPLE=FG_MEDIUM_PURPLE
    REBECCA_PURPLE=FG_REBECCA_PURPLE
    BLUE_VIOLET=FG_BLUE_VIOLET
    DARK_VIOLET=FG_DARK_VIOLET
    DARK_ORCHID=FG_DARK_ORCHID
    DARK_MAGENTA=FG_DARK_MAGENTA
    INDIGO=FG_INDIGO
    SLATE_BLUE=FG_SLATE_BLUE
    DARK_SLATE_BLUE=FG_DARK_SLATE_BLUE
    MEDIUM_SLATE_BLUE=FG_MEDIUM_SLATE_BLUE
    GREEN_YELLOW=FG_GREEN_YELLOW
    CHARTREUSE=FG_CHARTREUSE
    LAWN_GREEN=FG_LAWN_GREEN
    LIME=FG_LIME
    LIME_GREEN=FG_LIME_GREEN
    PALE_GREEN=FG_PALE_GREEN
    LIGHT_GREEN=FG_LIGHT_GREEN
    MEDIUM_SPRING_GREEN=FG_MEDIUM_SPRING_GREEN
    SPRING_GREEN=FG_SPRING_GREEN
    MEDIUM_SEA_GREEN=FG_MEDIUM_SEA_GREEN
    SEA_GREEN=FG_SEA_GREEN
    FOREST_GREEN=FG_FOREST_GREEN
    DARK_GREEN=FG_DARK_GREEN
    YELLOW_GREEN=FG_YELLOW_GREEN
    OLIVE_DRAB=FG_OLIVE_DRAB
    OLIVE=FG_OLIVE
    DARK_OLIVE_GREEN=FG_DARK_OLIVE_GREEN
    MEDIUM_AQUAMARINE=FG_MEDIUM_AQUAMARINE
    DARK_SEA_GREEN=FG_DARK_SEA_GREEN
    LIGHT_SEA_GREEN=FG_LIGHT_SEA_GREEN
    DARK_CYAN=FG_DARK_CYAN
    TEAL=FG_TEAL
    AQUA=FG_AQUA
    LIGHT_CYAN=FG_LIGHT_CYAN
    PALE_TURQUOISE=FG_PALE_TURQUOISE
    AQUAMARINE=FG_AQUAMARINE
    TURQUOISE=FG_TURQUOISE
    MEDIUM_TURQUOISE=FG_MEDIUM_TURQUOISE
    DARK_TURQUOISE=FG_DARK_TURQUOISE
    CADET_BLUE=FG_CADET_BLUE
    STEEL_BLUE=FG_STEEL_BLUE
    LIGHT_STEEL_BLUE=FG_LIGHT_STEEL_BLUE
    POWDER_BLUE=FG_POWDER_BLUE
    LIGHT_BLUE=FG_LIGHT_BLUE
    SKY_BLUE=FG_SKY_BLUE
    LIGHT_SKY_BLUE=FG_LIGHT_SKY_BLUE
    DEEP_SKY_BLUE=FG_DEEP_SKY_BLUE
    DODGER_BLUE=FG_DODGER_BLUE
    CORNFLOWER_BLUE=FG_CORNFLOWER_BLUE
    ROYAL_BLUE=FG_ROYAL_BLUE
    MEDIUM_BLUE=FG_MEDIUM_BLUE
    DARK_BLUE=FG_DARK_BLUE
    NAVY=FG_NAVY
    MIDNIGHT_BLUE=FG_MIDNIGHT_BLUE
    CORNSILK=FG_CORNSILK
    BLANCHED_ALMOND=FG_BLANCHED_ALMOND
    BISQUE=FG_BISQUE
    NAVAJO_WHITE=FG_NAVAJO_WHITE
    WHEAT=FG_WHEAT
    BURLY_WOOD=FG_BURLY_WOOD
    TAN=FG_TAN
    ROSY_BROWN=FG_ROSY_BROWN
    SANDY_BROWN=FG_SANDY_BROWN
    GOLDENROD=FG_GOLDENROD
    DARK_GOLDENROD=FG_DARK_GOLDENROD
    PERU=FG_PERU
    CHOCOLATE=FG_CHOCOLATE
    SADDLE_BROWN=FG_SADDLE_BROWN
    SIENNA=FG_SIENNA
    BROWN=FG_BROWN
    MAROON=FG_MAROON
    SNOW=FG_SNOW
    HONEY_DEW=FG_HONEY_DEW
    MINT_CREAM=FG_MINT_CREAM
    AZURE=FG_AZURE
    ALICE_BLUE=FG_ALICE_BLUE
    GHOST_WHITE=FG_GHOST_WHITE
    WHITE_SMOKE=FG_WHITE_SMOKE
    SEA_SHELL=FG_SEA_SHELL
    BEIGE=FG_BEIGE
    OLD_LACE=FG_OLD_LACE
    FLORAL_WHITE=FG_FLORAL_WHITE
    IVORY=FG_IVORY
    ANTIQUE_WHITE=FG_ANTIQUE_WHITE
    LINEN=FG_LINEN
    LAVENDER_BLUSH=FG_LAVENDER_BLUSH
    MISTY_ROSE=FG_MISTY_ROSE
    GAINSBORO=FG_GAINSBORO
    LIGHT_GRAY=FG_LIGHT_GRAY
    LIGHT_GREY=FG_LIGHT_GREY
    SILVER=FG_SILVER
    DARK_GRAY=FG_DARK_GRAY
    DARK_GREY=FG_DARK_GREY
    GRAY=FG_GRAY
    GREY=FG_GREY
    DIM_GRAY=FG_DIM_GRAY
    LIGHT_SLATE_GRAY=FG_LIGHT_SLATE_GRAY
    SLATE_GRAY=FG_SLATE_GRAY
    DARK_SLATE_GRAY=FG_DARK_SLATE_GRAY

    # Extended background color set (names match html names)
    BG_INDIAN_RED=f'{BG_SET_RGB};205;92;92'
    BG_LIGHT_CORAL=f'{BG_SET_RGB};240;128;128'
    BG_SALMON=f'{BG_SET_RGB};250;128;114'
    BG_DARK_SALMON=f'{BG_SET_RGB};233;150;122'
    BG_LIGHT_SALMON=f'{BG_SET_RGB};255;160;122'
    BG_CRIMSON=f'{BG_SET_RGB};220;20;60'
    BG_FIRE_BRICK=f'{BG_SET_RGB};178;34;34'
    BG_DARK_RED=f'{BG_SET_RGB};139;0;0'
    BG_PINK=f'{BG_SET_RGB};255;192;203'
    BG_LIGHT_PINK=f'{BG_SET_RGB};255;182;193'
    BG_HOT_PINK=f'{BG_SET_RGB};255;105;180'
    BG_DEEP_PINK=f'{BG_SET_RGB};255;20;147'
    BG_MEDIUM_VIOLET_RED=f'{BG_SET_RGB};199;21;133'
    BG_PALE_VIOLET_RED=f'{BG_SET_RGB};219;112;147'
    BG_ORANGE=f'{BG_SET_256};214'
    BG_CORAL=f'{BG_SET_RGB};255;127;80'
    BG_TOMATO=f'{BG_SET_RGB};255;99;71'
    BG_ORANGE_RED=f'{BG_SET_256};202'
    BG_DARK_ORANGE=f'{BG_SET_RGB};255;140;0'
    BG_GOLD=f'{BG_SET_RGB};255;215;0'
    BG_LIGHT_YELLOW=f'{BG_SET_RGB};255;255;224'
    BG_LEMON_CHIFFON=f'{BG_SET_RGB};255;250;205'
    BG_LIGHT_GOLDENROD_YELLOW=f'{BG_SET_RGB};250;250;210'
    BG_PAPAYA_WHIP=f'{BG_SET_RGB};255;239;213'
    BG_MOCCASIN=f'{BG_SET_RGB};255;228;181'
    BG_PEACH_PUFF=f'{BG_SET_RGB};255;218;185'
    BG_PALE_GOLDENROD=f'{BG_SET_RGB};238;232;170'
    BG_KHAKI=f'{BG_SET_RGB};240;230;140'
    BG_DARK_KHAKI=f'{BG_SET_RGB};189;183;107'
    BG_PURPLE=f'{BG_SET_256};90'
    BG_LAVENDER=f'{BG_SET_RGB};230;230;250'
    BG_THISTLE=f'{BG_SET_RGB};216;191;216'
    BG_PLUM=f'{BG_SET_RGB};221;160;221'
    BG_VIOLET=f'{BG_SET_RGB};238;130;238'
    BG_ORCHID=f'{BG_SET_RGB};218;112;214'
    BG_FUCHSIA=f'{BG_SET_RGB};255;0;255'
    BG_MEDIUM_ORCHID=f'{BG_SET_RGB};186;85;211'
    BG_MEDIUM_PURPLE=f'{BG_SET_RGB};147;112;219'
    BG_REBECCA_PURPLE=f'{BG_SET_RGB};102;51;153'
    BG_BLUE_VIOLET=f'{BG_SET_RGB};138;43;226'
    BG_DARK_VIOLET=f'{BG_SET_RGB};148;0;211'
    BG_DARK_ORCHID=f'{BG_SET_RGB};153;50;204'
    BG_DARK_MAGENTA=f'{BG_SET_RGB};139;0;139'
    BG_INDIGO=f'{BG_SET_RGB};75;0;130'
    BG_SLATE_BLUE=f'{BG_SET_RGB};106;90;205'
    BG_DARK_SLATE_BLUE=f'{BG_SET_RGB};72;61;139'
    BG_MEDIUM_SLATE_BLUE=f'{BG_SET_RGB};123;104;238'
    BG_GREEN_YELLOW=f'{BG_SET_RGB};173;255;47'
    BG_CHARTREUSE=f'{BG_SET_RGB};127;255;0'
    BG_LAWN_GREEN=f'{BG_SET_RGB};124;252;0'
    BG_LIME=f'{BG_SET_RGB};0;255;0'
    BG_LIME_GREEN=f'{BG_SET_RGB};50;205;50'
    BG_PALE_GREEN=f'{BG_SET_RGB};152;251;152'
    BG_LIGHT_GREEN=f'{BG_SET_RGB};144;238;144'
    BG_MEDIUM_SPRING_GREEN=f'{BG_SET_RGB};0;250;154'
    BG_SPRING_GREEN=f'{BG_SET_RGB};0;255;127'
    BG_MEDIUM_SEA_GREEN=f'{BG_SET_RGB};60;179;113'
    BG_SEA_GREEN=f'{BG_SET_RGB};46;139;87'
    BG_FOREST_GREEN=f'{BG_SET_RGB};34;139;34'
    BG_DARK_GREEN=f'{BG_SET_RGB};0;100;0'
    BG_YELLOW_GREEN=f'{BG_SET_RGB};154;205;50'
    BG_OLIVE_DRAB=f'{BG_SET_RGB};107;142;35'
    BG_OLIVE=f'{BG_SET_RGB};128;128;0'
    BG_DARK_OLIVE_GREEN=f'{BG_SET_RGB};85;107;47'
    BG_MEDIUM_AQUAMARINE=f'{BG_SET_RGB};102;205;170'
    BG_DARK_SEA_GREEN=f'{BG_SET_RGB};143;188;139'
    BG_LIGHT_SEA_GREEN=f'{BG_SET_RGB};32;178;170'
    BG_DARK_CYAN=f'{BG_SET_RGB};0;139;139'
    BG_TEAL=f'{BG_SET_RGB};0;128;128'
    BG_AQUA=f'{BG_SET_RGB};0;255;255'
    BG_LIGHT_CYAN=f'{BG_SET_RGB};224;255;255'
    BG_PALE_TURQUOISE=f'{BG_SET_RGB};175;238;238'
    BG_AQUAMARINE=f'{BG_SET_RGB};127;255;212'
    BG_TURQUOISE=f'{BG_SET_RGB};64;224;208'
    BG_MEDIUM_TURQUOISE=f'{BG_SET_RGB};72;209;204'
    BG_DARK_TURQUOISE=f'{BG_SET_RGB};0;206;209'
    BG_CADET_BLUE=f'{BG_SET_RGB};95;158;160'
    BG_STEEL_BLUE=f'{BG_SET_RGB};70;130;180'
    BG_LIGHT_STEEL_BLUE=f'{BG_SET_RGB};176;196;222'
    BG_POWDER_BLUE=f'{BG_SET_RGB};176;224;230'
    BG_LIGHT_BLUE=f'{BG_SET_RGB};173;216;230'
    BG_SKY_BLUE=f'{BG_SET_RGB};135;206;235'
    BG_LIGHT_SKY_BLUE=f'{BG_SET_RGB};135;206;250'
    BG_DEEP_SKY_BLUE=f'{BG_SET_RGB};0;191;255'
    BG_DODGER_BLUE=f'{BG_SET_RGB};30;144;255'
    BG_CORNFLOWER_BLUE=f'{BG_SET_RGB};100;149;237'
    BG_ROYAL_BLUE=f'{BG_SET_RGB};65;105;225'
    BG_MEDIUM_BLUE=f'{BG_SET_RGB};0;0;205'
    BG_DARK_BLUE=f'{BG_SET_RGB};0;0;139'
    BG_NAVY=f'{BG_SET_RGB};0;0;128'
    BG_MIDNIGHT_BLUE=f'{BG_SET_RGB};25;25;112'
    BG_CORNSILK=f'{BG_SET_RGB};255;248;220'
    BG_BLANCHED_ALMOND=f'{BG_SET_RGB};255;235;205'
    BG_BISQUE=f'{BG_SET_RGB};255;228;196'
    BG_NAVAJO_WHITE=f'{BG_SET_RGB};255;222;173'
    BG_WHEAT=f'{BG_SET_RGB};245;222;179'
    BG_BURLY_WOOD=f'{BG_SET_RGB};222;184;135'
    BG_TAN=f'{BG_SET_RGB};210;180;140'
    BG_ROSY_BROWN=f'{BG_SET_RGB};188;143;143'
    BG_SANDY_BROWN=f'{BG_SET_RGB};244;164;96'
    BG_GOLDENROD=f'{BG_SET_RGB};218;165;32'
    BG_DARK_GOLDENROD=f'{BG_SET_RGB};184;134;11'
    BG_PERU=f'{BG_SET_RGB};205;133;63'
    BG_CHOCOLATE=f'{BG_SET_RGB};210;105;30'
    BG_SADDLE_BROWN=f'{BG_SET_RGB};139;69;19'
    BG_SIENNA=f'{BG_SET_RGB};160;82;45'
    BG_BROWN=f'{BG_SET_RGB};165;42;42'
    BG_MAROON=f'{BG_SET_RGB};128;0;0'
    BG_SNOW=f'{BG_SET_RGB};255;250;250'
    BG_HONEY_DEW=f'{BG_SET_RGB};240;255;240'
    BG_MINT_CREAM=f'{BG_SET_RGB};245;255;250'
    BG_AZURE=f'{BG_SET_RGB};240;255;255'
    BG_ALICE_BLUE=f'{BG_SET_RGB};240;248;255'
    BG_GHOST_WHITE=f'{BG_SET_RGB};248;248;255'
    BG_WHITE_SMOKE=f'{BG_SET_RGB};245;245;245'
    BG_SEA_SHELL=f'{BG_SET_RGB};255;245;238'
    BG_BEIGE=f'{BG_SET_RGB};245;245;220'
    BG_OLD_LACE=f'{BG_SET_RGB};253;245;230'
    BG_FLORAL_WHITE=f'{BG_SET_RGB};255;250;240'
    BG_IVORY=f'{BG_SET_RGB};255;255;240'
    BG_ANTIQUE_WHITE=f'{BG_SET_RGB};250;235;215'
    BG_LINEN=f'{BG_SET_RGB};250;240;230'
    BG_LAVENDER_BLUSH=f'{BG_SET_RGB};255;240;245'
    BG_MISTY_ROSE=f'{BG_SET_RGB};255;228;225'
    BG_GAINSBORO=f'{BG_SET_RGB};220;220;220'
    BG_LIGHT_GRAY=f'{BG_SET_RGB};211;211;211'
    BG_LIGHT_GREY=BG_LIGHT_GRAY # Alias for my British English friends
    BG_SILVER=f'{BG_SET_RGB};192;192;192'
    BG_DARK_GRAY=f'{BG_SET_RGB};169;169;169'
    BG_DARK_GREY=BG_DARK_GRAY # Alias for my British English friends
    BG_GRAY=f'{BG_SET_256};244'
    BG_GREY=BG_GRAY # Alias for my British English friends
    BG_DIM_GRAY=f'{BG_SET_RGB};105;105;105'
    BG_LIGHT_SLATE_GRAY=f'{BG_SET_RGB};119;136;153'
    BG_SLATE_GRAY=f'{BG_SET_RGB};112;128;144'
    BG_DARK_SLATE_GRAY=f'{BG_SET_RGB};47;79;79'

    # Enable underline and set to color
    UL_BLACK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};0'
    UL_RED=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};9'
    UL_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};10'
    UL_YELLOW=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};11'
    UL_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};12'
    UL_MAGENTA=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};13'
    UL_CYAN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};14'
    UL_WHITE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};15'
    UL_INDIAN_RED=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};205;92;92'
    UL_LIGHT_CORAL=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};240;128;128'
    UL_SALMON=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};250;128;114'
    UL_DARK_SALMON=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};233;150;122'
    UL_LIGHT_SALMON=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;160;122'
    UL_CRIMSON=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};220;20;60'
    UL_FIRE_BRICK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};178;34;34'
    UL_DARK_RED=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};139;0;0'
    UL_PINK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;192;203'
    UL_LIGHT_PINK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;182;193'
    UL_HOT_PINK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;105;180'
    UL_DEEP_PINK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;20;147'
    UL_MEDIUM_VIOLET_RED=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};199;21;133'
    UL_PALE_VIOLET_RED=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};219;112;147'
    UL_ORANGE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};214'
    UL_CORAL=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;127;80'
    UL_TOMATO=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;99;71'
    UL_ORANGE_RED=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};202'
    UL_DARK_ORANGE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;140;0'
    UL_GOLD=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;215;0'
    UL_LIGHT_YELLOW=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;255;224'
    UL_LEMON_CHIFFON=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;250;205'
    UL_LIGHT_GOLDENROD_YELLOW=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};250;250;210'
    UL_PAPAYA_WHIP=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;239;213'
    UL_MOCCASIN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;228;181'
    UL_PEACH_PUFF=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;218;185'
    UL_PALE_GOLDENROD=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};238;232;170'
    UL_KHAKI=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};240;230;140'
    UL_DARK_KHAKI=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};189;183;107'
    UL_PURPLE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};90'
    UL_LAVENDER=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};230;230;250'
    UL_THISTLE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};216;191;216'
    UL_PLUM=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};221;160;221'
    UL_VIOLET=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};238;130;238'
    UL_ORCHID=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};218;112;214'
    UL_FUCHSIA=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;0;255'
    UL_MEDIUM_ORCHID=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};186;85;211'
    UL_MEDIUM_PURPLE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};147;112;219'
    UL_REBECCA_PURPLE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};102;51;153'
    UL_BLUE_VIOLET=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};138;43;226'
    UL_DARK_VIOLET=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};148;0;211'
    UL_DARK_ORCHID=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};153;50;204'
    UL_DARK_MAGENTA=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};139;0;139'
    UL_INDIGO=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};75;0;130'
    UL_SLATE_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};106;90;205'
    UL_DARK_SLATE_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};72;61;139'
    UL_MEDIUM_SLATE_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};123;104;238'
    UL_GREEN_YELLOW=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};173;255;47'
    UL_CHARTREUSE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};127;255;0'
    UL_LAWN_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};124;252;0'
    UL_LIME=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;255;0'
    UL_LIME_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};50;205;50'
    UL_PALE_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};152;251;152'
    UL_LIGHT_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};144;238;144'
    UL_MEDIUM_SPRING_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;250;154'
    UL_SPRING_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;255;127'
    UL_MEDIUM_SEA_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};60;179;113'
    UL_SEA_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};46;139;87'
    UL_FOREST_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};34;139;34'
    UL_DARK_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;100;0'
    UL_YELLOW_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};154;205;50'
    UL_OLIVE_DRAB=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};107;142;35'
    UL_OLIVE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};128;128;0'
    UL_DARK_OLIVE_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};85;107;47'
    UL_MEDIUM_AQUAMARINE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};102;205;170'
    UL_DARK_SEA_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};143;188;139'
    UL_LIGHT_SEA_GREEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};32;178;170'
    UL_DARK_CYAN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;139;139'
    UL_TEAL=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;128;128'
    UL_AQUA=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;255;255'
    UL_LIGHT_CYAN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};224;255;255'
    UL_PALE_TURQUOISE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};175;238;238'
    UL_AQUAMARINE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};127;255;212'
    UL_TURQUOISE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};64;224;208'
    UL_MEDIUM_TURQUOISE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};72;209;204'
    UL_DARK_TURQUOISE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;206;209'
    UL_CADET_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};95;158;160'
    UL_STEEL_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};70;130;180'
    UL_LIGHT_STEEL_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};176;196;222'
    UL_POWDER_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};176;224;230'
    UL_LIGHT_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};173;216;230'
    UL_SKY_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};135;206;235'
    UL_LIGHT_SKY_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};135;206;250'
    UL_DEEP_SKY_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;191;255'
    UL_DODGER_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};30;144;255'
    UL_CORNFLOWER_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};100;149;237'
    UL_ROYAL_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};65;105;225'
    UL_MEDIUM_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;0;205'
    UL_DARK_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;0;139'
    UL_NAVY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};0;0;128'
    UL_MIDNIGHT_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};25;25;112'
    UL_CORNSILK=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;248;220'
    UL_BLANCHED_ALMOND=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;235;205'
    UL_BISQUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;228;196'
    UL_NAVAJO_WHITE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;222;173'
    UL_WHEAT=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};245;222;179'
    UL_BURLY_WOOD=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};222;184;135'
    UL_TAN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};210;180;140'
    UL_ROSY_BROWN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};188;143;143'
    UL_SANDY_BROWN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};244;164;96'
    UL_GOLDENROD=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};218;165;32'
    UL_DARK_GOLDENROD=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};184;134;11'
    UL_PERU=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};205;133;63'
    UL_CHOCOLATE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};210;105;30'
    UL_SADDLE_BROWN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};139;69;19'
    UL_SIENNA=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};160;82;45'
    UL_BROWN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};165;42;42'
    UL_MAROON=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};128;0;0'
    UL_SNOW=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;250;250'
    UL_HONEY_DEW=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};240;255;240'
    UL_MINT_CREAM=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};245;255;250'
    UL_AZURE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};240;255;255'
    UL_ALICE_BLUE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};240;248;255'
    UL_GHOST_WHITE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};248;248;255'
    UL_WHITE_SMOKE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};245;245;245'
    UL_SEA_SHELL=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;245;238'
    UL_BEIGE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};245;245;220'
    UL_OLD_LACE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};253;245;230'
    UL_FLORAL_WHITE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;250;240'
    UL_IVORY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;255;240'
    UL_ANTIQUE_WHITE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};250;235;215'
    UL_LINEN=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};250;240;230'
    UL_LAVENDER_BLUSH=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;240;245'
    UL_MISTY_ROSE=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};255;228;225'
    UL_GAINSBORO=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};220;220;220'
    UL_LIGHT_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};211;211;211'
    UL_LIGHT_GREY=UL_LIGHT_GRAY # Alias for my British English friends
    UL_SILVER=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};192;192;192'
    UL_DARK_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};169;169;169'
    UL_DARK_GREY=UL_DARK_GRAY # Alias for my British English friends
    UL_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_256};244'
    UL_GREY=UL_GRAY # Alias for my British English friends
    UL_DIM_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};105;105;105'
    UL_LIGHT_SLATE_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};119;136;153'
    UL_SLATE_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};112;128;144'
    UL_DARK_SLATE_GRAY=f'{UNDERLINE};{SET_UNDERLINE_COLOR_RGB};47;79;79'

    @staticmethod
    def rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None, component:ColorComponentType=ColorComponentType.FOREGROUND):
        '''
        Generates a FG or BG ANSI sequence for the given RGB values.
        r_or_rgb: Either an 8-bit red component or the full 24-bit RGB value
        g: An 8-bit green component (b must also be specified when set)
        b: An 8-bit blue component (g must also be specified when set)
        component: The component to set color of (background, foreground, or underline)
        '''
        if r_or_rgb is None:
            raise ValueError('r_or_rgb must not be None')
        elif g is None or b is None:
            if g != b:
                raise ValueError('g and b must either both be an integer or both be None')
            r = (r_or_rgb & 0xFF0000) >> 16
            g = (r_or_rgb & 0x00FF00) >> 8
            b = (r_or_rgb & 0x0000FF)
        else:
            r=min(255, max(0, r_or_rgb))
            g=min(255, max(0, g))
            b=min(255, max(0, b))

        if component == ColorComponentType.UNDERLINE:
            return f'{__class__.UNDERLINE.value};{__class__.SET_UNDERLINE_COLOR_RGB.value};{r};{g};{b}'
        elif component == ColorComponentType.BACKGROUND:
            return f'{__class__.BG_SET_RGB.value};{r};{g};{b}'
        else:
            return f'{__class__.FG_SET_RGB.value};{r};{g};{b}'

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
    print('{::01;31}'.format(s))

    Example 5:
    s = AnsiString('This string will be formatted bold and red')
    # Use any name within AnsiFormat (can be lower or upper case representation of the name)
    print('{::bold;fg_red}'.format(s))

    Example 6:
    s = AnsiString('This string will be formatted bold and red')
    # The character '[' tells the format method to do no parsing/checking and use verbatim as codes
    print('{::[01;31}'.format(s))
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

    @staticmethod
    def _shift_settings_idx(settings_dict:dict, num:int, keep_origin:bool):
        for key in sorted(settings_dict.keys(), reverse=(num > 0)):
            if not keep_origin or key != 0:
                new_key = max(key + num, 0)
                settings_dict[new_key] = settings_dict.pop(key)

    def _insert_settings(self, idx:int, apply:bool, settings:Settings, topmost:bool=True):
        __class__._insert_settings_to_dict(self._color_settings, idx, apply, settings, topmost)

    def apply_formatting(
            self,
            setting_or_settings:Union[List[str], str, List[AnsiFormat], AnsiFormat],
            start_idx_or_slice:Union[int, slice]=0,
            length=None,
            topmost=True
    ):
        '''
        Sets the formatting for a given range of characters.
        Inputs: setting_or_settings - Can either be a single item or list of items;
                                      each item can either be a string or AnsiFormat type
                start_idx_or_slice - If int, the string start index where setting(s) are to be applied
                                     If slice, the slice specifying where to apply settings (length must not be set)
                length - Number of characters to apply settings or None to apply until end of string
                topmost - When true, this setting is placed at the end of the set for the given
                        start_index meaning it is applied last; when false, setting is applied first

        Note: The desired effect may not be achieved if the same setting is applied over an
              overlapping range of characters.
        '''
        if not setting_or_settings:
            # Ignore - nothing to apply
            return

        settings = __class__.Settings(setting_or_settings)

        if isinstance(start_idx_or_slice, slice):
            if length is not None:
                raise ValueError('length cannot be set when start_idx_or_slice is a slice')
            elif start_idx_or_slice.step is not None and start_idx_or_slice.step != 1:
                raise ValueError('Step other than 1 not supported')

            if start_idx_or_slice.start is None:
                start_idx = 0
            else:
                start_idx = start_idx_or_slice.start

            if start_idx_or_slice.stop is not None:
                length = start_idx_or_slice.stop - start_idx
        else:
            start_idx = start_idx_or_slice

        if length is not None and length <= 0:
            # Ignore - nothing to apply
            return

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

    @staticmethod
    def _re_search(expr:Union[str, "re.Pattern[str]"], string:str, result:List["re.Match[str]"]) -> Union["re.Match[str]", None]:
        '''
        Helper method so I can assign and check in the same "if" statement
        '''
        match = re.search(expr, string)
        if match:
            result.append(match)
        return match

    @staticmethod
    def _parse_rgb_string(s:str):
        component_dict = {
            'ul_': ColorComponentType.UNDERLINE,
            'bg_': ColorComponentType.BACKGROUND,
            'fg_': ColorComponentType.FOREGROUND
        }

        # rgb(), fg_rgb(), bg_rgb(), or ul_rgb() with 3 distinct values as decimal or hex
        match = re.search(r'^((?:fg_)?|(?:bg_)|(?:ul_))rgb\(\s*(0x)?([0-9a-fA-F]+)\s*,\s*(0x)?([0-9a-fA-F]+)\s*,\s*(0x)?([0-9a-fA-F]+)\s*\)$', s)
        if match:
            try:
                r = int(match.group(3), 16 if match.group(2) else 10)
                g = int(match.group(5), 16 if match.group(4) else 10)
                b = int(match.group(7), 16 if match.group(6) else 10)
            except ValueError:
                raise ValueError('Invalid rgb value(s)')
            return AnsiFormat.rgb(r, g, b, component_dict.get(match.group(1), ColorComponentType.FOREGROUND))

        # rgb(), fg_rgb(), bg_rgb(), or ul_rgb() with 1 value as decimal or hex
        match = re.search(r'^((?:fg_)?|(?:bg_)|(?:ul_))rgb\(\s*(0x)?([0-9a-fA-F]+)\s*\)$', s)
        if match:
            try:
                rgb = int(match.group(3), 16 if match.group(2) else 10)
            except ValueError:
                raise ValueError('Invalid rgb value')
            return AnsiFormat.rgb(rgb, component=component_dict.get(match.group(1), ColorComponentType.FOREGROUND))
        return None

    def __format__(self, __format_spec:str) -> str:
        '''
        Returns an ANSI format string with both internal and given formatting spec set.
        __format_spec: must be in the format "[string_format][:ansi_format]" where string_format is the standard
                       string format specifier and ansi_format contains 0 or more ansi directives separated by
                       semicolons (;)
                       ex: ">10:bold;fg_red" to make output right justify with width of 10, bold and red formatting
        '''
        if not __format_spec and not self._color_settings:
            # No formatting
            return self._s

        out_str = ''
        last_idx = 0
        string_format = None
        ansi_format = None
        normal_format_str = self._s

        if __format_spec:
            format_parts = __format_spec.split(':', 1)
            string_format = format_parts[0]
            if len(format_parts) > 1:
                ansi_format = format_parts[1]

        if string_format or ansi_format:
            # Make a copy
            settings_dict = copy.deepcopy(self._color_settings)
        else:
            settings_dict = self._color_settings

        if string_format:
            # Normal string formatting
            result = []
            if (
                __class__._re_search(r'^(.?)<([0-9]*)$', string_format, result)
                or __class__._re_search(r'^()([0-9]*)$', string_format, result)
            ):
                # Left justify
                custom_char = result[0].group(1) or ' '
                num = result[0].group(2)
                if num:
                    num_int = int(num) - len(normal_format_str)
                    if num_int > 0:
                        normal_format_str += custom_char * num_int
            elif __class__._re_search(r'^(.?)>([0-9]*)$', string_format, result):
                # Right justify
                custom_char = result[0].group(1) or ' '
                num = result[0].group(2)
                if num:
                    num_int = int(num) - len(normal_format_str)
                    if num_int > 0:
                        normal_format_str = custom_char * num_int + normal_format_str
                        # Shift all indices except for the origin
                        __class__._shift_settings_idx(settings_dict, num_int, True)
            elif __class__._re_search(r'^(.?)\^([0-9]*)$', string_format, result):
                # Center
                custom_char = result[0].group(1) or ' '
                num = result[0].group(2)
                if num:
                    num_int = int(num) - len(normal_format_str)
                    if num_int > 0:
                        left_spaces = math.floor((num_int) / 2)
                        right_spaces = num_int - left_spaces
                        normal_format_str = custom_char * left_spaces + normal_format_str + custom_char * right_spaces
                        # Shift all indices except for the origin
                        __class__._shift_settings_idx(settings_dict, left_spaces, True)
            elif __class__._re_search(r'^[<>\^]?[+-]?[0-9]*$', string_format, result):
                raise ValueError('Sign not allowed in string format specifier')
            elif __class__._re_search(r'^[<>\^]?[ ]?[0-9]*$', string_format, result):
                raise ValueError('Space not allowed in string format specifier')
            else:
                raise ValueError('Invalid format specifier')

        if ansi_format:
            if ansi_format.startswith("["):
                # Use the rest of the string as-is for settings
                format_settings = __class__.Settings(ansi_format[1:])
            else:
                # The format string contains names within AnsiFormat or integers, separated by semicolon
                formats = ansi_format.split(';')
                format_settings_strs = []
                for format in formats:
                    ansi_fmt_enum = None
                    try:
                        ansi_fmt_enum = AnsiFormat[format.upper()]
                    except KeyError:
                        pass
                    else:
                        format_settings_strs.append(ansi_fmt_enum.value)

                    if ansi_fmt_enum is None:
                        rgb_format = __class__._parse_rgb_string(format)
                        if not rgb_format:
                            try:
                                _ = int(format)
                            except ValueError:
                                raise ValueError(
                                    'AnsiString.__format__ failed to parse format ({}); invalid name: {}'
                                    .format(ansi_format, format)
                                )
                            else:
                                # Value is an integer - use the format verbatim
                                format_settings_strs.append(format)
                        else:
                            format_settings_strs.append(rgb_format)
                format_settings = __class__.Settings(';'.join(format_settings_strs))

            __class__._insert_settings_to_dict(settings_dict, 0, True, format_settings, True)

        clear_needed = False
        for idx, settings, current_settings in __class__.SettingsIterator(settings_dict):
            if idx >= len(normal_format_str):
                # Invalid
                break
            # Catch up output to current index
            out_str += normal_format_str[last_idx:idx]
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
        out_str += normal_format_str[last_idx:]
        if clear_needed:
            # Clear settings
            out_str += __class__.ANSI_ESCAPE_CLEAR

        return out_str
