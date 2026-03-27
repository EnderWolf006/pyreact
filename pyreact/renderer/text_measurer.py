# -*- coding: utf-8 -*-

try:
    _UNICODE_TYPE = unicode
    _TEXT_TYPES = (str, unicode)
except NameError:
    _UNICODE_TYPE = str
    _TEXT_TYPES = (str,)


class TextMeasurer(object):
    """
    TextMeasurer handles text size calculations by delegating to the native 
    Minecraft UI system.
    """
    
    # In NetEase UI runtime we treat fontSize as a *scale factor*.
    # Native label API uses SetTextFontSize(scale).
    BASE_FONT_PX = 14.0

    def __init__(self, native_measure=None):
        self._native_measure = native_measure

    def measure_text(self, content, style, max_width=None):
        """
        Calculate the width and height of the given text with the provided style.
        Returns a dict: {"width": float, "height": float}
        """
        text = self._to_text(content)
        
        # Always prefer native measurement if available
        if callable(self._native_measure):
            try:
                measured = self._native_measure(text, style, max_width=max_width)
                if isinstance(measured, dict):
                    width = self._safe_float(measured.get("width"), 0.0)
                    height = self._safe_float(measured.get("height"), 0.0)
                    if width > 0 and height > 0:
                        return {"width": width, "height": height}
            except Exception:
                pass

        # Fallback to a very simple heuristic if native measure fails or is not provided.
        # Use fontSize as scale factor (same semantics as native SetTextFontSize).
        font_size = self._get_font_size_px(style)
        
        # Simple estimation: 
        # - Latin/Symbols: ~0.6 * font_size
        # - CJK: ~1.0 * font_size
        width = 0.0
        for ch in text:
            code = ord(ch)
            if code < 128:
                width += font_size * 0.6
            else:
                width += font_size * 1.0
        
        # Basic line wrapping estimation
        line_count = 1
        max_w = self._safe_float(max_width, 0.0)
        if max_w > 0 and width > max_w:
            line_count = int(width / max_w) + 1
            width = max_w
            
        return {
            "width": width,
            "height": line_count * (font_size * 1.2)
        }

    def _get_font_size_scale(self, style):
        if not isinstance(style, dict):
            return 1.0

        font_size = style.get("fontSize")
        if font_size is None:
            return 1.0

        if isinstance(font_size, bool):
            return 1.0

        if isinstance(font_size, _TEXT_TYPES):
            token = self._to_text(font_size)
            try:
                token = token.strip()
            except Exception:
                pass
            try:
                return float(token)
            except Exception:
                return 1.0

        # Numeric fontSize is treated as scale in runtime
        return self._safe_float(font_size, 1.0)

    def _get_font_size_px(self, style):
        scale = self._get_font_size_scale(style)
        if scale <= 0.0:
            scale = 1.0
        return float(self.BASE_FONT_PX) * float(scale)

    def _to_text(self, value):
        if value is None:
            return _UNICODE_TYPE("")

        # Prefer unicode for correct width estimation per codepoint.
        if isinstance(value, _UNICODE_TYPE):
            return value

        # Python2: bytes -> try utf-8 decode. Python3: str already handled above.
        if isinstance(value, str) and _UNICODE_TYPE is not str:
            try:
                return value.decode('utf-8')
            except Exception:
                try:
                    return _UNICODE_TYPE(value)
                except Exception:
                    return _UNICODE_TYPE("")

        try:
            return _UNICODE_TYPE(value)
        except Exception:
            try:
                return _UNICODE_TYPE("%s" % value)
            except Exception:
                return _UNICODE_TYPE("")

    def _safe_float(self, value, default_value=0.0):
        try:
            return float(value)
        except Exception:
            return float(default_value)
