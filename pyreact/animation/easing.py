# -*- coding: utf-8 -*-

"""Easing functions for declarative animations.

All functions take progress ``t`` in the range [0.0, 1.0] and return the
eased progress. They must satisfy ``f(0) == 0`` and ``f(1) == 1``.
"""


def _clamp01(t):
    if t < 0.0:
        return 0.0
    if t > 1.0:
        return 1.0
    return t


def linear(t):
    return _clamp01(t)


def easeInQuad(t):
    t = _clamp01(t)
    return t * t


def easeOutQuad(t):
    t = _clamp01(t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def easeInOutQuad(t):
    t = _clamp01(t)
    if t < 0.5:
        return 2.0 * t * t
    v = -2.0 * t + 2.0
    return 1.0 - (v * v) / 2.0


def easeInCubic(t):
    t = _clamp01(t)
    return t * t * t


def easeOutCubic(t):
    t = _clamp01(t)
    v = 1.0 - t
    return 1.0 - v * v * v


def easeInOutCubic(t):
    t = _clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    v = -2.0 * t + 2.0
    return 1.0 - (v * v * v) / 2.0


def easeOutBack(t):
    t = _clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    v = t - 1.0
    return 1.0 + c3 * v * v * v + c1 * v * v


def easeInBack(t):
    t = _clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    return c3 * t * t * t - c1 * t * t


class Easing(object):
    """Namespace of common easing presets."""

    linear = staticmethod(linear)
    easeInQuad = staticmethod(easeInQuad)
    easeOutQuad = staticmethod(easeOutQuad)
    easeInOutQuad = staticmethod(easeInOutQuad)
    easeInCubic = staticmethod(easeInCubic)
    easeOutCubic = staticmethod(easeOutCubic)
    easeInOutCubic = staticmethod(easeInOutCubic)
    easeOutBack = staticmethod(easeOutBack)
    easeInBack = staticmethod(easeInBack)

    # Friendly aliases matching Framer Motion / CSS names.
    easeIn = staticmethod(easeInQuad)
    easeOut = staticmethod(easeOutQuad)
    easeInOut = staticmethod(easeInOutQuad)
