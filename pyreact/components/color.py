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
    """Flutter-like immutable ARGB color object."""

    __slots__ = ("_value",)

    def __init__(self, value):
        if isinstance(value, bool) or not isinstance(value, integer_types):
            raise TypeError("Color value must be 32-bit int ARGB")
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("Color value out of range: 0x00000000..0xFFFFFFFF")
        self._value = int(value)

    @staticmethod
    def fromARGB(a, r, g, b):
        a8 = _clamp_byte(a)
        r8 = _clamp_byte(r)
        g8 = _clamp_byte(g)
        b8 = _clamp_byte(b)
        return Color((a8 << 24) | (r8 << 16) | (g8 << 8) | b8)

    @staticmethod
    def fromRGBO(r, g, b, opacity):
        try:
            alpha = float(opacity)
        except Exception:
            alpha = 1.0
        if alpha < 0.0:
            alpha = 0.0
        if alpha > 1.0:
            alpha = 1.0
        return Color.fromARGB(int(round(alpha * 255.0)), r, g, b)

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
            # RRGGBB -> AARRGGBB (alpha defaults to 0xFF)
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
    def alpha(self):
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
        return self.alpha / 255.0

    def withAlpha(self, a):
        return Color.fromARGB(a, self.red, self.green, self.blue)

    def withRed(self, r):
        return Color.fromARGB(self.alpha, r, self.green, self.blue)

    def withGreen(self, g):
        return Color.fromARGB(self.alpha, self.red, g, self.blue)

    def withBlue(self, b):
        return Color.fromARGB(self.alpha, self.red, self.green, b)

    def withOpacity(self, opacity):
        return Color.fromRGBO(self.red, self.green, self.blue, opacity)

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
            self.alpha / 255.0,
        )

    def toCSSRGBA(self):
        return "rgba(%d,%d,%d,%.6f)" % (
            self.red,
            self.green,
            self.blue,
            self.opacity,
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
    green = Color(0xFF00FF00)
    blue = Color(0xFF0000FF)
    grey = Color(0xFF888888)
    gray = Color(0xFF888888)
    lightGrey = Color(0xFFCCCCCC)
