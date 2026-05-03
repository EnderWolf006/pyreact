# -*- coding: utf-8 -*-

import time

import mod.client.extraClientApi as clientApi


class RuntimeLifecycleMixin(object):
    def _perf_clock(self):
        clock = getattr(time, 'clock', None)
        if clock:
            return clock()
        return getattr(time, 'time')()

    def _log_render_stage_timings(self, component_ms, build_ms, diff_ms, layout_ms, native_ms, native_stats=None, native_update_stats=None, native_apply_ms=None, update_screen_ms=None):
        if not getattr(self, '_log_perf', False):
            return
        try:
            print('PyreactRuntime[perf] 1. 组件函数执行: %.3fms' % component_ms)
            print('PyreactRuntime[perf] 2. 构建VNode树: %.3fms' % build_ms)
            print('PyreactRuntime[perf] 3. Diff计算: %.3fms' % diff_ms)
            print('PyreactRuntime[perf] 4. 布局计算: %.3fms' % layout_ms)
            print('PyreactRuntime[perf] 5. 应用到原生UI: %.3fms' % native_ms)
            if native_apply_ms is not None:
                print('PyreactRuntime[perf] 5.1 原生控件应用: %.3fms' % native_apply_ms)
            if update_screen_ms is not None:
                print('PyreactRuntime[perf] 5.2 UpdateScreen: %.3fms' % update_screen_ms)
            stats = native_stats
            if stats is None:
                stats = self._get_native_api_perf_stats()
            print('PyreactRuntime[perf][native] 应用到原生UI total=%.3fms' % self._sum_native_api_perf_stats(stats))
            if native_update_stats is not None:
                print('PyreactRuntime[perf][native][update] 本次更新所有阶段 total=%.3fms' % self._sum_native_api_perf_stats(native_update_stats))
            for api_name, count, total_ms in stats:
                print('PyreactRuntime[perf][native] %s: count=%s total=%.3fms' % (api_name, count, total_ms))
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
                diff_start_time = self._perf_clock()
                mutations = self._reconciler.reconcile(self._prev_vtree, None)
                diff_ms = (self._perf_clock() - diff_start_time) * 1000.0

                self._reset_native_api_perf_stats()
                native_start_time = self._perf_clock()
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
                native_ms = (self._perf_clock() - native_start_time) * 1000.0
                self._log_render_stage_timings(component_ms, build_ms, diff_ms, 0.0, native_ms)
                return

            self._reset_native_api_perf_stats()
            width, height = self._get_root_size()

            new_vtree = self._tree_builder.build_tree(element)
            tree_perf = self._tree_builder.get_last_perf_stats()
            component_ms += tree_perf.get('component_exec_ms', 0.0)
            build_ms = tree_perf.get('build_only_ms', 0.0)

            diff_start_time = self._perf_clock()
            mutations = self._reconciler.reconcile(self._prev_vtree, new_vtree)
            diff_ms = (self._perf_clock() - diff_start_time) * 1000.0

            layout_start_time = self._perf_clock()
            shadow_root = self._layout_engine.calculate(new_vtree, width, height)
            layout_ms = (self._perf_clock() - layout_start_time) * 1000.0

            native_before_apply = self._copy_native_api_perf_stats()
            native_start_time = self._perf_clock()
            if self._can_apply_incremental(mutations):
                self._apply_incremental_updates(shadow_root, mutations)
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
                    cache_already_cleared=True,
                )
            native_apply_ms = (self._perf_clock() - native_start_time) * 1000.0

            update_screen_start_time = self._perf_clock()
            try:
                self._update_screen()
            except Exception:
                pass
            update_screen_ms = (self._perf_clock() - update_screen_start_time) * 1000.0
            native_ms = (self._perf_clock() - native_start_time) * 1000.0

            native_apply_stats = self._diff_native_api_perf_stats(native_before_apply)
            native_update_stats = self._get_native_api_perf_stats()
            self._log_render_stage_timings(component_ms, build_ms, diff_ms, layout_ms, native_ms, native_apply_stats, native_update_stats, native_apply_ms, update_screen_ms)

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
            size = self._native_api_call('GetSize', self._screen.GetSize, self._root_path)
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

        structural_count = 0
        created_node_count = 0
        removed_node_count = 0
        moved_node_count = 0
        max_created_subtree = 0
        max_removed_subtree = 0
        deleted_paths = {}
        created_paths = {}
        for m in mutations or []:
            try:
                mutation_type = self._safe_text(getattr(m, 'type_', ''))
            except Exception:
                mutation_type = ''
            if mutation_type == 'CREATE' or mutation_type == 'DELETE' or mutation_type == 'MOVE':
                structural_count += 1
                if mutation_type == 'CREATE':
                    node_count = self._count_vnode_subtree(getattr(m, 'new_node', None))
                    created_node_count += node_count
                    if node_count > max_created_subtree:
                        max_created_subtree = node_count
                    created_paths[tuple(getattr(m, 'path', []) or [])] = True
                elif mutation_type == 'DELETE':
                    node_count = self._count_vnode_subtree(getattr(m, 'old_node', None))
                    removed_node_count += node_count
                    if node_count > max_removed_subtree:
                        max_removed_subtree = node_count
                    deleted_paths[tuple(getattr(m, 'path', []) or [])] = True
                else:
                    moved_node_count += self._count_vnode_subtree(getattr(m, 'new_node', None))

        limit = getattr(self, '_full_rebuild_structural_mutation_limit', 16)
        try:
            limit = int(limit)
        except Exception:
            limit = 16
        if limit > 0 and structural_count > limit:
            return False

        created_limit = getattr(self, '_full_rebuild_created_node_limit', 64)
        try:
            created_limit = int(created_limit)
        except Exception:
            created_limit = 64
        if created_limit > 0 and created_node_count > created_limit:
            return False

        removed_limit = getattr(self, '_full_rebuild_removed_node_limit', 64)
        try:
            removed_limit = int(removed_limit)
        except Exception:
            removed_limit = 64
        if removed_limit > 0 and removed_node_count > removed_limit:
            return False

        total_node_limit = getattr(self, '_full_rebuild_structural_node_limit', 96)
        try:
            total_node_limit = int(total_node_limit)
        except Exception:
            total_node_limit = 96
        structural_node_count = created_node_count + removed_node_count + moved_node_count
        if total_node_limit > 0 and structural_node_count > total_node_limit:
            return False

        max_subtree_limit = getattr(self, '_full_rebuild_single_subtree_node_limit', 48)
        try:
            max_subtree_limit = int(max_subtree_limit)
        except Exception:
            max_subtree_limit = 48
        if max_subtree_limit > 0 and (max_created_subtree > max_subtree_limit or max_removed_subtree > max_subtree_limit):
            return False

        replace_pair_count = 0
        has_near_root_replace = False
        for path_tuple in created_paths:
            if path_tuple in deleted_paths:
                replace_pair_count += 1
                if len(path_tuple) <= 2:
                    has_near_root_replace = True

        replace_pair_limit = getattr(self, '_full_rebuild_replace_pair_limit', 8)
        try:
            replace_pair_limit = int(replace_pair_limit)
        except Exception:
            replace_pair_limit = 8
        if replace_pair_limit > 0 and replace_pair_count >= replace_pair_limit:
            return False

        if has_near_root_replace:
            return False

        # Incremental render can handle CREATE/DELETE/MOVE by creating missing
        # controls and pruning orphaned prefixed children during the layout walk.
        # For large structural switches, full root rebuild is faster because it
        # deletes subtree roots once instead of probing/removing many nodes.
        return True

    def _count_vnode_subtree(self, node):
        if node is None:
            return 0
        count = 1
        try:
            children = getattr(node, 'children', None) or []
        except Exception:
            children = []
        for child in children:
            count += self._count_vnode_subtree(child)
        return count

    def _apply_incremental_updates(self, new_shadow_root, mutations):
        recreate_paths = {}
        prune_parent_paths = {}
        muts = mutations or []
        for m in muts:
            try:
                mutation_type = self._safe_text(getattr(m, 'type_', ''))
                path = getattr(m, 'path', []) or []
                path_tuple = tuple(path)
                if mutation_type == 'CREATE':
                    recreate_paths[path_tuple] = True
                    shifted = [0]
                    shifted.extend(path)
                    recreate_paths[tuple(shifted)] = True
                    parent_path = list(path[:-1])
                    shifted_parent = [0]
                    shifted_parent.extend(parent_path)
                    prune_parent_paths[tuple(shifted_parent)] = True
                elif mutation_type == 'DELETE' or mutation_type == 'MOVE':
                    parent_path = list(path[:-1])
                    shifted_parent = [0]
                    shifted_parent.extend(parent_path)
                    prune_parent_paths[tuple(shifted_parent)] = True
            except Exception:
                pass
        self._apply_layout_to_existing_tree(
            current_node=[new_shadow_root],
            parent_control_path=self._root_path,
            parent_abs_x=0.0,
            parent_abs_y=0.0,
            shadow_path=[],
            recreate_paths=recreate_paths,
            prune_parent_paths=prune_parent_paths,
        )

    def _should_prune_prefixed_children(self, shadow_path, prune_parent_paths):
        if prune_parent_paths is None:
            return True
        return tuple(shadow_path or []) in prune_parent_paths

    def _apply_layout_to_existing_tree(self, current_node, parent_control_path, parent_abs_x, parent_abs_y, shadow_path, recreate_paths, prune_parent_paths=None):
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
            content_control = self._get_base_ui_control(content_path)
            if content_control:
                self._safe_set_size(content_path, node_layout.content_width, node_layout.content_height, content_control)
                children_parent_path = content_path

            self._apply_scroll_props(current_node, parent_control_path)

        if not children:
            if self._should_prune_prefixed_children(shadow_path, prune_parent_paths):
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
            control = self._get_base_ui_control(control_path)

            next_shadow_path = list(shadow_path)
            next_shadow_path.append(index)

            # If the reconciler says this path is newly created, ensure any stale
            # control at the same name is removed and rebuilt with the right def.
            try:
                if recreate_paths and recreate_paths.get(tuple(next_shadow_path)) and control:
                    try:
                        self._remove_component_by_path(control_path)
                    except Exception:
                        pass
                    control = None
            except Exception:
                pass

            if not control:
                parent_control = self._get_base_ui_control(children_parent_path)
                if not parent_control:
                    self._needs_render = True
                    return

                def_path = self._get_def_path(node_type)
                try:
                    self._clone(def_path, children_parent_path, child_name, False, False)
                except Exception:
                    pass
                control = self._get_base_ui_control(control_path)
                if not control:
                    self._needs_render = True
                    return
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
                prune_parent_paths=prune_parent_paths,
            )

            if self._needs_render:
                return
            index += 1

        if self._should_prune_prefixed_children(shadow_path, prune_parent_paths):
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
            names = self._get_children_name(self._root_path) or []
        except Exception:
            names = []

        for name in names:
            if not self._safe_text(name).startswith(self._CONTROL_NAME_PREFIX):
                continue
            child_path = self._root_path + "/" + name
            try:
                self._remove_component_by_path(child_path)
            except Exception:
                pass

    def _render_children(self, children, parent_path, parent_abs_x, parent_abs_y, cache_already_cleared=False):
        index = 0
        for child in children:
            self._render_node(child, parent_path, parent_abs_x, parent_abs_y, index, cache_already_cleared)
            index += 1

    def _render_node(self, node, parent_path, parent_abs_x, parent_abs_y, sibling_index, cache_already_cleared=False):
        if node is None:
            return

        node_type = self._safe_text(getattr(node, "node_type", "Panel") or "Panel")
        def_path = self._get_def_path(node_type)
        node_id = self._safe_text(getattr(node, "node_id", "node"))
        child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, node_id, sibling_index)

        parent_control = self._get_base_ui_control(parent_path)
        if not parent_control:
            return

        # child_control = self._screen.CreateChildControl(def_name, child_name, parent_control, False)
        child_control = self._clone(def_path, parent_path, child_name, False, False)

        if not child_control:
            return

        node_path = parent_path + "/" + child_name
        if not cache_already_cleared:
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
            content_control = self._get_base_ui_control(content_path)
            if content_control:
                self._safe_set_size(content_path, layout.content_width, layout.content_height, content_control)
                children_parent_path = content_path

            self._apply_scroll_props(node, node_path)

        child_parent_x = abs_x
        child_parent_y = abs_y
        children = self._get_render_children(node, node_type)
        self._render_children(children, children_parent_path, child_parent_x, child_parent_y, cache_already_cleared)

    def _apply_scroll_props(self, node, node_path):
        props = getattr(node, "props", {}) or {}
        show_scrollbar = props.get("showScrollbar", True)

        track_path = self._get_scrollbar_track_path(node_path)
        if track_path:
            self._safe_set_visible(track_path, show_scrollbar)

    def _get_real_scroll_view_path(self, scroll_node_path):
        if not scroll_node_path:
            return ""

        cache = getattr(self, '_scroll_path_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._scroll_path_cache = cache
        safe_scroll_node_path = self._safe_text(scroll_node_path)
        cached = cache.get(safe_scroll_node_path)
        if cached is not None:
            return cached

        touch_path = scroll_node_path + "/scroll_touch/scroll_view"
        try:
            touch_children = self._get_children_name(touch_path) or []
        except Exception:
            touch_children = []
        if touch_children:
            cache[safe_scroll_node_path] = touch_path
            return touch_path

        mouse_path = scroll_node_path + "/scroll_mouse/scroll_view"
        try:
            mouse_children = self._get_children_name(mouse_path) or []
        except Exception:
            mouse_children = []
        if mouse_children:
            cache[safe_scroll_node_path] = mouse_path
            return mouse_path

        cache[safe_scroll_node_path] = ""
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
