# -*- coding: utf-8 -*-

import time

import mod.client.extraClientApi as clientApi

from PyreactRuntimeScript.native_runtime.native_api_mixin import _perf_now


class RuntimeLifecycleMixin(object):
    _PERF_KIND_LABELS = {
        'Mount': u'首次挂载',
        'Update': u'更新渲染',
    }

    def _describe_perf_kind(self, render_kind):
        safe_kind = self._safe_text(render_kind)
        if not safe_kind:
            return u'渲染'
        return self._PERF_KIND_LABELS.get(safe_kind, safe_kind)

    def _begin_render_detail_tracking(self):
        self._render_detail_state = {}
        self._render_control_cache = {}
        self._render_grid_availability_cache = {}
        self._render_parent_target_cache = {}
        self._render_scroll_content_path_cache = {}

    def _finish_render_detail_tracking(self):
        detail_state = getattr(self, '_render_detail_state', None)
        if not isinstance(detail_state, dict):
            detail_state = {}
        self._render_detail_state = None
        self._render_control_cache = None
        self._render_grid_availability_cache = None
        self._render_parent_target_cache = None
        self._render_scroll_content_path_cache = None
        return detail_state

    def _record_render_detail_ms(self, key, elapsed_ms):
        detail_state = getattr(self, '_render_detail_state', None)
        if not isinstance(detail_state, dict):
            return
        safe_key = self._safe_text(key)
        if not safe_key:
            return
        detail_state[safe_key] = self._to_float(detail_state.get(safe_key), 0.0) + self._to_float(elapsed_ms, 0.0)

    def _record_render_detail_count(self, key, increment=1):
        detail_state = getattr(self, '_render_detail_state', None)
        if not isinstance(detail_state, dict):
            return
        safe_key = self._safe_text(key)
        if not safe_key:
            return
        try:
            inc_value = int(increment)
        except Exception:
            inc_value = 0
        detail_state[safe_key] = int(detail_state.get(safe_key, 0) or 0) + inc_value

    def _get_cached_control(self, path, refresh=False, bucket='control_lookup'):
        safe_path = self._safe_text(path)
        if not safe_path:
            return None

        cache = getattr(self, '_render_control_cache', None)
        if isinstance(cache, dict) and not refresh and safe_path in cache:
            return cache.get(safe_path)

        start_time = _perf_now()
        try:
            control = self._screen.GetBaseUIControl(safe_path)
        except Exception:
            control = None
        elapsed_ms = (_perf_now() - start_time) * 1000.0

        safe_bucket = self._safe_text(bucket) or 'control_lookup'
        self._record_render_detail_ms('%s_ms' % safe_bucket, elapsed_ms)
        self._record_render_detail_count('%s_count' % safe_bucket, 1)

        if isinstance(cache, dict) and control is not None:
            cache[safe_path] = control
        return control

    def _drop_cached_control(self, path_prefix=None):
        cache = getattr(self, '_render_control_cache', None)
        if not isinstance(cache, dict):
            return
        if not path_prefix:
            cache.clear()
            return

        prefix = self._safe_text(path_prefix)
        if not prefix:
            return
        prefix_with_sep = prefix + '/'
        for cached_path in list(cache.keys()):
            safe_cached_path = self._safe_text(cached_path)
            if safe_cached_path == prefix or safe_cached_path.startswith(prefix_with_sep):
                try:
                    del cache[cached_path]
                except Exception:
                    pass

    def _log_render_detail_breakdown(self, detail_state, indent='   '):
        if not getattr(self, '_log_perf', False):
            return
        if not isinstance(detail_state, dict):
            return

        flatten_ms = self._to_float(detail_state.get('flatten_ms'), 0.0)
        cleanup_build_ms = self._to_float(detail_state.get('cleanup_build_ms'), 0.0)
        clear_root_ms = self._to_float(detail_state.get('clear_root_ms'), 0.0)
        entry_loop_ms = self._to_float(detail_state.get('entry_loop_ms'), 0.0)
        grid_flush_ms = self._to_float(detail_state.get('grid_flush_ms'), 0.0)
        schedule_refresh_ms = self._to_float(detail_state.get('schedule_refresh_ms'), 0.0)
        sync_apply_ms = self._to_float(detail_state.get('sync_apply_ms'), 0.0)
        sync_grid_apply_ms = self._to_float(detail_state.get('sync_grid_apply_ms'), 0.0)
        deferred_schedule_ms = self._to_float(detail_state.get('deferred_schedule_ms'), 0.0)

        prepare_total_ms = flatten_ms + cleanup_build_ms
        commit_total_ms = clear_root_ms + entry_loop_ms + grid_flush_ms + schedule_refresh_ms
        lookup_total_ms = (
            self._to_float(detail_state.get('lookup_parent_ms'), 0.0) +
            self._to_float(detail_state.get('lookup_node_ms'), 0.0) +
            self._to_float(detail_state.get('lookup_after_create_ms'), 0.0) +
            self._to_float(detail_state.get('grid_lookup_ms'), 0.0) +
            self._to_float(detail_state.get('clear_lookup_ms'), 0.0) +
            self._to_float(detail_state.get('layer_lookup_ms'), 0.0) +
            self._to_float(detail_state.get('scroll_lookup_ms'), 0.0) +
            self._to_float(detail_state.get('grid_widget_lookup_ms'), 0.0)
        )

        if prepare_total_ms <= 0.0 and commit_total_ms <= 0.0 and lookup_total_ms <= 0.0 and sync_apply_ms <= 0.0 and sync_grid_apply_ms <= 0.0 and deferred_schedule_ms <= 0.0:
            return

        self._perf_log(u'%s└─ 脚本提交流程细分' % indent)
        child_indent = indent + '   '

        if prepare_total_ms > 0.0:
            self._perf_log(u'%s├─ %s | 扁平化准备 [条目: %s, 父级: %s]' % (
                child_indent,
                self._format_perf_ms(prepare_total_ms),
                int(detail_state.get('flat_entry_count', 0) or 0),
                int(detail_state.get('cleanup_parent_count', 0) or 0),
            ))
            if flatten_ms > 0.0:
                self._perf_log(u'%s│  ├─ %s | 扁平化节点' % (child_indent, self._format_perf_ms(flatten_ms)))
            if cleanup_build_ms > 0.0:
                self._perf_log(u'%s│  └─ %s | 构建清理状态' % (child_indent, self._format_perf_ms(cleanup_build_ms)))

        if commit_total_ms > 0.0:
            self._perf_log(u'%s├─ %s | 提交内部阶段' % (
                child_indent,
                self._format_perf_ms(commit_total_ms),
            ))
            if clear_root_ms > 0.0:
                self._perf_log(u'%s│  ├─ %s | 清理根节点子控件 [扫描: %s, 移除: %s]' % (
                    child_indent,
                    self._format_perf_ms(clear_root_ms),
                    int(detail_state.get('clear_root_scan_count', 0) or 0),
                    int(detail_state.get('clear_root_removed_count', 0) or 0),
                ))
            if entry_loop_ms > 0.0:
                self._perf_log(u'%s│  ├─ %s | 渲染条目循环 [条目: %s, 待入网格: %s]' % (
                    child_indent,
                    self._format_perf_ms(entry_loop_ms),
                    int(detail_state.get('entry_count', 0) or 0),
                    int(detail_state.get('pending_grid_entry_count', 0) or 0),
                ))
            if grid_flush_ms > 0.0:
                self._perf_log(u'%s│  ├─ %s | 网格预处理 [网格: %s, 扩容: %s, 同步: %s, 延迟: %s]' % (
                    child_indent,
                    self._format_perf_ms(grid_flush_ms),
                    int(detail_state.get('grid_path_count', 0) or 0),
                    int(detail_state.get('grid_expand_count', 0) or 0),
                    int(detail_state.get('sync_grid_entry_count', 0) or 0),
                    int(detail_state.get('deferred_grid_entry_count', 0) or 0),
                ))
            if schedule_refresh_ms > 0.0:
                self._perf_log(u'%s│  └─ %s | 安排界面刷新' % (child_indent, self._format_perf_ms(schedule_refresh_ms)))

        if lookup_total_ms > 0.0:
            self._perf_log(u'%s├─ %s | 控件查询 [父级: %s, 节点: %s, 创建后: %s, 网格: %s, 部件: %s]' % (
                child_indent,
                self._format_perf_ms(lookup_total_ms),
                int(detail_state.get('lookup_parent_count', 0) or 0),
                int(detail_state.get('lookup_node_count', 0) or 0),
                int(detail_state.get('lookup_after_create_count', 0) or 0),
                int(detail_state.get('grid_lookup_count', 0) or 0),
                int(detail_state.get('grid_widget_lookup_count', 0) or 0),
            ))

        if sync_apply_ms > 0.0 or sync_grid_apply_ms > 0.0 or deferred_schedule_ms > 0.0:
            self._perf_log(u'%s└─ %s | 应用与调度 [普通: %s, 网格: %s, 延迟任务: %s]' % (
                child_indent,
                self._format_perf_ms(sync_apply_ms + sync_grid_apply_ms + deferred_schedule_ms),
                self._format_perf_ms(sync_apply_ms),
                self._format_perf_ms(sync_grid_apply_ms),
                int(detail_state.get('deferred_task_count', 0) or 0),
            ))

    def _get_perf_render_kind(self):
        next_kind = self._safe_text(getattr(self, '_next_render_perf_kind', ''))
        self._next_render_perf_kind = None
        if next_kind:
            return next_kind
        if getattr(self, '_render_generation', 0) <= 1:
            return 'Mount'
        return 'Update'

    def _calc_perf_ratio(self, part, total):
        total_value = self._to_float(total, 0.0)
        if total_value <= 0.0:
            return 0
        return int(round((self._to_float(part, 0.0) / total_value) * 100.0))

    def _log_render_stage_timings(self, render_kind, component_ms, build_ms, diff_ms, layout_ms, native_ms, deferred_grid_count=0, native_call_counts=None, layout_detail=None, render_detail=None):
        if not getattr(self, '_log_perf', False):
            return
        try:
            sync_total_ms = component_ms + build_ms + diff_ms + layout_ms + native_ms
            overhead_ms = native_ms
            native_total_ms = 0.0
            if isinstance(native_call_counts, dict):
                _, native_total_ms, _ = self._get_native_api_call_summary(native_call_counts)
            overhead_ms = max(0.0, native_ms - native_total_ms)
            app_id = self._safe_text(getattr(self, 'app_id', 'unknown')) or 'unknown'
            self._perf_log(u'━━━ 渲染管线帧耗时统计 (%s: %s) ━━━' % (self._describe_perf_kind(render_kind), app_id))
            self._perf_blank_line()
            if deferred_grid_count > 0:
                self._perf_log(u'█ 主流程阶段 [合计: %s]' % self._format_perf_ms(sync_total_ms))
            else:
                self._perf_log(u'█ 主流程阶段 [合计: %s]' % self._format_perf_ms(sync_total_ms))
            self._perf_log(u'   ├─ %s | 组件执行' % self._format_perf_ms(component_ms))
            self._perf_log(u'   ├─ %s | 构建虚拟节点' % self._format_perf_ms(build_ms))
            self._perf_log(u'   ├─ %s | 差异计算' % self._format_perf_ms(diff_ms))
            self._perf_log(u'   ├─ %s | 布局计算' % self._format_perf_ms(layout_ms))
            if isinstance(layout_detail, dict):
                shadow_build_ms = self._to_float(layout_detail.get('shadow_build_ms'), 0.0)
                pass1_ms = self._to_float(layout_detail.get('pass1_ms'), 0.0)
                pass2_ms = self._to_float(layout_detail.get('pass2_ms'), 0.0)
                pass3_ms = self._to_float(layout_detail.get('pass3_ms'), 0.0)
                if shadow_build_ms > 0.0 or pass1_ms > 0.0 or pass2_ms > 0.0 or pass3_ms > 0.0:
                    layout_rows = [
                        (u'构建阴影树 [节点: %s]' % int(layout_detail.get('shadow_node_count', 0) or 0), shadow_build_ms),
                        (u'第一轮测量', pass1_ms),
                        (u'第二轮布局', pass2_ms),
                    ]
                    if self._to_bool(layout_detail.get('needs_third_pass')) or pass3_ms > 0.0:
                        layout_rows.append((u'第三轮稳定化', pass3_ms))
                    row_count = len(layout_rows)
                    for row_index, layout_row in enumerate(layout_rows):
                        branch = u'└─' if row_index == (row_count - 1) else u'├─'
                        self._perf_log(u'   │  %s %s | %s' % (
                            branch,
                            self._format_perf_ms(layout_row[1]),
                            layout_row[0],
                        ))
            if deferred_grid_count > 0:
                self._log_native_api_nested('提交原生界面 [延迟网格 %s 项]' % deferred_grid_count, native_total_ms, overhead_ms, native_call_counts, indent='   ')
            else:
                self._log_native_api_nested('提交原生界面', native_total_ms, overhead_ms, native_call_counts, indent='   ')
            self._log_render_detail_breakdown(render_detail, indent='      ')
            self._perf_blank_line()
        except Exception:
            pass

    def _clear_deferred_perf_state(self):
        self._deferred_perf_state = None

    def _cancel_pending_deferred_perf_state(self):
        perf_state = getattr(self, '_deferred_perf_state', None)
        if not isinstance(perf_state, dict):
            return

        generation = perf_state.get('generation')
        try:
            remaining = int(perf_state.get('remaining', 0))
        except Exception:
            remaining = 0

        while remaining > 0:
            self._mark_deferred_grid_entry_done(generation, succeeded=False)
            remaining -= 1

    def _begin_deferred_perf_tracking(self, generation, deferred_grid_count, native_submit_ms, native_start_time, sync_total_ms):
        if not getattr(self, '_log_perf', False):
            return
        if deferred_grid_count <= 0:
            self._clear_deferred_perf_state()
            return

        self._deferred_perf_state = {
            'generation': generation,
            'render_kind': self._safe_text(getattr(self, '_active_render_perf_kind', 'Update')) or 'Update',
            'remaining': deferred_grid_count,
            'total': deferred_grid_count,
            'completed': 0,
            'failed': 0,
            'native_submit_ms': native_submit_ms,
            'native_start_time': native_start_time,
            'sync_total_ms': self._to_float(sync_total_ms, 0.0),
            'update_ticks': 0,
            'native_call_counts': {},
        }

    def _mark_deferred_perf_update_tick(self):
        perf_state = getattr(self, '_deferred_perf_state', None)
        if not isinstance(perf_state, dict):
            return
        perf_state['update_ticks'] = perf_state.get('update_ticks', 0) + 1

    def _mark_deferred_grid_entry_done(self, generation, succeeded=True):
        perf_state = getattr(self, '_deferred_perf_state', None)
        if not isinstance(perf_state, dict):
            return
        if perf_state.get('generation') != generation:
            return
        if perf_state.get('remaining', 0) <= 0:
            return

        if succeeded:
            perf_state['completed'] = perf_state.get('completed', 0) + 1
        else:
            perf_state['failed'] = perf_state.get('failed', 0) + 1

        remaining = perf_state.get('remaining', 0) - 1
        perf_state['remaining'] = remaining
        if remaining > 0:
            return

        perf_state['pending_finalize'] = True
        if getattr(self, '_native_api_counting_active', False):
            return

        self._finalize_deferred_perf_state(perf_state)

    def _finalize_deferred_perf_state(self, perf_state=None):
        if perf_state is None:
            perf_state = getattr(self, '_deferred_perf_state', None)
        if not isinstance(perf_state, dict):
            return
        if perf_state.get('remaining', 0) > 0:
            return
        if not perf_state.get('pending_finalize'):
            return

        perf_state['pending_finalize'] = False

        total_elapsed_ms = 0.0
        try:
            total_elapsed_ms = (_perf_now() - perf_state.get('native_start_time', _perf_now())) * 1000.0
        except Exception:
            total_elapsed_ms = 0.0

        native_submit_ms = self._to_float(perf_state.get('native_submit_ms', 0.0), 0.0)
        if total_elapsed_ms < native_submit_ms:
            total_elapsed_ms = native_submit_ms
        deferred_wait_ms = total_elapsed_ms - native_submit_ms
        try:
            sync_total_ms = self._to_float(perf_state.get('sync_total_ms', 0.0), 0.0)
            total_pipeline_ms = sync_total_ms + total_elapsed_ms
            async_ratio = self._calc_perf_ratio(total_elapsed_ms, total_pipeline_ms)
            native_total_ms = 0.0
            native_counts = perf_state.get('native_call_counts')
            if isinstance(native_counts, dict):
                _, native_total_ms, _ = self._get_native_api_call_summary(native_counts)
            native_overhead_ms = max(0.0, native_submit_ms - native_total_ms)
            update_ticks = perf_state.get('update_ticks', 0)
            self._perf_log(u'█ 跨帧异步任务 [合计: %s / 占比: %s%%]' % (
                self._format_perf_ms(total_elapsed_ms),
                async_ratio,
            ))
            self._perf_log(u'   ├─ %s | 等待主流程帧完成以及帧间隔 [共等 %s 帧]' % (
                self._format_perf_ms(deferred_wait_ms),
                update_ticks,
            ))
            self._log_native_api_nested('提交原生界面', native_total_ms, native_overhead_ms, native_counts, indent='   ')
            self._perf_blank_line()
        except Exception:
            pass

        self._clear_deferred_perf_state()

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
        try:
            self._init_animation_state()
        except Exception:
            pass

    def mount(self):
        self._mounted = True
        self._next_render_perf_kind = 'Mount'
        self._clear_pending_screen_refresh(clear_request=True)
        self._bind_screen_update_handler()
        self._ensure_measure_label()
        self.render()

    def unmount(self):
        self._mounted = False
        self._clear_pending_screen_update_tasks()
        self._clear_pending_screen_refresh(clear_request=True)
        self._clear_deferred_perf_state()
        self._unbind_screen_update_handler()
        try:
            self._reset_animation_state()
        except Exception:
            pass
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
        self._clear_root_children(clear_grid_pool=True)

    def request_render(self):
        if not self._mounted:
            return
        self._next_render_perf_kind = 'Update'
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

        self._render_generation += 1
        self._active_render_perf_kind = self._get_perf_render_kind()
        self._render_scheduled = False
        self._is_rendering = True
        try:
            self._cancel_pending_deferred_perf_state()
            self._clear_pending_screen_update_tasks()
            self._clear_pending_screen_refresh(clear_request=True)
            self._button_callbacks = {}
            self._input_callbacks = {}
            self._input_paths = {}
            self._node_refs = {}
            self._current_node_id_path_map = {}

            element = self._component_instance.render()
            component_ms = getattr(self._component_instance, 'last_render_duration_ms', 0.0)
            new_vtree = None
            build_ms = 0.0

            if element is None:
                diff_start_time = _perf_now()
                mutations = self._reconciler.reconcile(self._prev_vtree, None)
                diff_ms = (_perf_now() - diff_start_time) * 1000.0

                native_start_time = _perf_now()
                self._begin_native_api_call_batch()
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
                    self._clear_root_children(clear_grid_pool=True)
                    self._schedule_pending_screen_refresh()
                finally:
                    native_call_counts = self._finish_native_api_call_batch()
                native_ms = (_perf_now() - native_start_time) * 1000.0
                self._log_render_stage_timings(self._active_render_perf_kind, component_ms, build_ms, diff_ms, 0.0, native_ms, native_call_counts=native_call_counts)
                return

            width, height = self._get_root_size()

            new_vtree = self._tree_builder.build_tree(element)
            tree_perf = self._tree_builder.get_last_perf_stats()
            component_ms += tree_perf.get('component_exec_ms', 0.0)
            build_ms = tree_perf.get('build_only_ms', 0.0)

            diff_start_time = _perf_now()
            mutations = self._reconciler.reconcile(self._prev_vtree, new_vtree)
            diff_ms = (_perf_now() - diff_start_time) * 1000.0

            layout_start_time = _perf_now()
            shadow_root = self._layout_engine.calculate(new_vtree, width, height)
            layout_ms = (_perf_now() - layout_start_time) * 1000.0
            layout_detail = self._layout_engine.get_last_perf_stats()

            render_detail = {}
            self._begin_render_detail_tracking()
            self._render_grid_counts = {}
            self._render_grid_slot_reservations = {}
            self._render_live_grid_node_slots = {}
            flatten_start_time = _perf_now()
            flat_entries = self._collect_flat_entries_for_root([shadow_root], self._root_path)
            render_detail['flatten_ms'] = (_perf_now() - flatten_start_time) * 1000.0
            render_detail['flat_entry_count'] = len(flat_entries)

            # Detect exit animations BEFORE building cleanup state so the grid
            # slot allocator (inside build_cleanup) can avoid handing the same
            # widget to a new node while an old one is still animating out.
            try:
                new_node_ids = set()
                for entry in flat_entries:
                    if not isinstance(entry, dict):
                        continue
                    nid = self._safe_text(entry.get('node_id'))
                    if nid:
                        new_node_ids.add(nid)
                self.detect_and_register_exit_animations(self._prev_shadow_root, new_node_ids, self._root_path)
            except Exception:
                pass

            cleanup_build_start_time = _perf_now()
            expected_children_by_parent, current_root_scroll_hosts = self._build_render_cleanup_state(flat_entries)
            render_detail['cleanup_build_ms'] = (_perf_now() - cleanup_build_start_time) * 1000.0
            render_detail['cleanup_parent_count'] = len(expected_children_by_parent)

            try:
                path_by_node_id = {}
                layout_snapshot_by_node_id = {}
                for entry in flat_entries:
                    if not isinstance(entry, dict):
                        continue
                    nid = self._safe_text(entry.get('node_id'))
                    if not nid:
                        continue
                    parent_path = self._safe_text(entry.get('resolved_parent_path'))
                    if not parent_path:
                        parent_path = self._resolve_parent_target(entry.get('parent_target'))
                    child_name = self._safe_text(entry.get('child_name'))
                    if parent_path and child_name:
                        node_obj = entry.get('node')
                        shadow_layout = getattr(node_obj, 'layout', None) if node_obj is not None else None
                        path_by_node_id[nid] = (parent_path + '/' + child_name, shadow_layout)
                        if shadow_layout is not None:
                            try:
                                layout_snapshot_by_node_id[nid] = {
                                    'x': float(getattr(shadow_layout, 'x', 0.0) or 0.0),
                                    'y': float(getattr(shadow_layout, 'y', 0.0) or 0.0),
                                }
                            except Exception:
                                pass
                mgr = getattr(self, '_animation_manager', None)
                if mgr is not None:
                    mgr.retarget_paths(path_by_node_id)
                self.merge_exiting_expected_children(expected_children_by_parent)
                # Stash for end-of-render gc. Includes every flat entry,
                # even ones deferred to the next frame via the grid pool —
                # without that, gc_seen_node_ids would prune deferred
                # nodes' ids, and next frame they'd be seen as "new" and
                # re-trigger enter animations.
                self._flat_entry_live_ids_this_render = set(path_by_node_id.keys())
                self._flat_entry_path_map_this_render = dict(path_by_node_id)
                self._flat_entry_layout_map_this_render = layout_snapshot_by_node_id
            except Exception:
                self._flat_entry_live_ids_this_render = set()
                self._flat_entry_path_map_this_render = {}
                self._flat_entry_layout_map_this_render = {}

            native_start_time = _perf_now()
            self._begin_native_api_call_batch()
            try:
                if getattr(self, '_debug_render', False):
                    counts = {}
                    muts = mutations or []
                    for m in muts:
                        t = self._safe_text(getattr(m, 'type_', ''))
                        counts[t] = counts.get(t, 0) + 1
                clear_root_start_time = _perf_now()
                self._clear_root_children(
                    clear_grid_pool=False,
                    expected_children_by_parent=expected_children_by_parent,
                    current_root_scroll_hosts=current_root_scroll_hosts,
                )
                render_detail['clear_root_ms'] = (_perf_now() - clear_root_start_time) * 1000.0

                render_tree_start_time = _perf_now()
                deferred_grid_count = self._render_flat_tree([shadow_root], self._root_path, entries=flat_entries)
                render_detail['render_tree_ms'] = (_perf_now() - render_tree_start_time) * 1000.0

                schedule_refresh_start_time = _perf_now()
                self._schedule_pending_screen_refresh()
                render_detail['schedule_refresh_ms'] = (_perf_now() - schedule_refresh_start_time) * 1000.0
            finally:
                tracked_detail = self._finish_render_detail_tracking()
                native_call_counts = self._finish_native_api_call_batch()
            native_ms = (_perf_now() - native_start_time) * 1000.0
            if isinstance(tracked_detail, dict):
                render_detail.update(tracked_detail)

            if deferred_grid_count > 0:
                sync_total_ms = component_ms + build_ms + diff_ms + layout_ms + native_ms
                self._begin_deferred_perf_tracking(self._render_generation, deferred_grid_count, native_ms, native_start_time, sync_total_ms)

            self._log_render_stage_timings(self._active_render_perf_kind, component_ms, build_ms, diff_ms, layout_ms, native_ms, deferred_grid_count, native_call_counts=native_call_counts, layout_detail=layout_detail, render_detail=render_detail)

            self._prev_vtree = new_vtree
            self._prev_shadow_root = shadow_root
            try:
                # Use the full flat_entries map (includes deferred grid entries)
                # instead of ``_current_node_id_path_map`` (which only has
                # sync-applied ones). Otherwise gc_seen_node_ids would prune
                # deferred nodes' ids and they'd re-trigger enter animations
                # when they apply next frame.
                full_map = getattr(self, '_flat_entry_path_map_this_render', None) or {}
                self._prev_node_id_path_map = {}
                for nid, pe in full_map.items():
                    try:
                        self._prev_node_id_path_map[nid] = pe[0]
                    except Exception:
                        pass
            except Exception:
                self._prev_node_id_path_map = {}
            # Snapshot the layout map so next render's _handle_node_applied
            # can diff positions and trigger auto layout tweens when a node
            # moves (e.g. after a sibling exits).
            try:
                self._layout_map_last_render = dict(
                    getattr(self, '_flat_entry_layout_map_this_render', None) or {}
                )
            except Exception:
                self._layout_map_last_render = {}
            try:
                mgr = getattr(self, '_animation_manager', None)
                if mgr is not None:
                    live_ids = getattr(self, '_flat_entry_live_ids_this_render', None) or set()
                    mgr.gc_seen_node_ids(live_ids)
            except Exception:
                pass
            try:
                self._cleanup_input_state()
            except Exception:
                pass
            try:
                self._cleanup_refs()
            except Exception:
                pass
        finally:
            self._active_render_perf_kind = None
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

    def _bind_screen_update_handler(self):
        screen = getattr(self, '_screen', None)
        if not screen:
            return

        runtime_list_attr = '_pyreact_update_runtimes'
        try:
            runtimes = getattr(screen, runtime_list_attr)
        except Exception:
            runtimes = None
        if not isinstance(runtimes, list):
            runtimes = []
            try:
                setattr(screen, runtime_list_attr, runtimes)
            except Exception:
                return

        if self not in runtimes:
            runtimes.append(self)

        screen_cls = screen.__class__
        marker_attr = '_pyreact_update_wrapper_installed'
        if getattr(screen_cls, marker_attr, False):
            return

        try:
            original_update = getattr(screen_cls, 'Update', None)
        except Exception:
            original_update = None

        def _pyreact_runtime_update(self_screen):
            try:
                if callable(original_update):
                    original_update(self_screen)
            except Exception:
                pass

            try:
                runtime_list = getattr(self_screen, runtime_list_attr, None) or []
            except Exception:
                runtime_list = []

            for runtime in list(runtime_list):
                try:
                    runtime._run_screen_update_tasks()
                except Exception:
                    pass

        try:
            setattr(screen_cls, 'Update', _pyreact_runtime_update)
            setattr(screen_cls, marker_attr, True)
        except Exception:
            pass

    def _unbind_screen_update_handler(self):
        screen = getattr(self, '_screen', None)
        if not screen:
            return

        try:
            runtimes = getattr(screen, '_pyreact_update_runtimes', None)
        except Exception:
            runtimes = None
        if not isinstance(runtimes, list):
            return

        try:
            while self in runtimes:
                runtimes.remove(self)
        except Exception:
            pass

    def _clear_pending_screen_update_tasks(self):
        self._screen_update_tasks = []
        self._clear_pending_screen_refresh(clear_request=False)

    def _clear_pending_screen_refresh(self, clear_request=True):
        self._screen_refresh_task_scheduled = False
        if not clear_request:
            return
        self._pending_screen_refresh = False
        self._pending_screen_refresh_sync = False
        self._pending_screen_refresh_use_current = True

    def _request_screen_refresh(self, sync_refresh=False, use_current=True):
        self._pending_screen_refresh = True
        if sync_refresh:
            self._pending_screen_refresh_sync = True
        if not hasattr(self, '_pending_screen_refresh_use_current'):
            self._pending_screen_refresh_use_current = True
        self._pending_screen_refresh_use_current = bool(self._pending_screen_refresh_use_current and use_current)

    def _flush_pending_screen_refresh(self):
        self._screen_refresh_task_scheduled = False
        if not getattr(self, '_mounted', False):
            self._clear_pending_screen_refresh(clear_request=True)
            return True
        if not getattr(self, '_pending_screen_refresh', False):
            return True

        sync_refresh = bool(getattr(self, '_pending_screen_refresh_sync', False))
        use_current = bool(getattr(self, '_pending_screen_refresh_use_current', True))
        self._pending_screen_refresh = False
        self._pending_screen_refresh_sync = False
        self._pending_screen_refresh_use_current = True

        screen = getattr(self, '_screen', None)
        if not screen or not hasattr(screen, 'UpdateScreen'):
            return True

        try:
            start_time = _perf_now()
            screen.UpdateScreen(sync_refresh, use_current)
            self._count_native_api_call('UpdateScreen', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            return True
        except Exception:
            self._request_screen_refresh(sync_refresh=sync_refresh, use_current=use_current)
            return False

    def _schedule_pending_screen_refresh(self):
        if not getattr(self, '_pending_screen_refresh', False):
            return
        if getattr(self, '_screen_refresh_task_scheduled', False):
            return
        self._screen_refresh_task_scheduled = True
        self._schedule_screen_update_task(
            self._flush_pending_screen_refresh,
            retries=3,
            on_give_up=self._clear_pending_screen_refresh,
        )

    def _schedule_screen_update_task(self, callback, retries=3, on_give_up=None):
        if not callable(callback):
            return

        try:
            retry_count = int(retries)
        except Exception:
            retry_count = 0
        if retry_count < 0:
            retry_count = 0

        self._screen_update_tasks.append({
            'callback': callback,
            'retries': retry_count,
            'on_give_up': on_give_up,
        })

    def _run_screen_update_tasks(self):
        if not getattr(self, '_mounted', False):
            self._clear_pending_screen_update_tasks()
            self._clear_deferred_perf_state()
            return

        tasks = getattr(self, '_screen_update_tasks', None) or []
        if not tasks:
            return

        self._mark_deferred_perf_update_tick()
        self._begin_native_api_call_batch()

        self._screen_update_tasks = []
        for task in tasks:
            callback = None
            retries = 0
            on_give_up = None
            if isinstance(task, dict):
                callback = task.get('callback')
                retries = task.get('retries', 0)
                on_give_up = task.get('on_give_up')
            if not callable(callback):
                continue

            should_retry = False
            task_failed = False
            try:
                result = callback()
                should_retry = (result is False)
            except Exception:
                should_retry = False
                task_failed = True

            if should_retry:
                try:
                    retries = int(retries)
                except Exception:
                    retries = 0
                if retries > 0:
                    self._screen_update_tasks.append({
                        'callback': callback,
                        'retries': retries - 1,
                        'on_give_up': on_give_up,
                    })
                elif callable(on_give_up):
                    try:
                        on_give_up()
                    except Exception:
                        pass
            elif task_failed and callable(on_give_up):
                try:
                    on_give_up()
                except Exception:
                    pass

        perf_state = getattr(self, '_deferred_perf_state', None)
        if isinstance(perf_state, dict):
            self._merge_native_api_call_counts(perf_state.get('native_call_counts'), self._finish_native_api_call_batch())
            self._finalize_deferred_perf_state(perf_state)
        else:
            self._finish_native_api_call_batch()

        self._schedule_pending_screen_refresh()

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
        parent_target_cache = getattr(self, '_render_parent_target_cache', None)
        cache_key = id(parent_target)
        use_parent_cache = kind not in ('scroll_content', 'scroll_content_of_entry')
        if use_parent_cache and isinstance(parent_target_cache, dict) and cache_key in parent_target_cache:
            return parent_target_cache.get(cache_key) or self._root_path

        if kind == 'scroll_content_of_entry':
            scroll_parent_path = self._resolve_parent_target(parent_target.get('parent_target'))
            scroll_child_name = self._safe_text(parent_target.get('scroll_child_name'))
            if not scroll_child_name:
                resolved_path = scroll_parent_path or self._root_path
                if use_parent_cache and isinstance(parent_target_cache, dict):
                    parent_target_cache[cache_key] = resolved_path
                return resolved_path
            scroll_node_path = (scroll_parent_path or self._root_path) + '/' + scroll_child_name
            resolved_path = self._get_scroll_content_path(scroll_node_path)
            if resolved_path != scroll_node_path and isinstance(parent_target_cache, dict):
                parent_target_cache[cache_key] = resolved_path
            return resolved_path

        path = parent_target.get('path')
        if kind == 'scroll_content':
            resolved_path = self._get_scroll_content_path(path)
        else:
            resolved_path = path or self._root_path
        if use_parent_cache and isinstance(parent_target_cache, dict):
            parent_target_cache[cache_key] = resolved_path
        elif kind == 'scroll_content' and resolved_path != (path or self._root_path) and isinstance(parent_target_cache, dict):
            parent_target_cache[cache_key] = resolved_path
        return resolved_path

    def _get_real_scroll_view_path_for_cleanup(self, scroll_node_path, cleanup_scroll_view_cache=None):
        safe_path = self._safe_text(scroll_node_path)
        if not safe_path:
            return ''
        if isinstance(cleanup_scroll_view_cache, dict) and safe_path in cleanup_scroll_view_cache:
            return cleanup_scroll_view_cache.get(safe_path) or ''

        resolved_path = self._get_real_scroll_view_path(safe_path)
        if isinstance(cleanup_scroll_view_cache, dict):
            cleanup_scroll_view_cache[safe_path] = resolved_path or ''
        return resolved_path

    def _get_scroll_content_path_for_cleanup(self, scroll_node_path, cleanup_scroll_content_cache=None, cleanup_scroll_view_cache=None):
        safe_path = self._safe_text(scroll_node_path)
        if not safe_path:
            return self._root_path
        if isinstance(cleanup_scroll_content_cache, dict) and safe_path in cleanup_scroll_content_cache:
            return cleanup_scroll_content_cache.get(safe_path) or safe_path

        real_scroll_view_path = self._get_real_scroll_view_path_for_cleanup(safe_path, cleanup_scroll_view_cache)
        if "/scroll_touch/" in real_scroll_view_path:
            content_path = real_scroll_view_path + "/panel/background_and_viewport/scrolling_view_port/scrolling_content"
        elif "/scroll_mouse/" in real_scroll_view_path:
            content_path = real_scroll_view_path + "/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content"
        else:
            content_path = safe_path

        if isinstance(cleanup_scroll_content_cache, dict):
            cleanup_scroll_content_cache[safe_path] = content_path
        return content_path

    def _resolve_parent_target_for_cleanup(self, parent_target, cleanup_parent_target_cache=None, cleanup_scroll_content_cache=None, cleanup_scroll_view_cache=None):
        if not isinstance(parent_target, dict):
            return self._root_path

        cache_key = id(parent_target)
        if isinstance(cleanup_parent_target_cache, dict) and cache_key in cleanup_parent_target_cache:
            return cleanup_parent_target_cache.get(cache_key) or self._root_path

        kind = parent_target.get('kind')
        if kind == 'scroll_content_of_entry':
            scroll_parent_path = self._resolve_parent_target_for_cleanup(
                parent_target.get('parent_target'),
                cleanup_parent_target_cache,
                cleanup_scroll_content_cache,
                cleanup_scroll_view_cache,
            )
            scroll_child_name = self._safe_text(parent_target.get('scroll_child_name'))
            if not scroll_child_name:
                resolved_path = scroll_parent_path or self._root_path
            else:
                scroll_node_path = (scroll_parent_path or self._root_path) + '/' + scroll_child_name
                resolved_path = self._get_scroll_content_path_for_cleanup(
                    scroll_node_path,
                    cleanup_scroll_content_cache,
                    cleanup_scroll_view_cache,
                )
        else:
            path = parent_target.get('path')
            if kind == 'scroll_content':
                resolved_path = self._get_scroll_content_path_for_cleanup(
                    path,
                    cleanup_scroll_content_cache,
                    cleanup_scroll_view_cache,
                )
            else:
                resolved_path = path or self._root_path

        if isinstance(cleanup_parent_target_cache, dict):
            cleanup_parent_target_cache[cache_key] = resolved_path
        return resolved_path

    def _is_grid_available_for_parent_for_cleanup(self, parent_path, node_type, cleanup_grid_availability_cache=None):
        cache_key = '%s|%s' % (self._safe_text(parent_path), self._safe_text(node_type))
        if isinstance(cleanup_grid_availability_cache, dict) and cache_key in cleanup_grid_availability_cache:
            return bool(cleanup_grid_availability_cache.get(cache_key))

        available = self._is_grid_available_for_parent(parent_path, node_type)
        if isinstance(cleanup_grid_availability_cache, dict):
            cleanup_grid_availability_cache[cache_key] = bool(available)
        return available

    def _get_entry_grid_render_index_for_cleanup(self, parent_path, node_type, grid_index_map=None, cleanup_grid_availability_cache=None):
        if not self._get_grid_type_config(node_type):
            return 0
        if not self._is_grid_available_for_parent_for_cleanup(parent_path, node_type, cleanup_grid_availability_cache):
            return 0
        return self._get_entry_grid_render_index(parent_path, node_type, grid_index_map)

    def _compute_native_layer_value(self, node, native_depth, layer_anchor=None, layer_depth=0):
        try:
            resolved_native_depth = int(native_depth)
        except Exception:
            resolved_native_depth = 0
        try:
            resolved_layer_depth = int(layer_depth)
        except Exception:
            resolved_layer_depth = 0

        try:
            style = getattr(node, 'style', None) or {}
            position_value = ''
            z_index = 0
            if isinstance(style, dict):
                position_value = self._safe_text(style.get('position')).strip().lower()
                z_index = int(round(self._to_float(style.get('zIndex'), 0.0)))
        except Exception:
            position_value = ''
            z_index = 0

        if layer_anchor is not None:
            try:
                resolved_anchor = int(layer_anchor)
            except Exception:
                resolved_anchor = 0
            return resolved_anchor + (resolved_layer_depth * 10) + z_index

        native_layer = (resolved_native_depth * 1000) + z_index
        if position_value == 'absolute' and z_index != 0:
            native_layer = (z_index * 10000) + resolved_native_depth
        return native_layer

    def _collect_flat_entries(self, current_node, parent_target, entries, native_depth=0, layer_anchor=None, layer_depth=0):
        if current_node is None:
            return

        if isinstance(current_node, (list, tuple)):
            for child in current_node:
                self._collect_flat_entries(child, parent_target, entries, native_depth, layer_anchor, layer_depth)
            return

        node_type = self._safe_text(getattr(current_node, 'node_type', 'Panel') or 'Panel')
        children = self._get_render_children(current_node, node_type)

        if self._is_virtual_node(node_type):
            for child in children:
                self._collect_flat_entries(child, parent_target, entries, native_depth, layer_anchor, layer_depth)
            return

        child_name = self._get_control_name(current_node)
        entry_native_depth = native_depth + 1
        entry_layer_depth = layer_depth + 1 if layer_anchor is not None else 0
        entry_native_layer = self._compute_native_layer_value(
            current_node,
            entry_native_depth,
            layer_anchor=layer_anchor,
            layer_depth=entry_layer_depth,
        )
        entries.append({
            'node': current_node,
            'node_type': node_type,
            'node_id': self._safe_text(getattr(current_node, 'node_id', 'node')),
            'parent_target': parent_target,
            'child_name': child_name,
            'native_depth': entry_native_depth,
            'native_final_layer': entry_native_layer,
        })

        next_parent_target = parent_target
        next_layer_anchor = layer_anchor
        next_layer_depth = entry_layer_depth
        if node_type == 'Scroll':
            next_parent_target = {
                'kind': 'scroll_content_of_entry',
                'parent_target': parent_target,
                'scroll_child_name': child_name,
            }
        if node_type == 'Button':
            next_layer_anchor = entry_native_layer + 10
            next_layer_depth = 0

        for child in children:
            self._collect_flat_entries(child, next_parent_target, entries, entry_native_depth, next_layer_anchor, next_layer_depth)

    def _collect_flat_entries_for_root(self, children, root_parent_path):
        entries = []
        self._collect_flat_entries(children, self._make_parent_target('path', root_parent_path), entries)
        return entries

    def _build_render_cleanup_state(self, entries):
        expected_children_by_parent = {}
        current_root_scroll_hosts = {}
        grid_index_map = {}
        cleanup_parent_target_cache = {}
        cleanup_scroll_content_cache = {}
        cleanup_scroll_view_cache = {}
        cleanup_grid_availability_cache = {}

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            parent_path = self._resolve_parent_target_for_cleanup(
                entry.get('parent_target'),
                cleanup_parent_target_cache,
                cleanup_scroll_content_cache,
                cleanup_scroll_view_cache,
            )
            node_type = self._safe_text(entry.get('node_type'))
            child_name = self._safe_text(entry.get('child_name'))
            if not parent_path or not child_name:
                continue

            entry['resolved_parent_path'] = parent_path

            child_path = parent_path + '/' + child_name
            if parent_path == self._root_path and node_type == 'Scroll':
                current_root_scroll_hosts[child_path] = True

            if not child_name.startswith(self._CONTROL_NAME_PREFIX):
                continue

            if self._is_grid_available_for_parent_for_cleanup(parent_path, node_type, cleanup_grid_availability_cache):
                grid_index = self._reserve_stable_grid_index(
                    parent_path,
                    node_type,
                    entry.get('node_id'),
                )
            else:
                grid_index = 0
            if grid_index > 0:
                entry['render_in_grid'] = True
                entry['grid_index'] = grid_index
                continue
            if 'render_in_grid' in entry:
                try:
                    del entry['render_in_grid']
                except Exception:
                    pass
            if 'grid_index' in entry:
                try:
                    del entry['grid_index']
                except Exception:
                    pass

            bucket = expected_children_by_parent.get(parent_path)
            if not isinstance(bucket, dict):
                bucket = {}
                expected_children_by_parent[parent_path] = bucket
            bucket[child_name] = True

        return expected_children_by_parent, current_root_scroll_hosts

    def _render_flat_tree(self, children, root_parent_path, entries=None):
        if not isinstance(entries, list):
            entries = self._collect_flat_entries_for_root(children, root_parent_path)

        pending_grid_entries = []
        self._record_render_detail_count('entry_count', len(entries))

        entry_loop_start_time = _perf_now()
        for entry in entries:
            pending_grid_entry = self._render_flat_entry(entry)
            if pending_grid_entry:
                pending_grid_entries.append(pending_grid_entry)
            if self._needs_render:
                return
        self._record_render_detail_ms('entry_loop_ms', (_perf_now() - entry_loop_start_time) * 1000.0)
        self._record_render_detail_count('pending_grid_entry_count', len(pending_grid_entries))

        deferred_count = 0
        grid_flush_start_time = _perf_now()
        if pending_grid_entries:
            deferred_count = self._flush_pending_grid_entries(pending_grid_entries)
        elif root_parent_path == self._root_path:
            self._hide_unused_grid_entries({}, {})
        self._record_render_detail_ms('grid_flush_ms', (_perf_now() - grid_flush_start_time) * 1000.0)

        return deferred_count

    def _render_flat_entry(self, entry):
        node = entry.get('node')
        parent_target = entry.get('parent_target')
        parent_kind = None
        if isinstance(parent_target, dict):
            parent_kind = self._safe_text(parent_target.get('kind'))
        parent_path = self._safe_text(entry.get('resolved_parent_path'))
        if parent_kind in ('scroll_content', 'scroll_content_of_entry'):
            parent_path = self._resolve_parent_target(parent_target)
        elif not parent_path:
            parent_path = self._resolve_parent_target(parent_target)
        node_type = entry.get('node_type')
        node_id = entry.get('node_id')
        child_name = entry.get('child_name')
        node_path = parent_path + '/' + child_name
        layout = getattr(node, 'layout', None)
        if layout is not None:
            existing_native_layer = getattr(layout, 'native_final_layer', None)
            existing_native_depth = getattr(layout, 'native_depth', None)
            if existing_native_layer is None:
                try:
                    native_depth = int(entry.get('native_depth', 0))
                except Exception:
                    native_depth = 0
                layout.native_depth = native_depth
                layout.native_final_layer = entry.get('native_final_layer')
            elif existing_native_depth is None:
                layout.native_depth = 0

        grid_entry = self._build_pending_grid_entry(entry, parent_path)
        if grid_entry is not None:
            return grid_entry

        parent_control = self._get_cached_control(parent_path, bucket='lookup_parent')
        if not parent_control:
            self._needs_render = True
            return

        control = self._get_cached_control(node_path, bucket='lookup_node')
        if not control:
            def_name = self._get_def_name(node_type)
            try:
                create_start_time = _perf_now()
                self._screen.CreateChildControl(def_name, child_name, parent_control)
                self._count_native_api_call('CreateChildControl', elapsed_ms=(_perf_now() - create_start_time) * 1000.0)
            except Exception:
                pass
            self._drop_cached_control(node_path)
            control = self._get_cached_control(node_path, refresh=True, bucket='lookup_after_create')
            if not control:
                self._needs_render = True
                return
            self._drop_native_common_style_cache(node_path)

        self._apply_rendered_entry(node, node_type, node_id, node_path, control)

    def _apply_rendered_entry(self, node, node_type, node_id, node_path, control, native_layer_path=None, native_layer_control=None):
        if not control:
            self._needs_render = True
            return False

        apply_start_time = _perf_now()

        layout = getattr(node, 'layout', None)
        local_x = self._to_float(getattr(layout, 'x', 0.0), 0.0)
        local_y = self._to_float(getattr(layout, 'y', 0.0), 0.0)
        width = self._to_float(getattr(layout, 'width', 0.0), 0.0)
        height = self._to_float(getattr(layout, 'height', 0.0), 0.0)

        position_locked = False
        size_locked = False
        try:
            if self.is_animation_field_locked(node_path, 'position'):
                position_locked = True
            if self.is_animation_field_locked(node_path, 'size'):
                size_locked = True
        except Exception:
            pass

        if not position_locked:
            self._safe_set_position(node_path, local_x, local_y, control)
        if node_type != 'Label' and not size_locked:
            self._safe_set_size(node_path, width, height, control)

        props = getattr(node, 'props', None)
        item_widget_path = None
        item_widget_control = None
        if node_type == 'Item' and not (control and hasattr(control, 'asItemRenderer')):
            item_widget_path = node_path + '/widget'
            item_widget_control = self._get_cached_control(item_widget_path, bucket='item_widget_lookup')
            if item_widget_control and not size_locked:
                self._safe_set_size(item_widget_path, width, height, item_widget_control)
        if isinstance(props, dict):
            props['__shadow_node__'] = node
            if native_layer_path:
                props['__native_layer_path__'] = native_layer_path
            if native_layer_control:
                props['__native_layer_control__'] = native_layer_control
            if item_widget_path:
                props['__native_item_widget_path__'] = item_widget_path
            if item_widget_control:
                props['__native_item_widget_control__'] = item_widget_control
        self._apply_node_props(node, node_path, node_type, node_id, control)
        if isinstance(props, dict) and '__shadow_node__' in props:
            try:
                del props['__shadow_node__']
            except Exception:
                pass
        if isinstance(props, dict) and '__native_layer_path__' in props:
            try:
                del props['__native_layer_path__']
            except Exception:
                pass
        if isinstance(props, dict) and '__native_layer_control__' in props:
            try:
                del props['__native_layer_control__']
            except Exception:
                pass
        if isinstance(props, dict) and '__native_item_widget_path__' in props:
            try:
                del props['__native_item_widget_path__']
            except Exception:
                pass
        if isinstance(props, dict) and '__native_item_widget_control__' in props:
            try:
                del props['__native_item_widget_control__']
            except Exception:
                pass

        if node_type == 'Scroll' and layout:
            content_path = self._get_scroll_content_path(node_path)
            content_control = self._get_cached_control(content_path, bucket='scroll_lookup')
            if content_control:
                self._safe_set_size(content_path, layout.content_width, layout.content_height, content_control)
            self._apply_scroll_props(node, node_path)
        self._record_render_detail_ms('sync_apply_ms', (_perf_now() - apply_start_time) * 1000.0)

        # Record the actual native path this node_id is bound to this render.
        # Used by the animation manager when detecting exits next time around
        # (so it can resolve the real grid-pool widget path instead of the
        # default flat-entry path).
        id_path_map = getattr(self, '_current_node_id_path_map', None)
        if isinstance(id_path_map, dict) and node_id:
            id_path_map[node_id] = node_path

        # Fire the animation hook — every entity node that gets applied,
        # whether via the flat path or the grid pool path, flows through
        # here. Inside the hook, ``seen_node_ids`` decides whether this is
        # a brand-new appearance (enter animation trigger).
        try:
            self._handle_node_applied_animations(node, node_path, node_id, node_type, control)
        except Exception:
            pass

        return True

    def _get_grid_type_config(self, node_type):
        return self._GRID_TYPE_CONFIG.get(node_type)

    def _get_grid_item_wrapper_name(self, template_name, index):
        return '%s%s' % (self._safe_text(template_name), int(index))

    def _get_grid_item_paths(self, parent_path, node_type, index):
        grid_config = self._get_grid_type_config(node_type)
        if not isinstance(grid_config, dict):
            return None

        grid_name = self._safe_text(grid_config.get('grid_name'))
        template_name = self._safe_text(grid_config.get('template_name'))
        if not grid_name or not template_name:
            return None

        grid_path = parent_path + '/' + grid_name
        wrapper_name = self._get_grid_item_wrapper_name(template_name, index)
        wrapper_path = grid_path + '/' + wrapper_name
        return {
            'grid_path': grid_path,
            'wrapper_name': wrapper_name,
            'wrapper_path': wrapper_path,
            'widget_path': wrapper_path + '/widget',
        }

    def _get_grid_slot_record(self, grid_path, node_type, index, create=False):
        safe_grid_path = self._safe_text(grid_path)
        if not safe_grid_path:
            return None
        try:
            slot_index = int(index)
        except Exception:
            slot_index = 0
        if slot_index <= 0:
            return None

        state = self._ensure_grid_pool_state(safe_grid_path, node_type)
        if not isinstance(state, dict):
            return None
        slots = state.get('slots')
        if not isinstance(slots, dict):
            slots = {}
            state['slots'] = slots

        slot_record = slots.get(slot_index)
        if isinstance(slot_record, dict):
            return slot_record
        if not create:
            return None

        grid_config = self._get_grid_type_config(node_type)
        template_name = self._safe_text(grid_config.get('template_name')) if isinstance(grid_config, dict) else ''
        if not template_name:
            return None

        wrapper_name = self._get_grid_item_wrapper_name(template_name, slot_index)
        wrapper_path = safe_grid_path + '/' + wrapper_name
        slot_record = {
            'index': slot_index,
            'grid_path': safe_grid_path,
            'wrapper_name': wrapper_name,
            'wrapper_path': wrapper_path,
            'widget_path': wrapper_path + '/widget',
            'widget_control': None,
        }
        slots[slot_index] = slot_record
        return slot_record

    def _is_grid_available_for_parent(self, parent_path, node_type):
        availability_cache = getattr(self, '_render_grid_availability_cache', None)
        cache_key = '%s|%s' % (self._safe_text(parent_path), self._safe_text(node_type))
        if isinstance(availability_cache, dict) and cache_key in availability_cache:
            return bool(availability_cache.get(cache_key))

        start_time = _perf_now()
        paths = self._get_grid_item_paths(parent_path, node_type, 1)
        if not isinstance(paths, dict):
            self._record_render_detail_ms('grid_check_ms', (_perf_now() - start_time) * 1000.0)
            self._record_render_detail_count('grid_check_count', 1)
            return False
        try:
            available = bool(self._get_cached_control(paths.get('grid_path'), bucket='grid_lookup'))
        except Exception:
            available = False
        self._record_render_detail_ms('grid_check_ms', (_perf_now() - start_time) * 1000.0)
        self._record_render_detail_count('grid_check_count', 1)
        if available and isinstance(availability_cache, dict):
            availability_cache[cache_key] = True
        return available

    def _get_entry_grid_render_index(self, parent_path, node_type, grid_index_map=None):
        grid_config = self._get_grid_type_config(node_type)
        if not grid_config:
            return 0
        if not self._is_grid_available_for_parent(parent_path, node_type):
            return 0

        if not isinstance(grid_index_map, dict):
            grid_index_map = {}
        key = '%s|%s' % (self._safe_text(parent_path), self._safe_text(node_type))
        next_index = grid_index_map.get(key, 0) + 1

        # Skip slot indices currently held by an exit animation so a freshly
        # mounted node never ends up sharing a widget with an animating-out
        # node (which would cause alpha/position writes to clash).
        exiting_indices = None
        mgr = getattr(self, '_animation_manager', None)
        if mgr is not None:
            grid_name = self._safe_text(grid_config.get('grid_name'))
            if grid_name:
                grid_path = self._safe_text(parent_path) + '/' + grid_name
                exiting_indices = mgr.exiting_grid_slots.get(grid_path)
        while exiting_indices and next_index in exiting_indices:
            next_index += 1

        max_pool_size = self._get_grid_pool_limit(node_type, 'max_pool_size', 0)
        if max_pool_size > 0 and next_index > max_pool_size:
            return 0

        grid_index_map[key] = next_index
        return next_index

    def _next_grid_index(self, parent_path, node_type):
        if not isinstance(getattr(self, '_render_grid_counts', None), dict):
            self._render_grid_counts = {}
        key = '%s|%s' % (self._safe_text(parent_path), self._safe_text(node_type))
        next_index = self._render_grid_counts.get(key, 0) + 1

        # Skip slot indices currently held by an exit animation.
        exiting_indices = None
        mgr = getattr(self, '_animation_manager', None)
        if mgr is not None:
            grid_config = self._get_grid_type_config(node_type)
            if isinstance(grid_config, dict):
                grid_name = self._safe_text(grid_config.get('grid_name'))
                if grid_name:
                    grid_path = self._safe_text(parent_path) + '/' + grid_name
                    exiting_indices = mgr.exiting_grid_slots.get(grid_path)
        while exiting_indices and next_index in exiting_indices:
            next_index += 1

        self._render_grid_counts[key] = next_index
        return next_index

    def _get_grid_path_for_parent(self, parent_path, node_type):
        paths = self._get_grid_item_paths(parent_path, node_type, 1)
        if not isinstance(paths, dict):
            return ''
        return self._safe_text(paths.get('grid_path'))

    def _reserve_stable_grid_index(self, parent_path, node_type, node_id):
        if not self._is_grid_available_for_parent(parent_path, node_type):
            return 0

        safe_node_id = self._safe_text(node_id)
        safe_grid_path = self._get_grid_path_for_parent(parent_path, node_type)
        if not safe_grid_path:
            return 0

        state = self._ensure_grid_pool_state(safe_grid_path, node_type)
        if not isinstance(state, dict):
            return 0

        node_slots = state.get('node_slots')
        if not isinstance(node_slots, dict):
            node_slots = {}
            state['node_slots'] = node_slots

        reservations = getattr(self, '_render_grid_slot_reservations', None)
        if not isinstance(reservations, dict):
            reservations = {}
            self._render_grid_slot_reservations = reservations
        reserved_indices = reservations.get(safe_grid_path)
        if not isinstance(reserved_indices, set):
            reserved_indices = set()
            reservations[safe_grid_path] = reserved_indices

        live_node_slots_by_grid = getattr(self, '_render_live_grid_node_slots', None)
        if not isinstance(live_node_slots_by_grid, dict):
            live_node_slots_by_grid = {}
            self._render_live_grid_node_slots = live_node_slots_by_grid
        live_node_slots = live_node_slots_by_grid.get(safe_grid_path)
        if not isinstance(live_node_slots, dict):
            live_node_slots = {}
            live_node_slots_by_grid[safe_grid_path] = live_node_slots

        existing_index = 0
        if safe_node_id:
            try:
                existing_index = int(node_slots.get(safe_node_id, 0) or 0)
            except Exception:
                existing_index = 0
        if existing_index > 0:
            if existing_index in reserved_indices:
                existing_index = 0
            else:
                if safe_node_id:
                    live_node_slots[safe_node_id] = existing_index
                reserved_indices.add(existing_index)
                key = '%s|%s' % (self._safe_text(parent_path), self._safe_text(node_type))
                if not isinstance(getattr(self, '_render_grid_counts', None), dict):
                    self._render_grid_counts = {}
                current_max = int(self._render_grid_counts.get(key, 0) or 0)
                if existing_index > current_max:
                    self._render_grid_counts[key] = existing_index
                return existing_index

        used_indices = set()
        for value in reserved_indices:
            try:
                index_value = int(value)
            except Exception:
                index_value = 0
            if index_value > 0:
                used_indices.add(index_value)

        exiting_indices = None
        mgr = getattr(self, '_animation_manager', None)
        if mgr is not None:
            exiting_indices = mgr.exiting_grid_slots.get(safe_grid_path)

        max_pool_size = self._get_grid_pool_limit(node_type, 'max_pool_size', 0)
        next_index = 1
        while True:
            if next_index in used_indices or next_index in reserved_indices:
                next_index += 1
                continue
            if exiting_indices and next_index in exiting_indices:
                next_index += 1
                continue
            break

        if max_pool_size > 0 and next_index > max_pool_size:
            return 0

        if safe_node_id:
            node_slots[safe_node_id] = next_index
            live_node_slots[safe_node_id] = next_index
        reserved_indices.add(next_index)
        key = '%s|%s' % (self._safe_text(parent_path), self._safe_text(node_type))
        if not isinstance(getattr(self, '_render_grid_counts', None), dict):
            self._render_grid_counts = {}
        current_max = int(self._render_grid_counts.get(key, 0) or 0)
        if next_index > current_max:
            self._render_grid_counts[key] = next_index
        return next_index

    def _build_pending_grid_entry(self, entry, parent_path):
        node_type = entry.get('node_type')
        grid_config = self._get_grid_type_config(node_type)
        if not grid_config:
            return None
        precomputed = entry.get('render_in_grid')
        if precomputed is True:
            index = entry.get('grid_index', 0)
        else:
            index = self._reserve_stable_grid_index(parent_path, node_type, entry.get('node_id'))
        max_pool_size = self._get_grid_pool_limit(node_type, 'max_pool_size', 0)
        if max_pool_size > 0 and index > max_pool_size:
            return None
        paths = self._get_grid_item_paths(parent_path, node_type, index)
        if not isinstance(paths, dict):
            return None
        slot_record = self._get_grid_slot_record(paths.get('grid_path'), node_type, index, create=True)
        if isinstance(slot_record, dict):
            wrapper_path = self._safe_text(slot_record.get('wrapper_path')) or paths.get('wrapper_path')
            widget_path = self._safe_text(slot_record.get('widget_path')) or paths.get('widget_path')
        else:
            wrapper_path = paths.get('wrapper_path')
            widget_path = paths.get('widget_path')

        return {
            'node': entry.get('node'),
            'node_type': node_type,
            'node_id': entry.get('node_id'),
            'parent_path': parent_path,
            'grid_path': paths.get('grid_path'),
            'wrapper_path': wrapper_path,
            'widget_path': widget_path,
            'grid_index': index,
            'generation': self._render_generation,
            'slot_record': slot_record,
        }

    def _flush_pending_grid_entries(self, pending_grid_entries):
        grid_counts = {}
        grid_types = {}
        for pending_entry in pending_grid_entries:
            if not isinstance(pending_entry, dict):
                continue
            grid_path = self._safe_text(pending_entry.get('grid_path'))
            grid_index = pending_entry.get('grid_index', 0)
            node_type = self._safe_text(pending_entry.get('node_type'))
            if not grid_path:
                continue
            try:
                grid_index = int(grid_index)
            except Exception:
                grid_index = 0
            if grid_index <= 0:
                continue
            prev_count = grid_counts.get(grid_path, 0)
            if grid_index > prev_count:
                grid_counts[grid_path] = grid_index
                grid_types[grid_path] = node_type

        self._record_render_detail_count('grid_path_count', len(grid_counts))

        # Check which grids need capacity expansion (requires async frame wait)
        grids_needing_expansion = {}
        for grid_path, grid_count in grid_counts.items():
            node_type = grid_types.get(grid_path)
            state = self._ensure_grid_pool_state(grid_path, node_type)
            current_capacity = int(state.get('capacity', 0)) if isinstance(state, dict) else 0
            needs_expansion = grid_count > current_capacity
            if needs_expansion:
                grids_needing_expansion[grid_path] = True

        self._record_render_detail_count('grid_expand_count', len(grids_needing_expansion))

        # Expand capacity for grids that need it (async path)
        for grid_path, grid_count in grid_counts.items():
            self._ensure_grid_pool_capacity(grid_path, grid_types.get(grid_path), grid_count)

        self._hide_unused_grid_entries(grid_counts, grid_types)

        deferred_count = 0
        deferred_entries = []
        for pending_entry in pending_grid_entries:
            if not isinstance(pending_entry, dict):
                continue
            grid_path = self._safe_text(pending_entry.get('grid_path'))
            if grid_path and grids_needing_expansion.get(grid_path):
                deferred_entries.append(pending_entry)
                deferred_count += 1
                continue
            self._apply_grid_entry_sync(pending_entry)
            self._record_render_detail_count('sync_grid_entry_count', 1)
        if deferred_entries:
            self._schedule_grid_entry_apply(deferred_entries)
        self._record_render_detail_count('deferred_grid_entry_count', deferred_count)
        return deferred_count

    def _schedule_grid_entry_apply(self, pending_entry):
        if isinstance(pending_entry, dict):
            pending_entries = [pending_entry]
        elif isinstance(pending_entry, list):
            pending_entries = pending_entry
        else:
            return

        remaining_entries = []
        for entry in pending_entries:
            if isinstance(entry, dict):
                remaining_entries.append(entry)
        if not remaining_entries:
            return

        self._record_render_detail_count('deferred_task_count', 1)

        def _mark_pending_grid_entry_failed():
            for entry in list(remaining_entries):
                self._mark_deferred_grid_entry_done(entry.get('generation'), succeeded=False)
            remaining_entries[:] = []

        def _apply_pending_grid_entry_batch():
            if not remaining_entries:
                return True

            generation = remaining_entries[0].get('generation')
            if generation != self._render_generation:
                _mark_pending_grid_entry_failed()
                return True

            deferred_schedule_start_time = _perf_now()
            next_remaining_entries = []
            for entry in remaining_entries:
                widget_path = self._safe_text(entry.get('widget_path'))
                if not widget_path:
                    self._mark_deferred_grid_entry_done(entry.get('generation'), succeeded=False)
                    continue
                slot_record = entry.get('slot_record')
                widget_control = slot_record.get('widget_control') if isinstance(slot_record, dict) else None
                if not widget_control:
                    widget_control = self._get_cached_control(widget_path, refresh=True, bucket='grid_widget_lookup')
                    if widget_control and isinstance(slot_record, dict):
                        slot_record['widget_control'] = widget_control
                if not widget_control:
                    next_remaining_entries.append(entry)
                    continue
                if self._apply_grid_entry_with_control(entry, widget_control, detail_bucket='deferred_grid_apply_ms'):
                    self._mark_deferred_grid_entry_done(entry.get('generation'))
                else:
                    next_remaining_entries.append(entry)
            remaining_entries[:] = next_remaining_entries
            self._record_render_detail_ms('deferred_schedule_ms', (_perf_now() - deferred_schedule_start_time) * 1000.0)
            return not remaining_entries

        self._schedule_screen_update_task(_apply_pending_grid_entry_batch, retries=6, on_give_up=_mark_pending_grid_entry_failed)

    def _apply_grid_entry_with_control(self, pending_entry, widget_control, detail_bucket='sync_grid_apply_ms'):
        if not isinstance(pending_entry, dict):
            return True
        if not widget_control:
            return False

        apply_start_time = _perf_now()
        widget_path = self._safe_text(pending_entry.get('widget_path'))
        wrapper_path = self._safe_text(pending_entry.get('wrapper_path'))
        node_type = pending_entry.get('node_type')
        slot_record = pending_entry.get('slot_record')
        current_node_id = self._safe_text(pending_entry.get('node_id'))
        last_node_id = ''
        if isinstance(slot_record, dict):
            last_node_id = self._safe_text(slot_record.get('last_node_id'))
        slot_rebound = bool(current_node_id) and current_node_id != last_node_id

        if not isinstance(getattr(self, '_grid_slot_visible_states', None), dict):
            self._grid_slot_visible_states = {}
        slot_states = self._grid_slot_visible_states
        slot_key = self._safe_text(widget_path)
        needs_reactivate = slot_states.get(slot_key) != True
        force_refresh_visible = slot_rebound
        if needs_reactivate:
            self._safe_set_visible(widget_path, True, widget_control, sync_refresh=False)
            slot_states[slot_key] = True
        elif force_refresh_visible:
            try:
                self._set_cached_native_prop(widget_path, 'visible', None)
            except Exception:
                pass
            self._safe_set_visible(widget_path, True, widget_control, sync_refresh=False)
            slot_states[slot_key] = True

        needs_native_reset = needs_reactivate or slot_rebound
        if needs_native_reset:
            self._reset_pooled_widget_native_state(widget_path, node_type, widget_control)
            self._drop_native_common_style_cache_fields(widget_path, ('opacity',))

        native_layer_path = None
        if node_type in ('Item', 'PaperDoll'):
            native_layer_path = wrapper_path

        applied = self._apply_rendered_entry(
            pending_entry.get('node'),
            node_type,
            pending_entry.get('node_id'),
            widget_path,
            widget_control,
            native_layer_path=native_layer_path,
        )
        if applied and isinstance(slot_record, dict):
            slot_record['last_node_id'] = current_node_id
        self._record_render_detail_ms(detail_bucket, (_perf_now() - apply_start_time) * 1000.0)
        return applied

    def _apply_grid_entry_sync(self, pending_entry):
        """Apply grid entry synchronously without waiting for next frame."""
        if not isinstance(pending_entry, dict):
            return True

        slot_record = pending_entry.get('slot_record')
        widget_path = self._safe_text(pending_entry.get('widget_path'))
        if not widget_path:
            return True

        widget_control = slot_record.get('widget_control') if isinstance(slot_record, dict) else None
        if not widget_control:
            widget_control = self._get_cached_control(widget_path, bucket='grid_widget_lookup')
            if widget_control and isinstance(slot_record, dict):
                slot_record['widget_control'] = widget_control
        if not widget_control:
            return False
        return self._apply_grid_entry_with_control(pending_entry, widget_control, detail_bucket='sync_grid_apply_ms')

    def _get_grid_pool_limit(self, node_type, field_name, fallback=0):
        grid_config = self._get_grid_type_config(node_type)
        if not isinstance(grid_config, dict):
            return fallback
        try:
            value = int(grid_config.get(field_name, fallback))
        except Exception:
            value = fallback
        if value < 0:
            value = fallback
        return value

    def _ensure_grid_pool_state(self, grid_path, node_type):
        if not isinstance(getattr(self, '_grid_pool_states', None), dict):
            self._grid_pool_states = {}
        safe_grid_path = self._safe_text(grid_path)
        if not safe_grid_path:
            return None

        state = self._grid_pool_states.get(safe_grid_path)
        initial_pool_size = self._get_grid_pool_limit(node_type, 'initial_pool_size', 0)
        max_pool_size = self._get_grid_pool_limit(node_type, 'max_pool_size', initial_pool_size)
        if max_pool_size < initial_pool_size:
            max_pool_size = initial_pool_size

        if not isinstance(state, dict):
            state = {
                'node_type': node_type,
                'capacity': int(initial_pool_size),
                'active_count': 0,
                'max_pool_size': max_pool_size,
                'initialized': bool(initial_pool_size > 0),
                'slots': {},
            }
            self._grid_pool_states[safe_grid_path] = state
            return state

        state['node_type'] = node_type
        state['max_pool_size'] = max_pool_size
        if self._to_float(state.get('active_count'), 0) < 0:
            state['active_count'] = 0
        return state

    def _ensure_grid_pool_capacity(self, grid_path, node_type, required_count):
        state = self._ensure_grid_pool_state(grid_path, node_type)
        if not isinstance(state, dict):
            return False

        try:
            needed = int(required_count)
        except Exception:
            needed = 0
        if needed <= 0:
            return True

        current_capacity = int(state.get('capacity', 0) or 0)
        target_capacity = needed
        if target_capacity <= current_capacity:
            state['initialized'] = True
            return True

        max_pool_size = int(state.get('max_pool_size', current_capacity) or current_capacity)
        if target_capacity > max_pool_size:
            target_capacity = max_pool_size

        # SetGridDimension appears to make NetEase re-layout every slot in
        # the grid. On list growth that would visually perturb every
        # already-rendered widget on each +1. Instead we grow geometrically:
        # first allocation sizes to exactly what's needed (keeping first-
        # mount cost low), subsequent growths at least double the capacity
        # so the number of SetGridDimension calls stays O(log N).
        if current_capacity > 0:
            doubled = current_capacity * 2
            if doubled > target_capacity:
                target_capacity = doubled
            if target_capacity > max_pool_size:
                target_capacity = max_pool_size

        if target_capacity <= current_capacity:
            state['initialized'] = True
            return True

        for slot_index in range(current_capacity + 1, target_capacity + 1):
            self._get_grid_slot_record(grid_path, node_type, slot_index, create=True)

        if self._safe_set_grid_dimension(grid_path, 1, target_capacity):
            # Hide newly created slots beyond current capacity
            if target_capacity > current_capacity:
                self._set_grid_entry_visibility_range(grid_path, node_type, current_capacity + 1, target_capacity, False)
            state['capacity'] = target_capacity
            state['initialized'] = True
            return True
        return False

    def _hide_unused_grid_entries(self, grid_counts, grid_types):
        pool_states = getattr(self, '_grid_pool_states', None)
        if not isinstance(pool_states, dict):
            return

        mgr = getattr(self, '_animation_manager', None)
        exiting_by_grid = getattr(mgr, 'exiting_grid_slots', None) if mgr is not None else None
        reservations = getattr(self, '_render_grid_slot_reservations', None)
        if not isinstance(reservations, dict):
            reservations = {}
        live_node_slots_by_grid = getattr(self, '_render_live_grid_node_slots', None)
        if not isinstance(live_node_slots_by_grid, dict):
            live_node_slots_by_grid = {}

        for grid_path, state in pool_states.items():
            if not isinstance(state, dict):
                continue
            node_type = grid_types.get(grid_path) or state.get('node_type')
            next_active = grid_counts.get(grid_path, 0)
            try:
                next_active = int(next_active)
            except Exception:
                next_active = 0
            try:
                prev_active = int(state.get('active_count', 0))
            except Exception:
                prev_active = 0

            exiting_indices = exiting_by_grid.get(grid_path) if isinstance(exiting_by_grid, dict) else None

            reserved_indices = reservations.get(grid_path)
            if not isinstance(reserved_indices, set):
                reserved_indices = set()

            keep_indices = set()
            for idx in reserved_indices:
                try:
                    safe_idx = int(idx)
                except Exception:
                    safe_idx = 0
                if safe_idx > 0:
                    keep_indices.add(safe_idx)
            if exiting_indices:
                for idx in exiting_indices:
                    try:
                        safe_idx = int(idx)
                    except Exception:
                        safe_idx = 0
                    if safe_idx > 0:
                        keep_indices.add(safe_idx)

            hide_end = prev_active
            if next_active > hide_end:
                hide_end = next_active
            for idx in keep_indices:
                if idx > hide_end:
                    hide_end = idx

            if hide_end > 0:
                self._set_grid_entry_visibility_range(
                    grid_path, node_type, 1, hide_end, False,
                    skip_indices=keep_indices,
                )

            effective_active = 0
            for idx in keep_indices:
                if idx > effective_active:
                    effective_active = idx
            state['active_count'] = effective_active
            live_node_slots = live_node_slots_by_grid.get(grid_path)
            if isinstance(live_node_slots, dict):
                state['node_slots'] = dict(live_node_slots)
            else:
                state['node_slots'] = {}

    def _hide_all_used_grid_entries(self):
        pool_states = getattr(self, '_grid_pool_states', None)
        if not isinstance(pool_states, dict):
            return

        for grid_path, state in pool_states.items():
            if not isinstance(state, dict):
                continue
            node_type = state.get('node_type')
            try:
                active_count = int(state.get('active_count', 0))
            except Exception:
                active_count = 0
            if active_count > 0:
                self._set_grid_entry_visibility_range(grid_path, node_type, 1, active_count, False)
            state['active_count'] = 0

    def _set_grid_entry_visibility_range(self, grid_path, node_type, start_index, end_index, visible, skip_indices=None):
        if not grid_path or not node_type:
            return

        try:
            begin = int(start_index)
            end = int(end_index)
        except Exception:
            return

        if begin <= 0 or end < begin:
            return

        skip_set = None
        if skip_indices:
            try:
                skip_set = set(int(i) for i in skip_indices)
            except Exception:
                skip_set = None

        # Track visible states to avoid redundant SetVisible calls
        if not isinstance(getattr(self, '_grid_slot_visible_states', None), dict):
            self._grid_slot_visible_states = {}
        slot_states = self._grid_slot_visible_states
        safe_grid_path = self._safe_text(grid_path)
        grid_config = self._get_grid_type_config(node_type)
        template_name = self._safe_text(grid_config.get('template_name')) if isinstance(grid_config, dict) else ''
        if not safe_grid_path or not template_name:
            return

        for index in range(begin, end + 1):
            if skip_set is not None and index in skip_set:
                continue
            slot_record = self._get_grid_slot_record(safe_grid_path, node_type, index, create=True)
            widget_path = self._safe_text(slot_record.get('widget_path')) if isinstance(slot_record, dict) else ''
            slot_key = self._safe_text(widget_path)
            current_state = slot_states.get(slot_key)
            if current_state == visible:
                continue
            widget_control = slot_record.get('widget_control') if isinstance(slot_record, dict) else None
            if not widget_control and widget_path:
                widget_control = self._get_cached_control(widget_path, bucket='grid_widget_lookup')
                if widget_control and isinstance(slot_record, dict):
                    slot_record['widget_control'] = widget_control
            if not widget_control:
                continue
            self._safe_set_visible(widget_path, visible, widget_control, sync_refresh=False)
            slot_states[slot_key] = visible

    def _get_grid_item_paths_by_grid_path(self, grid_path, node_type, index):
        grid_config = self._get_grid_type_config(node_type)
        if not isinstance(grid_config, dict):
            return None

        grid_name = self._safe_text(grid_config.get('grid_name'))
        template_name = self._safe_text(grid_config.get('template_name'))
        safe_grid_path = self._safe_text(grid_path)
        if not grid_name or not template_name or not safe_grid_path:
            return None

        suffix = '/' + grid_name
        if not safe_grid_path.endswith(suffix):
            return None

        parent_path = safe_grid_path[:-len(suffix)]
        wrapper_name = self._get_grid_item_wrapper_name(template_name, index)
        wrapper_path = safe_grid_path + '/' + wrapper_name
        return {
            'grid_path': safe_grid_path,
            'wrapper_name': wrapper_name,
            'wrapper_path': wrapper_path,
            'widget_path': wrapper_path + '/widget',
            'parent_path': parent_path,
        }

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

    def _collect_render_cleanup_state(self, children, root_parent_path):
        entries = self._collect_flat_entries_for_root(children, root_parent_path)
        return self._build_render_cleanup_state(entries)

    def _would_render_entry_in_grid(self, parent_path, node_type, grid_index_map=None):
        return self._get_entry_grid_render_index(parent_path, node_type, grid_index_map) > 0

    def _drop_grid_pool_states_under_path(self, root_path):
        safe_root_path = self._safe_text(root_path)
        if not safe_root_path:
            return
        pool_states = getattr(self, '_grid_pool_states', None)
        if not isinstance(pool_states, dict):
            return

        prefix = safe_root_path + '/'
        stale_paths = []
        for grid_path in pool_states.keys():
            safe_grid_path = self._safe_text(grid_path)
            if safe_grid_path == safe_root_path or safe_grid_path.startswith(prefix):
                stale_paths.append(safe_grid_path)

        for stale_path in stale_paths:
            try:
                del pool_states[stale_path]
            except Exception:
                pass

    def _drop_grid_slot_visible_states_under_path(self, root_path):
        safe_root_path = self._safe_text(root_path)
        if not safe_root_path:
            return

        slot_states = getattr(self, '_grid_slot_visible_states', None)
        if not isinstance(slot_states, dict):
            return

        prefix = safe_root_path + '/'
        stale_paths = []
        for widget_path in slot_states.keys():
            safe_widget_path = self._safe_text(widget_path)
            if safe_widget_path == safe_root_path or safe_widget_path.startswith(prefix):
                stale_paths.append(safe_widget_path)

        for stale_path in stale_paths:
            try:
                del slot_states[stale_path]
            except Exception:
                pass

    def _prune_preserved_host_subtree(self, parent_path, expected_children_by_parent):
        safe_parent_path = self._safe_text(parent_path)
        if not safe_parent_path:
            return

        expected_child_names = expected_children_by_parent.get(safe_parent_path, [])
        self._prune_prefixed_children(safe_parent_path, expected_child_names)

        for child_name in expected_child_names:
            safe_child_name = self._safe_text(child_name)
            if not safe_child_name.startswith(self._CONTROL_NAME_PREFIX):
                continue
            child_path = safe_parent_path + '/' + safe_child_name
            self._prune_preserved_host_subtree(child_path, expected_children_by_parent)
            scroll_content_path = self._get_scroll_content_path(child_path)
            if scroll_content_path and scroll_content_path != child_path:
                self._prune_preserved_host_subtree(scroll_content_path, expected_children_by_parent)

    def _clear_root_children(self, clear_grid_pool=False, expected_children_by_parent=None, current_root_scroll_hosts=None):
        if clear_grid_pool:
            self._drop_native_common_style_cache()
        self._render_grid_counts = {}
        if clear_grid_pool:
            self._hide_all_used_grid_entries()
            self._preserved_root_scroll_hosts = {}
            self._grid_slot_visible_states = {}
            self._drop_native_layout_cache()

        if not isinstance(expected_children_by_parent, dict):
            expected_children_by_parent = {}
        if not isinstance(current_root_scroll_hosts, dict):
            current_root_scroll_hosts = {}
        preserved_root_scroll_hosts = getattr(self, '_preserved_root_scroll_hosts', None)
        if not isinstance(preserved_root_scroll_hosts, dict):
            preserved_root_scroll_hosts = {}
            self._preserved_root_scroll_hosts = preserved_root_scroll_hosts

        children_read_start_time = _perf_now()
        try:
            names = self._screen.GetChildrenName(self._root_path) or []
        except Exception:
            names = []
        self._record_render_detail_ms('clear_root_list_ms', (_perf_now() - children_read_start_time) * 1000.0)
        self._record_render_detail_count('clear_root_scan_count', len(names))

        existing_root_paths = {}
        expected_root_children = expected_children_by_parent.get(self._root_path) or {}

        for name in names:
            safe_name = self._safe_text(name)
            if not safe_name.startswith(self._CONTROL_NAME_PREFIX):
                continue
            child_path = self._root_path + "/" + safe_name
            existing_root_paths[child_path] = True
            try:
                child_control = self._get_cached_control(child_path, bucket='clear_lookup')
                if not child_control:
                    continue

                is_preserved_scroll = (not clear_grid_pool) and (child_path in current_root_scroll_hosts or child_path in preserved_root_scroll_hosts)
                if is_preserved_scroll:
                    preserved_root_scroll_hosts[child_path] = True
                    if child_path in current_root_scroll_hosts:
                        self._safe_set_visible(child_path, True, child_control, sync_refresh=False)
                        self._prune_preserved_host_subtree(child_path, expected_children_by_parent)
                        scroll_content_path = self._get_scroll_content_path(child_path)
                        if scroll_content_path and scroll_content_path != child_path:
                            self._prune_preserved_host_subtree(scroll_content_path, expected_children_by_parent)
                    else:
                        self._safe_set_visible(child_path, False, child_control, sync_refresh=False)
                    continue

                if (not clear_grid_pool) and safe_name in expected_root_children:
                    # Keep alive — e.g. a node mid-exit-animation.
                    continue

                self._drop_grid_pool_states_under_path(child_path)
                self._drop_grid_slot_visible_states_under_path(child_path)
                self._drop_native_common_style_cache(child_path)
                self._drop_native_layout_cache(child_path)
                try:
                    self._drop_button_binding_cache(child_path)
                except Exception:
                    pass
                remove_start_time = _perf_now()
                self._screen.RemoveChildControl(child_control)
                self._count_native_api_call('RemoveChildControl', elapsed_ms=(_perf_now() - remove_start_time) * 1000.0)
                self._record_render_detail_count('clear_root_removed_count', 1)
                self._drop_cached_control(child_path)
            except Exception:
                pass

        for child_path in list(preserved_root_scroll_hosts.keys()):
            if child_path not in existing_root_paths:
                try:
                    del preserved_root_scroll_hosts[child_path]
                except Exception:
                    pass

    def _apply_scroll_props(self, node, node_path):
        props = getattr(node, "props", {}) or {}
        show_scrollbar = props.get("showScrollbar", True)

        track_path = self._get_scrollbar_track_path(node_path)
        if track_path:
            self._safe_set_visible(track_path, show_scrollbar, sync_refresh=False)

    def _get_real_scroll_view_path(self, scroll_node_path):
        if not scroll_node_path:
            return ""

        scroll_cache = getattr(self, '_render_scroll_content_path_cache', None)
        cache_key = 'real|' + self._safe_text(scroll_node_path)
        if isinstance(scroll_cache, dict) and cache_key in scroll_cache:
            return scroll_cache.get(cache_key) or ""

        touch_path = scroll_node_path + "/scroll_touch/scroll_view"
        try:
            touch_children = self._screen.GetChildrenName(touch_path) or []
        except Exception:
            touch_children = []
        if touch_children:
            if isinstance(scroll_cache, dict):
                scroll_cache[cache_key] = touch_path
            return touch_path

        mouse_path = scroll_node_path + "/scroll_mouse/scroll_view"
        try:
            mouse_children = self._screen.GetChildrenName(mouse_path) or []
        except Exception:
            mouse_children = []
        if mouse_children:
            if isinstance(scroll_cache, dict):
                scroll_cache[cache_key] = mouse_path
            return mouse_path

        return ""

    def _get_scroll_content_path(self, scroll_node_path):
        scroll_cache = getattr(self, '_render_scroll_content_path_cache', None)
        cache_key = 'content|' + self._safe_text(scroll_node_path)
        if isinstance(scroll_cache, dict) and cache_key in scroll_cache:
            return scroll_cache.get(cache_key) or scroll_node_path
        real_scroll_view_path = self._get_real_scroll_view_path(scroll_node_path)
        if "/scroll_touch/" in real_scroll_view_path:
            content_path = real_scroll_view_path + "/panel/background_and_viewport/scrolling_view_port/scrolling_content"
            if isinstance(scroll_cache, dict):
                scroll_cache[cache_key] = content_path
            return content_path
        if "/scroll_mouse/" in real_scroll_view_path:
            content_path = real_scroll_view_path + "/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content"
            if isinstance(scroll_cache, dict):
                scroll_cache[cache_key] = content_path
            return content_path

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
