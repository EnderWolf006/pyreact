# -*- coding: utf-8 -*-

"""Runtime animation support for Pyreact.

Drives declarative enter / exit / animate animations entirely in Python.
A per-frame tick is driven by ``GameRenderTickEvent`` (delivered by
``PyreactRuntimeClientSystem``). On each tick, active animation states
are advanced, interpolated values are applied directly via the existing
``_safe_set_alpha`` / ``_safe_set_position`` / ``_safe_set_size``
helpers, and finished states are reclaimed.

Exit animations delay native removal: the target ``RemoveChildControl``
is deferred via ``expected_children_by_parent`` in
``_clear_root_children`` until the animation completes.
"""

import time

from pyreact.animation.transition import normalize_animate

try:
    import mod.client.extraClientApi as _clientApi
except Exception:
    _clientApi = None


def _perf_now():
    perf_counter = getattr(time, 'perf_counter', None)
    if callable(perf_counter):
        return perf_counter()
    clock = getattr(time, 'clock', None)
    if callable(clock):
        return clock()
    return time.time()


def _anim_log(msg):
    try:
        print('[PyreactAnim] %s' % msg)
    except Exception:
        pass


_FIELD_TO_LOCK = {
    "opacity": "opacity",
    "translateX": "position",
    "translateY": "position",
    "width": "size",
    "height": "size",
}


def _lock_fields_for(properties):
    out = set()
    for f in properties:
        lock_name = _FIELD_TO_LOCK.get(f)
        if lock_name:
            out.add(lock_name)
    return out


def _layout_snapshot(layout):
    if layout is None:
        return None
    return {
        "x": float(getattr(layout, "x", 0.0) or 0.0),
        "y": float(getattr(layout, "y", 0.0) or 0.0),
        "width": float(getattr(layout, "width", 0.0) or 0.0),
        "height": float(getattr(layout, "height", 0.0) or 0.0),
    }


class AnimationState(object):
    __slots__ = (
        "path",
        "node_id",
        "node_type",
        "kind",
        "duration",
        "delay",
        "easing",
        "from_values",
        "to_values",
        "start_time",
        "shadow_layout",
        "on_complete",
        "properties",
        "locked_kinds",
        "grid_info",
    )

    def __init__(self, path, node_id, node_type, kind, duration, delay, easing,
                 from_values, to_values, start_time, shadow_layout, on_complete=None, grid_info=None):
        self.path = path
        self.node_id = node_id
        self.node_type = node_type
        self.kind = kind
        self.duration = int(duration or 0)
        self.delay = int(delay or 0)
        self.easing = easing
        self.from_values = dict(from_values or {})
        self.to_values = dict(to_values or {})
        self.start_time = float(start_time)
        self.shadow_layout = shadow_layout
        self.on_complete = on_complete if callable(on_complete) else None
        props = set()
        for k in self.from_values:
            props.add(k)
        for k in self.to_values:
            props.add(k)
        self.properties = props
        self.locked_kinds = _lock_fields_for(props)
        self.grid_info = grid_info


