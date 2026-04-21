# -*- coding: utf-8 -*-

from .animation import _filter_values
from .easing import Easing


class Transition(object):
    """Options wrapper for the ``animate`` prop on ``Animated``.

    Use this when you need to customize duration / easing / delay for a
    continuous transition; otherwise pass a plain dict of target values
    and defaults (200ms, easeOut) will apply.
    """

    def __init__(self, values=None, duration=200, delay=0, easing=None):
        try:
            self.duration = int(duration)
        except Exception:
            self.duration = 200
        if self.duration < 0:
            self.duration = 0
        try:
            self.delay = int(delay)
        except Exception:
            self.delay = 0
        if self.delay < 0:
            self.delay = 0
        self.easing = easing if callable(easing) else Easing.easeOutQuad
        self.values = _filter_values(values)

    def __repr__(self):
        return "Transition(values=%s, duration=%s)" % (self.values, self.duration)


def normalize_animate(animate_prop):
    """Return (values_dict, duration, delay, easing) from a user-supplied animate prop."""
    if animate_prop is None:
        return {}, 200, 0, Easing.easeOutQuad
    if isinstance(animate_prop, Transition):
        return dict(animate_prop.values), animate_prop.duration, animate_prop.delay, animate_prop.easing
    if isinstance(animate_prop, dict):
        return _filter_values(animate_prop), 200, 0, Easing.easeOutQuad
    return {}, 200, 0, Easing.easeOutQuad
