import threading

from .fiber import StateSlot
from .fiber import EffectSlot
from .fiber import MemoSlot
from .fiber import RefSlot
from .fiber import _NO_SETTER


_CURRENT_FIBER_KEY = "_pyreact_current_fiber"


try:
    _UNICODE_TYPE = unicode
except NameError:
    _UNICODE_TYPE = str


def _is_primitive_value(value):
    # Conservative bail-out types for state update equality.
    return isinstance(value, (type(None), bool, int, float, str, _UNICODE_TYPE))


def _get_current_fiber():
    thread = threading.current_thread()
    return getattr(thread, _CURRENT_FIBER_KEY, None)


def _set_current_fiber(fiber):
    thread = threading.current_thread()
    setattr(thread, _CURRENT_FIBER_KEY, fiber)


def _clear_current_fiber():
    thread = threading.current_thread()
    if hasattr(thread, _CURRENT_FIBER_KEY):
        setattr(thread, _CURRENT_FIBER_KEY, None)


class _FiberScope(object):
    def __init__(self, fiber):
        self._fiber = fiber
        self._previous = None

    def __enter__(self):
        self._previous = _get_current_fiber()
        _set_current_fiber(self._fiber)
        return self._fiber

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._previous is None:
            _clear_current_fiber()
        else:
            _set_current_fiber(self._previous)
        return False


def with_current_fiber(fiber):
    return _FiberScope(fiber)


def _require_fiber():
    fiber = _get_current_fiber()
    if fiber is None:
        raise RuntimeError("Hooks can only be used while rendering a component")
    return fiber


def _normalize_deps(deps):
    if deps is None:
        return None
    if isinstance(deps, tuple):
        return deps
    if isinstance(deps, list):
        return tuple(deps)
    return (deps,)


def _deps_changed(previous, current):
    if previous is None or current is None:
        return True
    if len(previous) != len(current):
        return True

    idx = 0
    size = len(previous)
    while idx < size:
        if previous[idx] != current[idx]:
            return True
        idx += 1
    return False


def useState(initial_value):
    fiber = _require_fiber()
    slot_index = fiber.consume_hook("state")

    if slot_index >= len(fiber.state_slots):
        slot = StateSlot(initial_value)
        fiber.state_slots.append(slot)
    else:
        slot = fiber.state_slots[slot_index]

    if slot.setter is _NO_SETTER:
        def setter(new_value):
            base_value = slot.value
            if slot.pending_updates:
                base_value = slot.pending_updates[-1]

            next_value = new_value
            if callable(new_value):
                next_value = new_value(base_value)

            # Optimization: if setting to same primitive value, skip rerender.
            # This reduces unnecessary full-tree renders for controlled inputs.
            try:
                if _is_primitive_value(base_value) and _is_primitive_value(next_value) and next_value == base_value:
                    return
            except Exception:
                pass

            slot.pending_updates.append(next_value)
            fiber.pending_state_update = True
            if fiber.rerender_callback is not None:
                fiber.rerender_callback()

        slot.setter = setter

    if slot.pending_updates:
        slot.value = slot.pending_updates[-1]
        slot.pending_updates = []

    return (slot.value, slot.setter)


def useEffect(effect_fn, deps):
    fiber = _require_fiber()
    slot_index = fiber.consume_hook("effect")
    normalized_deps = _normalize_deps(deps)

    if slot_index >= len(fiber.effect_slots):
        slot = EffectSlot(effect_fn, normalized_deps)
        fiber.effect_slots.append(slot)
        return None

    slot = fiber.effect_slots[slot_index]
    changed = _deps_changed(slot.deps, normalized_deps)
    slot.effect_fn = effect_fn
    slot.should_run = changed
    if changed:
        slot.deps = normalized_deps
    return None


def useMemo(factory_fn, deps):
    fiber = _require_fiber()
    slot_index = fiber.consume_hook("memo")
    normalized_deps = _normalize_deps(deps)

    if slot_index >= len(fiber.memo_slots):
        value = factory_fn()
        slot = MemoSlot(value, normalized_deps)
        fiber.memo_slots.append(slot)
        return value

    slot = fiber.memo_slots[slot_index]
    if _deps_changed(slot.deps, normalized_deps):
        slot.value = factory_fn()
        slot.deps = normalized_deps

    return slot.value


def useCallback(callback_fn, deps):
    return useMemo(lambda: callback_fn, deps)


def useRef(initial_value):
    fiber = _require_fiber()
    slot_index = fiber.consume_hook("ref")

    if slot_index >= len(fiber.ref_slots):
        slot = RefSlot(initial_value)
        fiber.ref_slots.append(slot)
    else:
        slot = fiber.ref_slots[slot_index]

    return slot.ref


def run_effects(fiber):
    if fiber is None:
        return

    index = 0
    total = len(fiber.effect_slots)
    while index < total:
        slot = fiber.effect_slots[index]
        if slot.should_run:
            if slot.cleanup is not None:
                slot.cleanup()
                slot.cleanup = None

            cleanup = slot.effect_fn()
            if callable(cleanup):
                slot.cleanup = cleanup
            slot.should_run = False
        index += 1


def cleanup_effects(fiber):
    if fiber is None:
        return

    index = 0
    total = len(fiber.effect_slots)
    while index < total:
        slot = fiber.effect_slots[index]
        if slot.cleanup is not None:
            slot.cleanup()
            slot.cleanup = None
        index += 1