class AnimationManager(object):
    """Per-runtime animation registry.

    The manager is passive with respect to time — callers (runtime) feed
    it the current timestamp via ``tick``. State keys combine node_id
    and kind so a single node can run enter + animate concurrently (the
    latter winning field conflicts because it's registered later).
    """

    def __init__(self):
        # key = (node_id, kind) -> AnimationState
        self.states = {}
        # path -> set of lock kinds currently in effect ('opacity', 'position', 'size')
        self.locked_fields_by_path = {}
        # node_id -> {field: last-applied value} for animate starting points
        self.last_applied_values = {}
        # node_id -> {field: last target value} for animate change detection
        self.last_animate_targets = {}
        # parent_path -> {control_name: True} for exiting nodes to keep alive
        # (root/scroll direct children only; grid pool slots use exiting_grid_slots)
        self.exiting_children_by_parent = {}
        # path -> AnimationState (exit) for quick lookup during _clear_root_children
        self.exiting_states_by_path = {}
        # grid_path -> set(int index) for grid pool slots currently animating out
        self.exiting_grid_slots = {}
        # node_ids seen in at least one render — used by is_new detection
        self.seen_node_ids = set()

    def has_active(self):
        return bool(self.states)

    def clear(self):
        self.states = {}
        self.locked_fields_by_path = {}
        self.last_applied_values = {}
        self.last_animate_targets = {}
        self.exiting_children_by_parent = {}
        self.exiting_states_by_path = {}
        self.exiting_grid_slots = {}
        self.seen_node_ids = set()

    def is_field_locked(self, path, lock_kind):
        s = self.locked_fields_by_path.get(path)
        if not s:
            return False
        return lock_kind in s

    def _rebuild_locks(self):
        locks = {}
        for state in self.states.values():
            if not state.locked_kinds:
                continue
            bucket = locks.get(state.path)
            if bucket is None:
                bucket = set()
                locks[state.path] = bucket
            for k in state.locked_kinds:
                bucket.add(k)
        self.locked_fields_by_path = locks

    def _cancel_exit_state(self, node_id):
        """Remove any active exit state for node_id and detach bookkeeping."""
        key = (node_id, 'exit')
        old = self.states.pop(key, None)
        if old is None:
            return None
        path = old.path
        try:
            del self.exiting_states_by_path[path]
        except Exception:
            pass
        grid_info = getattr(old, 'grid_info', None)
        if isinstance(grid_info, dict):
            grid_path = grid_info.get('grid_path')
            idx = grid_info.get('index')
            bucket = self.exiting_grid_slots.get(grid_path) if grid_path else None
            if bucket is not None:
                try:
                    bucket.discard(int(idx))
                except Exception:
                    pass
                if not bucket:
                    try:
                        del self.exiting_grid_slots[grid_path]
                    except Exception:
                        pass
        else:
            last_sep = path.rfind('/')
            if last_sep > 0:
                parent_path = path[:last_sep]
                child_name = path[last_sep + 1:]
                pb = self.exiting_children_by_parent.get(parent_path)
                if isinstance(pb, dict):
                    try:
                        del pb[child_name]
                    except Exception:
                        pass
                    if not pb:
                        try:
                            del self.exiting_children_by_parent[parent_path]
                        except Exception:
                            pass
        return old

    def register_enter(self, path, node_id, node_type, animation, shadow_layout, now):
        if animation is None:
            return
        # If the node is mid-exit and user reversed, start enter from the
        # current applied value so the tween is continuous.
        current = self.last_applied_values.get(node_id) or {}
        from_values = dict(animation.from_)
        for field in list(from_values.keys()):
            if field in current:
                from_values[field] = current[field]
        # Cancel any concurrent exit — enter takes over.
        self._cancel_exit_state(node_id)
        state = AnimationState(
            path=path,
            node_id=node_id,
            node_type=node_type,
            kind="enter",
            duration=animation.duration,
            delay=animation.delay,
            easing=animation.easing,
            from_values=from_values,
            to_values=animation.to,
            start_time=now,
            shadow_layout=_layout_snapshot(shadow_layout),
            on_complete=animation.onComplete,
        )
        self._replace_state(state)
        _anim_log('register_enter node=%s path=%s dur=%dms from=%s to=%s' % (
            node_id, path, animation.duration, from_values, animation.to,
        ))

    def register_exit(self, path, parent_path, child_name, node_id, node_type, animation, shadow_layout, now, grid_info=None):
        if animation is None:
            return
        # Start exit from current applied values so a mid-enter reversal is
        # smooth (fadeOut from 0.5 → 0 instead of snapping 1.0 → 0).
        current = self.last_applied_values.get(node_id) or {}
        from_values = dict(animation.from_)
        for field in list(from_values.keys()):
            if field in current:
                from_values[field] = current[field]
        # Cancel any concurrent enter / animate — exit takes over.
        ekey = (node_id, 'enter')
        if ekey in self.states:
            try:
                del self.states[ekey]
            except Exception:
                pass
        akey = (node_id, 'animate')
        if akey in self.states:
            try:
                del self.states[akey]
            except Exception:
                pass
        state = AnimationState(
            path=path,
            node_id=node_id,
            node_type=node_type,
            kind="exit",
            duration=animation.duration,
            delay=animation.delay,
            easing=animation.easing,
            from_values=from_values,
            to_values=animation.to,
            start_time=now,
            shadow_layout=_layout_snapshot(shadow_layout),
            on_complete=animation.onComplete,
            grid_info=grid_info,
        )
        self._replace_state(state)
        self.exiting_states_by_path[path] = state
        if grid_info is not None:
            grid_path = grid_info.get('grid_path') if isinstance(grid_info, dict) else None
            idx = grid_info.get('index') if isinstance(grid_info, dict) else None
            if grid_path and idx:
                bucket = self.exiting_grid_slots.get(grid_path)
                if bucket is None:
                    bucket = set()
                    self.exiting_grid_slots[grid_path] = bucket
                try:
                    bucket.add(int(idx))
                except Exception:
                    pass
        else:
            bucket = self.exiting_children_by_parent.get(parent_path)
            if bucket is None:
                bucket = {}
                self.exiting_children_by_parent[parent_path] = bucket
            bucket[child_name] = True
        _anim_log('register_exit node=%s path=%s parent=%s grid=%s dur=%dms from=%s to=%s' % (
            node_id, path, parent_path, bool(grid_info), animation.duration, from_values, animation.to,
        ))

    def register_animate(self, path, node_id, node_type, target_values, duration, delay, easing, shadow_layout, now):
        if not target_values:
            return
        prev_targets = self.last_animate_targets.get(node_id) or {}
        same = True
        for field, v in target_values.items():
            if prev_targets.get(field) != v:
                same = False
                break
        if same and len(prev_targets) == len(target_values):
            return
        # Tween from currently-applied value to new targets.
        current = self.last_applied_values.get(node_id) or {}
        from_values = {}
        for field, target in target_values.items():
            if field in current:
                from_values[field] = current[field]
            elif field in prev_targets:
                from_values[field] = prev_targets[field]
            else:
                from_values[field] = target
        state = AnimationState(
            path=path,
            node_id=node_id,
            node_type=node_type,
            kind="animate",
            duration=duration,
            delay=delay,
            easing=easing,
            from_values=from_values,
            to_values=target_values,
            start_time=now,
            shadow_layout=_layout_snapshot(shadow_layout),
            on_complete=None,
        )
        self._replace_state(state)
        self.last_animate_targets[node_id] = dict(target_values)
        _anim_log('register_animate node=%s path=%s target=%s from=%s dur=%dms' % (
            node_id, path, target_values, from_values, duration,
        ))

    def register_auto_layout(self, path, node_id, node_type, from_values, shadow_layout, now, duration=280, easing=None):
        """Automatic translate tween triggered when a live node's layout
        position shifts (e.g. a sibling got removed and children collapsed
        upwards).

        ``from_values`` is the offset the node starts at relative to its
        new layout position — e.g. ``{translateY: +32}`` means "start 32px
        below the new position, glide up to 0". Tweens always target 0.
        """
        if not from_values:
            return
        if easing is None:
            from pyreact.animation.easing import Easing as _E
            easing = _E.easeOutCubic
        to_values = {}
        for k in from_values:
            to_values[k] = 0.0
        state = AnimationState(
            path=path,
            node_id=node_id,
            node_type=node_type,
            kind="animate",
            duration=int(duration),
            delay=0,
            easing=easing,
            from_values=dict(from_values),
            to_values=to_values,
            start_time=now,
            shadow_layout=_layout_snapshot(shadow_layout),
            on_complete=None,
        )
        self._replace_state(state)
        # Treat 0 as the "current target" for these fields so the next render
        # with no translate will hit the same-target early-return.
        self.last_animate_targets[node_id] = dict(to_values)
        _anim_log('register_auto_layout node=%s path=%s offset=%s dur=%dms' % (
            node_id, path, from_values, int(duration),
        ))

    def clear_animate(self, node_id):
        if node_id in self.last_animate_targets:
            try:
                del self.last_animate_targets[node_id]
            except Exception:
                pass
        key = (node_id, "animate")
        if key in self.states:
            try:
                del self.states[key]
            except Exception:
                pass
            self._rebuild_locks()

    def _replace_state(self, state):
        key = (state.node_id, state.kind)
        self.states[key] = state
        self._rebuild_locks()

    def retarget_paths(self, path_by_node_id):
        """Update ``state.path`` and ``shadow_layout`` for still-active states.

        Called at render time to keep states aligned with the current
        flat entry paths / layouts (positional node_ids may shift).
        """
        if not isinstance(path_by_node_id, dict):
            return
        changed = False
        for key, state in self.states.items():
            if state.kind == "exit":
                continue
            entry = path_by_node_id.get(state.node_id)
            if not entry:
                continue
            new_path, new_shadow = entry
            if new_path and new_path != state.path:
                state.path = new_path
                changed = True
            if new_shadow is not None:
                state.shadow_layout = _layout_snapshot(new_shadow)
        if changed:
            self._rebuild_locks()

    def drop_node(self, node_id):
        keys = [k for k in self.states if k[0] == node_id]
        changed = False
        for key in keys:
            state = self.states.pop(key, None)
            if state is not None:
                changed = True
                if state.kind == "exit":
                    try:
                        del self.exiting_states_by_path[state.path]
                    except Exception:
                        pass
                    grid_info = getattr(state, 'grid_info', None)
                    if isinstance(grid_info, dict):
                        grid_path = grid_info.get('grid_path')
                        idx = grid_info.get('index')
                        bucket = self.exiting_grid_slots.get(grid_path) if grid_path else None
                        if bucket is not None:
                            try:
                                bucket.discard(int(idx))
                            except Exception:
                                pass
                            if not bucket:
                                try:
                                    del self.exiting_grid_slots[grid_path]
                                except Exception:
                                    pass
                    else:
                        # Clear this node's entry from the parent→children bucket too.
                        path = state.path
                        last_sep = path.rfind('/')
                        if last_sep > 0:
                            parent_path = path[:last_sep]
                            child_name = path[last_sep + 1:]
                            pbucket = self.exiting_children_by_parent.get(parent_path)
                            if isinstance(pbucket, dict):
                                try:
                                    del pbucket[child_name]
                                except Exception:
                                    pass
                                if not pbucket:
                                    try:
                                        del self.exiting_children_by_parent[parent_path]
                                    except Exception:
                                        pass
        if changed:
            self._rebuild_locks()
        if node_id in self.last_applied_values:
            try:
                del self.last_applied_values[node_id]
            except Exception:
                pass
        if node_id in self.last_animate_targets:
            try:
                del self.last_animate_targets[node_id]
            except Exception:
                pass
        self.seen_node_ids.discard(node_id)

    def gc_seen_node_ids(self, live_node_ids):
        if not isinstance(live_node_ids, (set, frozenset)):
            try:
                live_node_ids = set(live_node_ids or [])
            except Exception:
                return
        exiting_ids = set(k[0] for k in self.states.keys() if k[1] == 'exit')
        keep = live_node_ids | exiting_ids
        self.seen_node_ids = self.seen_node_ids & keep
        # Also drop per-node tracking for nodes that went away — otherwise a
        # node re-mounting under the same node_id would hit the "same target"
        # early-return in register_animate and never get a fresh tween, even
        # though its native alpha has been reset by the grid pool.
        for nid in list(self.last_applied_values.keys()):
            if nid not in keep:
                try:
                    del self.last_applied_values[nid]
                except Exception:
                    pass
        for nid in list(self.last_animate_targets.keys()):
            if nid not in keep:
                try:
                    del self.last_animate_targets[nid]
                except Exception:
                    pass

    def step(self, state, now):
        """Compute the interpolated values for ``state`` at ``now``.

        Returns (values_dict, progress_01, finished_bool).
        """
        elapsed_ms = (now - state.start_time) * 1000.0 - state.delay
        if elapsed_ms < 0.0:
            # Before the delay window; hold from_values.
            return dict(state.from_values), 0.0, False
        if state.duration <= 0:
            return dict(state.to_values), 1.0, True
        progress = elapsed_ms / float(state.duration)
        if progress >= 1.0:
            return dict(state.to_values), 1.0, True
        try:
            eased = state.easing(progress)
        except Exception:
            eased = progress
        values = {}
        for field in state.properties:
            to_val = state.to_values.get(field)
            fr_val = state.from_values.get(field, to_val)
            if fr_val is None or to_val is None:
                continue
            values[field] = fr_val + (to_val - fr_val) * eased
        return values, progress, False


