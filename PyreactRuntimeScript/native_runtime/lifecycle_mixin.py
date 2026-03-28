# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi


class RuntimeLifecycleMixin(object):
    def _dbg_render(self, msg):
        try:
            if not getattr(self, '_debug_render', False):
                return
        except Exception:
            return
        try:
            print('=====> PyreactRuntime[render] %s <=====' % (self._safe_text(msg)))
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
            if element is None:
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
                return

            width, height = self._get_root_size()
            new_vtree = self._tree_builder.build_tree(element)
            mutations = self._reconciler.reconcile(self._prev_vtree, new_vtree)
            shadow_root = self._layout_engine.calculate(element, width, height)

            if self._can_apply_incremental(mutations):
                if getattr(self, '_debug_render', False):
                    self._dbg_render('incremental mutations=%s' % (len(mutations) if mutations else 0))
                self._apply_incremental_updates(shadow_root, mutations)
                self._refresh_button_callbacks(shadow_root)
            else:
                if getattr(self, '_debug_render', False):
                    counts = {}
                    muts = mutations or []
                    for m in muts:
                        t = self._safe_text(getattr(m, 'type_', ''))
                        counts[t] = counts.get(t, 0) + 1
                    self._dbg_render('FULL rerender -> clear+rebuild, mutations=%s counts=%s' % (len(muts), counts))
                self._clear_root_children()
                self._render_children(
                    children=[shadow_root],
                    parent_path=self._root_path,
                    parent_abs_x=0.0,
                    parent_abs_y=0.0,
                )

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

    def _apply_layout_to_existing_tree(self, current_node, parent_control_path, parent_abs_x, parent_abs_y, shadow_path, recreate_paths):
        if current_node is None:
            return

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
            try:
                # Ensure we remove stale prefixed children when the new tree has none.
                self._prune_prefixed_children(children_parent_path, [])
            except Exception:
                pass
            return

        index = 0
        expected_child_names = []
        for node in children:
            node_id = self._safe_text(getattr(node, 'node_id', 'node'))
            child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, node_id, index)
            expected_child_names.append(child_name)
            
            node_type = self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
            layout = getattr(node, 'layout', None)
            abs_x = self._to_float(getattr(layout, 'x', 0.0), 0.0)
            abs_y = self._to_float(getattr(layout, 'y', 0.0), 0.0)
            width = self._to_float(getattr(layout, 'width', 0.0), 0.0)
            height = self._to_float(getattr(layout, 'height', 0.0), 0.0)

            control_path = children_parent_path + '/' + child_name
            child_control_paths = control_path
            control = self._screen.GetBaseUIControl(control_path)

            next_shadow_path = list(shadow_path)
            next_shadow_path.append(index)

            # If the reconciler says this path is newly created, ensure any stale
            # control at the same name is removed and rebuilt with the right def.
            try:
                if recreate_paths and recreate_paths.get(tuple(next_shadow_path)) and control:
                    try:
                        self._screen.RemoveChildControl(control)
                    except Exception:
                        pass
                    self._drop_native_common_style_cache(control_path)
                    control = None
            except Exception:
                pass

            if not control:
                parent_control = self._screen.GetBaseUIControl(children_parent_path)
                if not parent_control:
                    self._needs_render = True
                    return

                def_name = self._get_def_name(node_type)
                try:
                    self._screen.CreateChildControl(def_name, child_name, parent_control)
                except Exception:
                    pass
                control = self._screen.GetBaseUIControl(control_path)
                if not control:
                    self._needs_render = True
                    return
                self._drop_native_common_style_cache(control_path)
            self._safe_set_position(control_path, abs_x - parent_abs_x, abs_y - parent_abs_y, control)
            if node_type != "Label":
                self._safe_set_size(control_path, width, height, control)
            self._apply_node_props(node, control_path, node_type, node_id, control)

            self._apply_layout_to_existing_tree(
                current_node=node,
                parent_control_path=child_control_paths,
                parent_abs_x=abs_x,
                parent_abs_y=abs_y,
                shadow_path=next_shadow_path,
                recreate_paths=recreate_paths,
            )

            if self._needs_render:
                return
            index += 1

        try:
            # Remove any orphaned prefixed children not present in the new tree.
            self._prune_prefixed_children(children_parent_path, expected_child_names)
        except Exception:
            pass

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

        index = 0
        for child in children:
            child_id = self._safe_text(getattr(child, 'node_id', 'node'))
            child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, child_id, index)
            node_type = self._safe_text(getattr(child, 'node_type', 'Panel') or 'Panel')
            
            control_path = children_parent_path + '/' + child_name
            child_control_paths = control_path
            if node_type == 'Button':
                self._refresh_button_callback(child, control_path)

            self._refresh_button_callbacks_walk(child, child_control_paths)
            index += 1

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

    def _render_children(self, children, parent_path, parent_abs_x, parent_abs_y):
        index = 0
        for child in children:
            self._render_node(child, parent_path, parent_abs_x, parent_abs_y, index)
            index += 1

    def _render_node(self, node, parent_path, parent_abs_x, parent_abs_y, sibling_index):
        if node is None:
            return

        node_type = self._safe_text(getattr(node, "node_type", "Panel") or "Panel")
        def_name = self._get_def_name(node_type)
        node_id = self._safe_text(getattr(node, "node_id", "node"))
        child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, node_id, sibling_index)

        parent_control = self._screen.GetBaseUIControl(parent_path)
        if not parent_control:
            return

        child_control = self._screen.CreateChildControl(def_name, child_name, parent_control)
        if not child_control:
            return

        node_path = parent_path + "/" + child_name
        self._drop_native_common_style_cache(node_path)
        layout = getattr(node, "layout", None)
        abs_x = self._to_float(getattr(layout, "x", 0.0), 0.0)
        abs_y = self._to_float(getattr(layout, "y", 0.0), 0.0)
        width = self._to_float(getattr(layout, "width", 0.0), 0.0)
        height = self._to_float(getattr(layout, "height", 0.0), 0.0)
        local_x = abs_x - parent_abs_x
        local_y = abs_y - parent_abs_y

        self._safe_set_position(node_path, local_x, local_y, child_control)
        if node_type != "Label":
            self._safe_set_size(node_path, width, height, child_control)
        self._apply_node_props(node, node_path, node_type, node_id, child_control)

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
        self._render_children(children, children_parent_path, child_parent_x, child_parent_y)

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
