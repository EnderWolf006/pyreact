# -*- coding: utf-8 -*-

import time

import mod.client.extraClientApi as clientApi


class RuntimeLifecycleMixin(object):
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
        self._drop_native_common_style_cache()
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
            if getattr(self, '_debug_render', False):
                counts = {}
                muts = mutations or []
                for m in muts:
                    t = self._safe_text(getattr(m, 'type_', ''))
                    counts[t] = counts.get(t, 0) + 1
            self._clear_root_children()
            self._render_flat_tree([shadow_root], self._root_path)
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
        return False

    def _apply_incremental_updates(self, new_shadow_root, mutations):
        self._clear_root_children()
        self._render_flat_tree([new_shadow_root], self._root_path)

    def _get_control_name(self, node):
        node_id = self._safe_text(getattr(node, 'node_id', 'node'))
        return "%s%s" % (self._CONTROL_NAME_PREFIX, node_id)

    def _is_virtual_node(self, node_type):
        return node_type == 'Panel'

    def _make_parent_target(self, kind, path):
        return {
            'kind': kind,
            'path': path,
        }

    def _resolve_parent_target(self, parent_target):
        if not isinstance(parent_target, dict):
            return self._root_path

        kind = parent_target.get('kind')
        if kind == 'scroll_content_of_entry':
            scroll_parent_path = self._resolve_parent_target(parent_target.get('parent_target'))
            scroll_child_name = self._safe_text(parent_target.get('scroll_child_name'))
            if not scroll_child_name:
                return scroll_parent_path or self._root_path
            scroll_node_path = (scroll_parent_path or self._root_path) + '/' + scroll_child_name
            return self._get_scroll_content_path(scroll_node_path)

        path = parent_target.get('path')
        if kind == 'scroll_content':
            return self._get_scroll_content_path(path)
        return path or self._root_path

    def _collect_flat_entries(self, current_node, parent_target, entries):
        if current_node is None:
            return

        if isinstance(current_node, (list, tuple)):
            for child in current_node:
                self._collect_flat_entries(child, parent_target, entries)
            return

        node_type = self._safe_text(getattr(current_node, 'node_type', 'Panel') or 'Panel')
        children = self._get_render_children(current_node, node_type)

        if self._is_virtual_node(node_type):
            for child in children:
                self._collect_flat_entries(child, parent_target, entries)
            return

        child_name = self._get_control_name(current_node)
        entries.append({
            'node': current_node,
            'node_type': node_type,
            'node_id': self._safe_text(getattr(current_node, 'node_id', 'node')),
            'parent_target': parent_target,
            'child_name': child_name,
        })

        next_parent_target = parent_target
        if node_type == 'Scroll':
            next_parent_target = {
                'kind': 'scroll_content_of_entry',
                'parent_target': parent_target,
                'scroll_child_name': child_name,
            }

        for child in children:
            self._collect_flat_entries(child, next_parent_target, entries)

    def _render_flat_tree(self, children, root_parent_path):
        entries = []
        self._collect_flat_entries(children, self._make_parent_target('path', root_parent_path), entries)

        for entry in entries:
            self._render_flat_entry(entry)
            if self._needs_render:
                return

    def _render_flat_entry(self, entry):
        node = entry.get('node')
        parent_path = self._resolve_parent_target(entry.get('parent_target'))
        node_type = entry.get('node_type')
        node_id = entry.get('node_id')
        child_name = entry.get('child_name')
        node_path = parent_path + '/' + child_name

        parent_control = self._screen.GetBaseUIControl(parent_path)
        if not parent_control:
            self._needs_render = True
            return

        control = self._screen.GetBaseUIControl(node_path)
        if not control:
            def_name = self._get_def_name(node_type)
            try:
                self._screen.CreateChildControl(def_name, child_name, parent_control)
            except Exception:
                pass
            control = self._screen.GetBaseUIControl(node_path)
            if not control:
                self._needs_render = True
                return
            self._drop_native_common_style_cache(node_path)

        layout = getattr(node, 'layout', None)
        local_x = self._to_float(getattr(layout, 'x', 0.0), 0.0)
        local_y = self._to_float(getattr(layout, 'y', 0.0), 0.0)
        width = self._to_float(getattr(layout, 'width', 0.0), 0.0)
        height = self._to_float(getattr(layout, 'height', 0.0), 0.0)

        self._safe_set_position(node_path, local_x, local_y, control)
        if node_type != 'Label':
            self._safe_set_size(node_path, width, height, control)

        props = getattr(node, 'props', None)
        if isinstance(props, dict):
            props['__shadow_node__'] = node
        self._apply_node_props(node, node_path, node_type, node_id, control)
        if isinstance(props, dict) and '__shadow_node__' in props:
            try:
                del props['__shadow_node__']
            except Exception:
                pass

        if node_type == 'Scroll' and layout:
            content_path = self._get_scroll_content_path(node_path)
            content_control = self._screen.GetBaseUIControl(content_path)
            if content_control:
                self._safe_set_size(content_path, layout.content_width, layout.content_height, content_control)
            self._apply_scroll_props(node, node_path)

    def _refresh_button_callbacks(self, shadow_root):
        self._button_callbacks = {}
        self._refresh_button_callbacks_walk([shadow_root], self._root_path)

    def _refresh_button_callbacks_walk(self, current_node, parent_control_path):
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

        for child in children:
            node_type = self._safe_text(getattr(child, 'node_type', 'Panel') or 'Panel')
            if self._is_virtual_node(node_type):
                self._refresh_button_callbacks_walk(child, children_parent_path)
                continue

            child_name = self._get_control_name(child)
            control_path = children_parent_path + '/' + child_name
            child_control_paths = control_path
            if node_type == 'Button':
                self._refresh_button_callback(child, control_path)

            self._refresh_button_callbacks_walk(child, child_control_paths)

    def _refresh_button_callback(self, button_node, button_path):
        props = getattr(button_node, "props", None) or {}
        if not isinstance(props, dict):
            return
        onclick = props.get("onClick")
        if not callable(onclick):
            return
        node_id = self._safe_text(getattr(button_node, 'node_id', 'node'))
        self._button_callbacks[node_id] = onclick
        self._bind_button_click(button_path, node_id)

    def _clear_root_children(self):
        self._drop_native_common_style_cache()
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
                    self._screen.RemoveChildControl(child_control)
            except Exception:
                pass

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
