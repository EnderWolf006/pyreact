_NO_SETTER = object()


class HookSlot(object):
    def __init__(self):
        self.mounted = True


class StateSlot(HookSlot):
    def __init__(self, initial_value):
        HookSlot.__init__(self)
        self.value = initial_value
        self.pending_updates = []
        self.setter = _NO_SETTER


class EffectSlot(HookSlot):
    def __init__(self, effect_fn, deps):
        HookSlot.__init__(self)
        self.effect_fn = effect_fn
        self.deps = deps
        self.cleanup = None
        self.should_run = True


class MemoSlot(HookSlot):
    def __init__(self, value, deps):
        HookSlot.__init__(self)
        self.value = value
        self.deps = deps


class RefObject(object):
    def __init__(self, current=None):
        self.current = current


class RefSlot(HookSlot):
    def __init__(self, initial_value):
        HookSlot.__init__(self)
        self.ref = RefObject(initial_value)


class Fiber(object):
    def __init__(self, component_fn, props=None, rerender_callback=None):
        self.component_fn = component_fn
        self.props = props or {}

        self.state_slots = []
        self.effect_slots = []
        self.memo_slots = []
        self.ref_slots = []

        self.pending_state_update = False
        self.rerender_callback = rerender_callback
        self.children_fibers = []

        self._hook_kinds = []
        self._hook_index = 0
        self._state_cursor = 0
        self._effect_cursor = 0
        self._memo_cursor = 0
        self._ref_cursor = 0

    def begin_render(self):
        self._hook_index = 0
        self._state_cursor = 0
        self._effect_cursor = 0
        self._memo_cursor = 0
        self._ref_cursor = 0

    def abort_render(self):
        self._hook_index = 0
        self._state_cursor = 0
        self._effect_cursor = 0
        self._memo_cursor = 0
        self._ref_cursor = 0

    def consume_hook(self, kind):
        idx = self._hook_index
        if idx < len(self._hook_kinds):
            expected = self._hook_kinds[idx]
            if expected != kind:
                raise RuntimeError(
                    "Hook order mismatch at index %s: expected %s, got %s"
                    % (idx, expected, kind)
                )
        else:
            self._hook_kinds.append(kind)

        self._hook_index += 1

        if kind == "state":
            slot_index = self._state_cursor
            self._state_cursor += 1
            return slot_index
        if kind == "effect":
            slot_index = self._effect_cursor
            self._effect_cursor += 1
            return slot_index
        if kind == "memo":
            slot_index = self._memo_cursor
            self._memo_cursor += 1
            return slot_index
        if kind == "ref":
            slot_index = self._ref_cursor
            self._ref_cursor += 1
            return slot_index

        raise RuntimeError("Unknown hook kind: %s" % kind)

    def finish_render(self):
        if self._hook_index != len(self._hook_kinds):
            raise RuntimeError(
                "Hook count mismatch: expected %s, got %s"
                % (len(self._hook_kinds), self._hook_index)
            )
