# -*- coding: utf-8 -*-

import time

import mod.client.extraClientApi as clientApi


_PERF_CLOCK = getattr(time, 'clock', None) or getattr(time, 'time')


class RuntimeLifecycleMixin(object):
    def _perf_clock(self):
        return _PERF_CLOCK()

    def _log_render_stage_timings(self, component_ms, build_ms, diff_ms, layout_ms, native_ms, native_stats=None, native_update_stats=None, native_apply_ms=None, update_screen_ms=None, layout_stats=None, text_stats=None, update_screen_skipped=False, mutation_stats=None, button_slot_stats=None, native_commit_stats=None):
        if not getattr(self, '_log_perf', False):
            return
        try:
            print('PyreactRuntime[perf] 1. 组件函数执行: %.3fms' % component_ms)
            print('PyreactRuntime[perf] 2. 构建VNode树: %.3fms' % build_ms)
            print('PyreactRuntime[perf] 3. Diff计算: %.3fms' % diff_ms)
            if mutation_stats is not None:
                print('PyreactRuntime[perf][diff] CREATE=%s UPDATE=%s DELETE=%s MOVE=%s total=%s' % (
                    mutation_stats.get('CREATE', 0),
                    mutation_stats.get('UPDATE', 0),
                    mutation_stats.get('DELETE', 0),
                    mutation_stats.get('MOVE', 0),
                    mutation_stats.get('total', 0),
                ))
            print('PyreactRuntime[perf] 4. 布局计算: %.3fms' % layout_ms)
            if isinstance(layout_stats, dict) and layout_stats:
                print('PyreactRuntime[perf][layout] shadow_nodes=%s build=%.3fms measure=%.3fms layout=%.3fms stabilize=%.3fms' % (
                    layout_stats.get('shadow_nodes', 0),
                    layout_stats.get('build_shadow_ms', 0.0),
                    layout_stats.get('measure_pass_ms', 0.0),
                    layout_stats.get('layout_pass_ms', 0.0),
                    layout_stats.get('stabilize_pass_ms', 0.0),
                ))
            if isinstance(text_stats, dict) and text_stats:
                print('PyreactRuntime[perf][text] calls=%s hits=%s misses=%s native=%s fallback=%s' % (
                    text_stats.get('calls', 0),
                    text_stats.get('cache_hits', 0),
                    text_stats.get('cache_misses', 0),
                    text_stats.get('native_hits', 0),
                    text_stats.get('fallback_hits', 0),
                ))
            if isinstance(button_slot_stats, dict) and button_slot_stats:
                print('PyreactRuntime[perf][button_slot] direct_image=%s subtree=%s' % (
                    button_slot_stats.get('direct_image', {}).get('count', 0),
                    button_slot_stats.get('subtree', {}).get('count', 0),
                ))
            print('PyreactRuntime[perf] 5. 应用到原生UI: %.3fms' % native_ms)
            if native_apply_ms is not None:
                print('PyreactRuntime[perf] 5.1 原生控件应用: %.3fms' % native_apply_ms)
            if isinstance(native_commit_stats, dict) and native_commit_stats:
                native_total = self._sum_native_api_perf_stats(native_stats or [])
                py_ms = native_apply_ms - native_total if native_apply_ms is not None else 0.0
                if py_ms < 0.0:
                    py_ms = 0.0
                print('PyreactRuntime[perf][native_commit] python_unwrapped=%.3fms native_api=%.3fms' % (py_ms, native_total))
                print('PyreactRuntime[perf][native_commit] plan=%.3fms runtime_state=%.3fms walk=%.3fms render_self=%.3fms render_children_recursive=%.3fms props=%.3fms bind=%.3fms' % (
                    native_commit_stats.get('incremental_plan_ms', 0.0),
                    native_commit_stats.get('runtime_state_remove_ms', 0.0),
                    native_commit_stats.get('commit_walk_ms', 0.0),
                    native_commit_stats.get('render_node_ms', 0.0),
                    native_commit_stats.get('render_children_ms', 0.0),
                    native_commit_stats.get('apply_props_ms', 0.0),
                    native_commit_stats.get('button_bind_ms', 0.0),
                ))
                print('PyreactRuntime[perf][native_commit][plan] scan=%.3fms process=%.3fms index=%.3fms mutations=%s create=%s update=%s delete=%s move=%s commit_paths=%s recreate_paths=%s prune_paths=%s max_path=%s' % (
                    native_commit_stats.get('plan_scan_ms', 0.0),
                    native_commit_stats.get('plan_process_ms', 0.0),
                    native_commit_stats.get('plan_index_ms', 0.0),
                    native_commit_stats.get('plan_mutation_count', 0),
                    native_commit_stats.get('plan_create_count', 0),
                    native_commit_stats.get('plan_update_count', 0),
                    native_commit_stats.get('plan_delete_count', 0),
                    native_commit_stats.get('plan_move_count', 0),
                    native_commit_stats.get('plan_commit_paths', 0),
                    native_commit_stats.get('plan_recreate_paths', 0),
                    native_commit_stats.get('plan_prune_paths', 0),
                    native_commit_stats.get('plan_max_path_len', 0),
                ))
                print('PyreactRuntime[perf][native_commit][plan_detail] create=%.3fms delete=%.3fms move=%.3fms update=%.3fms path=%.3fms layout_check=%.3fms' % (
                    native_commit_stats.get('plan_process_create_ms', 0.0),
                    native_commit_stats.get('plan_process_delete_ms', 0.0),
                    native_commit_stats.get('plan_process_move_ms', 0.0),
                    native_commit_stats.get('plan_process_update_ms', 0.0),
                    native_commit_stats.get('plan_process_path_ms', 0.0),
                    native_commit_stats.get('plan_layout_check_ms', 0.0),
                ))
                print('PyreactRuntime[perf][native_commit][scan_detail] reuse=%s fallback=%s delete=%s max_path=%s' % (
                    native_commit_stats.get('plan_scan_reuse_count', 0),
                    native_commit_stats.get('plan_scan_fallback_count', 0),
                    native_commit_stats.get('plan_scan_delete_count', 0),
                    native_commit_stats.get('plan_max_path_len', 0),
                ))
                print('PyreactRuntime[perf][native_commit] visited=%s applied=%s skipped_path=%s skipped_sig=%s recreated=%s pruned_parent=%s removed=%s' % (
                    native_commit_stats.get('commit_visit', 0),
                    native_commit_stats.get('commit_apply', 0),
                    native_commit_stats.get('commit_skip_path', 0),
                    native_commit_stats.get('commit_skip_signature', 0),
                    native_commit_stats.get('commit_recreate', 0),
                    native_commit_stats.get('prune_calls', 0),
                    native_commit_stats.get('remove_component', 0),
                ))
                print('PyreactRuntime[perf][native_commit] signature count=%s total=%.3fms max=%.3fms prev_lookup count=%s total=%.3fms' % (
                    native_commit_stats.get('signature_count', 0),
                    native_commit_stats.get('signature_ms', 0.0),
                    native_commit_stats.get('signature_max_ms', 0.0),
                    native_commit_stats.get('prev_lookup_count', 0),
                    native_commit_stats.get('prev_lookup_ms', 0.0),
                ))
                print('PyreactRuntime[perf][native_commit] cache_drop calls=%s prefixes=%s scanned=%s deleted=%s total=%.3fms' % (
                    native_commit_stats.get('cache_drop_calls', 0),
                    native_commit_stats.get('cache_drop_prefixes', 0),
                    native_commit_stats.get('cache_drop_scanned', 0),
                    native_commit_stats.get('cache_drop_deleted', 0),
                    native_commit_stats.get('cache_drop_ms', 0.0),
                ))
                print('PyreactRuntime[perf][native_commit] control_cache hit=%s miss=%s geometry pos_set=%s pos_skip=%s size_set=%s size_skip=%s adapter_hit=%s adapter_miss=%s' % (
                    native_commit_stats.get('control_cache_hit', 0),
                    native_commit_stats.get('control_cache_miss', 0),
                    native_commit_stats.get('geometry_pos_set', 0),
                    native_commit_stats.get('geometry_pos_skip', 0),
                    native_commit_stats.get('geometry_size_set', 0),
                    native_commit_stats.get('geometry_size_skip', 0),
                    native_commit_stats.get('adapter_cache_hit', 0),
                    native_commit_stats.get('adapter_cache_miss', 0),
                ))
                print('PyreactRuntime[perf][native_commit] bind count=%s max=%.3fms state_remove count=%s max=%.3fms render_nodes=%s' % (
                    native_commit_stats.get('button_bind_count', 0),
                    native_commit_stats.get('button_bind_max_ms', 0.0),
                    native_commit_stats.get('runtime_state_remove_count', 0),
                    native_commit_stats.get('runtime_state_remove_max_ms', 0.0),
                    native_commit_stats.get('render_node_count', 0),
                ))
            if update_screen_ms is not None:
                if update_screen_skipped:
                    print('PyreactRuntime[perf] 5.2 UpdateScreen: skipped')
                else:
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
        self._drop_native_common_style_cache()
        try:
            self._cleanup_exit_animation_ghosts()
        except Exception:
            pass
        try:
            self._clear_animation_runtime_state()
        except Exception:
            pass
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

    def request_layout_render(self):
        self._force_layout_next_render = True
        self.request_render()

    def render(self):
        if not self._mounted:
            return

        self._render_scheduled = False
        self._is_rendering = True
        try:
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
                    self._cleanup_exit_animation_ghosts()
                except Exception:
                    pass
                try:
                    self._clear_animation_runtime_state()
                except Exception:
                    pass
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
            self._button_slot_perf_stats = {}
            self._native_commit_perf_stats = {}
            width, height = self._get_root_size()
            root_size = (
                int(round(self._to_float(width, 0.0) * 1000.0)),
                int(round(self._to_float(height, 0.0) * 1000.0)),
            )
            layout_refresh = bool(getattr(self, '_force_layout_next_render', False)) or getattr(self, '_last_root_size', None) != root_size

            new_vtree = self._tree_builder.build_tree(element)
            tree_perf = self._tree_builder.get_last_perf_stats()
            component_ms += tree_perf.get('component_exec_ms', 0.0)
            build_ms = tree_perf.get('build_only_ms', 0.0)

            diff_start_time = self._perf_clock()
            mutations = self._reconciler.reconcile(self._prev_vtree, new_vtree)
            diff_ms = (self._perf_clock() - diff_start_time) * 1000.0

            self._refresh_button_callbacks_from_vtree(new_vtree)

            mutation_stats = self._summarize_mutations(mutations)

            if self._prev_vtree is not None and self._prev_shadow_root is not None and not mutations and not layout_refresh:
                self._prev_vtree = new_vtree
                native_update_stats = self._get_native_api_perf_stats()
                self._log_render_stage_timings(component_ms, build_ms, diff_ms, 0.0, 0.0, [], native_update_stats, 0.0, 0.0, {}, {}, True, mutation_stats, {})
                try:
                    self._cleanup_input_state()
                except Exception:
                    pass
                try:
                    self._cleanup_refs()
                except Exception:
                    pass
                return

            try:
                self._text_measurer.reset_perf_stats()
            except Exception:
                pass

            layout_start_time = self._perf_clock()
            shadow_root = self._layout_engine.calculate(new_vtree, width, height)
            layout_ms = (self._perf_clock() - layout_start_time) * 1000.0
            try:
                layout_stats = self._layout_engine.get_last_perf_stats()
            except Exception:
                layout_stats = {}

            native_before_apply = self._copy_native_api_perf_stats()
            native_start_time = self._perf_clock()
            self._pending_button_binds = {}
            if layout_refresh and self._prev_shadow_root is not None and not mutations:
                try:
                    root_control = self._get_base_ui_control(self._root_path)
                except Exception:
                    root_control = None
                self._apply_layout_to_existing_tree(
                    current_node=[shadow_root],
                    parent_control_path=self._root_path,
                    parent_abs_x=0.0,
                    parent_abs_y=0.0,
                    shadow_path=[],
                    recreate_paths={},
                    move_sources=None,
                    prune_parent_paths=None,
                    commit_paths=None,
                    parent_control=root_control,
                )
            elif self._can_apply_incremental(mutations):
                self._apply_incremental_updates(shadow_root, mutations)
            else:
                self._button_callbacks = {}
                self._input_callbacks = {}
                self._input_paths = {}
                self._node_refs = {}
                try:
                    self._cleanup_exit_animation_ghosts()
                except Exception:
                    pass
                try:
                    self._clear_animation_runtime_state()
                except Exception:
                    pass
                self._clear_root_children()
                try:
                    root_control = self._get_base_ui_control(self._root_path)
                except Exception:
                    root_control = None
                self._render_children(
                    children=[shadow_root],
                    parent_path=self._root_path,
                    parent_abs_x=0.0,
                    parent_abs_y=0.0,
                    cache_already_cleared=True,
                    parent_control=root_control,
                )
            try:
                self._reapply_animation_values_for_tree(shadow_root, self._root_path)
            except Exception:
                pass
            try:
                bind_start_time = self._perf_clock()
                self._flush_pending_button_binds()
                self._record_native_commit_perf('button_bind_flush_ms', (self._perf_clock() - bind_start_time) * 1000.0)
            except Exception:
                pass
            native_apply_ms = (self._perf_clock() - native_start_time) * 1000.0

            native_apply_stats = self._diff_native_api_perf_stats(native_before_apply)

            update_screen_skipped = False
            if layout_refresh or (not getattr(self, '_log_perf', False)) or self._has_native_api_perf_entries(native_apply_stats):
                update_screen_start_time = self._perf_clock()
                try:
                    self._update_screen()
                except Exception:
                    pass
                update_screen_ms = (self._perf_clock() - update_screen_start_time) * 1000.0
            else:
                update_screen_ms = 0.0
                update_screen_skipped = True
            native_ms = (self._perf_clock() - native_start_time) * 1000.0

            native_update_stats = self._get_native_api_perf_stats()
            try:
                text_stats = self._text_measurer.get_perf_stats()
            except Exception:
                text_stats = {}
            button_slot_stats = getattr(self, '_button_slot_perf_stats', {})
            native_commit_stats = getattr(self, '_native_commit_perf_stats', {})
            self._log_render_stage_timings(component_ms, build_ms, diff_ms, layout_ms, native_ms, native_apply_stats, native_update_stats, native_apply_ms, update_screen_ms, layout_stats, text_stats, update_screen_skipped, mutation_stats, button_slot_stats, native_commit_stats)

            self._prev_vtree = new_vtree
            self._prev_shadow_root = shadow_root
            self._last_root_size = root_size
            self._force_layout_next_render = False
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

    def _record_native_commit_perf(self, key, value=1):
        if not getattr(self, '_log_perf', False):
            return
        stats = getattr(self, '_native_commit_perf_stats', None)
        if not isinstance(stats, dict):
            stats = {}
            self._native_commit_perf_stats = stats
        try:
            stats[key] = stats.get(key, 0) + value
        except Exception:
            pass

    def _record_native_commit_perf_max(self, key, value):
        if not getattr(self, '_log_perf', False):
            return
        stats = getattr(self, '_native_commit_perf_stats', None)
        if not isinstance(stats, dict):
            stats = {}
            self._native_commit_perf_stats = stats
        try:
            if value > stats.get(key, 0.0):
                stats[key] = value
        except Exception:
            pass

    def _get_root_size(self):
        try:
            game_comp = clientApi.CreateComponent(clientApi.GetLevelId(), 'Minecraft', 'game')
            if game_comp and hasattr(game_comp, 'GetScreenSize'):
                size = self._native_api_call('GetScreenSize', game_comp.GetScreenSize)
                if size and len(size) >= 2:
                    width = float(size[0])
                    height = float(size[1])
                    if width > 0 and height > 0:
                        return (width, height)
        except Exception:
            pass
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
        return True

    def _summarize_mutations(self, mutations):
        stats = {'CREATE': 0, 'UPDATE': 0, 'DELETE': 0, 'MOVE': 0, 'total': 0}
        for m in mutations or []:
            try:
                mutation_type = self._safe_text(getattr(m, 'type_', ''))
            except Exception:
                mutation_type = ''
            if mutation_type in stats:
                stats[mutation_type] = stats.get(mutation_type, 0) + 1
            stats['total'] = stats.get('total', 0) + 1
        return stats

    def _has_native_api_perf_entries(self, stats):
        for _, count, total_ms in stats or []:
            try:
                if int(count) > 0:
                    return True
            except Exception:
                pass
            try:
                if float(total_ms) > 0.0:
                    return True
            except Exception:
                pass
        return False

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
        perf_clock = self._perf_clock
        plan_start_time = perf_clock()
        recreate_paths = {}
        move_sources = {}
        prune_parent_paths = {}
        commit_paths = {}
        deleted_paths = {}
        deleted_old_nodes = []
        muts = mutations or []
        self._record_native_commit_perf('plan_mutation_count', len(muts))
        max_path_len = 0
        scan_start_time = perf_clock()
        scan_reuse_count = 0
        scan_fallback_count = 0
        scan_delete_count = 0
        for m in muts:
            try:
                try:
                    mutation_type = m.type_
                    shifted_tuple = m.shadow_path
                    path_len = m.path_len
                    scan_reuse_count += 1
                except Exception:
                    scan_fallback_count += 1
                    mutation_type = getattr(m, 'type_', '')
                    path = getattr(m, 'path', None) or ()
                    if isinstance(path, tuple):
                        path_tuple = path
                    else:
                        path_tuple = tuple(path)
                    shifted_tuple = (0,) + path_tuple
                    path_len = len(path_tuple)
                if path_len > max_path_len:
                    max_path_len = path_len
                if mutation_type == 'DELETE':
                    scan_delete_count += 1
                    deleted_paths[shifted_tuple] = True
            except Exception:
                pass
        self._record_native_commit_perf('plan_scan_ms', (perf_clock() - scan_start_time) * 1000.0)
        self._record_native_commit_perf('plan_scan_reuse_count', scan_reuse_count)
        self._record_native_commit_perf('plan_scan_fallback_count', scan_fallback_count)
        self._record_native_commit_perf('plan_scan_delete_count', scan_delete_count)
        process_start_time = perf_clock()
        create_count = 0
        update_count = 0
        delete_count = 0
        move_count = 0
        process_create_ms = 0.0
        process_delete_ms = 0.0
        process_move_ms = 0.0
        process_update_ms = 0.0
        layout_check_ms = 0.0
        for m in muts:
            try:
                try:
                    mutation_type = m.type_
                    shifted_tuple = m.shadow_path
                    shifted_parent_tuple = m.shadow_parent_path
                except Exception:
                    mutation_type = getattr(m, 'type_', '')
                    path = getattr(m, 'path', None) or ()
                    if isinstance(path, tuple):
                        path_tuple = path
                    else:
                        path_tuple = tuple(path)
                    shifted_tuple = (0,) + path_tuple
                    shifted_parent_tuple = (0,) + path_tuple[:-1]
                if mutation_type == 'CREATE':
                    branch_start_time = perf_clock()
                    create_count += 1
                    recreate_paths[shifted_tuple] = bool(deleted_paths.get(shifted_tuple))
                    commit_paths[shifted_parent_tuple] = True
                    prune_parent_paths[shifted_parent_tuple] = True
                    process_create_ms += (perf_clock() - branch_start_time) * 1000.0
                elif mutation_type == 'DELETE':
                    branch_start_time = perf_clock()
                    delete_count += 1
                    commit_paths[shifted_parent_tuple] = True
                    prune_parent_paths[shifted_parent_tuple] = True
                    if not self._has_deleted_ancestor(shifted_tuple, deleted_paths):
                        deleted_old_nodes.append(getattr(m, 'old_node', None))
                    process_delete_ms += (perf_clock() - branch_start_time) * 1000.0
                elif mutation_type == 'MOVE':
                    branch_start_time = perf_clock()
                    move_count += 1
                    recreate_paths[shifted_tuple] = False
                    move_sources[shifted_tuple] = getattr(m, 'old_node', None)
                    commit_paths[shifted_parent_tuple] = True
                    prune_parent_paths[shifted_parent_tuple] = True
                    process_move_ms += (perf_clock() - branch_start_time) * 1000.0
                elif mutation_type == 'UPDATE':
                    branch_start_time = perf_clock()
                    update_count += 1
                    layout_start_time = perf_clock()
                    try:
                        changed_props = m.changed_props
                    except Exception:
                        changed_props = None
                    if isinstance(changed_props, dict):
                        layout_affecting = 'style' in changed_props or 'children' in changed_props
                    else:
                        layout_affecting = self._is_layout_affecting_update(m)
                    layout_check_ms += (perf_clock() - layout_start_time) * 1000.0
                    if layout_affecting:
                        commit_paths[shifted_parent_tuple] = True
                    else:
                        commit_paths[shifted_tuple] = True
                    process_update_ms += (perf_clock() - branch_start_time) * 1000.0
            except Exception:
                pass
        self._record_native_commit_perf('plan_process_ms', (perf_clock() - process_start_time) * 1000.0)
        self._record_native_commit_perf('plan_create_count', create_count)
        self._record_native_commit_perf('plan_delete_count', delete_count)
        self._record_native_commit_perf('plan_move_count', move_count)
        self._record_native_commit_perf('plan_update_count', update_count)
        self._record_native_commit_perf('plan_process_create_ms', process_create_ms)
        self._record_native_commit_perf('plan_process_delete_ms', process_delete_ms)
        self._record_native_commit_perf('plan_process_move_ms', process_move_ms)
        self._record_native_commit_perf('plan_process_update_ms', process_update_ms)
        self._record_native_commit_perf('plan_layout_check_ms', layout_check_ms)
        if max_path_len:
            self._record_native_commit_perf_max('plan_max_path_len', max_path_len)
        if deleted_old_nodes:
            state_start_time = perf_clock()
            removed_count = self._remove_runtime_state_for_subtrees(deleted_old_nodes)
            state_ms = (perf_clock() - state_start_time) * 1000.0
            self._record_native_commit_perf('runtime_state_remove_count', removed_count)
            self._record_native_commit_perf('runtime_state_remove_ms', state_ms)
            self._record_native_commit_perf_max('runtime_state_remove_max_ms', state_ms)
        if not commit_paths:
            self._record_native_commit_perf('incremental_plan_ms', (perf_clock() - plan_start_time) * 1000.0)
            return
        index_start_time = perf_clock()
        commit_path_index = self._build_commit_path_index(commit_paths)
        self._record_native_commit_perf('plan_index_ms', (perf_clock() - index_start_time) * 1000.0)
        self._record_native_commit_perf('plan_commit_paths', len(commit_paths))
        self._record_native_commit_perf('plan_recreate_paths', len(recreate_paths))
        self._record_native_commit_perf('plan_prune_paths', len(prune_parent_paths))
        self._record_native_commit_perf('incremental_plan_ms', (perf_clock() - plan_start_time) * 1000.0)
        walk_start_time = perf_clock()
        try:
            root_control = self._get_base_ui_control(self._root_path)
        except Exception:
            root_control = None
        self._apply_layout_to_existing_tree(
            current_node=[new_shadow_root],
            parent_control_path=self._root_path,
            parent_abs_x=0.0,
            parent_abs_y=0.0,
            shadow_path=[],
            recreate_paths=recreate_paths,
            move_sources=move_sources,
            prune_parent_paths=prune_parent_paths,
            commit_paths=commit_path_index,
            parent_control=root_control,
        )
        self._record_native_commit_perf('commit_walk_ms', (perf_clock() - walk_start_time) * 1000.0)

    def _has_deleted_ancestor(self, shifted_path, deleted_paths):
        index = len(shifted_path) - 1
        while index > 0:
            if shifted_path[:index] in deleted_paths:
                return True
            index -= 1
        return False

    def _is_layout_affecting_update(self, mutation):
        try:
            changed_props = getattr(mutation, 'changed_props', None) or {}
        except Exception:
            changed_props = {}
        if not isinstance(changed_props, dict):
            return True
        # Style changes can alter flex layout for siblings and descendants, so
        # commit the parent subtree. Content/native prop changes can update only
        # the exact host node, React-style.
        return 'style' in changed_props or 'children' in changed_props

    def _is_path_prefix(self, prefix, path):
        if len(prefix) > len(path):
            return False
        index = 0
        while index < len(prefix):
            if prefix[index] != path[index]:
                return False
            index += 1
        return True

    def _should_visit_commit_path(self, shadow_path, commit_paths):
        if commit_paths is None:
            return True
        current = tuple(shadow_path or [])
        if not current:
            return True
        try:
            exact_paths = commit_paths.get('exact')
            ancestor_paths = commit_paths.get('ancestors')
        except Exception:
            exact_paths = commit_paths
            ancestor_paths = None
        if ancestor_paths is not None and current in ancestor_paths:
            return True
        if exact_paths is not None:
            index = 1
            while index <= len(current):
                if tuple(current[:index]) in exact_paths:
                    return True
                index += 1
        return False

    def _build_commit_path_index(self, commit_paths):
        exact = set()
        ancestors = set()
        for path_tuple in commit_paths or {}:
            path_tuple = tuple(path_tuple or ())
            exact.add(path_tuple)
            index = 0
            while index <= len(path_tuple):
                ancestors.add(tuple(path_tuple[:index]))
                index += 1
        return {'exact': exact, 'ancestors': ancestors}

    def _should_prune_prefixed_children(self, shadow_path, prune_parent_paths):
        if prune_parent_paths is None:
            return True
        return tuple(shadow_path or []) in prune_parent_paths

    def _apply_layout_to_existing_tree(self, current_node, parent_control_path, parent_abs_x, parent_abs_y, shadow_path, recreate_paths, move_sources=None, prune_parent_paths=None, commit_paths=None, parent_control=None):
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
        children_parent_control = parent_control
        if current_node_type == "Scroll" and node_layout:
            if commit_paths is not None and not self._should_visit_commit_path(shadow_path, commit_paths):
                self._record_native_commit_perf('commit_skip_path')
                return
            content_path = self._get_scroll_content_path(parent_control_path)
            content_control = self._get_base_ui_control(content_path)
            if content_control:
                self._safe_set_size(content_path, node_layout.content_width, node_layout.content_height, content_control)
                children_parent_path = content_path
                children_parent_control = content_control

            self._apply_scroll_props(current_node, parent_control_path)

        if not children:
            if self._should_prune_prefixed_children(shadow_path, prune_parent_paths):
                try:
                    self._record_native_commit_perf('prune_calls')
                    # Ensure we remove stale prefixed children when the new tree has none.
                    self._prune_prefixed_children(children_parent_path, [])
                except Exception:
                    pass
            return

        index = 0
        should_prune_children = self._should_prune_prefixed_children(shadow_path, prune_parent_paths)
        expected_child_names = [] if should_prune_children else None
        precleared_remove_paths = {}
        preclear_cache_paths = []
        preclear_index = 0
        for preclear_node in children:
            try:
                preclear_shadow_path = list(shadow_path)
                preclear_shadow_path.append(preclear_index)
                preclear_key = tuple(preclear_shadow_path)
                if recreate_paths and preclear_key in recreate_paths:
                    preclear_node_id = self._safe_text(getattr(preclear_node, 'node_id', 'node'))
                    preclear_child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, preclear_node_id, preclear_index)
                    preclear_control_path = children_parent_path + '/' + preclear_child_name
                    old_control_path = None
                    old_control = None
                    if recreate_paths.get(preclear_key):
                        try:
                            old_node = self._get_prev_shadow_node_by_shifted_path(preclear_shadow_path)
                            old_node_id = self._safe_text(getattr(old_node, 'node_id', 'node'))
                            old_child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, old_node_id, preclear_index)
                            old_control_path = children_parent_path + '/' + old_child_name
                            old_control = self._get_base_ui_control(old_control_path)
                        except Exception:
                            old_control_path = preclear_control_path
                            old_control = None
                    else:
                        try:
                            old_entry = self._find_prev_shadow_node_path_by_id(preclear_node_id)
                            if isinstance(old_entry, tuple) and len(old_entry) == 2:
                                old_control_path = old_entry[1]
                                old_control = self._get_base_ui_control(old_control_path)
                        except Exception:
                            old_control_path = None
                            old_control = None
                    if old_control_path and old_control:
                        precleared_remove_paths[old_control_path] = True
                        preclear_cache_paths.append(old_control_path)
                        if preclear_control_path != old_control_path:
                            preclear_cache_paths.append(preclear_control_path)
            except Exception:
                pass
            preclear_index += 1
        if preclear_cache_paths:
            try:
                self._drop_native_common_style_cache_many(preclear_cache_paths)
            except Exception:
                pass
        for node in children:
            node_id = self._safe_text(getattr(node, 'node_id', 'node'))
            child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, node_id, index)
            if expected_child_names is not None:
                expected_child_names.append(child_name)
            
            node_type = self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
            layout = getattr(node, 'layout', None)
            abs_x = self._to_float(getattr(layout, 'x', 0.0), 0.0)
            abs_y = self._to_float(getattr(layout, 'y', 0.0), 0.0)
            width = self._to_float(getattr(layout, 'width', 0.0), 0.0)
            height = self._to_float(getattr(layout, 'height', 0.0), 0.0)

            next_shadow_path = list(shadow_path)
            next_shadow_path.append(index)
            self._record_native_commit_perf('commit_visit')
            if not self._should_visit_commit_path(next_shadow_path, commit_paths):
                self._record_native_commit_perf('commit_skip_path')
                index += 1
                continue
            if self._can_skip_unchanged_commit_node(node, next_shadow_path, recreate_paths, commit_paths):
                self._record_native_commit_perf('commit_skip_signature')
                index += 1
                continue

            control_path = children_parent_path + '/' + child_name
            try:
                self._cancel_pending_animation_removal(control_path)
            except Exception:
                pass
            child_control_paths = control_path
            recreate_key = tuple(next_shadow_path)
            if recreate_paths and recreate_key in recreate_paths:
                self._record_native_commit_perf('commit_recreate')
                moved_old_node = None
                try:
                    moved_old_node = (move_sources or {}).get(recreate_key)
                except Exception:
                    moved_old_node = None
                if recreate_paths.get(recreate_key):
                    try:
                        old_node = self._get_prev_shadow_node_by_shifted_path(next_shadow_path)
                        old_node_id = self._safe_text(getattr(old_node, 'node_id', 'node'))
                        old_child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, old_node_id, index)
                        old_control_path = children_parent_path + '/' + old_child_name
                        old_control = self._get_base_ui_control(old_control_path)
                    except Exception:
                        old_node = None
                        old_control_path = control_path
                        old_control = None
                    if old_control:
                        try:
                            if not self._start_exit_animation_for_delete(old_node, old_control_path):
                                try:
                                    self._remove_animation_states_for_nodes([old_node])
                                except Exception:
                                    pass
                                self._remove_component_by_path(old_control_path, skip_cache_drop=bool(precleared_remove_paths.get(old_control_path)))
                        except Exception:
                            pass
                elif moved_old_node is not None:
                    try:
                        old_entry = self._find_prev_shadow_node_path_by_id(node_id)
                        old_shadow_node = None
                        old_control_path = None
                        if isinstance(old_entry, tuple) and len(old_entry) == 2:
                            old_shadow_node = old_entry[0]
                            old_control_path = old_entry[1]
                        if old_shadow_node is None:
                            old_shadow_node = moved_old_node
                        old_layout = getattr(old_shadow_node, 'layout', None)
                        old_abs_x = self._to_float(getattr(old_layout, 'x', 0.0), 0.0)
                        old_abs_y = self._to_float(getattr(old_layout, 'y', 0.0), 0.0)
                        node._pyreact_native_moved = True
                        node._pyreact_layout_move_from = {
                            'translateX': old_abs_x - abs_x,
                            'translateY': old_abs_y - abs_y,
                        }
                        if old_control_path and old_control_path != control_path:
                            self._remove_component_by_path(old_control_path, skip_cache_drop=bool(precleared_remove_paths.get(old_control_path)))
                    except Exception:
                        pass
                self._render_node(node, children_parent_path, parent_abs_x, parent_abs_y, index, True, children_parent_control)
                if self._needs_render:
                    return
                index += 1
                continue

            if not self._should_apply_commit_node(node, next_shadow_path, recreate_paths, commit_paths):
                try:
                    control = self._get_base_ui_control(control_path)
                except Exception:
                    control = None
                if not control:
                    self._needs_render = True
                    return
                self._apply_layout_to_existing_tree(
                    current_node=node,
                    parent_control_path=control_path,
                    parent_abs_x=abs_x,
                    parent_abs_y=abs_y,
                    shadow_path=next_shadow_path,
                    recreate_paths=recreate_paths,
                    move_sources=move_sources,
                    prune_parent_paths=prune_parent_paths,
                    commit_paths=commit_paths,
                    parent_control=control,
                )
                if self._needs_render:
                    return
                index += 1
                continue

            self._record_native_commit_perf('commit_apply')
            control = self._get_base_ui_control(control_path)

            if not control:
                parent_control = children_parent_control
                if parent_control is None:
                    parent_control = self._get_base_ui_control(children_parent_path)
                if not parent_control:
                    self._needs_render = True
                    return

                def_path = self._get_def_path(node_type)
                try:
                    control = self._clone(def_path, children_parent_path, child_name, False, False)
                except Exception:
                    control = None
                if not control:
                    control = self._get_base_ui_control(control_path)
                if not control:
                    self._needs_render = True
                    return
                try:
                    node._pyreact_native_created = True
                except Exception:
                    pass
            self._safe_set_position(control_path, abs_x - parent_abs_x, abs_y - parent_abs_y, control)
            if getattr(node, 'layout', None) is not None:
                try:
                    node.layout.native_local_x = abs_x - parent_abs_x
                    node.layout.native_local_y = abs_y - parent_abs_y
                except Exception:
                    pass
            if node_type != "Label":
                self._safe_set_size(control_path, width, height, control)
            self._apply_node_props(node, control_path, node_type, node_id, control)
            try:
                self._handle_node_applied_animations(node, control_path, node_type, node_id, control)
            except Exception:
                pass

            self._apply_layout_to_existing_tree(
                current_node=node,
                parent_control_path=child_control_paths,
                parent_abs_x=abs_x,
                parent_abs_y=abs_y,
                shadow_path=next_shadow_path,
                recreate_paths=recreate_paths,
                move_sources=move_sources,
                prune_parent_paths=prune_parent_paths,
                commit_paths=commit_paths,
                parent_control=control,
            )

            if self._needs_render:
                return
            index += 1

        if should_prune_children:
            try:
                self._record_native_commit_perf('prune_calls')
                # Remove any orphaned prefixed children not present in the new tree.
                self._prune_prefixed_children(children_parent_path, expected_child_names)
            except Exception:
                pass

    def _should_apply_commit_node(self, node, shadow_path, recreate_paths, commit_paths):
        if commit_paths is None:
            return True
        path_tuple = tuple(shadow_path or [])
        if recreate_paths and path_tuple in recreate_paths:
            return True
        node_type = self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
        if node_type == 'Scroll':
            return True
        exact_paths = None
        try:
            exact_paths = commit_paths.get('exact')
        except Exception:
            exact_paths = commit_paths
        if exact_paths and path_tuple in exact_paths:
            return True
        old_node = self._get_prev_shadow_node_by_shifted_path(shadow_path)
        if old_node is None:
            return True
        return self._shadow_node_native_signature(old_node) != self._shadow_node_native_signature(node)

    def _can_skip_unchanged_commit_node(self, node, shadow_path, recreate_paths, commit_paths):
        path_tuple = tuple(shadow_path or [])
        if recreate_paths and path_tuple in recreate_paths:
            return False
        exact_paths = None
        ancestor_paths = None
        if commit_paths:
            try:
                exact_paths = commit_paths.get('exact')
                ancestor_paths = commit_paths.get('ancestors')
            except Exception:
                exact_paths = commit_paths
        if exact_paths and path_tuple in exact_paths:
            return False
        if ancestor_paths and path_tuple in ancestor_paths:
            return False
        if commit_paths and ancestor_paths is None:
            for commit_path in commit_paths:
                if self._is_path_prefix(path_tuple, commit_path):
                    return False

        old_node = self._get_prev_shadow_node_by_shifted_path(shadow_path)
        if old_node is None:
            return False
        return self._shadow_node_native_signature(old_node) == self._shadow_node_native_signature(node)

    def _get_prev_shadow_node_by_shifted_path(self, shadow_path):
        start_time = self._perf_clock()
        path = list(shadow_path or [])
        if not path:
            self._record_native_commit_perf('prev_lookup_count')
            self._record_native_commit_perf('prev_lookup_ms', (self._perf_clock() - start_time) * 1000.0)
            return None
        if path[0] != 0:
            self._record_native_commit_perf('prev_lookup_count')
            self._record_native_commit_perf('prev_lookup_ms', (self._perf_clock() - start_time) * 1000.0)
            return None
        node = getattr(self, '_prev_shadow_root', None)
        index = 1
        while index < len(path):
            try:
                children = self._get_render_children(node, self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel'))
                node = children[path[index]]
            except Exception:
                self._record_native_commit_perf('prev_lookup_count')
                self._record_native_commit_perf('prev_lookup_ms', (self._perf_clock() - start_time) * 1000.0)
                return None
            index += 1
        self._record_native_commit_perf('prev_lookup_count')
        self._record_native_commit_perf('prev_lookup_ms', (self._perf_clock() - start_time) * 1000.0)
        return node

    def _find_prev_shadow_node_path_by_id(self, node_id):
        target_id = self._safe_text(node_id)
        if not target_id:
            return None
        root = getattr(self, '_prev_shadow_root', None)
        if root is None:
            return None
        root_path = self._safe_text(getattr(self, '_root_path', '/root'))
        stack = [(root, root_path, 0)]
        while stack:
            node, parent_path, index = stack.pop()
            current_id = self._safe_text(getattr(node, 'node_id', 'node'))
            child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, current_id, index)
            node_path = parent_path + '/' + child_name
            if current_id == target_id:
                return (node, node_path)

            node_type = self._safe_text(getattr(node, 'node_type', 'Panel') or 'Panel')
            children_parent_path = node_path
            if node_type == 'Scroll':
                try:
                    children_parent_path = self._get_scroll_content_path(node_path)
                except Exception:
                    children_parent_path = node_path
            try:
                children = self._get_render_children(node, node_type)
            except Exception:
                children = getattr(node, 'children', None) or []
            child_index = len(children or []) - 1
            while child_index >= 0:
                child = children[child_index]
                if child is not None:
                    stack.append((child, children_parent_path, child_index))
                child_index -= 1
        return None

    def _shadow_node_native_signature(self, node):
        start_time = self._perf_clock()
        if node is None:
            self._record_native_commit_perf('signature_count')
            self._record_native_commit_perf('signature_ms', (self._perf_clock() - start_time) * 1000.0)
            return None
        layout = getattr(node, 'layout', None)
        layout_sig = (
            int(round(self._to_float(getattr(layout, 'x', 0.0), 0.0) * 1000.0)),
            int(round(self._to_float(getattr(layout, 'y', 0.0), 0.0) * 1000.0)),
            int(round(self._to_float(getattr(layout, 'width', 0.0), 0.0) * 1000.0)),
            int(round(self._to_float(getattr(layout, 'height', 0.0), 0.0) * 1000.0)),
        )
        props = getattr(node, 'props', None) or {}
        if not isinstance(props, dict):
            props = {}
        style = getattr(node, 'style', None)
        if not isinstance(style, dict):
            style = props.get('style') if isinstance(props.get('style'), dict) else {}
        result = (
            self._safe_text(getattr(node, 'node_id', '')),
            self._safe_text(getattr(node, 'node_type', '')),
            layout_sig,
            self._make_commit_signature(style),
            self._make_commit_signature(props),
        )
        cost_ms = (self._perf_clock() - start_time) * 1000.0
        self._record_native_commit_perf('signature_count')
        self._record_native_commit_perf('signature_ms', cost_ms)
        self._record_native_commit_perf_max('signature_max_ms', cost_ms)
        return result

    def _make_commit_signature(self, value):
        if isinstance(value, dict):
            result = []
            for key in sorted(value.keys()):
                if key == 'children':
                    continue
                item = value.get(key)
                if callable(item):
                    result.append((key, 'callable'))
                else:
                    result.append((key, self._make_commit_signature(item)))
            return tuple(result)
        if isinstance(value, (list, tuple)):
            return tuple([self._make_commit_signature(item) for item in value])
        return self._safe_text(value)

    def _refresh_button_callbacks(self, shadow_root):
        self._button_callbacks = {}
        self._refresh_button_callbacks_walk([shadow_root], self._root_path)

    def _refresh_button_callbacks_from_vtree(self, vnode):
        callbacks = {}
        self._refresh_button_callbacks_from_vtree_walk(vnode, callbacks, [])
        self._button_callbacks = callbacks

    def _refresh_button_callbacks_from_vtree_walk(self, vnode, callbacks, path):
        if vnode is None:
            return
        try:
            node_type = self._safe_text(getattr(vnode, 'node_type', ''))
        except Exception:
            node_type = ''
        try:
            props = getattr(vnode, 'props', None) or {}
        except Exception:
            props = {}
        if node_type == 'Button' and isinstance(props, dict):
            onclick = props.get('onClick')
            if callable(onclick):
                node_id = self._vnode_node_id(vnode, path)
                if node_id:
                    callbacks[node_id] = onclick
        try:
            children = getattr(vnode, 'children', None) or []
        except Exception:
            children = []
        index = 0
        for child in children:
            child_path = list(path)
            child_path.append(index)
            self._refresh_button_callbacks_from_vtree_walk(child, callbacks, child_path)
            index += 1

    def _vnode_node_id(self, vnode, path):
        try:
            key = getattr(vnode, 'key', None)
        except Exception:
            key = None
        if key is not None:
            return 'k_%s' % self._sanitize_vnode_id_part(self._safe_text(key))
        if not path:
            return 'root'
        return 'p_%s' % '_'.join([self._safe_text(item) for item in path])

    def _sanitize_vnode_id_part(self, value):
        if value is None:
            return ''
        text = self._safe_text(value)
        out = []
        for ch in text:
            try:
                valid = ch.isalnum() or ch in ('_', '-', '.')
            except Exception:
                valid = False
            if valid:
                out.append(ch)
            else:
                try:
                    out.append('_%02x' % ord(ch))
                except Exception:
                    out.append('_')
        return ''.join(out)

    def _refresh_event_callback_tables(self, shadow_root):
        button_callbacks = {}
        input_callbacks = {}
        input_paths = {}
        self._refresh_event_callback_tables_walk([shadow_root], self._root_path, button_callbacks, input_callbacks, input_paths)
        self._button_callbacks = button_callbacks
        self._input_callbacks = input_callbacks
        self._input_paths = input_paths

    def _refresh_event_callback_tables_walk(self, current_node, parent_control_path, button_callbacks, input_callbacks, input_paths):
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
            props = getattr(child, 'props', None) or {}
            if isinstance(props, dict):
                if node_type == 'Button':
                    onclick = props.get('onClick')
                    if callable(onclick):
                        button_callbacks[child_id] = onclick
                elif node_type == 'Input':
                    input_paths[child_id] = control_path
                    onchange = props.get('onChange')
                    if callable(onchange):
                        input_callbacks[child_id] = onchange
                        self._ensure_input_edit_handlers_bound()
            self._refresh_event_callback_tables_walk(child, control_path, button_callbacks, input_callbacks, input_paths)
            index += 1

    def _remove_runtime_state_for_subtree(self, node):
        if node is None:
            return 0
        return self._remove_runtime_state_for_subtrees([node])

    def _remove_runtime_state_for_subtrees(self, nodes):
        stack = []
        for node in nodes or []:
            if node is not None:
                stack.append(node)
        if not stack:
            return 0

        ids = {}
        count = 0
        while stack:
            node = stack.pop()
            count += 1
            try:
                node_id = self._safe_text(getattr(node, 'node_id', ''))
            except Exception:
                node_id = ''
            if node_id:
                ids[node_id] = True
            try:
                children = getattr(node, 'children', None) or []
            except Exception:
                children = []
            for child in children:
                if child is not None:
                    stack.append(child)

        for table_name in ('_button_callbacks', '_input_callbacks', '_input_paths'):
            table = getattr(self, table_name, None)
            if not isinstance(table, dict):
                continue
            for node_id in ids:
                if node_id in table:
                    try:
                        del table[node_id]
                    except Exception:
                        pass

        refs = getattr(self, '_node_refs', None)
        if isinstance(refs, dict):
            for node_id in ids:
                if node_id in refs:
                    try:
                        self._set_ref_value(refs.get(node_id), None)
                        del refs[node_id]
                    except Exception:
                        pass
        return count

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
                    self._remove_component_by_path(child_path, skip_cache_drop=True)
            except Exception:
                pass

    def _render_children(self, children, parent_path, parent_abs_x, parent_abs_y, cache_already_cleared=False, parent_control=None):
        index = 0
        for child in children:
            self._render_node(child, parent_path, parent_abs_x, parent_abs_y, index, cache_already_cleared, parent_control)
            index += 1

    def _render_node(self, node, parent_path, parent_abs_x, parent_abs_y, sibling_index, cache_already_cleared=False, parent_control=None):
        render_start_time = self._perf_clock()
        if node is None:
            return

        node_type = self._safe_text(getattr(node, "node_type", "Panel") or "Panel")
        def_path = self._get_def_path(node_type)
        node_id = self._safe_text(getattr(node, "node_id", "node"))
        child_name = "%s%s_%s" % (self._CONTROL_NAME_PREFIX, node_id, sibling_index)

        if parent_control is None:
            parent_control = self._get_base_ui_control(parent_path)
        if not parent_control:
            return

        # child_control = self._screen.CreateChildControl(def_name, child_name, parent_control, False)
        child_control = self._clone(def_path, parent_path, child_name, False, False)

        if not child_control:
            return
        try:
            node._pyreact_native_created = True
        except Exception:
            pass

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
        if layout is not None:
            try:
                layout.native_local_x = local_x
                layout.native_local_y = local_y
            except Exception:
                pass
        if node_type != "Label":
            self._safe_set_size(node_path, width, height, child_control)
        props_start_time = self._perf_clock()
        self._apply_node_props(node, node_path, node_type, node_id, child_control, cache_already_cleared)
        try:
            self._handle_node_applied_animations(node, node_path, node_type, node_id, child_control)
        except Exception:
            pass
        self._record_native_commit_perf('apply_props_ms', (self._perf_clock() - props_start_time) * 1000.0)

        children_parent_path = node_path
        content_control = None
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
        self._record_native_commit_perf('render_node_count')
        self._record_native_commit_perf('render_node_ms', (self._perf_clock() - render_start_time) * 1000.0)
        children_start_time = self._perf_clock()
        next_parent_control = child_control
        if node_type == "Scroll":
            next_parent_control = content_control
        self._render_children(children, children_parent_path, child_parent_x, child_parent_y, cache_already_cleared, next_parent_control)
        self._record_native_commit_perf('render_children_ms', (self._perf_clock() - children_start_time) * 1000.0)

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
