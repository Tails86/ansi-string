from enum import Enum, auto as enum_auto
from typing import Any, Union, List, Dict, Tuple
from .ansi_param import AnsiParam, AnsiParamEffect

# The separator string used in an ANSI control sequence
ansi_sep = ';'
# The ansi escape character
ansi_escape = '\x1b'
# The start of an ANSI control sequence
ansi_control_sequence_introducer = ansi_escape + '['
# The last character of the ANSI control sequence
ansi_graphic_rendition_code_end = 'm'
# The escape sequence that needs to be formatted with command str
ansi_graphic_rendition_format = ansi_control_sequence_introducer + '{}' + ansi_graphic_rendition_code_end
# The escape sequence which will clear all previous formatting (empty command is same as 0)
ansi_escape_clear = ansi_graphic_rendition_format.format('')

class AnsiSetting:
    '''
    This class is used to wrap ANSI values which constitute as a single setting. Giving an AnsiSetting to the
    constructor of AnsiString has a similar effect as providing a format string which starts with "[".
    '''
    def __init__(self, setting:Union[str, int, List[int], Tuple[int], 'AnsiSetting'], parsable:bool=True):
        if isinstance(setting, list) or isinstance(setting, tuple):
            setting = ansi_sep.join([str(s) for s in setting])
        elif isinstance(setting, int) or isinstance(setting, AnsiSetting):
            setting = str(setting)
        elif not isinstance(setting, str):
            raise TypeError('Unsupported type for setting: {}'.format(type(setting)))

        if not setting:
            raise ValueError('Setting may not be None or empty string')

        self._str = setting
        self._parsable = parsable

    def __eq__(self, value) -> bool:
        if isinstance(value, str):
            return self._str == value
        elif isinstance(value, AnsiSetting):
            return self._str == value._str
        return False

    def __str__(self) -> str:
        return self._str

    @property
    def parsable(self) -> bool:
        return self._parsable

    def to_list(self) -> List[Union[int, str]]:
        '''
        Returns a list of integers and strings. If a code is not a valid integer, it will be set in the list as string.
        '''
        val_list = []
        for val in self._str.split(ansi_sep):
            val = val.strip()
            try:
                val_int = int(val)
            except ValueError:
                val_list.append(val)
            else:
                val_list.append(val_int)
        return val_list

    def get_initial_param(self) -> AnsiParam:
        '''
        Returns the first parameter of this set which should define its function. This will return None if first value
        in the set is not valid or the set is empty.
        '''
        val = self._str.split(ansi_sep, 1)
        if not val:
            return None

        try:
            return AnsiParam(int(val[0]))
        except ValueError:
            return None

    def to_effect(self) -> AnsiParamEffect:
        '''
        Returns the effect of this setting based on the first code value of the set. This is only guaranteed to be valid
        if self.parsable==True.
        '''
        param = self.get_initial_param()

        if param is None:
            return None

        return param.effect_type


class ColorComponentType(Enum):
    FOREGROUND=enum_auto(),
    BACKGROUND=enum_auto(),
    UNDERLINE=enum_auto(),
    DOUBLE_UNDERLINE=enum_auto()

ColourComponentType = ColorComponentType  # Alias for my British English friends

class _AnsiControlFn(Enum):
    '''
    Special formatting directives for internal use only
    '''
    FG_SET_256=([AnsiParam.FG_SET.value, 5], 1)
    FG_SET_24_BIT=([AnsiParam.FG_SET.value, 2], 3)
    FG_SET_RGB=FG_SET_24_BIT # Alias
    BG_SET_256=([AnsiParam.BG_SET.value, 5], 1)
    BG_SET_24_BIT=([AnsiParam.BG_SET.value, 2], 3)
    BG_SET_RGB=BG_SET_24_BIT # Alias
    SET_UNDERLINE_COLOR_256=([AnsiParam.UNDERLINE.value, AnsiParam.SET_UNDERLINE_COLOR.value, 5], 1)
    SET_UNDERLINE_COLOUR_256=SET_UNDERLINE_COLOR_256 # Alias for my British English friends
    SET_UNDERLINE_COLOR_24_BIT=([AnsiParam.UNDERLINE.value, AnsiParam.SET_UNDERLINE_COLOR.value, 2], 3)
    SET_UNDERLINE_COLOUR_24_BIT=SET_UNDERLINE_COLOR_24_BIT # Alias for my British English friends
    SET_UNDERLINE_COLOR_RGB=SET_UNDERLINE_COLOR_24_BIT # Alias
    SET_UNDERLINE_COLOUR_RGB=SET_UNDERLINE_COLOR_RGB # Alias for my British English friends
    SET_DOUBLE_UNDERLINE_COLOR_256=([AnsiParam.DOUBLE_UNDERLINE.value, AnsiParam.SET_UNDERLINE_COLOR.value, 5], 1)
    SET_DOUBLE_UNDERLINE_COLOUR_256=SET_DOUBLE_UNDERLINE_COLOR_256 # Alias for my British English friends
    SET_DOUBLE_UNDERLINE_COLOR_24_BIT=([AnsiParam.DOUBLE_UNDERLINE.value, AnsiParam.SET_UNDERLINE_COLOR.value, 2], 3)
    SET_DOUBLE_UNDERLINE_COLOUR_24_BIT=SET_DOUBLE_UNDERLINE_COLOR_24_BIT # Alias for my British English friends
    SET_DOUBLE_UNDERLINE_COLOR_RGB=SET_DOUBLE_UNDERLINE_COLOR_24_BIT # Alias
    SET_DOUBLE_UNDERLINE_COLOUR_RGB=SET_DOUBLE_UNDERLINE_COLOR_RGB # Alias for my British English friends

    def __init__(self, setup_seq:List[int], num_args:int):
        '''
        Initializes this enum
        setup_seq - control sequence which addresses the function
        num_args - the number of arguments expected for the function
        '''
        self._setup_seq = setup_seq
        self._num_args = num_args

    def fn(self, *args) -> List[int]:
        if len(args) != self._num_args:
            raise ValueError(f'Invalid number of arguments: {len(args)}; expected: {self._num_args}')
        return self._setup_seq + list(args)

    @staticmethod
    def rgb(
        r_or_rgb:int,
        g:Union[int,None]=None,
        b:Union[int,None]=None,
        component:ColorComponentType=ColorComponentType.FOREGROUND
    ) -> List[int]:
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
            return __class__.SET_UNDERLINE_COLOR_RGB.fn(r, g, b)
        elif component == ColorComponentType.DOUBLE_UNDERLINE:
            return __class__.SET_DOUBLE_UNDERLINE_COLOR_RGB.fn(r, g, b)
        elif component == ColorComponentType.BACKGROUND:
            return __class__.BG_SET_RGB.fn(r, g, b)
        else:
            return __class__.FG_SET_RGB.fn(r, g, b)

    @staticmethod
    def color256(val:int, component:ColorComponentType=ColorComponentType.FOREGROUND) -> List[int]:
        if component == ColorComponentType.UNDERLINE:
            return __class__.SET_UNDERLINE_COLOR_256.fn(val)
        elif component == ColorComponentType.DOUBLE_UNDERLINE:
            return __class__.SET_DOUBLE_UNDERLINE_COLOR_256.fn(val)
        elif component == ColorComponentType.BACKGROUND:
            return __class__.BG_SET_256.fn(val)
        else:
            return __class__.FG_SET_256.fn(val)

    @staticmethod
    def fg_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> List[int]:
        return __class__.rgb(r_or_rgb, g, b)

    @staticmethod
    def bg_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> List[int]:
        return __class__.rgb(r_or_rgb, g, b, ColorComponentType.BACKGROUND)

    @staticmethod
    def ul_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> List[int]:
        return __class__.rgb(r_or_rgb, g, b, ColorComponentType.UNDERLINE)

    @staticmethod
    def dul_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> List[int]:
        return __class__.rgb(r_or_rgb, g, b, ColorComponentType.DOUBLE_UNDERLINE)

    @staticmethod
    def fg_color256(val:int) -> List[int]:
        return __class__.color256(val)

    @staticmethod
    def bg_color256(val:int) -> List[int]:
        return __class__.color256(val, ColorComponentType.BACKGROUND)

    @staticmethod
    def ul_color256(val:int) -> List[int]:
        return __class__.color256(val, ColorComponentType.UNDERLINE)

    @staticmethod
    def dul_color256(val:int) -> List[int]:
        return __class__.color256(val, ColorComponentType.DOUBLE_UNDERLINE)

