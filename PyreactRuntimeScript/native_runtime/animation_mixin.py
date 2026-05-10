# -*- coding: utf-8 -*-


class RuntimeAnimationMixin(object):
    _animation_states = None
    _pending_animation_removals = None
    _animation_exit_ghost_seq = 0

    def _init_animation_runtime_state(self):
        self._animation_states = {}
        self._pending_animation_removals = {}
        self._animation_exit_ghost_seq = 0

    def _clear_animation_runtime_state(self):
        self._animation_states = {}
        self._pending_animation_removals = {}
        self._animation_exit_ghost_seq = 0

    def _handle_node_applied_animations(self, node, node_path, node_type, node_id, node_control=None):
        props = getattr(node, 'props', None) or {}
        if not isinstance(props, dict):
            return
        config = props.get('__animation__')
        if not isinstance(config, dict):
            return

        state = self._get_animation_state(node_id, node_path)
        moved_native = bool(getattr(node, '_pyreact_native_moved', False))
        if getattr(node, '_pyreact_native_created', False) and not moved_native:
            state.clear()
            state['values'] = {}
            try:
                node._pyreact_native_created = False
            except Exception:
                pass
        elif moved_native:
            try:
                node._pyreact_native_moved = False
            except Exception:
                pass
        if not state.get('entered'):
            enter = config.get('enter')
            if enter is not None:
                self._start_animation(node_id, node_path, node, node_control, enter, 'enter')
            state['entered'] = True
        elif moved_native:
            self._start_layout_move_animation(node_id, node_path, node, node_control)

        animate = config.get('animate')
        values, duration, delay, easing = self._normalize_runtime_transition(animate)
        signature = self._animation_values_signature(values)
        if signature and state.get('animate_signature') != signature:
            old_signature = state.get('animate_signature')
            state['animate_signature'] = signature
            if old_signature is None and not state.get('active'):
                self._apply_animation_values(node_path, node, node_control, values)
                state['values'].update(values)
            else:
                self._start_transition(node_id, node_path, node, node_control, values, duration, delay, easing)
        elif state.get('values'):
            self._apply_animation_values(node_path, node, node_control, state.get('values'))

    def _get_animation_state(self, node_id, node_path):
        states = getattr(self, '_animation_states', None)
        if not isinstance(states, dict):
            states = {}
            self._animation_states = states
        safe_path = self._animation_safe_text(node_path)
        safe_id = self._animation_safe_text(node_id)
        key = safe_id or safe_path
        state = states.get(key)
        if not isinstance(state, dict):
            state = dict()
            state['values'] = {}
            states[key] = state
        state['key'] = key
        if safe_id:
            state['node_id'] = safe_id
        if node_path:
            state['path'] = safe_path
        return state

    def _reapply_node_animation_values(self, node_id, node_path, node, node_control=None):
        state = self._get_animation_state(node_id, node_path)
        values = state.get('values') if isinstance(state, dict) else None
        if isinstance(values, dict) and values:
            self._apply_animation_values(node_path, node, node_control, values)

    def _reapply_animation_values_for_tree(self, node, parent_path):
        if node is None:
            return
        if isinstance(node, (list, tuple)):
            children = list(node)
            node_type = 'Panel'
            current_path = parent_path
        else:
            children = [node]
            node_type = 'Panel'
            current_path = parent_path

        index = 0
        for child in children:
            child_type = self._animation_safe_text(getattr(child, 'node_type', 'Panel') or 'Panel')
            child_id = self._animation_safe_text(getattr(child, 'node_id', 'node'))
            child_name = '%s%s_%s' % (self._animation_control_prefix(), child_id, index)
            child_path = ('%s' % current_path) + '/' + child_name
            props = getattr(child, 'props', None) or {}
            if isinstance(props, dict) and isinstance(props.get('__animation__'), dict):
                control = self._animation_get_base_ui_control(child_path)
                self._reapply_node_animation_values(child_id, child_path, child, control)
            child_parent = child_path
            if child_type == 'Scroll':
                try:
                    child_parent = self._animation_get_scroll_content_path(child_path)
                except Exception:
                    child_parent = child_path
            try:
                child_children = self._animation_get_render_children(child, child_type)
            except Exception:
                child_children = getattr(child, 'children', None) or []
            if isinstance(child_children, (list, tuple)) and child_children:
                self._reapply_animation_values_for_tree(list(child_children), child_parent)
            index += 1

    def _start_layout_move_animation(self, node_id, node_path, node, node_control):
        delta = getattr(node, '_pyreact_layout_move_from', None)
        if not isinstance(delta, dict):
            return False
        from_values = {}
        dx = self._animation_to_float(delta.get('translateX'), 0.0)
        dy = self._animation_to_float(delta.get('translateY'), 0.0)
        if abs(dx) > 0.001:
            from_values['translateX'] = dx
        if abs(dy) > 0.001:
            from_values['translateY'] = dy
        try:
            node._pyreact_layout_move_from = None
        except Exception:
            pass
        if not from_values:
            return False
        to_values = {}
        for key in from_values:
            to_values[key] = 0.0
        self._apply_animation_values(node_path, node, node_control, from_values)
        state = self._get_animation_state(node_id, node_path)
        state['values'].update(from_values)
        self._queue_runtime_animation(
            node_id,
            node_path,
            node,
            node_control,
            from_values,
            to_values,
            180,
            0,
            self._default_animation_easing(),
            None,
            'layout',
        )
        return True

    def _start_animation(self, node_id, node_path, node, node_control, animation, kind, on_complete_override=None):
        from_values = getattr(animation, 'from_', None) or {}
        to_values = getattr(animation, 'to', None) or {}
        duration = self._to_int(getattr(animation, 'duration', 0), 0)
        delay = self._to_int(getattr(animation, 'delay', 0), 0)
        easing = getattr(animation, 'easing', None)
        if not callable(easing):
            easing = self._default_animation_easing()
        state = self._get_animation_state(node_id, node_path)
        self._reset_stale_animation_values(node_path, node, node_control, state, from_values, to_values)
        if from_values:
            self._apply_animation_values(node_path, node, node_control, from_values)
            state['values'].update(from_values)
        on_complete = on_complete_override
        if on_complete is None:
            on_complete = getattr(animation, 'onComplete', None)
        self._queue_runtime_animation(node_id, node_path, node, node_control, from_values, to_values, duration, delay, easing, on_complete, kind)

    def _start_transition(self, node_id, node_path, node, node_control, values, duration, delay, easing):
        if values:
            current = self._get_current_animation_values(node_id, node_path, node, values)
            self._apply_animation_values(node_path, node, node_control, current)
            state = self._get_animation_state(node_id, node_path)
            state['values'].update(current)
            self._queue_runtime_animation(node_id, node_path, node, node_control, current, values, duration, delay, easing, None, 'animate')

    def _queue_runtime_animation(self, node_id, node_path, node, node_control, from_values, to_values, duration, delay, easing, on_complete, kind):
        if not to_values:
            return
        state = self._get_animation_state(node_id, node_path)
        now = self._animation_to_float(self._animation_perf_clock(), 0.0)
        active = dict()
        active['path'] = node_path
        active['node'] = node
        active['control'] = node_control
        active['from'] = dict(from_values or {})
        active['to'] = dict(to_values or {})
        active['start'] = now + (self._animation_to_float(delay, 0.0) / 1000.0)
        active['duration'] = max(0.0, self._animation_to_float(duration, 0.0) / 1000.0)
        active['easing'] = easing
        active['onComplete'] = on_complete
        active['kind'] = kind
        state['active'] = active

    def tick_animations(self):
        states = getattr(self, '_animation_states', None)
        if not isinstance(states, dict) or not states:
            return False
        now = self._animation_to_float(self._animation_perf_clock(), 0.0)
        changed = False
        for node_id in list(states.keys()):
            state = states.get(node_id)
            if not isinstance(state, dict):
                continue
            active = state.get('active')
            if not isinstance(active, dict):
                continue
            start = float(self._animation_to_float(active.get('start'), now))
            duration = float(self._animation_to_float(active.get('duration'), 0.0))
            if now < start:
                continue
            if duration <= 0.0:
                progress = 1.0
            else:
                progress = (now - start) / duration
            if progress < 0.0:
                progress = 0.0
            if progress > 1.0:
                progress = 1.0
            easing = active.get('easing')
            if not callable(easing):
                easing = self._default_animation_easing()
            try:
                eased_value = easing(progress)
                eased = self._animation_to_float(eased_value, progress)
            except Exception:
                eased = progress
            values = self._interpolate_animation_values(active.get('from') or {}, active.get('to') or {}, eased)
            self._apply_animation_values(active.get('path'), active.get('node'), active.get('control'), values)
            state['values'] = values
            changed = True
            if progress >= 1.0:
                try:
                    callback = active.get('onComplete')
                    if callable(callback):
                        callback()
                except Exception:
                    pass
                try:
                    del state['active']
                except Exception:
                    pass
        return changed

    def _interpolate_animation_values(self, from_values, to_values, progress):
        result = {}
        keys = {}
        for key in (from_values or {}).keys():
            keys[key] = True
        for key in (to_values or {}).keys():
            keys[key] = True
        for key in keys.keys():
            end_value = (to_values or {}).get(key)
            if end_value is None:
                end_value = self._get_animation_baseline_value(None, None, key)
            start_value = from_values.get(key)
            if start_value is None:
                start_value = self._get_animation_baseline_value(None, None, key)
            try:
                start_float = self._animation_to_float(start_value, 0.0)
                end_float = self._animation_to_float(end_value, 0.0)
                progress_float = self._animation_to_float(progress, 0.0)
                result[key] = start_float + (end_float - start_float) * progress_float
            except Exception:
                pass
        return result

    def _apply_animation_values(self, node_path, node, node_control, values):
        if not node_path or not isinstance(values, dict):
            return
        layout = getattr(node, 'layout', None)
        base_x = float(self._animation_to_float(getattr(layout, 'native_local_x', getattr(layout, 'x', 0.0)), 0.0))
        base_y = float(self._animation_to_float(getattr(layout, 'native_local_y', getattr(layout, 'y', 0.0)), 0.0))
        offset_x = float(self._animation_to_float(values.get('translateX'), 0.0))
        offset_y = float(self._animation_to_float(values.get('translateY'), 0.0))
        x = base_x + offset_x
        y = base_y + offset_y
        width = self._animation_to_float(getattr(layout, 'width', 0.0), 0.0)
        height = self._animation_to_float(getattr(layout, 'height', 0.0), 0.0)
        if values.get('width') is not None:
            width = self._animation_to_float(values.get('width'), width)
        if values.get('height') is not None:
            height = self._animation_to_float(values.get('height'), height)
        if values.get('translateX') is not None or values.get('translateY') is not None:
            self._animation_safe_set_position(node_path, x, y, node_control)
        if (values.get('width') is not None or values.get('height') is not None) and self._animation_safe_text(getattr(node, 'node_type', '')) != 'Label':
            self._animation_safe_set_size(node_path, width, height, node_control)
        has_opacity = values.get('opacity') is not None
        has_alpha = values.get('alpha') is not None
        if has_opacity or has_alpha:
            opacity = 1.0
            if has_opacity:
                opacity = self._animation_clamp_alpha(values.get('opacity'))
            alpha = 1.0
            if has_alpha:
                alpha = self._animation_clamp_alpha(values.get('alpha'))
            self._animation_safe_set_alpha(node_path, self._animation_resolve_node_base_alpha(node) * opacity * alpha, node_control)
            if has_opacity:
                self._apply_subtree_animation_alpha(node_path, node, opacity)
            if has_alpha:
                self._apply_direct_child_animation_alpha(node_path, node, alpha, opacity)

    def _animation_clamp_alpha(self, alpha):
        value = float(self._animation_to_float(alpha, 1.0))
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value

    def _animation_resolve_node_base_alpha(self, node):
        props = getattr(node, 'props', None) or {}
        if not isinstance(props, dict):
            props = {}
        style = props.get('style')
        if not isinstance(style, dict):
            style = getattr(node, 'style', None)
        if not isinstance(style, dict):
            style = {}
        try:
            resolve_alpha = getattr(self, '_resolve_common_alpha', None)
            if callable(resolve_alpha):
                return self._animation_clamp_alpha(resolve_alpha(style, props, node))
        except Exception:
            pass
        return 1.0

    def _reset_stale_animation_values(self, node_path, node, node_control, state, from_values, to_values):
        previous = state.get('values') if isinstance(state, dict) else None
        if not isinstance(previous, dict) or not previous:
            return
        reset = {}
        for key in previous.keys():
            if key in (from_values or {}) or key in (to_values or {}):
                continue
            reset[key] = self._get_animation_baseline_value(node, previous, key)
        if not reset:
            return
        self._apply_animation_values(node_path, node, node_control, reset)
        for key, value in reset.items():
            state['values'][key] = value

    def _get_animation_baseline_value(self, node, previous, key):
        if key == 'opacity':
            props = getattr(node, 'props', None) or {}
            style = props.get('style') if isinstance(props, dict) else {}
            if isinstance(style, dict):
                return self._animation_to_float(style.get('opacity'), 1.0)
            return 1.0
        if key == 'alpha':
            return 1.0
        if key in ('translateX', 'translateY'):
            return 0.0
        if key == 'width':
            return self._animation_to_float(getattr(getattr(node, 'layout', None), 'width', 0.0), 0.0)
        if key == 'height':
            return self._animation_to_float(getattr(getattr(node, 'layout', None), 'height', 0.0), 0.0)
        if isinstance(previous, dict) and previous.get(key) is not None:
            return previous.get(key)
        return 0.0

    def _apply_subtree_animation_alpha(self, node_path, node, opacity):
        node_type = self._animation_safe_text(getattr(node, 'node_type', '') or '')
        if node_type == 'Button':
            self._apply_button_slot_animation_alpha(node_path, opacity)

        children_parent_path = node_path
        if node_type == 'Scroll':
            children_parent_path = self._animation_get_scroll_content_path(node_path)
        try:
            children = self._animation_get_render_children(node, node_type)
        except Exception:
            children = []
        if not isinstance(children, (list, tuple)):
            return
        index = 0
        for child in children:
            child_id = self._animation_safe_text(getattr(child, 'node_id', 'node'))
            child_name = '%s%s_%s' % (self._animation_control_prefix(), child_id, index)
            child_path = ('%s/%s' % (children_parent_path, child_name))
            child_type = self._animation_safe_text(getattr(child, 'node_type', '') or '')
            self._animation_safe_set_alpha(child_path, self._animation_resolve_node_base_alpha(child) * opacity, None)
            if child_type == 'Button':
                self._apply_button_slot_animation_alpha(child_path, opacity)
            self._apply_subtree_animation_alpha(child_path, child, opacity)
            index += 1

    def _apply_direct_child_animation_alpha(self, node_path, node, alpha, inherited_opacity=1.0):
        node_type = self._animation_safe_text(getattr(node, 'node_type', '') or '')
        if node_type == 'Button':
            self._apply_button_slot_animation_alpha(node_path, alpha * inherited_opacity)

        children_parent_path = node_path
        if node_type == 'Scroll':
            children_parent_path = self._animation_get_scroll_content_path(node_path)
        try:
            children = self._animation_get_render_children(node, node_type)
        except Exception:
            children = []
        if not isinstance(children, (list, tuple)):
            return
        index = 0
        multiplier = alpha * inherited_opacity
        for child in children:
            child_id = self._animation_safe_text(getattr(child, 'node_id', 'node'))
            child_name = '%s%s_%s' % (self._animation_control_prefix(), child_id, index)
            child_path = ('%s/%s' % (children_parent_path, child_name))
            child_type = self._animation_safe_text(getattr(child, 'node_type', '') or '')
            self._animation_safe_set_alpha(child_path, self._animation_resolve_node_base_alpha(child) * multiplier, None)
            if child_type == 'Button':
                self._apply_button_slot_animation_alpha(child_path, multiplier)
            index += 1

    def _apply_button_slot_animation_alpha(self, node_path, opacity):
        for state_name in ('default', 'hover', 'pressed'):
            slot_path = ('%s/%s' % (node_path, state_name))
            base_alpha = 1.0
            try:
                cache = getattr(self, '_button_slot_base_alpha_cache', None)
                cached = cache.get(slot_path, {}) if isinstance(cache, dict) else {}
                if cached is not None:
                    base_alpha = self._animation_to_float(cached, 1.0)
            except Exception:
                base_alpha = 1.0
            effective = base_alpha * opacity
            if effective < 0.0:
                effective = 0.0
            elif effective > 1.0:
                effective = 1.0
            self._animation_safe_set_alpha(slot_path, effective, None)

    def _get_current_animation_values(self, node_id, node_path, node, target_values):
        state = self._get_animation_state(node_id, node_path)
        current = dict(state.get('values') or {})
        props = getattr(node, 'props', None) or {}
        style = props.get('style') if isinstance(props, dict) else {}
        if not isinstance(style, dict):
            style = {}
        for key in target_values:
            if key not in current:
                if key == 'opacity':
                    current[key] = self._animation_to_float(style.get('opacity'), 1.0)
                elif key == 'alpha':
                    current[key] = 1.0
                elif key in ('translateX', 'translateY'):
                    current[key] = 0.0
                elif key == 'width':
                    current[key] = self._animation_to_float(getattr(getattr(node, 'layout', None), 'width', 0.0), 0.0)
                elif key == 'height':
                    current[key] = self._animation_to_float(getattr(getattr(node, 'layout', None), 'height', 0.0), 0.0)
        return current

    def _remove_animation_states_for_nodes(self, nodes):
        states = getattr(self, '_animation_states', None)
        if not isinstance(states, dict) or not states:
            return 0
        ids = {}
        stack = []
        for node in nodes or []:
            if node is not None:
                stack.append(node)
        while stack:
            node = stack.pop()
            node_id = self._animation_safe_text(getattr(node, 'node_id', ''))
            if node_id:
                ids[node_id] = True
            try:
                children = getattr(node, 'children', None) or []
            except Exception:
                children = []
            for child in children:
                if child is not None:
                    stack.append(child)
        removed = 0
        for key in list(states.keys()):
            state = states.get(key)
            if not isinstance(state, dict):
                continue
            node_id = self._animation_safe_text(state.get('node_id'))
            if node_id and node_id in ids:
                try:
                    del states[key]
                    removed += 1
                except Exception:
                    pass
        return removed

    def _start_exit_animation_for_delete(self, node, root_path):
        safe_root_path = '%s' % self._animation_safe_text(root_path)
        if node is None or not safe_root_path:
            return False
        self._cancel_pending_animation_removal(safe_root_path, True)
        exits = []
        self._collect_exit_animation_nodes(node, safe_root_path, exits)
        if not exits:
            return False

        ghost_path = self._create_exit_animation_ghost(safe_root_path)
        if not ghost_path:
            return False
        self._animation_remove_component_by_path(safe_root_path)
        self._animation_drop_native_common_style_cache(safe_root_path)

        pending = getattr(self, '_pending_animation_removals', None)
        if not isinstance(pending, dict):
            pending = {}
            self._pending_animation_removals = pending

        pos = ghost_path.rfind('/')
        if pos <= 0:
            parent_path = '/'
            child_name = ghost_path
        else:
            parent_path = ghost_path[:pos]
            child_name = ghost_path[pos + 1:]
        pending[ghost_path] = {
            'parent_path': parent_path,
            'child_name': child_name,
            'node': node,
            'source_path': safe_root_path,
            'ghost_path': ghost_path,
            'state_keys': [],
        }
        self._animation_drop_native_common_style_cache(ghost_path)

        remaining = [len(exits)]

        def _done():
            remaining[0] -= 1
            if remaining[0] <= 0:
                self._finish_pending_animation_removal(ghost_path)

        for exit_node, exit_path, exit_animation in exits:
            ghost_exit_path = ghost_path + exit_path[len(safe_root_path):]
            node_id = self._animation_safe_text(getattr(exit_node, 'node_id', ''))
            ghost_state_key = '__pyreact_exit_state_%s:%s' % (ghost_path, node_id or ghost_exit_path)
            pending[ghost_path]['state_keys'].append(ghost_state_key)
            control = self._animation_get_base_ui_control(ghost_exit_path)
            self._start_animation(ghost_state_key, ghost_exit_path, exit_node, control, exit_animation, 'exit', _done)
        return True

    def _create_exit_animation_ghost(self, source_path):
        safe_source_path = '%s' % self._animation_safe_text(source_path)
        if not safe_source_path:
            return None
        pos = safe_source_path.rfind('/')
        if pos <= 0:
            parent_path = '/'
        else:
            parent_path = safe_source_path[:pos]
        try:
            seq = int(getattr(self, '_animation_exit_ghost_seq', 0)) + 1
        except Exception:
            seq = 1
        self._animation_exit_ghost_seq = seq
        ghost_name = '__pyreact_exit_%s' % seq
        clone = getattr(self, '_clone', None)
        if not callable(clone):
            return None
        try:
            control = clone(safe_source_path, parent_path, ghost_name, False, False)
            if not control:
                return None
            return parent_path + '/' + ghost_name
        except Exception:
            return None

    def _collect_exit_animation_nodes(self, node, node_path, exits):
        props = getattr(node, 'props', None) or {}
        if isinstance(props, dict):
            config = props.get('__animation__')
            if isinstance(config, dict) and config.get('exit') is not None:
                exits.append((node, node_path, config.get('exit')))

        node_type = self._animation_safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
        children_parent_path = node_path
        if node_type == 'Scroll':
            try:
                children_parent_path = self._animation_get_scroll_content_path(node_path)
            except Exception:
                children_parent_path = node_path
        try:
            children = self._animation_get_render_children(node, node_type)
            if not isinstance(children, (list, tuple)):
                children = []
        except Exception:
            children = getattr(node, 'children', None) or []
        index = 0
        for child in children or []:
            child_id = self._animation_safe_text(getattr(child, 'node_id', 'node'))
            child_name = '%s%s_%s' % (self._animation_control_prefix(), child_id, index)
            child_path = ('%s' % children_parent_path) + '/' + child_name
            self._collect_exit_animation_nodes(child, child_path, exits)
            index += 1

    def _finish_pending_animation_removal(self, root_path):
        pending = getattr(self, '_pending_animation_removals', None)
        if isinstance(pending, dict):
            info = pending.pop(root_path, None)
        else:
            info = None
        if not isinstance(info, dict):
            return
        try:
            self._animation_remove_component_by_path(root_path)
        except Exception:
            pass
        self._remove_animation_states_for_pending_info(info)

    def _cancel_pending_animation_removal(self, root_path, include_source_path=False):
        pending = getattr(self, '_pending_animation_removals', None)
        if not isinstance(pending, dict):
            return False
        safe_root_path = '%s' % self._animation_safe_text(root_path)
        if not safe_root_path:
            return False

        matched_paths = []
        if safe_root_path in pending:
            matched_paths.append(safe_root_path)
        if include_source_path:
            for ghost_path, info in list(pending.items()):
                if not isinstance(info, dict):
                    continue
                if self._animation_safe_text(info.get('source_path')) == safe_root_path:
                    if ghost_path not in matched_paths:
                        matched_paths.append(ghost_path)
        if not matched_paths:
            return False

        for ghost_path in matched_paths:
            info = pending.pop(ghost_path, None)
            try:
                self._animation_remove_component_by_path(ghost_path)
            except Exception:
                pass
            self._remove_animation_states_for_pending_info(info)
        return True

    def _is_exit_animation_ghost_child_name(self, child_name):
        return ('%s' % self._animation_safe_text(child_name)).startswith('__pyreact_exit_')

    def _start_exit_animation_for_existing_path(self, root_path):
        node = self._find_prev_animation_node_by_control_path(root_path)
        if node is None:
            return False
        return self._start_exit_animation_for_delete(node, root_path)

    def _find_prev_animation_node_by_control_path(self, target_path):
        target_path = '%s' % self._animation_safe_text(target_path)
        if not target_path:
            return None
        root = getattr(self, '_prev_shadow_root', None)
        if root is None:
            return None
        root_path = '%s' % self._animation_safe_text(getattr(self, '_root_path', '/root'))
        stack = [(root, root_path, 0)]
        while stack:
            node, parent_path, index = stack.pop()
            node_id = self._animation_safe_text(getattr(node, 'node_id', 'node'))
            child_name = '%s%s_%s' % (self._animation_control_prefix(), node_id, index)
            node_path = ('%s' % parent_path) + '/' + child_name
            if node_path == target_path:
                return node

            node_type = self._animation_safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
            children_parent_path = node_path
            if node_type == 'Scroll':
                try:
                    children_parent_path = self._animation_get_scroll_content_path(node_path)
                except Exception:
                    children_parent_path = node_path
            try:
                children = self._animation_get_render_children(node, node_type)
                if not isinstance(children, (list, tuple)):
                    children = []
            except Exception:
                children = getattr(node, 'children', None) or []
            child_index = len(children or []) - 1
            while child_index >= 0:
                child = children[child_index]
                if child is not None:
                    stack.append((child, '%s' % children_parent_path, child_index))
                child_index -= 1
        return None

    def _remove_animation_state_for_path(self, node_path):
        states = getattr(self, '_animation_states', None)
        if not isinstance(states, dict) or not states:
            return 0
        safe_path = '%s' % self._animation_safe_text(node_path)
        if not safe_path:
            return 0
        removed = 0
        for key in list(states.keys()):
            state = states.get(key)
            if not isinstance(state, dict):
                continue
            if self._animation_safe_text(state.get('path')) == safe_path:
                try:
                    del states[key]
                    removed += 1
                except Exception:
                    pass
        return removed

    def _get_pending_animation_child_names(self, parent_path):
        pending = getattr(self, '_pending_animation_removals', None)
        if not isinstance(pending, dict) or not pending:
            return []
        safe_parent = '%s' % self._animation_safe_text(parent_path)
        names = []
        for ghost_path, info in pending.items():
            if not isinstance(info, dict):
                continue
            if self._animation_safe_text(info.get('parent_path')) != safe_parent:
                continue
            child_name = self._animation_safe_text(info.get('child_name'))
            if child_name:
                names.append(child_name)
        return names

    def _cleanup_exit_animation_ghosts(self):
        pending = getattr(self, '_pending_animation_removals', None)
        if not isinstance(pending, dict):
            self._pending_animation_removals = {}
            return 0
        removed = 0
        for ghost_path in list(pending.keys()):
            info = pending.pop(ghost_path, None)
            try:
                self._animation_remove_component_by_path(ghost_path)
            except Exception:
                pass
            if isinstance(info, dict):
                self._remove_animation_states_for_pending_info(info)
            removed += 1
        return removed

    def _remove_animation_states_for_pending_info(self, info):
        if not isinstance(info, dict):
            return 0
        removed = 0
        states = getattr(self, '_animation_states', None)
        state_keys = info.get('state_keys')
        if isinstance(states, dict) and isinstance(state_keys, (list, tuple)):
            for key in list(state_keys):
                safe_key = self._animation_safe_text(key)
                if safe_key in states:
                    try:
                        del states[safe_key]
                        removed += 1
                    except Exception:
                        pass
        try:
            ghost_path = self._animation_safe_text(info.get('ghost_path'))
            if ghost_path:
                removed += self._remove_animation_state_for_path(ghost_path)
        except Exception:
            pass
        return removed

    def _normalize_runtime_transition(self, animate):
        try:
            from pyreact.animation.transition import normalize_animate
            return normalize_animate(animate)
        except Exception:
            return ({}, 0, 0, self._default_animation_easing())

    def _animation_values_signature(self, values):
        if not isinstance(values, dict) or not values:
            return None
        result = []
        for key in sorted(values.keys()):
            result.append((key, self._animation_to_float(values.get(key), 0.0)))
        return tuple(result)

    def _default_animation_easing(self):
        try:
            from pyreact.animation.easing import Easing
            return Easing.easeOutQuad
        except Exception:
            return lambda t: t

    def _to_int(self, value, fallback):
        try:
            return int(value)
        except Exception:
            return int(fallback)

    def _animation_safe_text(self, value):
        safe_text = getattr(self, '_safe_text', None)
        if callable(safe_text):
            return safe_text(value)
        if value is None:
            return ''
        try:
            return str(value)
        except Exception:
            return ''

    def _animation_perf_clock(self):
        perf_clock = getattr(self, '_perf_clock', None)
        if callable(perf_clock):
            try:
                value = perf_clock()
                if isinstance(value, (int, float)):
                    return float(value)
                return 0.0
            except Exception:
                return 0.0
        try:
            import time
            return float(time.time())
        except Exception:
            return 0.0

    def _animation_to_float(self, value, fallback):
        try:
            return float(value)
        except Exception:
            return float(fallback)

    def _animation_safe_set_position(self, node_path, x, y, node_control):
        setter = getattr(self, '_safe_set_position', None)
        if callable(setter):
            setter(node_path, x, y, node_control)

    def _animation_safe_set_size(self, node_path, width, height, node_control):
        setter = getattr(self, '_safe_set_size', None)
        if callable(setter):
            setter(node_path, width, height, node_control)

    def _animation_safe_set_alpha(self, node_path, opacity, node_control):
        setter = getattr(self, '_safe_set_alpha', None)
        if callable(setter):
            setter(node_path, opacity, node_control)

    def _animation_control_prefix(self):
        return self._animation_safe_text(getattr(self, '_CONTROL_NAME_PREFIX', 'pyreact_')) or 'pyreact_'

    def _animation_get_base_ui_control(self, path):
        getter = getattr(self, '_get_base_ui_control', None)
        if callable(getter):
            try:
                return getter(path)
            except Exception:
                return None
        return None

    def _animation_get_scroll_content_path(self, path):
        getter = getattr(self, '_get_scroll_content_path', None)
        if callable(getter):
            try:
                return getter(path)
            except Exception:
                return path
        return path

    def _animation_get_render_children(self, node, node_type):
        getter = getattr(self, '_get_render_children', None)
        if callable(getter):
            try:
                return getter(node, node_type)
            except Exception:
                return []
        return getattr(node, 'children', None) or []

    def _animation_remove_component_by_path(self, path):
        remover = getattr(self, '_remove_component_by_path', None)
        if callable(remover):
            remover(path)

    def _animation_drop_native_common_style_cache(self, path):
        dropper = getattr(self, '_drop_native_common_style_cache', None)
        if callable(dropper):
            try:
                dropper(path)
            except Exception:
                pass
