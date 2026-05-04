# -*- coding: utf-8 -*-

from .animation import Animation


def fadeIn(duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'opacity': 0.0}, to={'opacity': 1.0})


def fadeOut(duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'opacity': 1.0}, to={'opacity': 0.0})


def slideInUp(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateY': distance, 'opacity': 0.0}, to={'translateY': 0.0, 'opacity': 1.0})


def slideInDown(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateY': -distance, 'opacity': 0.0}, to={'translateY': 0.0, 'opacity': 1.0})


def slideInLeft(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateX': -distance, 'opacity': 0.0}, to={'translateX': 0.0, 'opacity': 1.0})


def slideInRight(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateX': distance, 'opacity': 0.0}, to={'translateX': 0.0, 'opacity': 1.0})


def slideOutUp(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateY': 0.0, 'opacity': 1.0}, to={'translateY': -distance, 'opacity': 0.0})


def slideOutDown(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateY': 0.0, 'opacity': 1.0}, to={'translateY': distance, 'opacity': 0.0})


def slideOutLeft(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateX': 0.0, 'opacity': 1.0}, to={'translateX': -distance, 'opacity': 0.0})


def slideOutRight(distance=20, duration=300, delay=0, easing=None):
    return Animation(duration=duration, delay=delay, easing=easing, from_={'translateX': 0.0, 'opacity': 1.0}, to={'translateX': distance, 'opacity': 0.0})
