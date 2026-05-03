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
        self._measure_cache = {}
        self._measure_cache_order = []
        self._perf_stats = self._new_perf_stats()

    def _new_perf_stats(self):
        return {
            "calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "native_hits": 0,
            "fallback_hits": 0,
        }

    def reset_perf_stats(self):
        self._perf_stats = self._new_perf_stats()

    def get_perf_stats(self):
        stats = getattr(self, '_perf_stats', None)
        if not isinstance(stats, dict):
            return self._new_perf_stats()
        return dict(stats)

    def _make_cache_key(self, text, style, max_width):
        items = []
        if isinstance(style, dict):
            for key in sorted(style.keys()):
                items.append((key, self._to_text(style.get(key))))
        return (text, tuple(items), self._safe_float(max_width, 0.0))

    def measure_text(self, content, style, max_width=None):
        """
        Calculate the width and height of the given text with the provided style.
        Returns a dict: {"width": float, "height": float}
        """
        text = self._to_text(content)
        stats = getattr(self, '_perf_stats', None)
        if not isinstance(stats, dict):
            stats = self._new_perf_stats()
            self._perf_stats = stats
        stats["calls"] = stats.get("calls", 0) + 1
        cache_key = self._make_cache_key(text, style, max_width)
        cached = self._measure_cache.get(cache_key)
        if cached is not None:
            stats["cache_hits"] = stats.get("cache_hits", 0) + 1
            return dict(cached)
        stats["cache_misses"] = stats.get("cache_misses", 0) + 1

        measured = self._native_measure(text, style, max_width=max_width)
        if isinstance(measured, dict):
            width = self._safe_float(measured.get("width"), 0.0)
            height = self._safe_float(measured.get("height"), 0.0)
            if width > 0 and height > 0:
                result = {"width": width, "height": height}
                self._remember_measure(cache_key, result)
                stats["native_hits"] = stats.get("native_hits", 0) + 1
                return dict(result)

        result = {"width": 100.0, "height": 20.0}
        self._remember_measure(cache_key, result)
        return dict(result)

    def _remember_measure(self, cache_key, result):
        cache = self._measure_cache
        order = getattr(self, '_measure_cache_order', None)
        if not isinstance(order, list):
            order = []
            self._measure_cache_order = order
        if cache_key not in cache:
            order.append(cache_key)
        if len(cache) >= 1024:
            remove_count = 128
            while remove_count > 0 and order:
                old_key = order.pop(0)
                cache.pop(old_key, None)
                remove_count -= 1
        cache[cache_key] = dict(result)

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