class RuntimeAnimationMixin(object):
    """Mixin wired into ``PyreactNativeRuntime``.

    Owns the ``AnimationManager`` instance and implements the per-frame
    tick plus helpers to apply interpolated values via existing native
    helpers.
    """

    def _init_animation_state(self):
        if not hasattr(self, '_animation_manager') or self._animation_manager is None:
            self._animation_manager = AnimationManager()
        self._anim_tick_count = 0
        self._anim_tick_first_logged = False
        self._anim_tick_last_log_time = 0.0
        self._anim_apply_last_log_time = 0.0
        self._anim_applied_hit_count = 0
        self._anim_fallback_tick_pending = False
        self._anim_fallback_tick_logged = False

    def _reset_animation_state(self):
        mgr = getattr(self, '_animation_manager', None)
        if mgr is not None:
            mgr.clear()
        self._anim_tick_count = 0
        self._anim_tick_first_logged = False
        self._anim_tick_last_log_time = 0.0
        self._anim_apply_last_log_time = 0.0
        self._anim_applied_hit_count = 0
        self._anim_fallback_tick_pending = False
        self._anim_fallback_tick_logged = False

    def _get_animation_manager(self):
        mgr = getattr(self, '_animation_manager', None)
        if mgr is None:
            mgr = AnimationManager()
            self._animation_manager = mgr
        return mgr

    def is_animation_field_locked(self, path, lock_kind):
        mgr = getattr(self, '_animation_manager', None)
        if mgr is None:
            return False
        return mgr.is_field_locked(path, lock_kind)

    def _cleanup_stale_exiting_widget(self, state):
        """Tear down the native control for an exit state that got cancelled
        by a remount (user toggled back before the animation finished).

        Grid-pool widgets get hidden (pool will reuse them); non-grid widgets
        are removed outright. Without this step the old control would stay
        visible next to the newly-mounted control → "two copies" visible.
        """
        if state is None:
            return
        path = getattr(state, 'path', None)
        grid_info = getattr(state, 'grid_info', None)
        if isinstance(grid_info, dict):
            grid_path = grid_info.get('grid_path')
            node_type = grid_info.get('node_type')
            idx = grid_info.get('index')
            if grid_path and node_type and idx:
                try:
                    self._set_grid_entry_visibility_range(grid_path, node_type, int(idx), int(idx), False)
                except Exception:
                    pass
            return
        if not path:
            return
        control = None
        if hasattr(self, '_get_cached_control'):
            try:
                control = self._get_cached_control(path)
            except Exception:
                control = None
        if control is None:
            try:
                control = self._screen.GetBaseUIControl(path)
            except Exception:
                control = None
        if control is not None:
            try:
                self._screen.RemoveChildControl(control)
            except Exception:
                pass
        try:
            self._drop_cached_control(path)
        except Exception:
            pass
        try:
            self._drop_native_common_style_cache(path)
        except Exception:
            pass
        try:
            self._drop_native_layout_cache(path)
        except Exception:
            pass
        try:
            self._drop_button_binding_cache(path)
        except Exception:
            pass

    def _extract_animation_config(self, props):
        if not isinstance(props, dict):
            return None
        cfg = props.get('__animation__')
        if not isinstance(cfg, dict):
            return None
        if not cfg.get('enter') and not cfg.get('exit') and cfg.get('animate') in (None, {}):
            return None
        return cfg

    def _handle_node_applied_animations(self, node, node_path, node_id, node_type, control):
        mgr = self._get_animation_manager()
        props = getattr(node, 'props', None)
        anim_config = self._extract_animation_config(props)
        shadow_layout = getattr(node, 'layout', None)
        now = _perf_now()

        # If this node is mid-exit and the user reversed (re-mounted the
        # same node_id), we need to (a) cancel the exit state so enter can
        # run fresh, and (b) clean up the stale native widget that was
        # being kept alive for the exit — otherwise the old widget stays
        # visible alongside the new one and we see "two copies".
        old_exit = mgr.states.get((node_id, 'exit'))
        if old_exit is not None and old_exit.path != node_path:
            self._cleanup_stale_exiting_widget(old_exit)
            mgr._cancel_exit_state(node_id)
            # Force this remount to be treated as "new" so enter fires.
            mgr.seen_node_ids.discard(node_id)

        # node_id-based "first-time seen" check — works for both flat and
        # grid pool render paths since both go through _apply_rendered_entry.
        is_new = node_id not in mgr.seen_node_ids
        mgr.seen_node_ids.add(node_id)

        if anim_config is not None and is_new:
            _anim_log('node_applied (new) node=%s path=%s type=%s config_keys=%s' % (
                node_id, node_path, node_type,
                sorted([k for k in anim_config.keys() if anim_config.get(k) is not None]),
            ))

        # Refresh path / layout for any existing (non-exit) state tied to this node.
        existing_keys = [k for k in list(mgr.states.keys()) if k[0] == node_id and k[1] != 'exit']
        if existing_keys:
            changed = False
            for key in existing_keys:
                st = mgr.states.get(key)
                if st is None:
                    continue
                if st.path != node_path:
                    st.path = node_path
                    changed = True
                if shadow_layout is not None:
                    st.shadow_layout = _layout_snapshot(shadow_layout)
            if changed:
                mgr._rebuild_locks()

        if anim_config is None:
            if node_id in mgr.last_animate_targets:
                mgr.clear_animate(node_id)
            return

        enter_anim = anim_config.get('enter')
        if is_new and enter_anim is not None:
            mgr.register_enter(node_path, node_id, node_type, enter_anim, shadow_layout, now)
            # Apply initial-frame values immediately so the node doesn't
            # flash its final state before the tick runs.
            initial_values = dict(enter_anim.from_)
            if initial_values:
                snapshot = _layout_snapshot(shadow_layout)
                self._apply_animated_values(node_path, snapshot, initial_values, node_type, control)
                applied = mgr.last_applied_values.get(node_id)
                if applied is None:
                    applied = {}
                    mgr.last_applied_values[node_id] = applied
                for field, v in initial_values.items():
                    applied[field] = v

        animate_prop = anim_config.get('animate')
        user_has_translate = False
        if animate_prop is not None:
            target, duration, delay, easing = normalize_animate(animate_prop)
            if target:
                if 'translateX' in target or 'translateY' in target:
                    user_has_translate = True
                mgr.register_animate(node_path, node_id, node_type, target, duration, delay, easing, shadow_layout, now)
                if is_new:
                    # On first mount this render, force-apply the target so
                    # native doesn't show whatever value _apply_common_style_props
                    # / _reset_pooled_widget_native_state just wrote (which
                    # is usually 1.0 / layout default) until the next tick.
                    snapshot = _layout_snapshot(shadow_layout)
                    self._apply_animated_values(node_path, snapshot, target, node_type, control)
                    applied = mgr.last_applied_values.get(node_id)
                    if applied is None:
                        applied = {}
                        mgr.last_applied_values[node_id] = applied
                    for field, v in target.items():
                        applied[field] = v
            else:
                mgr.clear_animate(node_id)
        else:
            if node_id in mgr.last_animate_targets:
                mgr.clear_animate(node_id)

        # Auto layout animation: if this node isn't freshly mounted and its
        # layout position shifted since last render (e.g. a sibling got
        # removed and children flow upwards), glide it to the new position
        # instead of snapping. Skip if the user already claims translateX/Y
        # via ``animate=`` — their intent wins.
        if not is_new and not user_has_translate and shadow_layout is not None:
            prev_layout_map = getattr(self, '_layout_map_last_render', None) or {}
            prev_pos = prev_layout_map.get(node_id)
            if prev_pos:
                try:
                    new_x = float(getattr(shadow_layout, 'x', 0.0) or 0.0)
                    new_y = float(getattr(shadow_layout, 'y', 0.0) or 0.0)
                    prev_x = float(prev_pos.get('x', new_x))
                    prev_y = float(prev_pos.get('y', new_y))
                except Exception:
                    prev_x = new_x = 0.0
                    prev_y = new_y = 0.0
                dx = prev_x - new_x
                dy = prev_y - new_y
                if abs(dx) > 0.5 or abs(dy) > 0.5:
                    offset = {}
                    if abs(dx) > 0.5:
                        offset['translateX'] = dx
                    if abs(dy) > 0.5:
                        offset['translateY'] = dy
                    mgr.register_auto_layout(
                        node_path, node_id, node_type, offset, shadow_layout, now,
                        duration=280,
                    )
                    # Apply the initial offset immediately so native doesn't
                    # snap to the new layout for one frame.
                    snapshot = _layout_snapshot(shadow_layout)
                    self._apply_animated_values(node_path, snapshot, offset, node_type, control)
                    applied = mgr.last_applied_values.get(node_id)
                    if applied is None:
                        applied = {}
                        mgr.last_applied_values[node_id] = applied
                    for field, v in offset.items():
                        applied[field] = v

        # Ensure fallback tick is running in case GameRenderTickEvent is not
        # delivered in the current client build.
        self._maybe_start_fallback_tick()

    def detect_and_register_exit_animations(self, prev_shadow_root, new_node_ids_set, root_path, now=None):
        """Scan the previous shadow tree for nodes whose exit animation
        needs to be started (they were present last render, are gone
        this render, and have a non-None ``exit`` animation)."""
        if prev_shadow_root is None:
            return
        mgr = self._get_animation_manager()
        if now is None:
            now = _perf_now()
        # Flatten the prev shadow tree under the same parent targets the
        # runtime uses. We piggy-back on ``_collect_flat_entries_for_root``
        # which understands virtual Panels / Scroll content paths.
        try:
            prev_entries = self._collect_flat_entries_for_root([prev_shadow_root], root_path)
        except Exception:
            prev_entries = []
        if not prev_entries:
            return

        prev_path_map = getattr(self, '_prev_node_id_path_map', None) or {}
        cleanup_parent_target_cache = {}
        cleanup_scroll_content_cache = {}
        cleanup_scroll_view_cache = {}

        for entry in prev_entries:
            if not isinstance(entry, dict):
                continue
            node = entry.get('node')
            node_id = self._safe_text(entry.get('node_id'))
            if not node or not node_id:
                continue

            if node_id in new_node_ids_set:
                continue

            props = getattr(node, 'props', None)
            anim_config = self._extract_animation_config(props)
            if anim_config is None:
                continue
            exit_anim = anim_config.get('exit')
            if exit_anim is None:
                continue

            # Prefer the actual native path recorded last render; fall back to
            # the flat parent/child if unknown (node was never applied).
            recorded_path = prev_path_map.get(node_id)
            grid_info = None
            if recorded_path:
                native_path = recorded_path
                grid_info = self._extract_grid_info_from_widget_path(native_path)
            else:
                parent_path_fb = self._resolve_parent_target_for_cleanup(
                    entry.get('parent_target'),
                    cleanup_parent_target_cache,
                    cleanup_scroll_content_cache,
                    cleanup_scroll_view_cache,
                )
                child_name_fb = self._safe_text(entry.get('child_name'))
                if not parent_path_fb or not child_name_fb:
                    continue
                native_path = parent_path_fb + '/' + child_name_fb

            # Parent / child for expected_children_by_parent — derived from
            # the actual native path (root/scroll direct child only).
            last_sep = native_path.rfind('/')
            if last_sep > 0:
                parent_path = native_path[:last_sep]
                child_name = native_path[last_sep + 1:]
            else:
                parent_path = root_path
                child_name = native_path

            parent_preserved = self._is_parent_preserved(entry, prev_entries, new_node_ids_set)
            if not parent_preserved:
                continue

            # Skip re-registering every render while animation runs.
            existing = mgr.states.get((node_id, 'exit'))
            if existing is not None:
                mgr.exiting_states_by_path[native_path] = existing
                existing_grid_info = getattr(existing, 'grid_info', None)
                if existing_grid_info is None:
                    bucket = mgr.exiting_children_by_parent.get(parent_path)
                    if bucket is None:
                        bucket = {}
                        mgr.exiting_children_by_parent[parent_path] = bucket
                    bucket[child_name] = True
                continue

            node_type = self._safe_text(entry.get('node_type')) or 'Panel'
            mgr.register_exit(
                path=native_path,
                parent_path=parent_path,
                child_name=child_name,
                node_id=node_id,
                node_type=node_type,
                animation=exit_anim,
                shadow_layout=getattr(node, 'layout', None),
                now=now,
                grid_info=grid_info,
            )
            self._maybe_start_fallback_tick()

    def _extract_grid_info_from_widget_path(self, path):
        """Detect whether ``path`` points to a grid pool widget slot.

        Grid pool widget paths look like ``.../{gridName}/{template}{N}/widget``.
        Returns a dict with grid_path / index / wrapper_path / widget_path / node_type
        when recognized, else ``None``.
        """
        if not path:
            return None
        safe_path = self._safe_text(path)
        if not safe_path.endswith('/widget'):
            return None
        wrapper_path = safe_path[:-len('/widget')]
        last_sep = wrapper_path.rfind('/')
        if last_sep <= 0:
            return None
        grid_path = wrapper_path[:last_sep]
        wrapper_name = wrapper_path[last_sep + 1:]

        pool_states = getattr(self, '_grid_pool_states', None) or {}
        state = pool_states.get(grid_path)
        if not isinstance(state, dict):
            return None
        node_type = state.get('node_type')
        grid_config = self._get_grid_type_config(node_type) if node_type else None
        if not isinstance(grid_config, dict):
            return None
        template_name = self._safe_text(grid_config.get('template_name'))
        if not template_name or not wrapper_name.startswith(template_name):
            return None
        index_str = wrapper_name[len(template_name):]
        try:
            index = int(index_str)
        except Exception:
            return None
        return {
            'grid_path': grid_path,
            'index': index,
            'wrapper_path': wrapper_path,
            'widget_path': safe_path,
            'node_type': self._safe_text(node_type),
        }

    def _is_parent_preserved(self, entry, prev_entries, new_node_ids_set):
        parent_target = entry.get('parent_target') if isinstance(entry, dict) else None
        if not isinstance(parent_target, dict):
            return True
        kind = parent_target.get('kind')
        if kind == 'path':
            return True  # root-level
        # scroll_content_of_entry → look at scroll host's node_id
        if kind == 'scroll_content_of_entry':
            scroll_child_name = parent_target.get('scroll_child_name')
            if not scroll_child_name:
                return True
            # Find the prev entry whose child_name matches; its node_id must be in new set.
            for prev in prev_entries:
                if not isinstance(prev, dict):
                    continue
                if prev.get('child_name') == scroll_child_name:
                    parent_node_id = self._safe_text(prev.get('node_id'))
                    if parent_node_id:
                        return parent_node_id in new_node_ids_set
                    break
        return True

    def merge_exiting_expected_children(self, expected_children_by_parent):
        mgr = self._get_animation_manager()
        exiting = mgr.exiting_children_by_parent
        if not exiting:
            return
        for parent_path, children in exiting.items():
            if not isinstance(children, dict):
                continue
            bucket = expected_children_by_parent.get(parent_path)
            if not isinstance(bucket, dict):
                bucket = {}
                expected_children_by_parent[parent_path] = bucket
            for child_name in children:
                bucket[child_name] = True

    def tick_animations(self):
        self._anim_tick_count = getattr(self, '_anim_tick_count', 0) + 1
        if not getattr(self, '_anim_tick_first_logged', False):
            self._anim_tick_first_logged = True
            _anim_log('tick_animations 首次被调用 app=%s mounted=%s' % (
                getattr(self, 'app_id', '?'),
                getattr(self, '_mounted', False),
            ))

        mgr = getattr(self, '_animation_manager', None)
        if mgr is None or not mgr.states:
            return
        if not getattr(self, '_mounted', False):
            return

        now = _perf_now()

        # 每秒输出一次活跃动画摘要
        last_log = getattr(self, '_anim_tick_last_log_time', 0.0)
        if now - last_log >= 1.0:
            self._anim_tick_last_log_time = now
            summary = []
            for (nid, kind), st in list(mgr.states.items())[:5]:
                elapsed_ms = (now - st.start_time) * 1000.0 - st.delay
                dur = max(1, st.duration)
                pct = int(max(0.0, min(1.0, elapsed_ms / float(dur))) * 100)
                summary.append('%s/%s %d%%' % (nid, kind, pct))
            more = len(mgr.states) - len(summary)
            extra = ' +%d more' % more if more > 0 else ''
            _anim_log('tick active=%d states=[%s%s]' % (len(mgr.states), ', '.join(summary), extra))

        finished = []
        applied_any = False
        for key, state in list(mgr.states.items()):
            values, progress, done = mgr.step(state, now)
            if not values:
                if done:
                    finished.append(key)
                continue
            control = self._get_cached_control(state.path) if hasattr(self, '_get_cached_control') else None
            if control is None:
                try:
                    control = self._screen.GetBaseUIControl(state.path)
                except Exception:
                    control = None
            if control is None:
                # Native control may not exist yet (deferred grid expand or
                # freshly-torn-down path). Skip this frame and try again.
                if done:
                    finished.append(key)
                continue
            self._apply_animated_values(state.path, state.shadow_layout, values, state.node_type, control)
            applied = mgr.last_applied_values.get(state.node_id)
            if applied is None:
                applied = {}
                mgr.last_applied_values[state.node_id] = applied
            for field, v in values.items():
                applied[field] = v
            applied_any = True
            if done:
                finished.append(key)

        for key in finished:
            state = mgr.states.pop(key, None)
            if state is None:
                continue
            if state.kind == 'exit':
                self._finalize_exit_animation(state)
            if state.on_complete is not None:
                try:
                    state.on_complete()
                except Exception:
                    pass
            _anim_log('animation finished node=%s kind=%s' % (state.node_id, state.kind))
        if finished:
            mgr._rebuild_locks()

        if applied_any:
            try:
                self._request_screen_refresh(sync_refresh=False)
                self._schedule_pending_screen_refresh()
            except Exception:
                pass

    def _apply_animated_values(self, node_path, shadow_snapshot, values, node_type, control):
        if not values:
            return
        if control is None and hasattr(self, '_get_cached_control'):
            control = self._get_cached_control(node_path)
        if control is None:
            return

        if 'opacity' in values:
            try:
                self._safe_set_alpha(node_path, float(values['opacity']), control)
            except Exception:
                pass

        if 'translateX' in values or 'translateY' in values:
            base_x = 0.0
            base_y = 0.0
            if isinstance(shadow_snapshot, dict):
                base_x = shadow_snapshot.get('x', 0.0) or 0.0
                base_y = shadow_snapshot.get('y', 0.0) or 0.0
            dx = values.get('translateX', 0.0) or 0.0
            dy = values.get('translateY', 0.0) or 0.0
            try:
                self._safe_set_position(node_path, base_x + dx, base_y + dy, control)
            except Exception:
                pass

        if 'width' in values or 'height' in values:
            base_w = 0.0
            base_h = 0.0
            if isinstance(shadow_snapshot, dict):
                base_w = shadow_snapshot.get('width', 0.0) or 0.0
                base_h = shadow_snapshot.get('height', 0.0) or 0.0
            w = values.get('width', base_w)
            h = values.get('height', base_h)
            if node_type == 'Label':
                # Label size is auto-measured; skip to avoid clipping.
                return
            try:
                self._safe_set_size(node_path, w, h, control)
            except Exception:
                pass

    def _finalize_exit_animation(self, state):
        mgr = self._get_animation_manager()
        path = state.path
        grid_info = getattr(state, 'grid_info', None)

        # Clean up tracking tables.
        try:
            del mgr.exiting_states_by_path[path]
        except Exception:
            pass

        if isinstance(grid_info, dict):
            grid_path = grid_info.get('grid_path')
            index = grid_info.get('index')
            bucket = mgr.exiting_grid_slots.get(grid_path) if grid_path else None
            if bucket is not None:
                try:
                    bucket.discard(int(index))
                except Exception:
                    pass
                if not bucket:
                    try:
                        del mgr.exiting_grid_slots[grid_path]
                    except Exception:
                        pass
            # Grid slot — just hide the wrapper; the pool keeps the widget
            # alive for reuse on later renders.
            node_type = grid_info.get('node_type')
            try:
                self._set_grid_entry_visibility_range(grid_path, node_type, int(index), int(index), False)
            except Exception:
                pass
        else:
            # Non-grid: clean the per-parent bucket and remove the native control.
            last_sep = path.rfind('/')
            if last_sep > 0:
                parent_path = path[:last_sep]
                child_name = path[last_sep + 1:]
            else:
                parent_path = None
                child_name = path
            bucket = mgr.exiting_children_by_parent.get(parent_path) if parent_path else None
            if isinstance(bucket, dict):
                try:
                    del bucket[child_name]
                except Exception:
                    pass
                if not bucket and parent_path is not None:
                    try:
                        del mgr.exiting_children_by_parent[parent_path]
                    except Exception:
                        pass

            control = None
            if hasattr(self, '_get_cached_control'):
                control = self._get_cached_control(path)
            if control is None:
                try:
                    control = self._screen.GetBaseUIControl(path)
                except Exception:
                    control = None
            if control is not None:
                try:
                    self._screen.RemoveChildControl(control)
                except Exception:
                    pass
            try:
                self._drop_cached_control(path)
            except Exception:
                pass
            try:
                self._drop_native_common_style_cache(path)
            except Exception:
                pass
            try:
                self._drop_native_layout_cache(path)
            except Exception:
                pass
            try:
                self._drop_button_binding_cache(path)
            except Exception:
                pass

        mgr.drop_node(state.node_id)
        try:
            self._request_screen_refresh(sync_refresh=False)
            self._schedule_pending_screen_refresh()
        except Exception:
            pass

    # ---- Fallback self-scheduled tick ---------------------------------

    def _maybe_start_fallback_tick(self):
        """Ensure a timer-based tick runs while there are active animations.

        ``GameRenderTickEvent`` delivery varies across NetEase client builds;
        when it's unavailable the animation manager would never advance. The
        fallback ticker uses ``game.AddTimer`` to request the next frame. It
        self-terminates once there are no active animations, so the steady-
        state overhead when nothing is animating is zero.
        """
        mgr = getattr(self, '_animation_manager', None)
        if mgr is None or not mgr.states:
            return
        if getattr(self, '_anim_fallback_tick_pending', False):
            return
        if not getattr(self, '_mounted', False):
            return
        if _clientApi is None:
            return

        try:
            game_comp = _clientApi.CreateComponent(_clientApi.GetLevelId(), 'Minecraft', 'game')
        except Exception as err:
            _anim_log('fallback tick CreateComponent failed: %s' % err)
            return
        if not game_comp:
            return

        self._anim_fallback_tick_pending = True

        runtime = self

        def _fallback_tick_cb():
            runtime._anim_fallback_tick_pending = False
            if not getattr(runtime, '_anim_fallback_tick_logged', False):
                runtime._anim_fallback_tick_logged = True
                _anim_log('fallback timer tick 启动 (AddTimer 调度) app=%s' % (
                    getattr(runtime, 'app_id', '?'),
                ))
            try:
                runtime.tick_animations()
            except Exception as inner_err:
                _anim_log('fallback tick 异常: %s' % inner_err)
            runtime._maybe_start_fallback_tick()

        try:
            game_comp.AddTimer(1.0 / 60.0, _fallback_tick_cb)
        except Exception as err:
            self._anim_fallback_tick_pending = False
            _anim_log('fallback tick AddTimer failed: %s' % err)
