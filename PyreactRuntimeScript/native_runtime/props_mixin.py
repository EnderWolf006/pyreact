# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
from pyreact.components.color import Color


class RuntimePropsMixin(object):
    def _dbg(self, tag, msg):
        try:
            if not getattr(self, '_debug_input', False):
                return
        except Exception:
            return
        try:
            print('=====> PyreactRuntime[%s] %s <=====' % (self._safe_text(tag), self._safe_text(msg)))
        except Exception:
            pass

    def _apply_node_props(self, node, node_path, node_type, node_id, node_control=None, cache_already_cleared=False):
        props = getattr(node, "props", None) or {}
        if not isinstance(props, dict):
            return

        # Track and apply ref for this node.
        try:
            self._track_ref(node_id, node_path, props.get('ref'), node_control)
        except Exception:
            pass

        style = self._extract_node_style(node, props)
        self._apply_common_style_props(node_path, style, props, node_control, node)

        if node_type == "Image":
            image_props = self._extract_image_props(props)
            self._apply_image_style_props(
                node_path=node_path,
                image_props=image_props,
                node_control=node_control,
            )
            return

        if node_type == "Label":
            layout = getattr(node, "layout", None)
            label_width = self._to_float(getattr(layout, "width", 0.0), 0.0)
            label_height = self._to_float(getattr(layout, "height", 0.0), 0.0)
            self._safe_set_size(node_path, label_width, label_height, node_control)

            content = self._safe_text(props.get("content", ""))
            label_props = self._extract_label_props(props)
            self._apply_label_native_props_then_text(node_path, label_props, content, node_control)
            return

        if node_type == "Item":
            item_props = self._resolve_item_props(props)
            self._apply_item_native_props(node_path, item_props, node_control)
            return

        if node_type == "Button":
            onclick = props.get("onClick")
            if callable(onclick):
                self._button_callbacks[node_id] = onclick
                self._queue_button_bind(node_path, node_id)

            self._render_button_state_slots(node, node_path, cache_already_cleared)
            return

        if node_type == "Input":
            self._apply_input_props(node_path, node_id, props, node_control)
            return

        if node_type == "PaperDoll":
            paper_doll_props = self._extract_paper_doll_props(props)
            self._apply_paper_doll_native_props(node_path, paper_doll_props, node_control)
            return

    def _get_native_common_style_cache(self):
        cache = getattr(self, '_native_common_style_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._native_common_style_cache = cache
        return cache

    def _drop_native_common_style_cache(self, path_prefix=None):
        cache = self._get_native_common_style_cache()
        if not path_prefix:
            start_time = self._perf_clock()
            scanned = 0
            deleted = 0
            for cache_obj in (
                cache,
                getattr(self, '_native_control_cache', None),
                getattr(self, '_native_adapter_cache', None),
                getattr(self, '_native_label_props_cache', None),
                getattr(self, '_native_image_props_cache', None),
                getattr(self, '_native_paper_doll_props_cache', None),
                getattr(self, '_native_geometry_cache', None),
                getattr(self, '_button_bind_cache', None),
                getattr(self, '_button_slot_cache', None),
                getattr(self, '_pending_button_binds', None),
                getattr(self, '_scroll_path_cache', None),
                getattr(self, '_button_slot_base_alpha_cache', None),
            ):
                if isinstance(cache_obj, dict):
                    scanned += len(cache_obj)
                    deleted += len(cache_obj)
            cache.clear()
            try:
                self._native_control_cache = {}
                self._native_adapter_cache = {}
                self._native_label_props_cache = {}
                self._native_image_props_cache = {}
                self._native_paper_doll_props_cache = {}
                self._native_geometry_cache = {}
                self._button_bind_cache = {}
                self._button_slot_cache = {}
                self._pending_button_binds = {}
                self._scroll_path_cache = {}
                self._button_slot_base_alpha_cache = {}
            except Exception:
                pass
            self._record_native_commit_perf('cache_drop_calls')
            self._record_native_commit_perf('cache_drop_scanned', scanned)
            self._record_native_commit_perf('cache_drop_deleted', deleted)
            self._record_native_commit_perf('cache_drop_ms', (self._perf_clock() - start_time) * 1000.0)
            return

        prefix = self._safe_text(path_prefix)
        if not prefix:
            self._drop_native_common_style_cache()
            return

        self._drop_native_common_style_cache_many([prefix])

    def _drop_native_common_style_cache_many(self, path_prefixes):
        prefix_set = {}
        for path_prefix in path_prefixes or []:
            prefix = self._safe_text(path_prefix)
            if prefix:
                prefix_set[prefix] = True
        if not prefix_set:
            return

        prefix_set = self._compact_cache_prefixes(prefix_set)

        start_time = self._perf_clock()
        scanned = 0
        deleted = 0
        cache_items = (
            (self._get_native_common_style_cache(), False),
            (getattr(self, '_native_control_cache', None), False),
            (getattr(self, '_native_adapter_cache', None), True),
            (getattr(self, '_native_label_props_cache', None), False),
            (getattr(self, '_native_image_props_cache', None), False),
            (getattr(self, '_native_paper_doll_props_cache', None), False),
            (getattr(self, '_native_geometry_cache', None), False),
            (getattr(self, '_button_bind_cache', None), False),
            (getattr(self, '_button_slot_cache', None), False),
            (getattr(self, '_pending_button_binds', None), False),
            (getattr(self, '_scroll_path_cache', None), False),
            (getattr(self, '_button_slot_base_alpha_cache', None), False),
        )
        for cache_obj, is_adapter_cache in cache_items:
            if not isinstance(cache_obj, dict):
                continue
            for cached_key in list(cache_obj.keys()):
                scanned += 1
                safe_key = self._safe_text(cached_key)
                if is_adapter_cache:
                    pos = safe_key.find(':')
                    if pos >= 0:
                        safe_key = safe_key[pos + 1:]
                if self._matches_any_cache_prefix(safe_key, prefix_set):
                    try:
                        del cache_obj[cached_key]
                        deleted += 1
                    except Exception:
                        pass

        self._record_native_commit_perf('cache_drop_calls')
        self._record_native_commit_perf('cache_drop_prefixes', len(prefix_set))
        self._record_native_commit_perf('cache_drop_scanned', scanned)
        self._record_native_commit_perf('cache_drop_deleted', deleted)
        self._record_native_commit_perf('cache_drop_ms', (self._perf_clock() - start_time) * 1000.0)

    def _compact_cache_prefixes(self, prefixes):
        compact = {}
        items = []
        try:
            items = list(prefixes.keys())
        except Exception:
            return prefixes
        items.sort(key=lambda item: len(item))
        for prefix in items:
            if not self._matches_any_cache_prefix(prefix, compact):
                compact[prefix] = True
        return compact

    def _matches_any_cache_prefix(self, safe_key, prefixes):
        if safe_key in prefixes:
            return True
        end = len(safe_key)
        while end > 0:
            pos = safe_key.rfind('/', 0, end)
            if pos <= 0:
                return False
            safe_key = safe_key[:pos]
            if safe_key in prefixes:
                return True
        return False

    def _set_ref_value(self, ref_obj, value):
        if ref_obj is None:
            return
        if callable(ref_obj):
            try:
                ref_obj(value)
            except Exception:
                pass
            return

        try:
            setattr(ref_obj, 'current', value)
        except Exception:
            pass

    def _track_ref(self, node_id, node_path, ref_obj, node_control=None):
        if ref_obj is None:
            return
        if not isinstance(getattr(self, '_node_refs', None), dict):
            self._node_refs = {}

        # Prefer the actual control instance; fall back to resolving by path.
        control_obj = node_control
        if not control_obj:
            try:
                control_obj = self._get_base_ui_control(node_path)
            except Exception:
                control_obj = None
        try:
            self._node_refs[node_id] = ref_obj
        except Exception:
            pass
        self._set_ref_value(ref_obj, control_obj)

    def _cleanup_refs(self):
        prev = getattr(self, '_prev_node_refs', None)
        if not isinstance(prev, dict):
            prev = {}

        cur = getattr(self, '_node_refs', None)
        if not isinstance(cur, dict):
            cur = {}

        for node_id, ref_obj in prev.items():
            if node_id not in cur:
                self._set_ref_value(ref_obj, None)

        # Snapshot current
        self._prev_node_refs = dict(cur)

    def _clear_all_refs(self):
        prev = getattr(self, '_prev_node_refs', None)
        if isinstance(prev, dict):
            for _, ref_obj in prev.items():
                self._set_ref_value(ref_obj, None)
        self._prev_node_refs = {}
        self._node_refs = {}

    def _apply_input_props(self, node_path, node_id, props, node_control=None):
        self._input_paths[node_id] = node_path

        onchange = props.get('onChange')
        if callable(onchange):
            self._input_callbacks[node_id] = onchange
            self._ensure_input_edit_handlers_bound()

        # Controlled input: keep native text aligned with props.value.
        # Note: on full rerender we recreate controls, so we MUST compare with
        # current control text, not cached last value.
        if isinstance(props, dict) and props.get('value') is not None:
            desired = self._safe_text(props.get('value'))
            current = self._safe_get_edit_text(node_path, node_control)
            if current is not None:
                current = self._safe_text(current)
            if current != desired:
                ok = self._safe_set_edit_text(node_path, desired, node_control)
                self._dbg('Input.set', 'controlled path=%s id=%s current=%r desired=%r ok=%s' % (
                    node_path, node_id, current, desired, ok,
                ))
            self._input_last_values[node_id] = desired
            return

        # Uncontrolled input: preserve text across full rerenders.
        cached = self._input_last_values.get(node_id)
        current = self._safe_get_edit_text(node_path, node_control)
        if current is not None:
            current = self._safe_text(current)

        if cached is None:
            # First time seeing this input: initialize cache from current.
            if current is not None:
                self._input_last_values[node_id] = current
            return

        # If the control was recreated (full rerender), its current text may be empty.
        if current != cached:
            ok = self._safe_set_edit_text(node_path, cached, node_control)
            self._dbg('Input.set', 'uncontrolled restore path=%s id=%s current=%r cached=%r ok=%s' % (
                node_path, node_id, current, cached, ok,
            ))

    def _cleanup_input_state(self):
        # Remove stale nodes (unmounted inputs)
        alive = set(self._input_paths.keys())
        for node_id in list(self._input_last_values.keys()):
            if node_id not in alive:
                try:
                    del self._input_last_values[node_id]
                except Exception:
                    pass

    def _ensure_input_edit_handlers_bound(self):
        if getattr(self, '_input_edit_bound', False):
            return

        screen = getattr(self, '_screen', None)
        if not screen:
            return

        try:
            screen_name = getattr(screen, 'screen_name', None) or getattr(screen, 'full_name', None) or ''
            screen_name = self._safe_text(screen_name)
        except Exception:
            screen_name = ''

        if not screen_name:
            return

        try:
            ViewBinder = clientApi.GetViewBinderCls()
            flags = ViewBinder.BF_EditChanged | ViewBinder.BF_EditFinished
        except Exception:
            return

        binding_name = '%%%s.message_text_edit_box0' % (self._safe_text(getattr(self, '_base_namespace', 'PyreactBase')) or 'PyreactBase')

        method_name = '__pyreact_input_edit_handler_%s_%s' % (self._safe_text(getattr(self, 'app_id', 'app')), str(id(self)))
        self._input_edit_handler_method_name = method_name

        runtime = self

        def _handler(self_screen, args=None):
            runtime._on_any_input_edit_event(args)

        # Important: some engine-side callback dispatchers appear to use
        # func.func_name to resolve the method on the screen instance.
        # If we keep the default name "_handler", it may try to call
        # screen._handler (which doesn't exist) and crash.
        try:
            _handler.func_name = method_name
        except Exception:
            pass
        try:
            _handler.__name__ = method_name
        except Exception:
            pass

        _handler.binding_flags = flags
        _handler.binding_name = binding_name

        # Patch method into screen class so it becomes a bound method.
        try:
            setattr(screen.__class__, method_name, _handler)
        except Exception:
            return

        try:
            bound = getattr(screen, method_name)
            # Register only this handler to avoid re-registering other bindings.
            screen._process_default(bound, screen_name)
            self._input_edit_bound = True
        except Exception:
            self._input_edit_bound = False

    def _unbind_input_edit_handlers(self):
        if not getattr(self, '_input_edit_bound', False):
            return
        screen = getattr(self, '_screen', None)
        if not screen:
            return
        method_name = getattr(self, '_input_edit_handler_method_name', None)
        if not method_name:
            return
        try:
            screen_name = getattr(screen, 'screen_name', None) or getattr(screen, 'full_name', None) or ''
            screen_name = self._safe_text(screen_name)
        except Exception:
            screen_name = ''
        if not screen_name:
            return
        try:
            bound = getattr(screen, method_name)
            screen._process_default_unregister(bound, screen_name)
        except Exception:
            pass
        self._input_edit_bound = False

    def _on_any_input_edit_event(self, args=None):
        # No path info in args -> scan all inputs and diff.
        paths = getattr(self, '_input_paths', None) or {}
        if not paths:
            return

        for node_id, path in list(paths.items()):
            cb = self._input_callbacks.get(node_id)
            if not callable(cb):
                continue

            current = self._safe_get_edit_text(path)
            if current is None:
                continue
            current = self._safe_text(current)

            prev = self._input_last_values.get(node_id)
            if prev == current:
                continue

            self._input_last_values[node_id] = current
            try:
                cb(current)
            except Exception:
                pass

    def _render_button_state_slots(self, button_node, button_path, cache_already_cleared=False):
        props = getattr(button_node, "props", None) or {}
        if not isinstance(props, dict):
            return

        builder = props.get("buttonBuilder")
        if not callable(builder):
            builder = self._default_button_state_builder

        layout = getattr(button_node, "layout", None)
        button_width = self._to_float(getattr(layout, "width", 0.0), 0.0)
        button_height = self._to_float(getattr(layout, "height", 0.0), 0.0)
        if button_width <= 0.0 or button_height <= 0.0:
            return

        button_opacity = self._get_node_effective_opacity(button_node, 1.0)

        state_elements = {}
        all_full_image = True
        for state in self._BUTTON_STATES:
            state_element = self._call_button_builder(builder, state)
            state_elements[state] = state_element
            if not self._is_full_size_image_state_element(state_element):
                all_full_image = False

        for state in self._BUTTON_STATES:
            slot_path = button_path + "/" + state
            slot_control = self._get_base_ui_control(slot_path)
            if not slot_control:
                continue

            state_element = state_elements.get(state)
            if state_element is None:
                if not cache_already_cleared:
                    self._clear_prefixed_children(slot_path)
                self._make_button_slot_image_transparent(slot_path, slot_control)
                continue

            slot_signature = self._make_button_slot_signature(state_element, button_width, button_height, all_full_image, button_opacity)
            slot_cache = getattr(self, '_button_slot_cache', None)
            if not isinstance(slot_cache, dict):
                slot_cache = {}
                self._button_slot_cache = slot_cache
            if slot_cache.get(slot_path) == slot_signature:
                if all_full_image:
                    self._restore_button_slot_image_alpha(state_element, slot_path, slot_control, button_opacity)
                continue

            self._safe_set_position(slot_path, 0, 0, slot_control)
            self._safe_set_size(slot_path, button_width, button_height, slot_control)
            if not cache_already_cleared:
                self._clear_prefixed_children(slot_path)

            if all_full_image:
                self._apply_full_size_image_to_button_slot(state_element, slot_path, slot_control, button_opacity)
                slot_cache[slot_path] = slot_signature
                self._record_button_slot_perf('direct_image')
                continue

            self._make_button_slot_image_transparent(slot_path, slot_control)

            self._render_state_element_into_slot(
                state_element=state_element,
                slot_path=slot_path,
                slot_width=button_width,
                slot_height=button_height,
                cache_already_cleared=cache_already_cleared,
                inherited_opacity=button_opacity,
            )
            slot_cache[slot_path] = slot_signature
            self._record_button_slot_perf('subtree')

    def _make_button_slot_signature(self, state_element, slot_width, slot_height, direct_image=False, inherited_opacity=1.0):
        return (
            'direct_image' if direct_image else 'subtree',
            int(round(slot_width)),
            int(round(slot_height)),
            int(round(self._clamp_alpha(inherited_opacity) * 1000.0)),
            self._make_element_signature(state_element),
        )

    def _is_full_size_image_state_element(self, state_element):
        if state_element is None:
            return False
        node_type = self._safe_text(getattr(state_element, 'node_type', '') or '')
        if node_type != 'Image':
            return False
        props = getattr(state_element, 'props', None) or {}
        if not isinstance(props, dict):
            return False
        children = props.get('children')
        if children:
            return False
        style = props.get('style')
        if not isinstance(style, dict):
            style = getattr(state_element, 'style', None)
        if not isinstance(style, dict):
            return False
        return self._is_full_percent_value(style.get('width')) and self._is_full_percent_value(style.get('height'))

    def _is_full_percent_value(self, value):
        text = self._safe_text(value).replace(' ', '').lower()
        return text == '100%'

    def _apply_full_size_image_to_button_slot(self, state_element, slot_path, slot_control, inherited_opacity=1.0):
        props = getattr(state_element, 'props', None) or {}
        if not isinstance(props, dict):
            props = {}
        style = props.get('style')
        if not isinstance(style, dict):
            style = getattr(state_element, 'style', None)
        if not isinstance(style, dict):
            style = {}

        self._apply_common_style_props(slot_path, style, props, slot_control, None, inherited_opacity)
        self._cache_button_slot_base_alpha(slot_path, self._resolve_common_alpha(style, props, None, inherited_opacity))
        image_props = self._extract_image_props(props)
        self._apply_image_style_props(slot_path, image_props, slot_control)

    def _restore_button_slot_image_alpha(self, state_element, slot_path, slot_control, inherited_opacity=1.0):
        props = getattr(state_element, 'props', None) or {}
        if not isinstance(props, dict):
            props = {}
        style = props.get('style')
        if not isinstance(style, dict):
            style = getattr(state_element, 'style', None)
        if not isinstance(style, dict):
            style = {}
        self._apply_common_style_props(slot_path, style, props, slot_control, None, inherited_opacity)
        self._cache_button_slot_base_alpha(slot_path, self._resolve_common_alpha(style, props, None, inherited_opacity))

    def _make_button_slot_image_transparent(self, slot_path, slot_control):
        try:
            cache = getattr(self, '_native_common_style_cache', None)
            if isinstance(cache, dict) and slot_path in cache:
                del cache[slot_path]
        except Exception:
            pass
        try:
            slot_cache = getattr(self, '_button_slot_cache', None)
            if isinstance(slot_cache, dict) and slot_path in slot_cache:
                del slot_cache[slot_path]
        except Exception:
            pass
        try:
            alpha_cache = getattr(self, '_button_slot_base_alpha_cache', None)
            if isinstance(alpha_cache, dict) and slot_path in alpha_cache:
                del alpha_cache[slot_path]
        except Exception:
            pass
        self._safe_set_alpha(slot_path, 0.0, slot_control)

    def _cache_button_slot_base_alpha(self, slot_path, alpha):
        cache = getattr(self, '_button_slot_base_alpha_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._button_slot_base_alpha_cache = cache
        cache[slot_path] = alpha

    def _clamp_alpha(self, alpha):
        value = self._to_float(alpha, 1.0)
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value

    def _get_node_effective_opacity(self, node, fallback=1.0):
        if node is None:
            return self._clamp_alpha(fallback)
        try:
            return self._clamp_alpha(getattr(node, 'effective_opacity', fallback))
        except Exception:
            return self._clamp_alpha(fallback)

    def _resolve_common_alpha(self, style, props, node=None, inherited_opacity=None):
        if not isinstance(style, dict):
            style = {}
        if not isinstance(props, dict):
            props = {}
        opacity = style.get('opacity')
        color = props.get('color')
        if node is not None:
            base_opacity = self._get_node_effective_opacity(node, 1.0)
        elif inherited_opacity is not None:
            base_opacity = self._clamp_alpha(inherited_opacity)
            if opacity is not None:
                base_opacity = base_opacity * self._clamp_alpha(opacity)
        else:
            base_opacity = self._clamp_alpha(opacity) if opacity is not None else 1.0
        try:
            color_alpha = color.alpha if color is not None else 1.0
        except Exception:
            color_alpha = 1.0
        final_alpha = base_opacity * color_alpha
        return self._clamp_alpha(final_alpha)

    def _record_button_slot_perf(self, mode):
        if not getattr(self, '_log_perf', False):
            return
        stats = getattr(self, '_button_slot_perf_stats', None)
        if not isinstance(stats, dict):
            stats = {}
            self._button_slot_perf_stats = stats
        item = stats.get(mode)
        if not isinstance(item, dict):
            item = {'count': 0}
            stats[mode] = item
        item['count'] = item.get('count', 0) + 1

    def _make_element_signature(self, value):
        if value is None:
            return ('none',)
        if isinstance(value, (list, tuple)):
            result = []
            result.append(('kind', 'list'))
            for item in value:
                result.append(self._make_element_signature(item))
            return tuple(result)

        node_type = getattr(value, 'node_type', None)
        props = getattr(value, 'props', None)
        children = getattr(value, 'children', None)
        if node_type is not None or props is not None or children is not None:
            return (
                'node',
                self._safe_text(getattr(node_type, '__name__', node_type)),
                self._make_props_signature(props),
                self._make_element_signature(children or []),
            )
        return ('value', self._safe_text(value))

    def _make_props_signature(self, props):
        if not isinstance(props, dict):
            return ()
        result = []
        for key in sorted(props.keys()):
            if key == 'children':
                result.append((key, self._make_element_signature(props.get(key))))
            else:
                value = props.get(key)
                if callable(value):
                    result.append((key, 'callable'))
                elif isinstance(value, dict):
                    result.append((key, self._make_props_signature(value)))
                elif isinstance(value, (list, tuple)):
                    result.append((key, tuple([self._safe_text(v) for v in value])))
                else:
                    result.append((key, self._safe_text(value)))
        return tuple(result)

    def _call_button_builder(self, builder, state):
        try:
            return builder(state)
        except Exception:
            return None

    def _default_button_state_builder(self, state, children=None):
        from pyreact.components.primitives import Image

        texture = self._BUTTON_STATE_TEXTURES.get(state)
        if not texture:
            return None

        return Image(
            style={
                "width": "100%",
                "height": "100%",
            },
            src=texture,
        )

    def _render_state_element_into_slot(self, state_element, slot_path, slot_width, slot_height, cache_already_cleared=False, inherited_opacity=1.0):
        from pyreact.components.primitives import Panel

        state_children = self._normalize_children_for_builder(state_element)
        if not state_children:
            return

        state_root = Panel(
            style={
                "width": "100%",
                "height": "100%",
            },
            children=state_children,
        )
        shadow_root = self._layout_engine.calculate(state_root, slot_width, slot_height, inherited_opacity=inherited_opacity)
        try:
            slot_control = self._get_base_ui_control(slot_path)
        except Exception:
            slot_control = None
        self._render_children(
            children=getattr(shadow_root, "children", []) or [],
            parent_path=slot_path,
            parent_abs_x=0.0,
            parent_abs_y=0.0,
            cache_already_cleared=cache_already_cleared,
            parent_control=slot_control,
        )

    def _normalize_children_for_builder(self, value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    def _get_def_path(self, node_type):
        return self._root_path + "/" + self._TYPE_DEF_SUFFIX_MAP.get(node_type, "panelBase")

    def _extract_node_style(self, node, props):
        style = getattr(node, "style", None)
        if isinstance(style, dict):
            return style
        maybe_style = props.get("style")
        if isinstance(maybe_style, dict):
            return maybe_style
        return {}

    def _extract_image_props(self, props):
        image_props = {}
        prop_keys = (
            "src",
            "color",
            "grayscale",
            "clipRatio",
            "uv",
            "uvSize",
            "resizeMode",
            "imageAdaptionType",
            "nineSlice",
            "nineSliceType",
            "rotation",
            "rotatePivot",
        )
        for key in prop_keys:
            if isinstance(props, dict) and props.get(key) is not None:
                image_props[key] = props.get(key)
        return image_props

    def _extract_label_props(self, props):
        label_props = {}
        prop_keys = (
            "color",
            "fontSize",
            "font",
            "textAlign",
            "linePadding",
            "shadow",
        )
        for key in prop_keys:
            if isinstance(props, dict) and props.get(key) is not None:
                label_props[key] = props.get(key)
        return label_props

    def _resolve_item_props(self, props):
        resolved = {
            'identifier': None,
            'aux': None,
            'enchant': None,
            'userData': None,
        }
        if not isinstance(props, dict):
            return resolved

        item_dict = props.get('itemDict')
        if isinstance(item_dict, dict):
            resolved.update(self._build_item_props_from_dict(item_dict))

        if props.get('identifier') is not None:
            resolved['identifier'] = props.get('identifier')
        if props.get('aux') is not None:
            resolved['aux'] = props.get('aux')
        if props.get('enchant') is not None:
            resolved['enchant'] = props.get('enchant')
        if props.get('userData') is not None:
            resolved['userData'] = props.get('userData')

        return resolved

    def _build_item_props_from_dict(self, item_dict):
        resolved = {
            'identifier': None,
            'aux': None,
            'enchant': None,
            'userData': None,
        }
        if not isinstance(item_dict, dict):
            return resolved

        if item_dict.get('newItemName') is not None:
            resolved['identifier'] = item_dict.get('newItemName')
        elif item_dict.get('itemName') is not None:
            resolved['identifier'] = item_dict.get('itemName')

        if item_dict.get('newAuxValue') is not None:
            resolved['aux'] = item_dict.get('newAuxValue')
        elif item_dict.get('auxValue') is not None:
            resolved['aux'] = item_dict.get('auxValue')

        if item_dict.get('userData') is not None:
            resolved['userData'] = item_dict.get('userData')

        enchant_data = item_dict.get('enchantData')
        mod_enchant_data = item_dict.get('modEnchantData')
        resolved['enchant'] = bool(enchant_data or mod_enchant_data)

        return resolved

    def _apply_item_native_props(self, node_path, item_props, node_control=None):
        if not isinstance(item_props, dict):
            return

        identifier = self._safe_text(item_props.get('identifier'))
        if not identifier:
            return

        aux_value = item_props.get('aux')
        if aux_value is None:
            aux_value = 0

        enchant_flag = item_props.get('enchant')
        if enchant_flag is None:
            enchant_flag = False

        self._safe_set_ui_item(
            node_path,
            identifier,
            aux_value,
            enchant_flag,
            item_props.get('userData'),
            node_control,
        )

    def _extract_paper_doll_props(self, props):
        result = {}
        if not isinstance(props, dict):
            return result
        for key in (
            'renderType',
            'entityId',
            'entityIdentifier',
            'skeletonModelName',
            'animation',
            'animationLooped',
            'blockGeometryModelName',
            'scale',
            'renderDepth',
            'initRotX',
            'initRotY',
            'initRotZ',
            'molangDict',
            'rotationAxis',
            'lightDirection',
        ):
            if props.get(key) is not None:
                result[key] = props.get(key)
        return result

    def _apply_paper_doll_native_props(self, node_path, paper_doll_props, node_control=None):
        if not isinstance(paper_doll_props, dict):
            return
        control = self._to_paper_doll_control(node_control, node_path)
        if not control:
            return

        params = self._build_paper_doll_params(paper_doll_props)
        signature = self._make_props_signature(params)
        cache = getattr(self, '_native_paper_doll_props_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._native_paper_doll_props_cache = cache
        if cache.get(node_path) == signature:
            return

        render_type = self._safe_text(paper_doll_props.get('renderType') or 'entity')
        ok = False
        if render_type == 'skeleton':
            if hasattr(control, 'RenderSkeletonModel'):
                ok = self._native_api_call('RenderSkeletonModel', control.RenderSkeletonModel, params)
        elif render_type == 'blockGeometry':
            if hasattr(control, 'RenderBlockGeometryModel'):
                ok = self._native_api_call('RenderBlockGeometryModel', control.RenderBlockGeometryModel, params)
        else:
            if hasattr(control, 'RenderEntity'):
                ok = self._native_api_call('RenderEntity', control.RenderEntity, params)
        if ok is not False:
            cache[node_path] = signature

    def _build_paper_doll_params(self, props):
        params = {}
        key_map = {
            'entityId': 'entity_id',
            'entityIdentifier': 'entity_identifier',
            'skeletonModelName': 'skeleton_model_name',
            'animation': 'animation',
            'animationLooped': 'animation_looped',
            'blockGeometryModelName': 'block_geometry_model_name',
            'scale': 'scale',
            'renderDepth': 'render_depth',
            'initRotX': 'init_rot_x',
            'initRotY': 'init_rot_y',
            'initRotZ': 'init_rot_z',
            'molangDict': 'molang_dict',
            'rotationAxis': 'rotation_axis',
            'lightDirection': 'light_direction',
        }
        for key, native_key in key_map.items():
            if props.get(key) is None:
                continue
            value = props.get(key)
            if key in ('rotationAxis', 'lightDirection'):
                parsed = self._parse_vec3(value)
                if parsed is not None:
                    value = parsed
                else:
                    continue
            params[native_key] = value
        return params

    def _apply_common_style_props(self, node_path, style, props, node_control, node=None, inherited_opacity=None):
        if not isinstance(style, dict):
            style = {}
        if not isinstance(props, dict):
            props = {}

        cache = self._get_native_common_style_cache()
        cached_style = cache.get(node_path, {})
        next_cached_style = {}

        display = self._safe_text(style.get("display")).strip().lower()
        if display == "none":
            next_cached_style['display'] = display
            if cached_style.get('display') != display:
                self._safe_set_visible(node_path, False, node_control)
        elif display:
            next_cached_style['display'] = display
            if cached_style.get('display') != display:
                self._safe_set_visible(node_path, True, node_control)
        elif 'display' in cached_style:
            self._safe_set_visible(node_path, True, node_control)

        opacity = style.get("opacity")
        color = props.get("color")  # type: Color

        if opacity is not None or color is not None or node is not None or inherited_opacity is not None:
            final_alpha = self._resolve_common_alpha(style, props, node, inherited_opacity)
            next_cached_style['opacity'] = final_alpha
            if cached_style.get('opacity') != final_alpha:
                self._safe_set_alpha(node_path, final_alpha, node_control)

        elif 'opacity' in cached_style:
            self._safe_set_alpha(node_path, 1.0, node_control)

        layer = style.get("zIndex")
        if layer is not None:
            layer_value = int(round(self._to_float(layer, 0.0)))
            next_cached_style['zIndex'] = layer_value
            if cached_style.get('zIndex') != layer_value:
                self._safe_set_layer(node_path, layer_value, node_control)
        elif 'zIndex' in cached_style:
            self._safe_set_layer(node_path, 0, node_control)

        cache[node_path] = next_cached_style

    def _apply_image_style_props(self, node_path, image_props, node_control):
        if not isinstance(image_props, dict):
            image_props = {}

        cache = getattr(self, '_native_image_props_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._native_image_props_cache = cache
        cached = cache.get(node_path, {})
        next_cached = {}

        src = self._safe_text(image_props.get("src", ""))
        if not src:
            src = self._DEFAULT_WHITE_TEXTURE
        next_cached['src'] = src
        if cached.get('src') != src:
            self._safe_set_sprite(node_path, src, node_control)

        color = self._parse_text_color(image_props.get("color"))
        if color is not None:
            color_sig = self._to_rgb_tuple(color)
            next_cached['color'] = color_sig
            if cached.get('color') != color_sig:
                self._safe_set_sprite_color(node_path, color, node_control)

        gray_value = image_props.get("grayscale")
        if gray_value is not None:
            gray_sig = self._to_bool(gray_value)
            next_cached['grayscale'] = gray_sig
            if cached.get('grayscale') != gray_sig:
                self._safe_set_sprite_gray(node_path, gray_sig, node_control)

        clip_ratio = image_props.get("clipRatio")
        if clip_ratio is not None:
            clip_sig = self._to_float(clip_ratio, 1.0)
            next_cached['clipRatio'] = clip_sig
            if cached.get('clipRatio') != clip_sig:
                self._safe_set_sprite_clip_ratio(node_path, clip_ratio, node_control)

        uv = self._parse_vec2(image_props.get("uv"))
        if uv is not None:
            next_cached['uv'] = uv
            if cached.get('uv') != uv:
                self._safe_set_sprite_uv(node_path, uv, node_control)

        uv_size = self._parse_vec2(image_props.get("uvSize"))
        if uv_size is not None:
            next_cached['uvSize'] = uv_size
            if cached.get('uvSize') != uv_size:
                self._safe_set_sprite_uv_size(node_path, uv_size, node_control)

        adaption_type = self._parse_image_adaption_type(image_props)
        nine_slice = self._parse_vec4(image_props.get("nineSlice"))
        if adaption_type:
            adaption_sig = (adaption_type, nine_slice)
            next_cached['imageAdaptionType'] = adaption_sig
            if cached.get('imageAdaptionType') != adaption_sig:
                self._safe_set_image_adaption_type(node_path, adaption_type, nine_slice, node_control)
        elif nine_slice is not None:
            nine_slice_type = self._safe_text(image_props.get("nineSliceType", "originNineSlice"))
            if nine_slice_type not in ("oldNineSlice", "originNineSlice"):
                nine_slice_type = "originNineSlice"
            adaption_sig = (nine_slice_type, nine_slice)
            next_cached['imageAdaptionType'] = adaption_sig
            if cached.get('imageAdaptionType') != adaption_sig:
                self._safe_set_image_adaption_type(node_path, nine_slice_type, nine_slice, node_control)

        rotation = image_props.get("rotation")
        if rotation is not None:
            rotation_sig = self._to_float(rotation, 0.0)
            next_cached['rotation'] = rotation_sig
            if cached.get('rotation') != rotation_sig:
                self._safe_rotate(node_path, rotation_sig, node_control)

        rotate_pivot = self._parse_vec2(image_props.get("rotatePivot"))
        if rotate_pivot is not None:
            next_cached['rotatePivot'] = rotate_pivot
            if cached.get('rotatePivot') != rotate_pivot:
                self._safe_set_rotate_pivot(node_path, rotate_pivot, node_control)

        cache[node_path] = next_cached

    def _queue_button_bind(self, button_path, node_id):
        safe_button_path = self._safe_text(button_path)
        bind_cache = getattr(self, '_button_bind_cache', None)
        if isinstance(bind_cache, dict) and bind_cache.get(safe_button_path):
            return
        pending = getattr(self, '_pending_button_binds', None)
        if not isinstance(pending, dict):
            pending = {}
            self._pending_button_binds = pending
        pending[safe_button_path] = node_id

    def _flush_pending_button_binds(self):
        pending = getattr(self, '_pending_button_binds', None)
        if not isinstance(pending, dict) or not pending:
            return
        items = list(pending.items())
        pending.clear()
        for button_path, node_id in items:
            self._bind_button_click(button_path, node_id)

    def _bind_button_click(self, button_path, node_id):
        bind_start_time = self._perf_clock()
        bind_cache = getattr(self, '_button_bind_cache', None)
        if not isinstance(bind_cache, dict):
            bind_cache = {}
            self._button_bind_cache = bind_cache
        safe_button_path = self._safe_text(button_path)
        if bind_cache.get(safe_button_path):
            self._record_native_commit_perf('button_bind_skip')
            return

        control = self._get_base_ui_control(button_path)
        if not control:
            return
        try:
            button_control = self._to_button_control(control, button_path)
            if not button_control:
                return

            try:
                self._native_api_call('AddTouchEventParams', button_control.AddTouchEventParams, {"isSwallow":True})
            except Exception:
                pass

            def _callback(args=None):
                self._dispatch_click(node_id)

            self._native_api_call('SetButtonTouchUpCallback', button_control.SetButtonTouchUpCallback, _callback)
            bind_cache[safe_button_path] = True
            bind_ms = (self._perf_clock() - bind_start_time) * 1000.0
            self._record_native_commit_perf('button_bind_count')
            self._record_native_commit_perf('button_bind_ms', bind_ms)
            self._record_native_commit_perf_max('button_bind_max_ms', bind_ms)
        except Exception:
            pass

    def _dispatch_click(self, node_id):
        callback = self._button_callbacks.get(node_id)
        if callback:
            callback()

    def _clear_prefixed_children(self, parent_path):
        try:
            names = self._get_children_name(parent_path) or []
        except Exception:
            names = []

        remove_paths = []
        for name in names:
            safe_name = self._safe_text(name)
            is_ghost = False
            try:
                is_ghost = self._is_exit_animation_ghost_child_name(safe_name)
            except Exception:
                is_ghost = False
            if (not safe_name.startswith(self._CONTROL_NAME_PREFIX)) and (not is_ghost):
                continue
            child_path = parent_path + "/" + safe_name
            remove_paths.append(child_path)

        if remove_paths:
            self._drop_native_common_style_cache_many(remove_paths)

        for child_path in remove_paths:
            try:
                try:
                    self._remove_animation_state_for_path(child_path)
                except Exception:
                    pass
                self._remove_component_by_path(child_path, skip_cache_drop=True)
                self._record_native_commit_perf('remove_component')
            except Exception:
                pass

    def _prune_prefixed_children(self, parent_path, expected_child_names):
        expected_child_names = expected_child_names or []
        expected = {}
        for n in expected_child_names:
            try:
                expected[self._safe_text(n)] = True
            except Exception:
                pass

        try:
            names = self._get_children_name(parent_path) or []
        except Exception:
            names = []

        remove_paths = []
        for name in names:
            safe_name = self._safe_text(name)
            is_ghost = False
            try:
                is_ghost = self._is_exit_animation_ghost_child_name(safe_name)
            except Exception:
                is_ghost = False
            if (not safe_name.startswith(self._CONTROL_NAME_PREFIX)) and (not is_ghost):
                continue
            if safe_name in expected:
                continue

            child_path = parent_path + "/" + safe_name
            remove_paths.append(child_path)

        actual_remove_paths = []
        for child_path in remove_paths:
            try:
                if self._start_exit_animation_for_existing_path(child_path):
                    continue
            except Exception:
                pass
            actual_remove_paths.append(child_path)

        if actual_remove_paths:
            self._drop_native_common_style_cache_many(actual_remove_paths)

        for child_path in actual_remove_paths:
            try:
                try:
                    self._remove_animation_state_for_path(child_path)
                except Exception:
                    pass
                self._remove_component_by_path(child_path, skip_cache_drop=True)
                self._record_native_commit_perf('remove_component')
            except Exception:
                pass
