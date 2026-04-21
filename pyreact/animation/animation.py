# -*- coding: utf-8 -*-

from .easing import Easing


_SUPPORTED_FIELDS = ("opacity", "translateX", "translateY", "width", "height")


class Animation(object):
    """Declarative animation descriptor.

    Fields supported in ``from_`` / ``to``:
    ``opacity``, ``translateX``, ``translateY``, ``width``, ``height``.
    """

    def __init__(
        self,
        duration=300,
        delay=0,
        easing=None,
        from_=None,
        to=None,
        onComplete=None,
    ):
        try:
            self.duration = int(duration)
        except Exception:
            self.duration = 300
        if self.duration < 0:
            self.duration = 0

        try:
            self.delay = int(delay)
        except Exception:
            self.delay = 0
        if self.delay < 0:
            self.delay = 0

        self.easing = easing if callable(easing) else Easing.easeOutQuad
        self.from_ = _filter_values(from_)
        self.to = _filter_values(to)
        self.onComplete = onComplete if callable(onComplete) else None

    def get_property_keys(self):
        keys = set()
        for k in self.from_:
            keys.add(k)
        for k in self.to:
            keys.add(k)
        return keys

    def clone(self, **overrides):
        init = {
            "duration": self.duration,
            "delay": self.delay,
            "easing": self.easing,
            "from_": dict(self.from_),
            "to": dict(self.to),
            "onComplete": self.onComplete,
        }
        for k, v in overrides.items():
            init[k] = v
        return Animation(**init)

    def __repr__(self):
        return "Animation(duration=%s, delay=%s, from=%s, to=%s)" % (
            self.duration, self.delay, self.from_, self.to,
        )


def _filter_values(values):
    if not isinstance(values, dict):
        return {}
    out = {}
    for key, raw in values.items():
        if key not in _SUPPORTED_FIELDS:
            continue
        try:
            out[key] = float(raw)
        except Exception:
            pass
    return out
