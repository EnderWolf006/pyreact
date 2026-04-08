# -*- coding: utf-8 -*-

import time

import mod.client.extraClientApi as clientApi


class RuntimeLifecycleMixin(object):
    def _get_native_control_def_cache(self):
        cache = getattr(self, '_native_control_def_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._native_control_def_cache = cache
        return cache

    def _remember_native_control_def(self, control_path, def_name):
        cache = self._get_native_control_def_cache()
        cache[self._safe_text(control_path)] = self._safe_text(def_name)

    def _get_native_control_def(self, control_path):
        cache = self._get_native_control_def_cache()
        return self._safe_text(cache.get(self._safe_text(control_path)))

    def _drop_native_control_defs(self, path_prefix=None):
        cache = self._get_native_control_def_cache()
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

    def _get_pooled_control_paths(self):
        pooled = getattr(self, '_pooled_control_paths', None)
        if not isinstance(pooled, dict):
            pooled = {}
            self._pooled_control_paths = pooled
        return pooled

    def _mark_control_pooled(self, control_path, pooled=True):
        cache = self._get_pooled_control_paths()
        safe_path = self._safe_text(control_path)
        if not safe_path:
            return
        if pooled:
            cache[safe_path] = True
            return
        try:
            del cache[safe_path]
        except Exception:
            pass

    def _is_control_pooled(self, control_path):
        cache = self._get_pooled_control_paths()
        return bool(cache.get(self._safe_text(control_path)))

    def _drop_pooled_control_paths(self, path_prefix=None):
        cache = self._get_pooled_control_paths()
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

    def _park_control(self, control_path, control=None):
        hidden_pos = getattr(self, '_POOL_HIDDEN_POSITION', -100000.0)
        self._safe_set_visible(control_path, False, control)
        self._safe_set_position(control_path, hidden_pos, hidden_pos, control)

    def _pool_control_if_exists(self, control_path, control=None):
        target = control
        if not target:
            try:
                target = self._screen.GetBaseUIControl(control_path)
            except Exception:
                target = None
        if not target:
            return False
        self._park_control(control_path, target)
        self._mark_control_pooled(control_path, True)
        return True

    def _activate_control_for_reuse(self, control_path, control=None):
        self._drop_native_prop_cache(control_path)
        self._drop_native_common_style_cache(control_path)
        self._safe_set_visible(control_path, True, control)
        self._mark_control_pooled(control_path, False)

    def _obtain_native_control(self, parent_control_path, control_path, child_name, node_type, parent_control=None):
        def_name = self._get_def_name(node_type)
        try:
            control = self._screen.GetBaseUIControl(control_path)
        except Exception:
            control = None

        if control:
            cached_def_name = self._get_native_control_def(control_path)
            if cached_def_name and cached_def_name != def_name:
                try:
                    self._remove_control_if_exists(control_path, control)
                except Exception:
                    pass
                control = None
            else:
                self._activate_control_for_reuse(control_path, control)

        if not control:
            if not parent_control:
                try:
                    parent_control = self._screen.GetBaseUIControl(parent_control_path)
                except Exception:
                    parent_control = None
            if not parent_control:
                return None

            try:
                self._screen.CreateChildControl(def_name, child_name, parent_control)
            except Exception:
                pass
            control = self._screen.GetBaseUIControl(control_path)
            if not control:
                return None
            self._count_native_api_call('CreateChildControl')
            self._drop_native_common_style_cache(control_path)
            self._drop_native_prop_cache(control_path)

        self._remember_native_control_def(control_path, def_name)
        return control

    def _is_stable_keyed_node_id(self, node_id):
        safe_node_id = self._safe_text(node_id or '')
        return safe_node_id.startswith('k_')

    def _build_native_child_name(self, node_id, shadow_path):
        safe_node_id = self._safe_text(node_id or 'node') or 'node'
        if self._is_stable_keyed_node_id(safe_node_id):
            return "%s%s" % (self._CONTROL_NAME_PREFIX, safe_node_id)
        if not shadow_path:
            return "%s%s_root" % (self._CONTROL_NAME_PREFIX, safe_node_id)
        path_token = '_'.join([str(index) for index in shadow_path])
        return "%s%s_%s" % (self._CONTROL_NAME_PREFIX, safe_node_id, path_token)

    def _get_child_shadow_base(self, node, shadow_path):
        if self._is_stable_keyed_node_id(getattr(node, 'node_id', None)):
            return []
        return shadow_path

    def _is_layout_only_panel_node(self, node):
        if node is None or isinstance(node, (list, tuple)):
            return False
        if self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel') != 'Panel':
            return False
        if self._is_stable_keyed_node_id(getattr(node, 'node_id', None)):
            return False

        props = getattr(node, 'props', None) or {}
        if not isinstance(props, dict):
            props = {}
        if props.get('ref') is not None:
            return False

        style = getattr(node, 'style', None) or {}
        if not isinstance(style, dict):
            style = {}

        display = self._safe_text(style.get('display')).strip().lower()
        if display == 'none':
            return False
        if style.get('opacity') is not None:
            return False
        if style.get('zIndex') is not None:
            return False
        return True

    def _remove_control_if_exists(self, control_path, control=None):
        target = control
        if not target:
            try:
                target = self._screen.GetBaseUIControl(control_path)
            except Exception:
                target = None
        if not target:
            return False
        try:
            self._screen.RemoveChildControl(target)
            self._count_native_api_call('RemoveChildControl')
        except Exception:
            return False
        self._drop_native_control_defs(control_path)
        self._drop_pooled_control_paths(control_path)
        self._drop_native_common_style_cache(control_path)
        self._drop_native_prop_cache(control_path)
        self._drop_button_slot_vtrees(control_path)
        return True

    def _log_render_stage_timings(self, component_ms, build_ms, diff_ms, layout_ms, native_ms):
        if not getattr(self, '_log_perf', False):
            return
        try:
            print('=====> PyreactRuntime[perf] 1. 组件函数执行: %.3fms <=====' % component_ms)
            print('=====> PyreactRuntime[perf] 2. 构建VNode树: %.3fms <=====' % build_ms)
            print('=====> PyreactRuntime[perf] 3. Diff计算: %.3fms <=====' % diff_ms)
            print('=====> PyreactRuntime[perf] 4. 布局计算: %.3fms <=====' % layout_ms)
            print('=====> PyreactRuntime[perf] 5. 应用到原生UI: %.3fms <=====' % native_ms)
        except Exception:
            pass

    def _init_pyreact_runtime(self):
        from pyreact.layout.layout_engine import LayoutEngine
        from pyreact.renderer.text_measurer import TextMeasurer
        from pyreact.core.component import ComponentInstance
        from pyreact.core.tree_builder import TreeBuilder
        from pyreact.core.reconciler import Reconciler

        self._text_measurer = TextMeasurer(native_measure=self._measure_text_native)
        self._layout_engine = LayoutEngine(text_measurer=self._text_measurer)
        self._component_instance = ComponentInstance(
            component_fn=self._app_fn,
            rerender_callback=self.request_render,
        )
        self._tree_builder = TreeBuilder()
        self._reconciler = Reconciler()

    def mount(self):
        self._mounted = True
        self._ensure_measure_label()
        self.render()

    def unmount(self):
        self._mounted = False
        self._button_callbacks = {}
        self._input_callbacks = {}
        self._input_paths = {}
        self._input_last_values = {}
        self._node_refs = {}
        try:
            self._clear_all_refs()
        except Exception:
            pass
        try:
            self._unbind_input_edit_handlers()
        except Exception:
            pass
        self._prev_vtree = None
        self._prev_shadow_root = None
        self._measure_label_path = None
        self._drop_pooled_control_paths()
        self._drop_native_common_style_cache()
        self._drop_native_prop_cache()
        self._drop_native_control_defs()
        self._drop_button_slot_vtrees()
        self._clear_root_children()

    def request_render(self):
        if not self._mounted:
            return
        if self._is_rendering:
            self._needs_render = True
            return
        if self._render_scheduled:
            return
        self._render_scheduled = True
        if not self._schedule_render():
            self._render_scheduled = False
            self.render()

    def render(self):
        if not self._mounted:
            return

        self._render_scheduled = False
        self._is_rendering = True
        try:
            self._button_callbacks = {}
            self._input_callbacks = {}
            self._input_paths = {}
            self._node_refs = {}

            element = self._component_instance.render()
            component_ms = getattr(self._component_instance, 'last_render_duration_ms', 0.0)
            new_vtree = None
            build_ms = 0.0

            if element is None:
                diff_start_time = time.time()
                mutations = self._reconciler.reconcile(self._prev_vtree, None)
                diff_ms = (time.time() - diff_start_time) * 1000.0

                native_start_time = time.time()
                self._begin_native_update_batch()
                try:
                    self._prev_vtree = None
                    self._prev_shadow_root = None
                    self._input_callbacks = {}
                    self._input_paths = {}
                    self._input_last_values = {}
                    self._node_refs = {}
                    try:
                        self._clear_all_refs()
                    except Exception:
                        pass
                    try:
                        self._unbind_input_edit_handlers()
                    except Exception:
                        pass
                    self._clear_root_children()
                finally:
                    self._flush_native_update_batch()
                native_ms = (time.time() - native_start_time) * 1000.0
                self._log_render_stage_timings(component_ms, build_ms, diff_ms, 0.0, native_ms)
                return

            width, height = self._get_root_size()

            new_vtree = self._tree_builder.build_tree(element)
            tree_perf = self._tree_builder.get_last_perf_stats()
            component_ms += tree_perf.get('component_exec_ms', 0.0)
            build_ms = tree_perf.get('build_only_ms', 0.0)

            diff_start_time = time.time()
            mutations = self._reconciler.reconcile(self._prev_vtree, new_vtree)
            diff_ms = (time.time() - diff_start_time) * 1000.0

            layout_start_time = time.time()
            shadow_root = self._layout_engine.calculate(new_vtree, width, height)
            layout_ms = (time.time() - layout_start_time) * 1000.0

            native_start_time = time.time()
            self._begin_native_update_batch()
            try:
                if self._can_apply_incremental(mutations):
                    self._apply_incremental_updates(shadow_root, mutations)
                    self._refresh_button_callbacks(shadow_root)
                else:
                    if getattr(self, '_debug_render', False):
                        counts = {}
                        muts = mutations or []
                        for m in muts:
                            t = self._safe_text(getattr(m, 'type_', ''))
                            counts[t] = counts.get(t, 0) + 1
                    self._clear_root_children()
                    self._render_children(
                        children=[shadow_root],
                        parent_path=self._root_path,
                        parent_abs_x=0.0,
                        parent_abs_y=0.0,
                        parent_shadow_path=[],
                    )
            finally:
                self._flush_native_update_batch()
            native_ms = (time.time() - native_start_time) * 1000.0

            self._log_render_stage_timings(component_ms, build_ms, diff_ms, layout_ms, native_ms)

            self._prev_vtree = new_vtree
            self._prev_shadow_root = shadow_root
            try:
                self._cleanup_input_state()
            except Exception:
                pass
            try:
                self._cleanup_refs()
            except Exception:
                pass
        finally:
            self._is_rendering = False
            if self._needs_render:
                self._needs_render = False
                self.request_render()

    def _schedule_render(self):
        try:
            game_comp = clientApi.CreateComponent(clientApi.GetLevelId(), 'Minecraft', 'game')
            if not game_comp:
                return False

            def _deferred_render():
                self.render()

            game_comp.AddTimer(0, _deferred_render)
            return True
        except Exception:
            return False

    def _get_root_size(self):
        try:
            size = self._screen.GetSize(self._root_path)
            if size and len(size) >= 2:
                width = float(size[0])
                height = float(size[1])
                if width > 0 and height > 0:
                    return (width, height)
        except Exception:
            pass
        return (1280.0, 720.0)

    def _can_apply_incremental(self, mutations):
        if self._prev_vtree is None or self._prev_shadow_root is None:
            return False

        # Incremental render can handle CREATE/DELETE/MOVE by creating missing
        # controls and pruning orphaned prefixed children during the layout walk.
        # We only fall back to a full rebuild when the previous tree is absent.
        return True

    def _apply_incremental_updates(self, new_shadow_root, mutations):
        recreate_paths = {}
        muts = mutations or []
        for m in muts:
            try:
                if self._safe_text(getattr(m, 'type_', '')) != 'CREATE':
                    continue
                path = getattr(m, 'path', []) or []
                recreate_paths[tuple(path)] = True
            except Exception:
                pass
        self._apply_layout_to_existing_tree(
            current_node=[new_shadow_root],
            parent_control_path=self._root_path,
            parent_abs_x=0.0,
            parent_abs_y=0.0,
            shadow_path=[],
            recreate_paths=recreate_paths,
        )

    def _apply_layout_to_existing_tree(self, current_node, parent_control_path, parent_abs_x, parent_abs_y, shadow_path, recreate_paths, prune_current_level=True):
        if current_node is None:
            return []

        if isinstance(current_node, (list, tuple)):
            children = list(current_node)
            current_node_type = "Panel"
            node_layout = None
            node_props = {}
        else:
            current_node_type = self._safe_text(getattr(current_node, 'node_type', 'Panel') or 'Panel')
            children = self._get_render_children(current_node, current_node_type)
            node_layout = getattr(current_node, 'layout', None)
            node_props = getattr(current_node, 'props', {}) or {}

        children_parent_path = parent_control_path
        if current_node_type == "Scroll" and node_layout:
            content_path = self._get_scroll_content_path(parent_control_path)
            content_control = self._screen.GetBaseUIControl(content_path)
            if content_control:
                self._safe_set_size(content_path, node_layout.content_width, node_layout.content_height, content_control)
                children_parent_path = content_path

            self._apply_scroll_props(current_node, parent_control_path)

        if not children:
            if prune_current_level:
                try:
                    # Ensure we remove stale prefixed children when the new tree has none.
                    self._prune_prefixed_children(children_parent_path, [])
                except Exception:
                    pass
            return []

        index = 0
        expected_child_names = []
        for node in children:
            node_id = self._safe_text(getattr(node, 'node_id', 'node'))
            node_type = self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
            layout = getattr(node, 'layout', None)
            abs_x = self._to_float(getattr(layout, 'x', 0.0), 0.0)
            abs_y = self._to_float(getattr(layout, 'y', 0.0), 0.0)
            width = self._to_float(getattr(layout, 'width', 0.0), 0.0)
            height = self._to_float(getattr(layout, 'height', 0.0), 0.0)

            next_shadow_path = list(shadow_path)
            next_shadow_path.append(index)
            child_name = self._build_native_child_name(node_id, next_shadow_path)

            control_path = children_parent_path + '/' + child_name
            child_control_paths = control_path

            if self._is_layout_only_panel_node(node):
                self._pool_control_if_exists(control_path)
                nested_expected = self._apply_layout_to_existing_tree(
                    current_node=node,
                    parent_control_path=children_parent_path,
                    parent_abs_x=parent_abs_x,
                    parent_abs_y=parent_abs_y,
                    shadow_path=next_shadow_path,
                    recreate_paths=recreate_paths,
                    prune_current_level=False,
                )
                if nested_expected:
                    expected_child_names.extend(nested_expected)
                if self._needs_render:
                    return expected_child_names
                index += 1
                continue

            expected_child_names.append(child_name)
            control = self._obtain_native_control(
                parent_control_path=children_parent_path,
                control_path=control_path,
                child_name=child_name,
                node_type=node_type,
            )
            if not control:
                self._needs_render = True
                return expected_child_names
            self._apply_deferred_node_props(node, control_path, control)
            self._safe_set_position(control_path, abs_x - parent_abs_x, abs_y - parent_abs_y, control)
            if node_type != "Label":
                self._safe_set_size(control_path, width, height, control)
            self._apply_node_props(node, control_path, node_type, node_id, control)
            self._apply_immediate_node_props(node, control_path, control)

            self._apply_layout_to_existing_tree(
                current_node=node,
                parent_control_path=child_control_paths,
                parent_abs_x=abs_x,
                parent_abs_y=abs_y,
                shadow_path=self._get_child_shadow_base(node, next_shadow_path),
                recreate_paths=recreate_paths,
            )

            if self._needs_render:
                return expected_child_names
            index += 1

        if prune_current_level:
            try:
                # Remove any orphaned prefixed children not present in the new tree.
                self._prune_prefixed_children(children_parent_path, expected_child_names)
            except Exception:
                pass
        return expected_child_names

    def _refresh_button_callbacks(self, shadow_root):
        self._button_callbacks = {}
        self._refresh_button_callbacks_walk([shadow_root], self._root_path, [])

    def _refresh_button_callbacks_walk(self, current_node, parent_control_path, shadow_path):
        if current_node is None:
            return

        if isinstance(current_node, (list, tuple)):
            children = list(current_node)
            current_type = "Panel"
        else:
            current_type = self._safe_text(getattr(current_node, 'node_type', 'Panel') or 'Panel')
            children = self._get_render_children(current_node, current_type)

        children_parent_path = parent_control_path
        if current_type == "Scroll":
            children_parent_path = self._get_scroll_content_path(parent_control_path)

        index = 0
        for child in children:
            child_id = self._safe_text(getattr(child, 'node_id', 'node'))
            node_type = self._safe_text(getattr(child, 'node_type', 'Panel') or 'Panel')
            next_shadow_path = list(shadow_path)
            next_shadow_path.append(index)
            child_name = self._build_native_child_name(child_id, next_shadow_path)

            if self._is_layout_only_panel_node(child):
                self._refresh_button_callbacks_walk(child, children_parent_path, next_shadow_path)
                index += 1
                continue

            control_path = children_parent_path + '/' + child_name
            child_control_paths = control_path
            if node_type == 'Button':
                self._refresh_button_callback(child, control_path)

            child_shadow_base = self._get_child_shadow_base(child, next_shadow_path)
            self._refresh_button_callbacks_walk(child, child_control_paths, child_shadow_base)
            index += 1

    def _refresh_button_callback(self, button_node, button_path):
        props = getattr(button_node, "props", None) or {}
        if not isinstance(props, dict):
            return
        onclick = props.get("onClick")
        if not callable(onclick):
            return
        self._button_callbacks[button_path] = onclick
        self._bind_button_click(button_path)

    def _clear_root_children(self):
        try:
            names = self._screen.GetChildrenName(self._root_path) or []
        except Exception:
            names = []

        for name in names:
            if not self._safe_text(name).startswith(self._CONTROL_NAME_PREFIX):
                continue
            child_path = self._root_path + "/" + name
            try:
                child_control = self._screen.GetBaseUIControl(child_path)
                if child_control:
                    self._pool_control_if_exists(child_path, child_control)
            except Exception:
                pass

    def _render_children(self, children, parent_path, parent_abs_x, parent_abs_y, parent_shadow_path):
        index = 0
        for child in children:
            self._render_node(child, parent_path, parent_abs_x, parent_abs_y, index, parent_shadow_path)
            index += 1

    def _render_node(self, node, parent_path, parent_abs_x, parent_abs_y, sibling_index, parent_shadow_path):
        if node is None:
            return

        node_type = self._safe_text(getattr(node, "node_type", "Panel") or "Panel")
        def_name = self._get_def_name(node_type)
        node_id = self._safe_text(getattr(node, "node_id", "node"))
        shadow_path = list(parent_shadow_path)
        shadow_path.append(sibling_index)

        if self._is_layout_only_panel_node(node):
            children = self._get_render_children(node, node_type)
            self._render_children(children, parent_path, parent_abs_x, parent_abs_y, shadow_path)
            return

        child_name = self._build_native_child_name(node_id, shadow_path)

        parent_control = self._screen.GetBaseUIControl(parent_path)
        if not parent_control:
            return

        child_control = self._obtain_native_control(
            parent_control_path=parent_path,
            control_path=parent_path + "/" + child_name,
            child_name=child_name,
            node_type=node_type,
            parent_control=parent_control,
        )
        if not child_control:
            return

        node_path = parent_path + "/" + child_name
        layout = getattr(node, "layout", None)
        abs_x = self._to_float(getattr(layout, "x", 0.0), 0.0)
        abs_y = self._to_float(getattr(layout, "y", 0.0), 0.0)
        width = self._to_float(getattr(layout, "width", 0.0), 0.0)
        height = self._to_float(getattr(layout, "height", 0.0), 0.0)
        local_x = abs_x - parent_abs_x
        local_y = abs_y - parent_abs_y

        self._apply_deferred_node_props(node, node_path, child_control)
        self._safe_set_position(node_path, local_x, local_y, child_control)
        if node_type != "Label":
            self._safe_set_size(node_path, width, height, child_control)
        self._apply_node_props(node, node_path, node_type, node_id, child_control)
        self._apply_immediate_node_props(node, node_path, child_control)

        children_parent_path = node_path
        if node_type == "Scroll" and layout:
            content_path = self._get_scroll_content_path(node_path)
            content_control = self._screen.GetBaseUIControl(content_path)
            if content_control:
                self._safe_set_size(content_path, layout.content_width, layout.content_height, content_control)
                children_parent_path = content_path

            self._apply_scroll_props(node, node_path)

        child_parent_x = abs_x
        child_parent_y = abs_y
        children = self._get_render_children(node, node_type)
        child_shadow_base = self._get_child_shadow_base(node, shadow_path)
        self._render_children(children, children_parent_path, child_parent_x, child_parent_y, child_shadow_base)

    def _apply_scroll_props(self, node, node_path):
        props = getattr(node, "props", {}) or {}
        show_scrollbar = props.get("showScrollbar", True)

        track_path = self._get_scrollbar_track_path(node_path)
        if track_path:
            self._safe_set_visible(track_path, show_scrollbar)

    def _get_real_scroll_view_path(self, scroll_node_path):
        if not scroll_node_path:
            return ""

        touch_path = scroll_node_path + "/scroll_touch/scroll_view"
        try:
            touch_children = self._screen.GetChildrenName(touch_path) or []
        except Exception:
            touch_children = []
        if touch_children:
            return touch_path

        mouse_path = scroll_node_path + "/scroll_mouse/scroll_view"
        try:
            mouse_children = self._screen.GetChildrenName(mouse_path) or []
        except Exception:
            mouse_children = []
        if mouse_children:
            return mouse_path

        return ""

    def _get_scroll_content_path(self, scroll_node_path):
        real_scroll_view_path = self._get_real_scroll_view_path(scroll_node_path)
        if "/scroll_touch/" in real_scroll_view_path:
            return real_scroll_view_path + "/panel/background_and_viewport/scrolling_view_port/scrolling_content"
        if "/scroll_mouse/" in real_scroll_view_path:
            return real_scroll_view_path + "/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content"

        return scroll_node_path

    def _get_scrollbar_track_path(self, scroll_node_path):
        real_scroll_view_path = self._get_real_scroll_view_path(scroll_node_path)
        if "/scroll_touch/" in real_scroll_view_path:
            return real_scroll_view_path + "/panel/bar_and_track"
        if "/scroll_mouse/" in real_scroll_view_path:
            return real_scroll_view_path + "/stack_panel/bar_and_track"

        return ""

    def _get_render_children(self, node, node_type):
        children = getattr(node, "children", []) or []
        return children
