import types

integer_types = (int,)
long_type = getattr(types, "LongType", None)
if long_type is not None:
    integer_types = (int, long_type)


def _clamp_byte(value):
    try:
        number = int(round(float(value)))
    except Exception:
        number = 0
    if number < 0:
        return 0
    if number > 255:
        return 255
    return number


class Color(object):
    __slots__ = ("_value",)

    def __init__(self, value):
        if isinstance(value, bool) or not isinstance(value, integer_types):
            raise TypeError("Color value must be 32-bit int ARGB")
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("Color value out of range: 0x00000000..0xFFFFFFFF")
        self._value = int(value)

    @staticmethod
    def _fromARGB8888(a, r, g, b):
        a8 = _clamp_byte(a)
        r8 = _clamp_byte(r)
        g8 = _clamp_byte(g)
        b8 = _clamp_byte(b)
        return Color((a8 << 24) | (r8 << 16) | (g8 << 8) | b8)

    @staticmethod
    def fromRGB(r, g, b):
        return Color._fromARGB8888(255, r, g, b)

    @staticmethod
    def fromRGBA(r, g, b, a):
        try:
            alpha = float(a)
        except Exception:
            alpha = 1.0
        if alpha < 0.0:
            alpha = 0.0
        if alpha > 1.0:
            alpha = 1.0
        return Color._fromARGB8888(int(round(alpha * 255.0)), r, g, b)

    @staticmethod
    def fromHex(value):
        if not isinstance(value, (str, type(u""))):
            raise TypeError("Color.fromHex expects a hex string")

        text = value.strip()
        if not text:
            raise ValueError("Color.fromHex got empty string")

        if text.startswith("#"):
            text = text[1:]
        if text.startswith("0x") or text.startswith("0X"):
            text = text[2:]

        size = len(text)
        if size == 3:
            # RGB -> RRGGBB
            text = text[0] * 2 + text[1] * 2 + text[2] * 2
            size = 6
        elif size == 4:
            # ARGB -> AARRGGBB
            text = text[0] * 2 + text[1] * 2 + text[2] * 2 + text[3] * 2
            size = 8

        if size == 6:
            # RRGGBB -> AARRGGBB (alpha8 defaults to 0xFF)
            text = "FF" + text
        elif size != 8:
            raise ValueError("Color.fromHex supports #RGB/#ARGB/#RRGGBB/#AARRGGBB")

        try:
            parsed = int(text, 16)
        except Exception:
            raise ValueError("Color.fromHex invalid hex: %s" % value)

        return Color(parsed)

    @property
    def value(self):
        return self._value

    @property
    def alpha8(self):
        return (self._value >> 24) & 0xFF

    @property
    def red(self):
        return (self._value >> 16) & 0xFF

    @property
    def green(self):
        return (self._value >> 8) & 0xFF

    @property
    def blue(self):
        return self._value & 0xFF

    @property
    def opacity(self):
        return self.alpha8 / 255.0

    @property
    def alpha(self):
        return self.alpha8 / 255.0

    def withAlpha(self, a):
        return Color.fromRGBA(self.red, self.green, self.blue, a)

    def withAlpha8(self, a):
        return Color._fromARGB8888(a, self.red, self.green, self.blue)

    def withRed(self, r):
        return Color._fromARGB8888(self.alpha8, r, self.green, self.blue)

    def withGreen(self, g):
        return Color._fromARGB8888(self.alpha8, self.red, g, self.blue)

    def withBlue(self, b):
        return Color._fromARGB8888(self.alpha8, self.red, self.green, b)

    def withOpacity(self, opacity):
        return Color.fromRGBA(self.red, self.green, self.blue, opacity)

    def toRGBUnitTuple(self):
        return (
            self.red / 255.0,
            self.green / 255.0,
            self.blue / 255.0,
        )

    def toRGBAUnitTuple(self):
        return (
            self.red / 255.0,
            self.green / 255.0,
            self.blue / 255.0,
            self.alpha8 / 255.0,
        )

    def __eq__(self, other):
        if not isinstance(other, Color):
            return False
        return self._value == other._value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return "Color(0x%08x)" % self._value


