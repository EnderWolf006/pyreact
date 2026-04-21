# -*- coding: utf-8 -*-

from .animation import Animation
from .easing import Easing


def fadeIn(duration=300, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeOutQuad,
        from_={"opacity": 0.0},
        to={"opacity": 1.0},
    )


def fadeOut(duration=200, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeInQuad,
        from_={"opacity": 1.0},
        to={"opacity": 0.0},
    )


def slideInUp(distance=20, duration=300, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeOutCubic,
        from_={"opacity": 0.0, "translateY": float(distance)},
        to={"opacity": 1.0, "translateY": 0.0},
    )


def slideInDown(distance=20, duration=300, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeOutCubic,
        from_={"opacity": 0.0, "translateY": -float(distance)},
        to={"opacity": 1.0, "translateY": 0.0},
    )


def slideInLeft(distance=20, duration=300, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeOutCubic,
        from_={"opacity": 0.0, "translateX": float(distance)},
        to={"opacity": 1.0, "translateX": 0.0},
    )


def slideInRight(distance=20, duration=300, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeOutCubic,
        from_={"opacity": 0.0, "translateX": -float(distance)},
        to={"opacity": 1.0, "translateX": 0.0},
    )


def slideOutUp(distance=20, duration=200, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeInQuad,
        from_={"opacity": 1.0, "translateY": 0.0},
        to={"opacity": 0.0, "translateY": -float(distance)},
    )


def slideOutDown(distance=20, duration=200, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeInQuad,
        from_={"opacity": 1.0, "translateY": 0.0},
        to={"opacity": 0.0, "translateY": float(distance)},
    )


def slideOutLeft(distance=20, duration=200, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeInQuad,
        from_={"opacity": 1.0, "translateX": 0.0},
        to={"opacity": 0.0, "translateX": -float(distance)},
    )


def slideOutRight(distance=20, duration=200, delay=0, easing=None):
    return Animation(
        duration=duration,
        delay=delay,
        easing=easing or Easing.easeInQuad,
        from_={"opacity": 1.0, "translateX": 0.0},
        to={"opacity": 0.0, "translateX": float(distance)},
    )
