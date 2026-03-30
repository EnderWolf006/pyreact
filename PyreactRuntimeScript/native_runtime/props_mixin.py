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

    def _apply_node_props(self, node, node_path, node_type, node_id, node_control=None):
        props = getattr(node, "props", None) or {}
        if not isinstance(props, dict):
            return

        # Track and apply ref for this node.
        try:
            self._track_ref(node_id, node_path, props.get('ref'), node_control)
        except Exception:
            pass

        style = self._extract_node_style(node, props)
        self._apply_common_style_props(node_path, style, node_control)

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
                self._bind_button_click(node_path, node_id)

            self._render_button_state_slots(node, node_path)
            return

        if node_type == "Input":
            self._apply_input_props(node_path, node_id, props, node_control)
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
            cache.clear()
            return

        prefix = self._safe_text(path_prefix)
        if not prefix:
            cache.clear()
            return

        prefix_with_sep = prefix + '/'
        for cached_path in list(cache.keys()):
            safe_cached_path = self._safe_text(cached_path)
            if safe_cached_path == prefix or safe_cached_path.startswith(prefix_with_sep):
                try:
                    del cache[cached_path]
                except Exception:
                    pass

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
                control_obj = self._screen.GetBaseUIControl(node_path)
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

    def _render_button_state_slots(self, button_node, button_path):
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

        for state in self._BUTTON_STATES:
            slot_path = button_path + "/" + state
            slot_control = self._screen.GetBaseUIControl(slot_path)
            if not slot_control:
                continue

            self._safe_set_position(slot_path, 0, 0, slot_control)
            self._safe_set_size(slot_path, button_width, button_height, slot_control)
            self._clear_prefixed_children(slot_path)

            state_element = self._call_button_builder(builder, state)
            if state_element is None:
                continue

            self._render_state_element_into_slot(
                state_element=state_element,
                slot_path=slot_path,
                slot_width=button_width,
                slot_height=button_height,
            )

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

    def _render_state_element_into_slot(self, state_element, slot_path, slot_width, slot_height):
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
        shadow_root = self._layout_engine.calculate(state_root, slot_width, slot_height)
        self._render_children(
            children=getattr(shadow_root, "children", []) or [],
            parent_path=slot_path,
            parent_abs_x=0.0,
            parent_abs_y=0.0,
        )

    def _normalize_children_for_builder(self, value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    def _get_def_name(self, node_type):
        suffix = self._TYPE_DEF_SUFFIX_MAP.get(node_type, "panelBase")
        return "%s.%s" % (self._base_namespace, suffix)

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

    def _apply_common_style_props(self, node_path, style, node_control):
        if not isinstance(style, dict):
            return

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
        color = style.get("color") # type: Color
        if opacity is not None:
            alpha = self._to_float(opacity, 1.0)
            if color is not None:
                alpha *= color.alpha
            if alpha < 0.0:
                alpha = 0.0
            if alpha > 1.0:
                alpha = 1.0
            next_cached_style['opacity'] = alpha
            if cached_style.get('opacity') != alpha:
                self._safe_set_alpha(node_path, alpha, node_control)
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

        src = self._safe_text(image_props.get("src", ""))
        if not src:
            src = self._DEFAULT_WHITE_TEXTURE
        self._safe_set_sprite(node_path, src, node_control)

        color = self._parse_text_color(image_props.get("color"))
        if color is not None:
            self._safe_set_sprite_color(node_path, color, node_control)

        gray_value = image_props.get("grayscale")
        if gray_value is not None:
            self._safe_set_sprite_gray(node_path, self._to_bool(gray_value), node_control)

        clip_ratio = image_props.get("clipRatio")
        if clip_ratio is not None:
            self._safe_set_sprite_clip_ratio(node_path, clip_ratio, node_control)

        uv = self._parse_vec2(image_props.get("uv"))
        if uv is not None:
            self._safe_set_sprite_uv(node_path, uv, node_control)

        uv_size = self._parse_vec2(image_props.get("uvSize"))
        if uv_size is not None:
            self._safe_set_sprite_uv_size(node_path, uv_size, node_control)

        adaption_type = self._parse_image_adaption_type(image_props)
        nine_slice = self._parse_vec4(image_props.get("nineSlice"))
        if adaption_type:
            self._safe_set_image_adaption_type(node_path, adaption_type, nine_slice, node_control)
        elif nine_slice is not None:
            nine_slice_type = self._safe_text(image_props.get("nineSliceType", "originNineSlice"))
            if nine_slice_type not in ("oldNineSlice", "originNineSlice"):
                nine_slice_type = "originNineSlice"
            self._safe_set_image_adaption_type(node_path, nine_slice_type, nine_slice, node_control)

        rotation = image_props.get("rotation")
        if rotation is not None:
            self._safe_rotate(node_path, self._to_float(rotation, 0.0), node_control)

        rotate_pivot = self._parse_vec2(image_props.get("rotatePivot"))
        if rotate_pivot is not None:
            self._safe_set_rotate_pivot(node_path, rotate_pivot, node_control)

    def _bind_button_click(self, button_path, node_id):
        control = self._screen.GetBaseUIControl(button_path)
        if not control:
            return
        try:
            button_control = control.asButton()
            if not button_control:
                return

            try:
                button_control.AddTouchEventParams({"isSwallow":True})
            except Exception:
                pass

            def _callback(args=None):
                self._dispatch_click(node_id)

            button_control.SetButtonTouchUpCallback(_callback)
        except Exception:
            pass

    def _dispatch_click(self, node_id):
        callback = self._button_callbacks.get(node_id)
        if callback:
            callback()

    def _clear_prefixed_children(self, parent_path):
        try:
            names = self._screen.GetChildrenName(parent_path) or []
        except Exception:
            names = []

        for name in names:
            if not self._safe_text(name).startswith(self._CONTROL_NAME_PREFIX):
                continue
            child_path = parent_path + "/" + name
            try:
                child_control = self._screen.GetBaseUIControl(child_path)
                if child_control:
                    self._screen.RemoveChildControl(child_control)
                    self._drop_native_common_style_cache(child_path)
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
            names = self._screen.GetChildrenName(parent_path) or []
        except Exception:
            names = []

        for name in names:
            safe_name = self._safe_text(name)
            if not safe_name.startswith(self._CONTROL_NAME_PREFIX):
                continue
            if safe_name in expected:
                continue

            child_path = parent_path + "/" + safe_name
            try:
                child_control = self._screen.GetBaseUIControl(child_path)
                if child_control:
                    self._screen.RemoveChildControl(child_control)
                    self._drop_native_common_style_cache(child_path)
            except Exception:
                pass
