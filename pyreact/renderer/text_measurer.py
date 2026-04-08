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

    _CACHE_LIMIT = 512

    def __init__(self, native_measure=None):
        self._native_measure = native_measure
        self._measure_cache = {}
        self._measure_cache_order = []

    def measure_text(self, content, style, max_width=None):
        """
        Calculate the width and height of the given text with the provided style.
        Returns a dict: {"width": float, "height": float}
        """
        text = self._to_text(content)
        cache_key = self._build_cache_key(text, style, max_width)
        cached = self._measure_cache.get(cache_key)
        if isinstance(cached, dict):
            self._touch_cache_key(cache_key)
            return {
                "width": self._safe_float(cached.get("width"), 0.0),
                "height": self._safe_float(cached.get("height"), 0.0),
            }
        
        # Always prefer native measurement if available
        if callable(self._native_measure):
            try:
                measured = self._native_measure(text, style, max_width=max_width)
                if isinstance(measured, dict):
                    width = self._safe_float(measured.get("width"), 0.0)
                    height = self._safe_float(measured.get("height"), 0.0)
                    if width > 0 and height > 0:
                        result = {"width": width, "height": height}
                        self._store_measurement(cache_key, result)
                        return dict(result)
            except Exception:
                pass

        # Fallback to a very simple heuristic if native measure fails or is not provided.
        # Match runtime semantics: numeric fontSize represents a font size token/value,
        # then runtime converts it to scale via value / 10.
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
            
        result = {
            "width": width,
            "height": line_count * (font_size * 1.2)
        }
        return dict(result)

    def _build_cache_key(self, text, style, max_width):
        if not isinstance(style, dict):
            style = {}

        return (
            text,
            self._normalize_font_size_for_cache(style.get("fontSize")),
            self._normalize_text_align_for_cache(style.get("textAlign")),
            self._normalize_line_padding_for_cache(style.get("linePadding")),
            self._normalize_shadow_for_cache(style.get("shadow")),
            self._safe_float(max_width, 0.0) if max_width is not None else None,
        )

    def _normalize_font_size_for_cache(self, value):
        return self._get_font_size_px({"fontSize": value})

    def _normalize_text_align_for_cache(self, value):
        text_value = self._to_text(value).strip().lower()
        if text_value in ("left", "start"):
            return "left"
        if text_value in ("right", "end"):
            return "right"
        if text_value in ("center", "middle"):
            return "center"
        return None

    def _normalize_line_padding_for_cache(self, value):
        if value is None or isinstance(value, bool):
            return None
        return self._safe_float(value, 0.0)

    def _normalize_shadow_for_cache(self, value):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        text = self._to_text(value).strip().lower()
        if not text:
            return False
        if text in ('false', '0', 'no', 'off', 'none', 'null'):
            return False
        if text in ('true', '1', 'yes', 'on'):
            return True
        return True

    def _touch_cache_key(self, cache_key):
        try:
            self._measure_cache_order.remove(cache_key)
        except ValueError:
            pass
        except Exception:
            return
        self._measure_cache_order.append(cache_key)

    def _store_measurement(self, cache_key, result):
        if not isinstance(result, dict):
            return

        if cache_key in self._measure_cache:
            self._measure_cache[cache_key] = dict(result)
            self._touch_cache_key(cache_key)
            return

        self._measure_cache[cache_key] = dict(result)
        self._measure_cache_order.append(cache_key)
        if len(self._measure_cache_order) <= self._CACHE_LIMIT:
            return

        oldest_key = self._measure_cache_order.pop(0)
        try:
            del self._measure_cache[oldest_key]
        except Exception:
            pass

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
                return float(token) / 10.0
            except Exception:
                return 1.0

        return self._safe_float(font_size, 10.0) / 10.0

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
