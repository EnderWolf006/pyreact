# -*- coding: utf-8 -*-

from .easing import Easing


_SUPPORTED_FIELDS = ("opacity", "alpha", "translateX", "translateY", "width", "height")


def _normalize_number_map(value):
    result = {}
    if not isinstance(value, dict):
        return result
    for key in _SUPPORTED_FIELDS:
        item = value.get(key)
        if item is None:
            continue
        try:
            result[key] = float(item)
        except Exception:
            pass
    return result


def _normalize_duration(value):
    try:
        value = int(value)
    except Exception:
        value = 0
    if value < 0:
        value = 0
    return value


class Animation(object):
    def __init__(self, duration=300, delay=0, easing=None, from_=None, to=None, onComplete=None):
        self.duration = _normalize_duration(duration)
        self.delay = _normalize_duration(delay)
        self.easing = easing or Easing.easeOutQuad
        self.from_ = _normalize_number_map(from_)
        self.to = _normalize_number_map(to)
        self.onComplete = onComplete

    def get_property_keys(self):
        keys = {}
        for key in self.from_:
            keys[key] = True
        for key in self.to:
            keys[key] = True
        result = list(keys.keys())
        result.sort()
        return result

    def clone(self, **overrides):
        duration = self.duration
        delay = self.delay
        easing = self.easing
        from_ = dict(self.from_)
        to = dict(self.to)
        onComplete = self.onComplete
        values = {}
        values['duration'] = duration
        values['delay'] = delay
        values['easing'] = easing
        values['from_'] = from_
        values['to'] = to
        values['onComplete'] = onComplete
        values.update(overrides)
        return Animation(
            duration=values.get('duration', self.duration),
            delay=values.get('delay', self.delay),
            easing=values.get('easing'),
            from_=values.get('from_'),
            to=values.get('to'),
            onComplete=values.get('onComplete'),
        )

    def __repr__(self):
        return "Animation(duration=%s, delay=%s, from_=%r, to=%r)" % (
            self.duration,
            self.delay,
            self.from_,
            self.to,
        )
