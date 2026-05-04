# -*- coding: utf-8 -*-

from .animation import _SUPPORTED_FIELDS, _normalize_duration
from .easing import Easing


def _normalize_values(values):
    result = {}
    if not isinstance(values, dict):
        return result
    for key in _SUPPORTED_FIELDS:
        item = values.get(key)
        if item is None:
            continue
        try:
            result[key] = float(item)
        except Exception:
            pass
    return result


class Transition(object):
    def __init__(self, values=None, duration=200, delay=0, easing=None):
        self.values = _normalize_values(values)
        self.duration = _normalize_duration(duration)
        self.delay = _normalize_duration(delay)
        self.easing = easing or Easing.easeOutQuad


def normalize_animate(animate_prop):
    if animate_prop is None:
        return ({}, 0, 0, Easing.easeOutQuad)
    if isinstance(animate_prop, Transition):
        return (dict(animate_prop.values), animate_prop.duration, animate_prop.delay, animate_prop.easing)
    if isinstance(animate_prop, dict):
        return (_normalize_values(animate_prop), 200, 0, Easing.easeOutQuad)
    return ({}, 0, 0, Easing.easeOutQuad)