class AnsiFormat(Enum):
    '''
    Formatting sequences which may be supplied to AnsiString. All values and function results in
    this Enum are fully qualified control sequences which can be passed to AnsiString.
    '''

    BOLD=AnsiParam.BOLD.value
    FAINT=AnsiParam.FAINT.value
    ITALIC=AnsiParam.ITALIC.value
    ITALICS=ITALIC # Alias
    UNDERLINE=AnsiParam.UNDERLINE.value
    SLOW_BLINK=AnsiParam.SLOW_BLINK.value
    RAPID_BLINK=AnsiParam.RAPID_BLINK.value
    SWAP_BG_FG=AnsiParam.SWAP_BG_FG.value
    HIDE=AnsiParam.HIDE.value
    CROSSED_OUT=AnsiParam.CROSSED_OUT.value
    DEFAULT_FONT=AnsiParam.DEFAULT_FONT.value
    ALT_FONT_1=AnsiParam.ALT_FONT_1.value
    ALT_FONT_2=AnsiParam.ALT_FONT_2.value
    ALT_FONT_3=AnsiParam.ALT_FONT_3.value
    ALT_FONT_4=AnsiParam.ALT_FONT_4.value
    ALT_FONT_5=AnsiParam.ALT_FONT_5.value
    ALT_FONT_6=AnsiParam.ALT_FONT_6.value
    ALT_FONT_7=AnsiParam.ALT_FONT_7.value
    ALT_FONT_8=AnsiParam.ALT_FONT_8.value
    ALT_FONT_9=AnsiParam.ALT_FONT_9.value
    GOTHIC_FONT=AnsiParam.GOTHIC_FONT.value
    DOUBLE_UNDERLINE=AnsiParam.DOUBLE_UNDERLINE.value
    NO_BOLD_FAINT=AnsiParam.NO_BOLD_FAINT.value
    NO_ITALIC=AnsiParam.NO_ITALIC.value
    NO_UNDERLINE=AnsiParam.NO_UNDERLINE.value
    NO_BLINK=AnsiParam.NO_BLINK.value
    PROPORTIONAL_SPACING=AnsiParam.PROPORTIONAL_SPACING.value
    NO_SWAP_BG_FG=AnsiParam.NO_SWAP_BG_FG.value
    NO_HIDE=AnsiParam.NO_HIDE.value
    NO_CROSSED_OUT=AnsiParam.NO_CROSSED_OUT.value
    NO_PROPORTIONAL_SPACING=AnsiParam.NO_PROPORTIONAL_SPACING.value
    FRAMED=AnsiParam.FRAMED.value
    ENCIRCLED=AnsiParam.ENCIRCLED.value
    OVERLINED=AnsiParam.OVERLINED.value
    NO_FRAMED_ENCIRCLED=AnsiParam.NO_FRAMED_ENCIRCLED.value
    NO_OVERLINED=AnsiParam.NO_OVERLINED.value
    DEFAULT_UNDERLINE_COLOR=AnsiParam.DEFAULT_UNDERLINE_COLOR.value
    DEFAULT_UNDERLINE_COLOUR=DEFAULT_UNDERLINE_COLOR # Alias for my British English friends

    FG_BLACK=AnsiParam.FG_BLACK.value
    FG_RED=AnsiParam.FG_RED.value
    FG_GREEN=AnsiParam.FG_GREEN.value
    FG_YELLOW=AnsiParam.FG_YELLOW.value
    FG_BLUE=AnsiParam.FG_BLUE.value
    FG_MAGENTA=AnsiParam.FG_MAGENTA.value
    FG_CYAN=AnsiParam.FG_CYAN.value
    FG_WHITE=AnsiParam.FG_WHITE.value
    FG_DEFAULT=AnsiParam.FG_DEFAULT.value

    FG_BRIGHT_BLACK=AnsiParam.FG_BRIGHT_BLACK.value
    FG_BRIGHT_RED=AnsiParam.FG_BRIGHT_RED.value
    FG_BRIGHT_GREEN=AnsiParam.FG_BRIGHT_GREEN.value
    FG_BRIGHT_YELLOW=AnsiParam.FG_BRIGHT_YELLOW.value
    FG_BRIGHT_BLUE=AnsiParam.FG_BRIGHT_BLUE.value
    FG_BRIGHT_MAGENTA=AnsiParam.FG_BRIGHT_MAGENTA.value
    FG_BRIGHT_CYAN=AnsiParam.FG_BRIGHT_CYAN.value
    FG_BRIGHT_WHITE=AnsiParam.FG_BRIGHT_WHITE.value

    # Alias FG_XXX to XXX
    BLACK=FG_BLACK
    RED=FG_RED
    GREEN=FG_GREEN
    YELLOW=FG_YELLOW
    BLUE=FG_BLUE
    MAGENTA=FG_MAGENTA
    CYAN=FG_CYAN
    WHITE=FG_WHITE
    BRIGHT_BLACK=FG_BRIGHT_BLACK
    BRIGHT_RED=FG_BRIGHT_RED
    BRIGHT_GREEN=FG_BRIGHT_GREEN
    BRIGHT_YELLOW=FG_BRIGHT_YELLOW
    BRIGHT_BLUE=FG_BRIGHT_BLUE
    BRIGHT_MAGENTA=FG_BRIGHT_MAGENTA
    BRIGHT_CYAN=FG_BRIGHT_CYAN
    BRIGHT_WHITE=FG_BRIGHT_WHITE

    BG_BLACK=AnsiParam.BG_BLACK.value
    BG_RED=AnsiParam.BG_RED.value
    BG_GREEN=AnsiParam.BG_GREEN.value
    BG_YELLOW=AnsiParam.BG_YELLOW.value
    BG_BLUE=AnsiParam.BG_BLUE.value
    BG_MAGENTA=AnsiParam.BG_MAGENTA.value
    BG_CYAN=AnsiParam.BG_CYAN.value
    BG_WHITE=AnsiParam.BG_WHITE.value
    BG_DEFAULT=AnsiParam.BG_DEFAULT.value

    BG_BRIGHT_BLACK=AnsiParam.BG_BRIGHT_BLACK.value
    BG_BRIGHT_RED=AnsiParam.BG_BRIGHT_RED.value
    BG_BRIGHT_GREEN=AnsiParam.BG_BRIGHT_GREEN.value
    BG_BRIGHT_YELLOW=AnsiParam.BG_BRIGHT_YELLOW.value
    BG_BRIGHT_BLUE=AnsiParam.BG_BRIGHT_BLUE.value
    BG_BRIGHT_MAGENTA=AnsiParam.BG_BRIGHT_MAGENTA.value
    BG_BRIGHT_CYAN=AnsiParam.BG_BRIGHT_CYAN.value
    BG_BRIGHT_WHITE=AnsiParam.BG_BRIGHT_WHITE.value

    # Extended color set (names match html names)
    FG_INDIAN_RED=_AnsiControlFn.fg_rgb(205, 92, 92)
    FG_LIGHT_CORAL=_AnsiControlFn.fg_rgb(240, 128, 128)
    FG_SALMON=_AnsiControlFn.fg_rgb(250, 128, 114)
    FG_DARK_SALMON=_AnsiControlFn.fg_rgb(233, 150, 122)
    FG_LIGHT_SALMON=_AnsiControlFn.fg_rgb(255, 160, 122)
    FG_CRIMSON=_AnsiControlFn.fg_rgb(220, 20, 60)
    FG_FIRE_BRICK=_AnsiControlFn.fg_rgb(178, 34, 34)
    FG_DARK_RED=_AnsiControlFn.fg_rgb(139, 0, 0)
    FG_PINK=_AnsiControlFn.fg_rgb(255, 192, 203)
    FG_LIGHT_PINK=_AnsiControlFn.fg_rgb(255, 182, 193)
    FG_HOT_PINK=_AnsiControlFn.fg_rgb(255, 105, 180)
    FG_DEEP_PINK=_AnsiControlFn.fg_rgb(255, 20, 147)
    FG_MEDIUM_VIOLET_RED=_AnsiControlFn.fg_rgb(199, 21, 133)
    FG_PALE_VIOLET_RED=_AnsiControlFn.fg_rgb(219, 112, 147)
    FG_ORANGE=_AnsiControlFn.fg_color256(214)
    FG_CORAL=_AnsiControlFn.fg_rgb(255, 127, 80)
    FG_TOMATO=_AnsiControlFn.fg_rgb(255, 99, 71)
    FG_ORANGE_RED=_AnsiControlFn.fg_color256(202)
    FG_DARK_ORANGE=_AnsiControlFn.fg_rgb(255, 140, 0)
    FG_GOLD=_AnsiControlFn.fg_rgb(255, 215, 0)
    FG_LIGHT_YELLOW=_AnsiControlFn.fg_rgb(255, 255, 224)
    FG_LEMON_CHIFFON=_AnsiControlFn.fg_rgb(255, 250, 205)
    FG_LIGHT_GOLDENROD_YELLOW=_AnsiControlFn.fg_rgb(250, 250, 210)
    FG_PAPAYA_WHIP=_AnsiControlFn.fg_rgb(255, 239, 213)
    FG_MOCCASIN=_AnsiControlFn.fg_rgb(255, 228, 181)
    FG_PEACH_PUFF=_AnsiControlFn.fg_rgb(255, 218, 185)
    FG_PALE_GOLDENROD=_AnsiControlFn.fg_rgb(238, 232, 170)
    FG_KHAKI=_AnsiControlFn.fg_rgb(240, 230, 140)
    FG_DARK_KHAKI=_AnsiControlFn.fg_rgb(189, 183, 107)
    FG_PURPLE=_AnsiControlFn.fg_color256(90)
    FG_LAVENDER=_AnsiControlFn.fg_rgb(230, 230, 250)
    FG_THISTLE=_AnsiControlFn.fg_rgb(216, 191, 216)
    FG_PLUM=_AnsiControlFn.fg_rgb(221, 160, 221)
    FG_VIOLET=_AnsiControlFn.fg_rgb(238, 130, 238)
    FG_ORCHID=_AnsiControlFn.fg_rgb(218, 112, 214)
    FG_FUCHSIA=_AnsiControlFn.fg_rgb(255, 0, 255)
    FG_MEDIUM_ORCHID=_AnsiControlFn.fg_rgb(186, 85, 211)
    FG_MEDIUM_PURPLE=_AnsiControlFn.fg_rgb(147, 112, 219)
    FG_REBECCA_PURPLE=_AnsiControlFn.fg_rgb(102, 51, 153)
    FG_BLUE_VIOLET=_AnsiControlFn.fg_rgb(138, 43, 226)
    FG_DARK_VIOLET=_AnsiControlFn.fg_rgb(148, 0, 211)
    FG_DARK_ORCHID=_AnsiControlFn.fg_rgb(153, 50, 204)
    FG_DARK_MAGENTA=_AnsiControlFn.fg_rgb(139, 0, 139)
    FG_INDIGO=_AnsiControlFn.fg_rgb(75, 0, 130)
    FG_SLATE_BLUE=_AnsiControlFn.fg_rgb(106, 90, 205)
    FG_DARK_SLATE_BLUE=_AnsiControlFn.fg_rgb(72, 61, 139)
    FG_MEDIUM_SLATE_BLUE=_AnsiControlFn.fg_rgb(123, 104, 238)
    FG_GREEN_YELLOW=_AnsiControlFn.fg_rgb(173, 255, 47)
    FG_CHARTREUSE=_AnsiControlFn.fg_rgb(127, 255, 0)
    FG_LAWN_GREEN=_AnsiControlFn.fg_rgb(124, 252, 0)
    FG_LIME=_AnsiControlFn.fg_rgb(0, 255, 0)
    FG_LIME_GREEN=_AnsiControlFn.fg_rgb(50, 205, 50)
    FG_PALE_GREEN=_AnsiControlFn.fg_rgb(152, 251, 152)
    FG_LIGHT_GREEN=_AnsiControlFn.fg_rgb(144, 238, 144)
    FG_MEDIUM_SPRING_GREEN=_AnsiControlFn.fg_rgb(0, 250, 154)
    FG_SPRING_GREEN=_AnsiControlFn.fg_rgb(0, 255, 127)
    FG_MEDIUM_SEA_GREEN=_AnsiControlFn.fg_rgb(60, 179, 113)
    FG_SEA_GREEN=_AnsiControlFn.fg_rgb(46, 139, 87)
    FG_FOREST_GREEN=_AnsiControlFn.fg_rgb(34, 139, 34)
    FG_DARK_GREEN=_AnsiControlFn.fg_rgb(0, 100, 0)
    FG_YELLOW_GREEN=_AnsiControlFn.fg_rgb(154, 205, 50)
    FG_OLIVE_DRAB=_AnsiControlFn.fg_rgb(107, 142, 35)
    FG_OLIVE=_AnsiControlFn.fg_rgb(128, 128, 0)
    FG_DARK_OLIVE_GREEN=_AnsiControlFn.fg_rgb(85, 107, 47)
    FG_MEDIUM_AQUAMARINE=_AnsiControlFn.fg_rgb(102, 205, 170)
    FG_DARK_SEA_GREEN=_AnsiControlFn.fg_rgb(143, 188, 139)
    FG_LIGHT_SEA_GREEN=_AnsiControlFn.fg_rgb(32, 178, 170)
    FG_DARK_CYAN=_AnsiControlFn.fg_rgb(0, 139, 139)
    FG_TEAL=_AnsiControlFn.fg_rgb(0, 128, 128)
    FG_AQUA=_AnsiControlFn.fg_rgb(0, 255, 255)
    FG_LIGHT_CYAN=_AnsiControlFn.fg_rgb(224, 255, 255)
    FG_PALE_TURQUOISE=_AnsiControlFn.fg_rgb(175, 238, 238)
    FG_AQUAMARINE=_AnsiControlFn.fg_rgb(127, 255, 212)
    FG_TURQUOISE=_AnsiControlFn.fg_rgb(64, 224, 208)
    FG_MEDIUM_TURQUOISE=_AnsiControlFn.fg_rgb(72, 209, 204)
    FG_DARK_TURQUOISE=_AnsiControlFn.fg_rgb(0, 206, 209)
    FG_CADET_BLUE=_AnsiControlFn.fg_rgb(95, 158, 160)
    FG_STEEL_BLUE=_AnsiControlFn.fg_rgb(70, 130, 180)
    FG_LIGHT_STEEL_BLUE=_AnsiControlFn.fg_rgb(176, 196, 222)
    FG_POWDER_BLUE=_AnsiControlFn.fg_rgb(176, 224, 230)
    FG_LIGHT_BLUE=_AnsiControlFn.fg_rgb(173, 216, 230)
    FG_SKY_BLUE=_AnsiControlFn.fg_rgb(135, 206, 235)
    FG_LIGHT_SKY_BLUE=_AnsiControlFn.fg_rgb(135, 206, 250)
    FG_DEEP_SKY_BLUE=_AnsiControlFn.fg_rgb(0, 191, 255)
    FG_DODGER_BLUE=_AnsiControlFn.fg_rgb(30, 144, 255)
    FG_CORNFLOWER_BLUE=_AnsiControlFn.fg_rgb(100, 149, 237)
    FG_ROYAL_BLUE=_AnsiControlFn.fg_rgb(65, 105, 225)
    FG_MEDIUM_BLUE=_AnsiControlFn.fg_rgb(0, 0, 205)
    FG_DARK_BLUE=_AnsiControlFn.fg_rgb(0, 0, 139)
    FG_NAVY=_AnsiControlFn.fg_rgb(0, 0, 128)
    FG_MIDNIGHT_BLUE=_AnsiControlFn.fg_rgb(25, 25, 112)
    FG_CORNSILK=_AnsiControlFn.fg_rgb(255, 248, 220)
    FG_BLANCHED_ALMOND=_AnsiControlFn.fg_rgb(255, 235, 205)
    FG_BISQUE=_AnsiControlFn.fg_rgb(255, 228, 196)
    FG_NAVAJO_WHITE=_AnsiControlFn.fg_rgb(255, 222, 173)
    FG_WHEAT=_AnsiControlFn.fg_rgb(245, 222, 179)
    FG_BURLY_WOOD=_AnsiControlFn.fg_rgb(222, 184, 135)
    FG_TAN=_AnsiControlFn.fg_rgb(210, 180, 140)
    FG_ROSY_BROWN=_AnsiControlFn.fg_rgb(188, 143, 143)
    FG_SANDY_BROWN=_AnsiControlFn.fg_rgb(244, 164, 96)
    FG_GOLDENROD=_AnsiControlFn.fg_rgb(218, 165, 32)
    FG_DARK_GOLDENROD=_AnsiControlFn.fg_rgb(184, 134, 11)
    FG_PERU=_AnsiControlFn.fg_rgb(205, 133, 63)
    FG_CHOCOLATE=_AnsiControlFn.fg_rgb(210, 105, 30)
    FG_SADDLE_BROWN=_AnsiControlFn.fg_rgb(139, 69, 19)
    FG_SIENNA=_AnsiControlFn.fg_rgb(160, 82, 45)
    FG_BROWN=_AnsiControlFn.fg_rgb(165, 42, 42)
    FG_MAROON=_AnsiControlFn.fg_rgb(128, 0, 0)
    FG_SNOW=_AnsiControlFn.fg_rgb(255, 250, 250)
    FG_HONEY_DEW=_AnsiControlFn.fg_rgb(240, 255, 240)
    FG_MINT_CREAM=_AnsiControlFn.fg_rgb(245, 255, 250)
    FG_AZURE=_AnsiControlFn.fg_rgb(240, 255, 255)
    FG_ALICE_BLUE=_AnsiControlFn.fg_rgb(240, 248, 255)
    FG_GHOST_WHITE=_AnsiControlFn.fg_rgb(248, 248, 255)
    FG_WHITE_SMOKE=_AnsiControlFn.fg_rgb(245, 245, 245)
    FG_SEA_SHELL=_AnsiControlFn.fg_rgb(255, 245, 238)
    FG_BEIGE=_AnsiControlFn.fg_rgb(245, 245, 220)
    FG_OLD_LACE=_AnsiControlFn.fg_rgb(253, 245, 230)
    FG_FLORAL_WHITE=_AnsiControlFn.fg_rgb(255, 250, 240)
    FG_IVORY=_AnsiControlFn.fg_rgb(255, 255, 240)
    FG_ANTIQUE_WHITE=_AnsiControlFn.fg_rgb(250, 235, 215)
    FG_LINEN=_AnsiControlFn.fg_rgb(250, 240, 230)
    FG_LAVENDER_BLUSH=_AnsiControlFn.fg_rgb(255, 240, 245)
    FG_MISTY_ROSE=_AnsiControlFn.fg_rgb(255, 228, 225)
    FG_GAINSBORO=_AnsiControlFn.fg_rgb(220, 220, 220)
    FG_LIGHT_GRAY=_AnsiControlFn.fg_rgb(211, 211, 211)
    FG_LIGHT_GREY=FG_LIGHT_GRAY # Alias for my British English friends
    FG_SILVER=_AnsiControlFn.fg_rgb(192, 192, 192)
    FG_DARK_GRAY=_AnsiControlFn.fg_rgb(169, 169, 169)
    FG_DARK_GREY=FG_DARK_GRAY # Alias for my British English friends
    FG_GRAY=_AnsiControlFn.fg_color256(244)
    FG_GREY=FG_GRAY # Alias for my British English friends
    FG_DIM_GRAY=_AnsiControlFn.fg_rgb(105, 105, 105)
    FG_LIGHT_SLATE_GRAY=_AnsiControlFn.fg_rgb(119, 136, 153)
    FG_SLATE_GRAY=_AnsiControlFn.fg_rgb(112, 128, 144)
    FG_DARK_SLATE_GRAY=_AnsiControlFn.fg_rgb(47, 79, 79)

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
    BG_INDIAN_RED=_AnsiControlFn.bg_rgb(205, 92, 92)
    BG_LIGHT_CORAL=_AnsiControlFn.bg_rgb(240, 128, 128)
    BG_SALMON=_AnsiControlFn.bg_rgb(250, 128, 114)
    BG_DARK_SALMON=_AnsiControlFn.bg_rgb(233, 150, 122)
    BG_LIGHT_SALMON=_AnsiControlFn.bg_rgb(255, 160, 122)
    BG_CRIMSON=_AnsiControlFn.bg_rgb(220, 20, 60)
    BG_FIRE_BRICK=_AnsiControlFn.bg_rgb(178, 34, 34)
    BG_DARK_RED=_AnsiControlFn.bg_rgb(139, 0, 0)
    BG_PINK=_AnsiControlFn.bg_rgb(255, 192, 203)
    BG_LIGHT_PINK=_AnsiControlFn.bg_rgb(255, 182, 193)
    BG_HOT_PINK=_AnsiControlFn.bg_rgb(255, 105, 180)
    BG_DEEP_PINK=_AnsiControlFn.bg_rgb(255, 20, 147)
    BG_MEDIUM_VIOLET_RED=_AnsiControlFn.bg_rgb(199, 21, 133)
    BG_PALE_VIOLET_RED=_AnsiControlFn.bg_rgb(219, 112, 147)
    BG_ORANGE=_AnsiControlFn.bg_color256(214)
    BG_CORAL=_AnsiControlFn.bg_rgb(255, 127, 80)
    BG_TOMATO=_AnsiControlFn.bg_rgb(255, 99, 71)
    BG_ORANGE_RED=_AnsiControlFn.bg_color256(202)
    BG_DARK_ORANGE=_AnsiControlFn.bg_rgb(255, 140, 0)
    BG_GOLD=_AnsiControlFn.bg_rgb(255, 215, 0)
    BG_LIGHT_YELLOW=_AnsiControlFn.bg_rgb(255, 255, 224)
    BG_LEMON_CHIFFON=_AnsiControlFn.bg_rgb(255, 250, 205)
    BG_LIGHT_GOLDENROD_YELLOW=_AnsiControlFn.bg_rgb(250, 250, 210)
    BG_PAPAYA_WHIP=_AnsiControlFn.bg_rgb(255, 239, 213)
    BG_MOCCASIN=_AnsiControlFn.bg_rgb(255, 228, 181)
    BG_PEACH_PUFF=_AnsiControlFn.bg_rgb(255, 218, 185)
    BG_PALE_GOLDENROD=_AnsiControlFn.bg_rgb(238, 232, 170)
    BG_KHAKI=_AnsiControlFn.bg_rgb(240, 230, 140)
    BG_DARK_KHAKI=_AnsiControlFn.bg_rgb(189, 183, 107)
    BG_PURPLE=_AnsiControlFn.bg_color256(90)
    BG_LAVENDER=_AnsiControlFn.bg_rgb(230, 230, 250)
    BG_THISTLE=_AnsiControlFn.bg_rgb(216, 191, 216)
    BG_PLUM=_AnsiControlFn.bg_rgb(221, 160, 221)
    BG_VIOLET=_AnsiControlFn.bg_rgb(238, 130, 238)
    BG_ORCHID=_AnsiControlFn.bg_rgb(218, 112, 214)
    BG_FUCHSIA=_AnsiControlFn.bg_rgb(255, 0, 255)
    BG_MEDIUM_ORCHID=_AnsiControlFn.bg_rgb(186, 85, 211)
    BG_MEDIUM_PURPLE=_AnsiControlFn.bg_rgb(147, 112, 219)
    BG_REBECCA_PURPLE=_AnsiControlFn.bg_rgb(102, 51, 153)
    BG_BLUE_VIOLET=_AnsiControlFn.bg_rgb(138, 43, 226)
    BG_DARK_VIOLET=_AnsiControlFn.bg_rgb(148, 0, 211)
    BG_DARK_ORCHID=_AnsiControlFn.bg_rgb(153, 50, 204)
    BG_DARK_MAGENTA=_AnsiControlFn.bg_rgb(139, 0, 139)
    BG_INDIGO=_AnsiControlFn.bg_rgb(75, 0, 130)
    BG_SLATE_BLUE=_AnsiControlFn.bg_rgb(106, 90, 205)
    BG_DARK_SLATE_BLUE=_AnsiControlFn.bg_rgb(72, 61, 139)
    BG_MEDIUM_SLATE_BLUE=_AnsiControlFn.bg_rgb(123, 104, 238)
    BG_GREEN_YELLOW=_AnsiControlFn.bg_rgb(173, 255, 47)
    BG_CHARTREUSE=_AnsiControlFn.bg_rgb(127, 255, 0)
    BG_LAWN_GREEN=_AnsiControlFn.bg_rgb(124, 252, 0)
    BG_LIME=_AnsiControlFn.bg_rgb(0, 255, 0)
    BG_LIME_GREEN=_AnsiControlFn.bg_rgb(50, 205, 50)
    BG_PALE_GREEN=_AnsiControlFn.bg_rgb(152, 251, 152)
    BG_LIGHT_GREEN=_AnsiControlFn.bg_rgb(144, 238, 144)
    BG_MEDIUM_SPRING_GREEN=_AnsiControlFn.bg_rgb(0, 250, 154)
    BG_SPRING_GREEN=_AnsiControlFn.bg_rgb(0, 255, 127)
    BG_MEDIUM_SEA_GREEN=_AnsiControlFn.bg_rgb(60, 179, 113)
    BG_SEA_GREEN=_AnsiControlFn.bg_rgb(46, 139, 87)
    BG_FOREST_GREEN=_AnsiControlFn.bg_rgb(34, 139, 34)
    BG_DARK_GREEN=_AnsiControlFn.bg_rgb(0, 100, 0)
    BG_YELLOW_GREEN=_AnsiControlFn.bg_rgb(154, 205, 50)
    BG_OLIVE_DRAB=_AnsiControlFn.bg_rgb(107, 142, 35)
    BG_OLIVE=_AnsiControlFn.bg_rgb(128, 128, 0)
    BG_DARK_OLIVE_GREEN=_AnsiControlFn.bg_rgb(85, 107, 47)
    BG_MEDIUM_AQUAMARINE=_AnsiControlFn.bg_rgb(102, 205, 170)
    BG_DARK_SEA_GREEN=_AnsiControlFn.bg_rgb(143, 188, 139)
    BG_LIGHT_SEA_GREEN=_AnsiControlFn.bg_rgb(32, 178, 170)
    BG_DARK_CYAN=_AnsiControlFn.bg_rgb(0, 139, 139)
    BG_TEAL=_AnsiControlFn.bg_rgb(0, 128, 128)
    BG_AQUA=_AnsiControlFn.bg_rgb(0, 255, 255)
    BG_LIGHT_CYAN=_AnsiControlFn.bg_rgb(224, 255, 255)
    BG_PALE_TURQUOISE=_AnsiControlFn.bg_rgb(175, 238, 238)
    BG_AQUAMARINE=_AnsiControlFn.bg_rgb(127, 255, 212)
    BG_TURQUOISE=_AnsiControlFn.bg_rgb(64, 224, 208)
    BG_MEDIUM_TURQUOISE=_AnsiControlFn.bg_rgb(72, 209, 204)
    BG_DARK_TURQUOISE=_AnsiControlFn.bg_rgb(0, 206, 209)
    BG_CADET_BLUE=_AnsiControlFn.bg_rgb(95, 158, 160)
    BG_STEEL_BLUE=_AnsiControlFn.bg_rgb(70, 130, 180)
    BG_LIGHT_STEEL_BLUE=_AnsiControlFn.bg_rgb(176, 196, 222)
    BG_POWDER_BLUE=_AnsiControlFn.bg_rgb(176, 224, 230)
    BG_LIGHT_BLUE=_AnsiControlFn.bg_rgb(173, 216, 230)
    BG_SKY_BLUE=_AnsiControlFn.bg_rgb(135, 206, 235)
    BG_LIGHT_SKY_BLUE=_AnsiControlFn.bg_rgb(135, 206, 250)
    BG_DEEP_SKY_BLUE=_AnsiControlFn.bg_rgb(0, 191, 255)
    BG_DODGER_BLUE=_AnsiControlFn.bg_rgb(30, 144, 255)
    BG_CORNFLOWER_BLUE=_AnsiControlFn.bg_rgb(100, 149, 237)
    BG_ROYAL_BLUE=_AnsiControlFn.bg_rgb(65, 105, 225)
    BG_MEDIUM_BLUE=_AnsiControlFn.bg_rgb(0, 0, 205)
    BG_DARK_BLUE=_AnsiControlFn.bg_rgb(0, 0, 139)
    BG_NAVY=_AnsiControlFn.bg_rgb(0, 0, 128)
    BG_MIDNIGHT_BLUE=_AnsiControlFn.bg_rgb(25, 25, 112)
    BG_CORNSILK=_AnsiControlFn.bg_rgb(255, 248, 220)
    BG_BLANCHED_ALMOND=_AnsiControlFn.bg_rgb(255, 235, 205)
    BG_BISQUE=_AnsiControlFn.bg_rgb(255, 228, 196)
    BG_NAVAJO_WHITE=_AnsiControlFn.bg_rgb(255, 222, 173)
    BG_WHEAT=_AnsiControlFn.bg_rgb(245, 222, 179)
    BG_BURLY_WOOD=_AnsiControlFn.bg_rgb(222, 184, 135)
    BG_TAN=_AnsiControlFn.bg_rgb(210, 180, 140)
    BG_ROSY_BROWN=_AnsiControlFn.bg_rgb(188, 143, 143)
    BG_SANDY_BROWN=_AnsiControlFn.bg_rgb(244, 164, 96)
    BG_GOLDENROD=_AnsiControlFn.bg_rgb(218, 165, 32)
    BG_DARK_GOLDENROD=_AnsiControlFn.bg_rgb(184, 134, 11)
    BG_PERU=_AnsiControlFn.bg_rgb(205, 133, 63)
    BG_CHOCOLATE=_AnsiControlFn.bg_rgb(210, 105, 30)
    BG_SADDLE_BROWN=_AnsiControlFn.bg_rgb(139, 69, 19)
    BG_SIENNA=_AnsiControlFn.bg_rgb(160, 82, 45)
    BG_BROWN=_AnsiControlFn.bg_rgb(165, 42, 42)
    BG_MAROON=_AnsiControlFn.bg_rgb(128, 0, 0)
    BG_SNOW=_AnsiControlFn.bg_rgb(255, 250, 250)
    BG_HONEY_DEW=_AnsiControlFn.bg_rgb(240, 255, 240)
    BG_MINT_CREAM=_AnsiControlFn.bg_rgb(245, 255, 250)
    BG_AZURE=_AnsiControlFn.bg_rgb(240, 255, 255)
    BG_ALICE_BLUE=_AnsiControlFn.bg_rgb(240, 248, 255)
    BG_GHOST_WHITE=_AnsiControlFn.bg_rgb(248, 248, 255)
    BG_WHITE_SMOKE=_AnsiControlFn.bg_rgb(245, 245, 245)
    BG_SEA_SHELL=_AnsiControlFn.bg_rgb(255, 245, 238)
    BG_BEIGE=_AnsiControlFn.bg_rgb(245, 245, 220)
    BG_OLD_LACE=_AnsiControlFn.bg_rgb(253, 245, 230)
    BG_FLORAL_WHITE=_AnsiControlFn.bg_rgb(255, 250, 240)
    BG_IVORY=_AnsiControlFn.bg_rgb(255, 255, 240)
    BG_ANTIQUE_WHITE=_AnsiControlFn.bg_rgb(250, 235, 215)
    BG_LINEN=_AnsiControlFn.bg_rgb(250, 240, 230)
    BG_LAVENDER_BLUSH=_AnsiControlFn.bg_rgb(255, 240, 245)
    BG_MISTY_ROSE=_AnsiControlFn.bg_rgb(255, 228, 225)
    BG_GAINSBORO=_AnsiControlFn.bg_rgb(220, 220, 220)
    BG_LIGHT_GRAY=_AnsiControlFn.bg_rgb(211, 211, 211)
    BG_LIGHT_GREY=BG_LIGHT_GRAY # Alias for my British English friends
    BG_SILVER=_AnsiControlFn.bg_rgb(192, 192, 192)
    BG_DARK_GRAY=_AnsiControlFn.bg_rgb(169, 169, 169)
    BG_DARK_GREY=BG_DARK_GRAY # Alias for my British English friends
    BG_GRAY=_AnsiControlFn.bg_color256(244)
    BG_GREY=BG_GRAY # Alias for my British English friends
    BG_DIM_GRAY=_AnsiControlFn.bg_rgb(105, 105, 105)
    BG_LIGHT_SLATE_GRAY=_AnsiControlFn.bg_rgb(119, 136, 153)
    BG_SLATE_GRAY=_AnsiControlFn.bg_rgb(112, 128, 144)
    BG_DARK_SLATE_GRAY=_AnsiControlFn.bg_rgb(47, 79, 79)

    # Enable underline and set to color
    UL_BLACK=_AnsiControlFn.ul_color256(0)
    UL_RED=_AnsiControlFn.ul_color256(9)
    UL_GREEN=_AnsiControlFn.ul_color256(10)
    UL_YELLOW=_AnsiControlFn.ul_color256(11)
    UL_BLUE=_AnsiControlFn.ul_color256(12)
    UL_MAGENTA=_AnsiControlFn.ul_color256(13)
    UL_CYAN=_AnsiControlFn.ul_color256(14)
    UL_WHITE=_AnsiControlFn.ul_color256(15)
    UL_INDIAN_RED=_AnsiControlFn.ul_rgb(205, 92, 92)
    UL_LIGHT_CORAL=_AnsiControlFn.ul_rgb(240, 128, 128)
    UL_SALMON=_AnsiControlFn.ul_rgb(250, 128, 114)
    UL_DARK_SALMON=_AnsiControlFn.ul_rgb(233, 150, 122)
    UL_LIGHT_SALMON=_AnsiControlFn.ul_rgb(255, 160, 122)
    UL_CRIMSON=_AnsiControlFn.ul_rgb(220, 20, 60)
    UL_FIRE_BRICK=_AnsiControlFn.ul_rgb(178, 34, 34)
    UL_DARK_RED=_AnsiControlFn.ul_rgb(139, 0, 0)
    UL_PINK=_AnsiControlFn.ul_rgb(255, 192, 203)
    UL_LIGHT_PINK=_AnsiControlFn.ul_rgb(255, 182, 193)
    UL_HOT_PINK=_AnsiControlFn.ul_rgb(255, 105, 180)
    UL_DEEP_PINK=_AnsiControlFn.ul_rgb(255, 20, 147)
    UL_MEDIUM_VIOLET_RED=_AnsiControlFn.ul_rgb(199, 21, 133)
    UL_PALE_VIOLET_RED=_AnsiControlFn.ul_rgb(219, 112, 147)
    UL_ORANGE=_AnsiControlFn.ul_color256(214)
    UL_CORAL=_AnsiControlFn.ul_rgb(255, 127, 80)
    UL_TOMATO=_AnsiControlFn.ul_rgb(255, 99, 71)
    UL_ORANGE_RED=_AnsiControlFn.ul_color256(202)
    UL_DARK_ORANGE=_AnsiControlFn.ul_rgb(255, 140, 0)
    UL_GOLD=_AnsiControlFn.ul_rgb(255, 215, 0)
    UL_LIGHT_YELLOW=_AnsiControlFn.ul_rgb(255, 255, 224)
    UL_LEMON_CHIFFON=_AnsiControlFn.ul_rgb(255, 250, 205)
    UL_LIGHT_GOLDENROD_YELLOW=_AnsiControlFn.ul_rgb(250, 250, 210)
    UL_PAPAYA_WHIP=_AnsiControlFn.ul_rgb(255, 239, 213)
    UL_MOCCASIN=_AnsiControlFn.ul_rgb(255, 228, 181)
    UL_PEACH_PUFF=_AnsiControlFn.ul_rgb(255, 218, 185)
    UL_PALE_GOLDENROD=_AnsiControlFn.ul_rgb(238, 232, 170)
    UL_KHAKI=_AnsiControlFn.ul_rgb(240, 230, 140)
    UL_DARK_KHAKI=_AnsiControlFn.ul_rgb(189, 183, 107)
    UL_PURPLE=_AnsiControlFn.ul_color256(90)
    UL_LAVENDER=_AnsiControlFn.ul_rgb(230, 230, 250)
    UL_THISTLE=_AnsiControlFn.ul_rgb(216, 191, 216)
    UL_PLUM=_AnsiControlFn.ul_rgb(221, 160, 221)
    UL_VIOLET=_AnsiControlFn.ul_rgb(238, 130, 238)
    UL_ORCHID=_AnsiControlFn.ul_rgb(218, 112, 214)
    UL_FUCHSIA=_AnsiControlFn.ul_rgb(255, 0, 255)
    UL_MEDIUM_ORCHID=_AnsiControlFn.ul_rgb(186, 85, 211)
    UL_MEDIUM_PURPLE=_AnsiControlFn.ul_rgb(147, 112, 219)
    UL_REBECCA_PURPLE=_AnsiControlFn.ul_rgb(102, 51, 153)
    UL_BLUE_VIOLET=_AnsiControlFn.ul_rgb(138, 43, 226)
    UL_DARK_VIOLET=_AnsiControlFn.ul_rgb(148, 0, 211)
    UL_DARK_ORCHID=_AnsiControlFn.ul_rgb(153, 50, 204)
    UL_DARK_MAGENTA=_AnsiControlFn.ul_rgb(139, 0, 139)
    UL_INDIGO=_AnsiControlFn.ul_rgb(75, 0, 130)
    UL_SLATE_BLUE=_AnsiControlFn.ul_rgb(106, 90, 205)
    UL_DARK_SLATE_BLUE=_AnsiControlFn.ul_rgb(72, 61, 139)
    UL_MEDIUM_SLATE_BLUE=_AnsiControlFn.ul_rgb(123, 104, 238)
    UL_GREEN_YELLOW=_AnsiControlFn.ul_rgb(173, 255, 47)
    UL_CHARTREUSE=_AnsiControlFn.ul_rgb(127, 255, 0)
    UL_LAWN_GREEN=_AnsiControlFn.ul_rgb(124, 252, 0)
    UL_LIME=_AnsiControlFn.ul_rgb(0, 255, 0)
    UL_LIME_GREEN=_AnsiControlFn.ul_rgb(50, 205, 50)
    UL_PALE_GREEN=_AnsiControlFn.ul_rgb(152, 251, 152)
    UL_LIGHT_GREEN=_AnsiControlFn.ul_rgb(144, 238, 144)
    UL_MEDIUM_SPRING_GREEN=_AnsiControlFn.ul_rgb(0, 250, 154)
    UL_SPRING_GREEN=_AnsiControlFn.ul_rgb(0, 255, 127)
    UL_MEDIUM_SEA_GREEN=_AnsiControlFn.ul_rgb(60, 179, 113)
    UL_SEA_GREEN=_AnsiControlFn.ul_rgb(46, 139, 87)
    UL_FOREST_GREEN=_AnsiControlFn.ul_rgb(34, 139, 34)
    UL_DARK_GREEN=_AnsiControlFn.ul_rgb(0, 100, 0)
    UL_YELLOW_GREEN=_AnsiControlFn.ul_rgb(154, 205, 50)
    UL_OLIVE_DRAB=_AnsiControlFn.ul_rgb(107, 142, 35)
    UL_OLIVE=_AnsiControlFn.ul_rgb(128, 128, 0)
    UL_DARK_OLIVE_GREEN=_AnsiControlFn.ul_rgb(85, 107, 47)
    UL_MEDIUM_AQUAMARINE=_AnsiControlFn.ul_rgb(102, 205, 170)
    UL_DARK_SEA_GREEN=_AnsiControlFn.ul_rgb(143, 188, 139)
    UL_LIGHT_SEA_GREEN=_AnsiControlFn.ul_rgb(32, 178, 170)
    UL_DARK_CYAN=_AnsiControlFn.ul_rgb(0, 139, 139)
    UL_TEAL=_AnsiControlFn.ul_rgb(0, 128, 128)
    UL_AQUA=_AnsiControlFn.ul_rgb(0, 255, 255)
    UL_LIGHT_CYAN=_AnsiControlFn.ul_rgb(224, 255, 255)
    UL_PALE_TURQUOISE=_AnsiControlFn.ul_rgb(175, 238, 238)
    UL_AQUAMARINE=_AnsiControlFn.ul_rgb(127, 255, 212)
    UL_TURQUOISE=_AnsiControlFn.ul_rgb(64, 224, 208)
    UL_MEDIUM_TURQUOISE=_AnsiControlFn.ul_rgb(72, 209, 204)
    UL_DARK_TURQUOISE=_AnsiControlFn.ul_rgb(0, 206, 209)
    UL_CADET_BLUE=_AnsiControlFn.ul_rgb(95, 158, 160)
    UL_STEEL_BLUE=_AnsiControlFn.ul_rgb(70, 130, 180)
    UL_LIGHT_STEEL_BLUE=_AnsiControlFn.ul_rgb(176, 196, 222)
    UL_POWDER_BLUE=_AnsiControlFn.ul_rgb(176, 224, 230)
    UL_LIGHT_BLUE=_AnsiControlFn.ul_rgb(173, 216, 230)
    UL_SKY_BLUE=_AnsiControlFn.ul_rgb(135, 206, 235)
    UL_LIGHT_SKY_BLUE=_AnsiControlFn.ul_rgb(135, 206, 250)
    UL_DEEP_SKY_BLUE=_AnsiControlFn.ul_rgb(0, 191, 255)
    UL_DODGER_BLUE=_AnsiControlFn.ul_rgb(30, 144, 255)
    UL_CORNFLOWER_BLUE=_AnsiControlFn.ul_rgb(100, 149, 237)
    UL_ROYAL_BLUE=_AnsiControlFn.ul_rgb(65, 105, 225)
    UL_MEDIUM_BLUE=_AnsiControlFn.ul_rgb(0, 0, 205)
    UL_DARK_BLUE=_AnsiControlFn.ul_rgb(0, 0, 139)
    UL_NAVY=_AnsiControlFn.ul_rgb(0, 0, 128)
    UL_MIDNIGHT_BLUE=_AnsiControlFn.ul_rgb(25, 25, 112)
    UL_CORNSILK=_AnsiControlFn.ul_rgb(255, 248, 220)
    UL_BLANCHED_ALMOND=_AnsiControlFn.ul_rgb(255, 235, 205)
    UL_BISQUE=_AnsiControlFn.ul_rgb(255, 228, 196)
    UL_NAVAJO_WHITE=_AnsiControlFn.ul_rgb(255, 222, 173)
    UL_WHEAT=_AnsiControlFn.ul_rgb(245, 222, 179)
    UL_BURLY_WOOD=_AnsiControlFn.ul_rgb(222, 184, 135)
    UL_TAN=_AnsiControlFn.ul_rgb(210, 180, 140)
    UL_ROSY_BROWN=_AnsiControlFn.ul_rgb(188, 143, 143)
    UL_SANDY_BROWN=_AnsiControlFn.ul_rgb(244, 164, 96)
    UL_GOLDENROD=_AnsiControlFn.ul_rgb(218, 165, 32)
    UL_DARK_GOLDENROD=_AnsiControlFn.ul_rgb(184, 134, 11)
    UL_PERU=_AnsiControlFn.ul_rgb(205, 133, 63)
    UL_CHOCOLATE=_AnsiControlFn.ul_rgb(210, 105, 30)
    UL_SADDLE_BROWN=_AnsiControlFn.ul_rgb(139, 69, 19)
    UL_SIENNA=_AnsiControlFn.ul_rgb(160, 82, 45)
    UL_BROWN=_AnsiControlFn.ul_rgb(165, 42, 42)
    UL_MAROON=_AnsiControlFn.ul_rgb(128, 0, 0)
    UL_SNOW=_AnsiControlFn.ul_rgb(255, 250, 250)
    UL_HONEY_DEW=_AnsiControlFn.ul_rgb(240, 255, 240)
    UL_MINT_CREAM=_AnsiControlFn.ul_rgb(245, 255, 250)
    UL_AZURE=_AnsiControlFn.ul_rgb(240, 255, 255)
    UL_ALICE_BLUE=_AnsiControlFn.ul_rgb(240, 248, 255)
    UL_GHOST_WHITE=_AnsiControlFn.ul_rgb(248, 248, 255)
    UL_WHITE_SMOKE=_AnsiControlFn.ul_rgb(245, 245, 245)
    UL_SEA_SHELL=_AnsiControlFn.ul_rgb(255, 245, 238)
    UL_BEIGE=_AnsiControlFn.ul_rgb(245, 245, 220)
    UL_OLD_LACE=_AnsiControlFn.ul_rgb(253, 245, 230)
    UL_FLORAL_WHITE=_AnsiControlFn.ul_rgb(255, 250, 240)
    UL_IVORY=_AnsiControlFn.ul_rgb(255, 255, 240)
    UL_ANTIQUE_WHITE=_AnsiControlFn.ul_rgb(250, 235, 215)
    UL_LINEN=_AnsiControlFn.ul_rgb(250, 240, 230)
    UL_LAVENDER_BLUSH=_AnsiControlFn.ul_rgb(255, 240, 245)
    UL_MISTY_ROSE=_AnsiControlFn.ul_rgb(255, 228, 225)
    UL_GAINSBORO=_AnsiControlFn.ul_rgb(220, 220, 220)
    UL_LIGHT_GRAY=_AnsiControlFn.ul_rgb(211, 211, 211)
    UL_LIGHT_GREY=UL_LIGHT_GRAY # Alias for my British English friends
    UL_SILVER=_AnsiControlFn.ul_rgb(192, 192, 192)
    UL_DARK_GRAY=_AnsiControlFn.ul_rgb(169, 169, 169)
    UL_DARK_GREY=UL_DARK_GRAY # Alias for my British English friends
    UL_GRAY=_AnsiControlFn.ul_color256(244)
    UL_GREY=UL_GRAY # Alias for my British English friends
    UL_DIM_GRAY=_AnsiControlFn.ul_rgb(105, 105, 105)
    UL_LIGHT_SLATE_GRAY=_AnsiControlFn.ul_rgb(119, 136, 153)
    UL_SLATE_GRAY=_AnsiControlFn.ul_rgb(112, 128, 144)
    UL_DARK_SLATE_GRAY=_AnsiControlFn.ul_rgb(47, 79, 79)

    # Enable double underline and set to color
    DUL_BLACK=_AnsiControlFn.dul_color256(0)
    DUL_RED=_AnsiControlFn.dul_color256(9)
    DUL_GREEN=_AnsiControlFn.dul_color256(10)
    DUL_YELLOW=_AnsiControlFn.dul_color256(11)
    DUL_BLUE=_AnsiControlFn.dul_color256(12)
    DUL_MAGENTA=_AnsiControlFn.dul_color256(13)
    DUL_CYAN=_AnsiControlFn.dul_color256(14)
    DUL_WHITE=_AnsiControlFn.dul_color256(15)
    DUL_INDIAN_RED=_AnsiControlFn.dul_rgb(205, 92, 92)
    DUL_LIGHT_CORAL=_AnsiControlFn.dul_rgb(240, 128, 128)
    DUL_SALMON=_AnsiControlFn.dul_rgb(250, 128, 114)
    DUL_DARK_SALMON=_AnsiControlFn.dul_rgb(233, 150, 122)
    DUL_LIGHT_SALMON=_AnsiControlFn.dul_rgb(255, 160, 122)
    DUL_CRIMSON=_AnsiControlFn.dul_rgb(220, 20, 60)
    DUL_FIRE_BRICK=_AnsiControlFn.dul_rgb(178, 34, 34)
    DUL_DARK_RED=_AnsiControlFn.dul_rgb(139, 0, 0)
    DUL_PINK=_AnsiControlFn.dul_rgb(255, 192, 203)
    DUL_LIGHT_PINK=_AnsiControlFn.dul_rgb(255, 182, 193)
    DUL_HOT_PINK=_AnsiControlFn.dul_rgb(255, 105, 180)
    DUL_DEEP_PINK=_AnsiControlFn.dul_rgb(255, 20, 147)
    DUL_MEDIUM_VIOLET_RED=_AnsiControlFn.dul_rgb(199, 21, 133)
    DUL_PALE_VIOLET_RED=_AnsiControlFn.dul_rgb(219, 112, 147)
    DUL_ORANGE=_AnsiControlFn.dul_color256(214)
    DUL_CORAL=_AnsiControlFn.dul_rgb(255, 127, 80)
    DUL_TOMATO=_AnsiControlFn.dul_rgb(255, 99, 71)
    DUL_ORANGE_RED=_AnsiControlFn.dul_color256(202)
    DUL_DARK_ORANGE=_AnsiControlFn.dul_rgb(255, 140, 0)
    DUL_GOLD=_AnsiControlFn.dul_rgb(255, 215, 0)
    DUL_LIGHT_YELLOW=_AnsiControlFn.dul_rgb(255, 255, 224)
    DUL_LEMON_CHIFFON=_AnsiControlFn.dul_rgb(255, 250, 205)
    DUL_LIGHT_GOLDENROD_YELLOW=_AnsiControlFn.dul_rgb(250, 250, 210)
    DUL_PAPAYA_WHIP=_AnsiControlFn.dul_rgb(255, 239, 213)
    DUL_MOCCASIN=_AnsiControlFn.dul_rgb(255, 228, 181)
    DUL_PEACH_PUFF=_AnsiControlFn.dul_rgb(255, 218, 185)
    DUL_PALE_GOLDENROD=_AnsiControlFn.dul_rgb(238, 232, 170)
    DUL_KHAKI=_AnsiControlFn.dul_rgb(240, 230, 140)
    DUL_DARK_KHAKI=_AnsiControlFn.dul_rgb(189, 183, 107)
    DUL_PURPLE=_AnsiControlFn.dul_color256(90)
    DUL_LAVENDER=_AnsiControlFn.dul_rgb(230, 230, 250)
    DUL_THISTLE=_AnsiControlFn.dul_rgb(216, 191, 216)
    DUL_PLUM=_AnsiControlFn.dul_rgb(221, 160, 221)
    DUL_VIOLET=_AnsiControlFn.dul_rgb(238, 130, 238)
    DUL_ORCHID=_AnsiControlFn.dul_rgb(218, 112, 214)
    DUL_FUCHSIA=_AnsiControlFn.dul_rgb(255, 0, 255)
    DUL_MEDIUM_ORCHID=_AnsiControlFn.dul_rgb(186, 85, 211)
    DUL_MEDIUM_PURPLE=_AnsiControlFn.dul_rgb(147, 112, 219)
    DUL_REBECCA_PURPLE=_AnsiControlFn.dul_rgb(102, 51, 153)
    DUL_BLUE_VIOLET=_AnsiControlFn.dul_rgb(138, 43, 226)
    DUL_DARK_VIOLET=_AnsiControlFn.dul_rgb(148, 0, 211)
    DUL_DARK_ORCHID=_AnsiControlFn.dul_rgb(153, 50, 204)
    DUL_DARK_MAGENTA=_AnsiControlFn.dul_rgb(139, 0, 139)
    DUL_INDIGO=_AnsiControlFn.dul_rgb(75, 0, 130)
    DUL_SLATE_BLUE=_AnsiControlFn.dul_rgb(106, 90, 205)
    DUL_DARK_SLATE_BLUE=_AnsiControlFn.dul_rgb(72, 61, 139)
    DUL_MEDIUM_SLATE_BLUE=_AnsiControlFn.dul_rgb(123, 104, 238)
    DUL_GREEN_YELLOW=_AnsiControlFn.dul_rgb(173, 255, 47)
    DUL_CHARTREUSE=_AnsiControlFn.dul_rgb(127, 255, 0)
    DUL_LAWN_GREEN=_AnsiControlFn.dul_rgb(124, 252, 0)
    DUL_LIME=_AnsiControlFn.dul_rgb(0, 255, 0)
    DUL_LIME_GREEN=_AnsiControlFn.dul_rgb(50, 205, 50)
    DUL_PALE_GREEN=_AnsiControlFn.dul_rgb(152, 251, 152)
    DUL_LIGHT_GREEN=_AnsiControlFn.dul_rgb(144, 238, 144)
    DUL_MEDIUM_SPRING_GREEN=_AnsiControlFn.dul_rgb(0, 250, 154)
    DUL_SPRING_GREEN=_AnsiControlFn.dul_rgb(0, 255, 127)
    DUL_MEDIUM_SEA_GREEN=_AnsiControlFn.dul_rgb(60, 179, 113)
    DUL_SEA_GREEN=_AnsiControlFn.dul_rgb(46, 139, 87)
    DUL_FOREST_GREEN=_AnsiControlFn.dul_rgb(34, 139, 34)
    DUL_DARK_GREEN=_AnsiControlFn.dul_rgb(0, 100, 0)
    DUL_YELLOW_GREEN=_AnsiControlFn.dul_rgb(154, 205, 50)
    DUL_OLIVE_DRAB=_AnsiControlFn.dul_rgb(107, 142, 35)
    DUL_OLIVE=_AnsiControlFn.dul_rgb(128, 128, 0)
    DUL_DARK_OLIVE_GREEN=_AnsiControlFn.dul_rgb(85, 107, 47)
    DUL_MEDIUM_AQUAMARINE=_AnsiControlFn.dul_rgb(102, 205, 170)
    DUL_DARK_SEA_GREEN=_AnsiControlFn.dul_rgb(143, 188, 139)
    DUL_LIGHT_SEA_GREEN=_AnsiControlFn.dul_rgb(32, 178, 170)
    DUL_DARK_CYAN=_AnsiControlFn.dul_rgb(0, 139, 139)
    DUL_TEAL=_AnsiControlFn.dul_rgb(0, 128, 128)
    DUL_AQUA=_AnsiControlFn.dul_rgb(0, 255, 255)
    DUL_LIGHT_CYAN=_AnsiControlFn.dul_rgb(224, 255, 255)
    DUL_PALE_TURQUOISE=_AnsiControlFn.dul_rgb(175, 238, 238)
    DUL_AQUAMARINE=_AnsiControlFn.dul_rgb(127, 255, 212)
    DUL_TURQUOISE=_AnsiControlFn.dul_rgb(64, 224, 208)
    DUL_MEDIUM_TURQUOISE=_AnsiControlFn.dul_rgb(72, 209, 204)
    DUL_DARK_TURQUOISE=_AnsiControlFn.dul_rgb(0, 206, 209)
    DUL_CADET_BLUE=_AnsiControlFn.dul_rgb(95, 158, 160)
    DUL_STEEL_BLUE=_AnsiControlFn.dul_rgb(70, 130, 180)
    DUL_LIGHT_STEEL_BLUE=_AnsiControlFn.dul_rgb(176, 196, 222)
    DUL_POWDER_BLUE=_AnsiControlFn.dul_rgb(176, 224, 230)
    DUL_LIGHT_BLUE=_AnsiControlFn.dul_rgb(173, 216, 230)
    DUL_SKY_BLUE=_AnsiControlFn.dul_rgb(135, 206, 235)
    DUL_LIGHT_SKY_BLUE=_AnsiControlFn.dul_rgb(135, 206, 250)
    DUL_DEEP_SKY_BLUE=_AnsiControlFn.dul_rgb(0, 191, 255)
    DUL_DODGER_BLUE=_AnsiControlFn.dul_rgb(30, 144, 255)
    DUL_CORNFLOWER_BLUE=_AnsiControlFn.dul_rgb(100, 149, 237)
    DUL_ROYAL_BLUE=_AnsiControlFn.dul_rgb(65, 105, 225)
    DUL_MEDIUM_BLUE=_AnsiControlFn.dul_rgb(0, 0, 205)
    DUL_DARK_BLUE=_AnsiControlFn.dul_rgb(0, 0, 139)
    DUL_NAVY=_AnsiControlFn.dul_rgb(0, 0, 128)
    DUL_MIDNIGHT_BLUE=_AnsiControlFn.dul_rgb(25, 25, 112)
    DUL_CORNSILK=_AnsiControlFn.dul_rgb(255, 248, 220)
    DUL_BLANCHED_ALMOND=_AnsiControlFn.dul_rgb(255, 235, 205)
    DUL_BISQUE=_AnsiControlFn.dul_rgb(255, 228, 196)
    DUL_NAVAJO_WHITE=_AnsiControlFn.dul_rgb(255, 222, 173)
    DUL_WHEAT=_AnsiControlFn.dul_rgb(245, 222, 179)
    DUL_BURLY_WOOD=_AnsiControlFn.dul_rgb(222, 184, 135)
    DUL_TAN=_AnsiControlFn.dul_rgb(210, 180, 140)
    DUL_ROSY_BROWN=_AnsiControlFn.dul_rgb(188, 143, 143)
    DUL_SANDY_BROWN=_AnsiControlFn.dul_rgb(244, 164, 96)
    DUL_GOLDENROD=_AnsiControlFn.dul_rgb(218, 165, 32)
    DUL_DARK_GOLDENROD=_AnsiControlFn.dul_rgb(184, 134, 11)
    DUL_PERU=_AnsiControlFn.dul_rgb(205, 133, 63)
    DUL_CHOCOLATE=_AnsiControlFn.dul_rgb(210, 105, 30)
    DUL_SADDLE_BROWN=_AnsiControlFn.dul_rgb(139, 69, 19)
    DUL_SIENNA=_AnsiControlFn.dul_rgb(160, 82, 45)
    DUL_BROWN=_AnsiControlFn.dul_rgb(165, 42, 42)
    DUL_MAROON=_AnsiControlFn.dul_rgb(128, 0, 0)
    DUL_SNOW=_AnsiControlFn.dul_rgb(255, 250, 250)
    DUL_HONEY_DEW=_AnsiControlFn.dul_rgb(240, 255, 240)
    DUL_MINT_CREAM=_AnsiControlFn.dul_rgb(245, 255, 250)
    DUL_AZURE=_AnsiControlFn.dul_rgb(240, 255, 255)
    DUL_ALICE_BLUE=_AnsiControlFn.dul_rgb(240, 248, 255)
    DUL_GHOST_WHITE=_AnsiControlFn.dul_rgb(248, 248, 255)
    DUL_WHITE_SMOKE=_AnsiControlFn.dul_rgb(245, 245, 245)
    DUL_SEA_SHELL=_AnsiControlFn.dul_rgb(255, 245, 238)
    DUL_BEIGE=_AnsiControlFn.dul_rgb(245, 245, 220)
    DUL_OLD_LACE=_AnsiControlFn.dul_rgb(253, 245, 230)
    DUL_FLORAL_WHITE=_AnsiControlFn.dul_rgb(255, 250, 240)
    DUL_IVORY=_AnsiControlFn.dul_rgb(255, 255, 240)
    DUL_ANTIQUE_WHITE=_AnsiControlFn.dul_rgb(250, 235, 215)
    DUL_LINEN=_AnsiControlFn.dul_rgb(250, 240, 230)
    DUL_LAVENDER_BLUSH=_AnsiControlFn.dul_rgb(255, 240, 245)
    DUL_MISTY_ROSE=_AnsiControlFn.dul_rgb(255, 228, 225)
    DUL_GAINSBORO=_AnsiControlFn.dul_rgb(220, 220, 220)
    DUL_LIGHT_GRAY=_AnsiControlFn.dul_rgb(211, 211, 211)
    DUL_LIGHT_GREY=DUL_LIGHT_GRAY # Alias for my British English friends
    DUL_SILVER=_AnsiControlFn.dul_rgb(192, 192, 192)
    DUL_DARK_GRAY=_AnsiControlFn.dul_rgb(169, 169, 169)
    DUL_DARK_GREY=DUL_DARK_GRAY # Alias for my British English friends
    DUL_GRAY=_AnsiControlFn.dul_color256(244)
    DUL_GREY=DUL_GRAY # Alias for my British English friends
    DUL_DIM_GRAY=_AnsiControlFn.dul_rgb(105, 105, 105)
    DUL_LIGHT_SLATE_GRAY=_AnsiControlFn.dul_rgb(119, 136, 153)
    DUL_SLATE_GRAY=_AnsiControlFn.dul_rgb(112, 128, 144)
    DUL_DARK_SLATE_GRAY=_AnsiControlFn.dul_rgb(47, 79, 79)

    def __init__(self, seq:Union[int, List[int]]):
        '''
        Initializes this enum
        seq - control sequence which fully specifies this setting value
        '''
        if isinstance(seq, int):
            self._seq = [seq]
        else:
            self._seq = seq

    @property
    def setting(self) -> AnsiSetting:
        ''' Returns a unique instance of AnsiSetting which fully specifies this setting value '''
        # Unique instance is important for AnsiString use
        return AnsiSetting(self._seq)

    @staticmethod
    def rgb(
        r_or_rgb:int,
        g:Union[int,None]=None,
        b:Union[int,None]=None,
        component:ColorComponentType=ColorComponentType.FOREGROUND
    ) -> 'AnsiSetting':
        '''
        Generates a FG, BG, or UL ANSI sequence for the given RGB values.
        r_or_rgb: Either an 8-bit red component or the full 24-bit RGB value
        g: An 8-bit green component (b must also be specified when set)
        b: An 8-bit blue component (g must also be specified when set)
        component: The component to set color of (background, foreground, or underline)
        '''
        # AnsiSetting is used to wrap the format string so AnsiString may interpret it as a sequence
        return AnsiSetting(_AnsiControlFn.rgb(r_or_rgb, g, b, component))

    @staticmethod
    def fg_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> 'AnsiSetting':
        '''
        Generates a foreground ANSI sequence for the given RGB values.
        r_or_rgb: Either an 8-bit red component or the full 24-bit RGB value
        g: An 8-bit green component (b must also be specified when set)
        b: An 8-bit blue component (g must also be specified when set)
        '''
        return AnsiFormat.rgb(r_or_rgb, g, b)

    @staticmethod
    def bg_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> 'AnsiSetting':
        '''
        Generates a background ANSI sequence for the given RGB values.
        r_or_rgb: Either an 8-bit red component or the full 24-bit RGB value
        g: An 8-bit green component (b must also be specified when set)
        b: An 8-bit blue component (g must also be specified when set)
        '''
        return AnsiFormat.rgb(r_or_rgb, g, b, ColorComponentType.BACKGROUND)

    @staticmethod
    def ul_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> 'AnsiSetting':
        '''
        Generates an underline ANSI sequence for the given RGB values.
        r_or_rgb: Either an 8-bit red component or the full 24-bit RGB value
        g: An 8-bit green component (b must also be specified when set)
        b: An 8-bit blue component (g must also be specified when set)
        '''
        return AnsiFormat.rgb(r_or_rgb, g, b, ColorComponentType.UNDERLINE)

    @staticmethod
    def dul_rgb(r_or_rgb:int, g:Union[int,None]=None, b:Union[int,None]=None) -> 'AnsiSetting':
        '''
        Generates a double underline ANSI sequence for the given RGB values.
        r_or_rgb: Either an 8-bit red component or the full 24-bit RGB value
        g: An 8-bit green component (b must also be specified when set)
        b: An 8-bit blue component (g must also be specified when set)
        '''
        return AnsiFormat.rgb(r_or_rgb, g, b, ColorComponentType.DOUBLE_UNDERLINE)