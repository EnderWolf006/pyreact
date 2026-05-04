# -*- coding: utf-8 -*-


def _clamp01(value):
    try:
        value = float(value)
    except Exception:
        value = 0.0
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def linear(t):
    return _clamp01(t)


def easeInQuad(t):
    t = _clamp01(t)
    return t * t


def easeOutQuad(t):
    t = _clamp01(t)
    return t * (2.0 - t)


def easeInOutQuad(t):
    t = _clamp01(t)
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t


def easeInCubic(t):
    t = _clamp01(t)
    return t * t * t


def easeOutCubic(t):
    t = _clamp01(t) - 1.0
    return t * t * t + 1.0


def easeInOutCubic(t):
    t = _clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    t = (2.0 * t) - 2.0
    return 0.5 * t * t * t + 1.0


def easeOutBack(t):
    t = _clamp01(t) - 1.0
    c = 1.70158
    return t * t * ((c + 1.0) * t + c) + 1.0


def easeInBack(t):
    t = _clamp01(t)
    c = 1.70158
    return t * t * ((c + 1.0) * t - c)


class Easing(object):
    linear = staticmethod(linear)
    easeInQuad = staticmethod(easeInQuad)
    easeOutQuad = staticmethod(easeOutQuad)
    easeInOutQuad = staticmethod(easeInOutQuad)
    easeInCubic = staticmethod(easeInCubic)
    easeOutCubic = staticmethod(easeOutCubic)
    easeInOutCubic = staticmethod(easeInOutCubic)
    easeOutBack = staticmethod(easeOutBack)
    easeInBack = staticmethod(easeInBack)
    easeIn = staticmethod(easeInQuad)
    easeOut = staticmethod(easeOutQuad)
    easeInOut = staticmethod(easeInOutQuad)