class Colors(object):
    transparent = Color(0x00000000)

    black = Color(0xFF000000)
    white = Color(0xFFFFFFFF)
    red = Color(0xFFFF0000)
    lime = Color(0xFF00FF00) 
    blue = Color(0xFF0000FF)
    yellow = Color(0xFFFFFF00)
    cyan = Color(0xFF00FFFF)
    magenta = Color(0xFFFF00FF)
    silver = Color(0xFFC0C0C0)
    gray = Color(0xFF808080)
    grey = Color(0xFF808080)
    maroon = Color(0xFF800000)
    olive = Color(0xFF808000)
    green = Color(0xFF008000)
    purple = Color(0xFF800080)
    teal = Color(0xFF008080)
    navy = Color(0xFF000080)

    aliceBlue = Color(0xFFF0F8FF)
    antiqueWhite = Color(0xFFFAEBD7)
    aqua = Color(0xFF00FFFF)
    aquamarine = Color(0xFF7FFFD4)
    azure = Color(0xFFF0FFFF)
    beige = Color(0xFFF5F5DC)
    bisque = Color(0xFFFFE4C4)
    blanchedAlmond = Color(0xFFFFEBCD)
    blueViolet = Color(0xFF8A2BE2)
    brown = Color(0xFFA52A2A)
    burlyWood = Color(0xFFDEB887)
    cadetBlue = Color(0xFF5F9EA0)
    chartreuse = Color(0xFF7FFF00)
    chocolate = Color(0xFFD2691E)
    coral = Color(0xFFFF7F50)
    cornflowerBlue = Color(0xFF6495ED)
    cornsilk = Color(0xFFFFF8DC)
    crimson = Color(0xFFDC143C)
    darkBlue = Color(0xFF00008B)
    darkCyan = Color(0xFF008B8B)
    darkGoldenRod = Color(0xFFB8860B)
    darkGray = Color(0xFFA9A9A9)
    darkGrey = Color(0xFFA9A9A9)
    darkGreen = Color(0xFF006400)
    darkKhaki = Color(0xFFBDB76B)
    darkMagenta = Color(0xFF8B008B)
    darkOliveGreen = Color(0xFF556B2F)
    darkOrange = Color(0xFFFF8C00)
    darkOrchid = Color(0xFF9932CC)
    darkRed = Color(0xFF8B0000)
    darkSalmon = Color(0xFFE9967A)
    darkSeaGreen = Color(0xFF8FBC8F)
    darkSlateBlue = Color(0xFF483D8B)
    darkSlateGray = Color(0xFF2F4F4F)
    darkSlateGrey = Color(0xFF2F4F4F)
    darkTurquoise = Color(0xFF00CED1)
    darkViolet = Color(0xFF9400D3)
    deepPink = Color(0xFFFF1493)
    deepSkyBlue = Color(0xFF00BFFF)
    dimGray = Color(0xFF696969)
    dimGrey = Color(0xFF696969)
    dodgerBlue = Color(0xFF1E90FF)
    fireBrick = Color(0xFFB22222)
    floralWhite = Color(0xFFFFFAF0)
    forestGreen = Color(0xFF228B22)
    fuchsia = Color(0xFFFF00FF)
    gainsboro = Color(0xFFDCDCDC)
    ghostWhite = Color(0xFFF8F8FF)
    gold = Color(0xFFFFD700)
    goldenRod = Color(0xFFDAA520)
    greenYellow = Color(0xFFADFF2F)
    honeyDew = Color(0xFFF0FFF0)
    hotPink = Color(0xFFFF69B4)
    indianRed = Color(0xFFCD5C5C)
    indigo = Color(0xFF4B0082)
    ivory = Color(0xFFFFFFF0)
    khaki = Color(0xFFF0E68C)
    lavender = Color(0xFFE6E6FA)
    lavenderBlush = Color(0xFFFFF0F5)
    lawnGreen = Color(0xFF7CFC00)
    lemonChiffon = Color(0xFFFFFACD)
    lightBlue = Color(0xFFADD8E6)
    lightCoral = Color(0xFFF08080)
    lightCyan = Color(0xFFE0FFFF)
    lightGoldenRodYellow = Color(0xFFFAFAD2)
    lightGray = Color(0xFFD3D3D3)
    lightGrey = Color(0xFFD3D3D3)
    lightGreen = Color(0xFF90EE90)
    lightPink = Color(0xFFFFB6C1)
    lightSalmon = Color(0xFFFFA07A)
    lightSeaGreen = Color(0xFF20B2AA)
    lightSkyBlue = Color(0xFF87CEFA)
    lightSlateGray = Color(0xFF778899)
    lightSlateGrey = Color(0xFF778899)
    lightSteelBlue = Color(0xFFB0C4DE)
    lightYellow = Color(0xFFFFFFE0)
    limeGreen = Color(0xFF32CD32)
    linen = Color(0xFFFAF0E6)
    mediumAquaMarine = Color(0xFF66CDAA)
    mediumBlue = Color(0xFF0000CD)
    mediumOrchid = Color(0xFFBA55D3)
    mediumPurple = Color(0xFF9370DB)
    mediumSeaGreen = Color(0xFF3CB371)
    mediumSlateBlue = Color(0xFF7B68EE)
    mediumSpringGreen = Color(0xFF00FA9A)
    mediumTurquoise = Color(0xFF48D1CC)
    mediumVioletRed = Color(0xFFC71585)
    midnightBlue = Color(0xFF191970)
    mintCream = Color(0xFFF5FFFA)
    mistyRose = Color(0xFFFFE4E1)
    moccasin = Color(0xFFFFE4B5)
    navajoWhite = Color(0xFFFFDEAD)
    oldLace = Color(0xFFFDF5E6)
    oliveDrab = Color(0xFF6B8E23)
    orange = Color(0xFFFFA500)
    orangeRed = Color(0xFFFF4500)
    orchid = Color(0xFFDA70D6)
    paleGoldenRod = Color(0xFFEEE8AA)
    paleGreen = Color(0xFF98FB98)
    paleTurquoise = Color(0xFFAFEEEE)
    paleVioletRed = Color(0xFFDB7093)
    papayaWhip = Color(0xFFFFEFD5)
    peachPuff = Color(0xFFFFDAB9)
    peru = Color(0xFFCD853F)
    pink = Color(0xFFFFC0CB)
    plum = Color(0xFFDDA0DD)
    powderBlue = Color(0xFFB0E0E6)
    rebeccaPurple = Color(0xFF663399)
    rosyBrown = Color(0xFFBC8F8F)
    royalBlue = Color(0xFF4169E1)
    saddleBrown = Color(0xFF8B4513)
    salmon = Color(0xFFFA8072)
    sandyBrown = Color(0xFFF4A460)
    seaGreen = Color(0xFF2E8B57)
    seaShell = Color(0xFFFFF5EE)
    sienna = Color(0xFFA0522D)
    skyBlue = Color(0xFF87CEEB)
    slateBlue = Color(0xFF6A5ACD)
    slateGray = Color(0xFF708090)
    slateGrey = Color(0xFF708090)
    snow = Color(0xFFFFFAFA)
    springGreen = Color(0xFF00FF7F)
    steelBlue = Color(0xFF4682B4)
    tan = Color(0xFFD2B48C)
    thistle = Color(0xFFD8BFD8)
    tomato = Color(0xFFFF6347)
    turquoise = Color(0xFF40E0D0)
    violet = Color(0xFFEE82EE)
    wheat = Color(0xFFF5DEB3)
    whiteSmoke = Color(0xFFF5F5F5)
    yellowGreen = Color(0xFF9ACD32)