# -*- coding: utf-8 -*-

from .animation import Animation
from .easing import Easing
from .transition import Transition, normalize_animate
from .presets import (
    fadeIn,
    fadeOut,
    slideInUp,
    slideInDown,
    slideInLeft,
    slideInRight,
    slideOutUp,
    slideOutDown,
    slideOutLeft,
    slideOutRight,
)


__all__ = [
    'Animation',
    'Easing',
    'Transition',
    'normalize_animate',
    'fadeIn',
    'fadeOut',
    'slideInUp',
    'slideInDown',
    'slideInLeft',
    'slideInRight',
    'slideOutUp',
    'slideOutDown',
    'slideOutLeft',
    'slideOutRight',
]
