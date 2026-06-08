# -*- coding: utf-8 -*-

import json
import mod.client.extraClientApi as clientApi
from PyreactRuntimeScript.PyreactNativeRuntime import PyreactNativeRuntime

ClientSystem = clientApi.GetClientSystemCls()


class PyreactRuntimeClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.mPlayerId = clientApi.GetLocalPlayerId()
        self.mLevelId = clientApi.GetLevelId()
        self._apps = {}
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self, self.UiInitFinished)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'ScreenSizeChangedClientEvent', self, self.ScreenSizeChangedClientEvent)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'GameRenderTickEvent', self, self.GameRenderTickEvent)

    def UiInitFinished(self, args):
       print('=====> PyreactRuntime UiInitFinished <=====')

    def ScreenSizeChangedClientEvent(self, args):
        args = args or {}
        before_x = args.get('beforeX')
        before_y = args.get('beforeY')
        after_x = args.get('afterX')
        after_y = args.get('afterY')

        has_size_args = before_x is not None and before_y is not None and after_x is not None and after_y is not None
        if has_size_args and before_x == after_x and before_y == after_y:
            return

        app_ids = list(self._apps.keys())
        if not app_ids:
            return

        for app_id in app_ids:
            runtime = self._apps.get(app_id)
            if runtime is None:
                continue
            try:
                if hasattr(runtime, 'request_layout_render'):
                    runtime.request_layout_render()
                else:
                    runtime.render()
            except Exception as e:
                print('=====> PyreactRuntime resize rerender failed: %s, %s <=====' % (app_id, e))

    def _poll_debug_clipboard(self):
        """Check clipboard for a debug trigger JSON and dispatch it. Only active when debug_mode=True."""
        if not any(getattr(r, '_debug_mode', False) for r in self._apps.values()):
            return
        try:
            comp = clientApi.GetEngineCompFactory().CreateGame(self.mLevelId)
            content = comp.GetClipboardContent()
            if not content or '"pyreact_debug"' not in content:
                return
            trigger = json.loads(content)
            cmd = trigger.get('pyreact_debug')
            if not cmd:
                return
            # Clear immediately to avoid re-triggering; use a sentinel so SetClipboardContent('') empty-string no-op is bypassed
            comp.SetClipboardContent('__pyreact_ack__')
            params = trigger.get('params') or {}
            if cmd == 'dump_tree':
                self.DebugDumpUiTree(params)
            elif cmd == 'dump_subtree':
                self.DebugDumpSubtree(params)
            elif cmd == 'dump_node':
                self.DebugDumpNodeProps(params)
            elif cmd == 'click':
                self.DebugClickButton(params)
            elif cmd == 'set_input':
                self.DebugSetInput(params)
        except Exception as e:
            print('=====> PyreactRuntime _poll_debug_clipboard failed: %s <=====' % e)

    def GameRenderTickEvent(self, args):
        self._poll_debug_clipboard()
        app_ids = list(self._apps.keys())
        if not app_ids:
            return
        changed = False
        for app_id in app_ids:
            runtime = self._apps.get(app_id)
            if runtime is None:
                continue
            try:
                if hasattr(runtime, 'tick_active_touches') and runtime.tick_active_touches():
                    changed = True
            except Exception:
                pass
            try:
                if hasattr(runtime, 'tick_animations') and runtime.tick_animations():
                    changed = True
            except Exception:
                pass
        if changed:
            try:
                for app_id in app_ids:
                    runtime = self._apps.get(app_id)
                    if runtime is not None:
                        runtime._update_screen()
                        break
            except Exception:
                pass

    def MountApp(self, params):
        params = params or {}
        app_id = params.get('app_id') or params.get('appId')
        screen = params.get('screen')
        root_path = params.get('root_path') or params.get('root') or '/root'
        app_fn = params.get('app_fn') or params.get('appFn')
        base_namespace = params.get('base_namespace') or params.get('baseNamespace') or 'PyreactBase'
        log_perf = bool(params.get('log_perf'))
        debug_mode = bool(params.get('debug_mode'))

        if not app_id or screen is None or not callable(app_fn):
            print('=====> PyreactRuntime MountApp failed: invalid params <=====')
            return False

        self.UnmountApp({'app_id': app_id})

        runtime = PyreactNativeRuntime(app_id, screen, root_path, app_fn, base_namespace, log_perf=log_perf, debug_mode=debug_mode)
        runtime.mount()
        self._apps[app_id] = runtime
        print('=====> PyreactRuntime MountApp success: %s <=====' % app_id)
        return True

    def UnmountApp(self, params):
        params = params or {}
        app_id = params.get('app_id') or params.get('appId')
        runtime = self._apps.pop(app_id, None)
        if runtime is not None:
            runtime.unmount()
            print('=====> PyreactRuntime UnmountApp: %s <=====' % app_id)
            return True
        return False

    def RerenderApp(self, params):
        params = params or {}
        app_id = params.get('app_id') or params.get('appId')
        runtime = self._apps.get(app_id)
        if runtime is None:
            return False
        runtime.request_render()
        return True
        
    def DebugDumpUiTree(self, params):
        """Write full UI tree JSON to clipboard. Called by external debug tools via studio command."""
        params = params or {}
        app_id = params.get('app_id')
        runtime = self._apps.get(app_id) if app_id else (list(self._apps.values())[0] if self._apps else None)
        if runtime is None:
            return False
        try:
            data = runtime.debug_get_ui_tree()
            content = json.dumps(data, ensure_ascii=True)
            comp = clientApi.GetEngineCompFactory().CreateGame(self.mLevelId)
            return comp.SetClipboardContent(content)
        except Exception as e:
            print('=====> PyreactRuntime DebugDumpUiTree failed: %s <=====' % e)
            return False

    def DebugDumpSubtree(self, params):
        """Write subtree JSON for a given node_id to clipboard."""
        params = params or {}
        app_id = params.get('app_id')
        node_id = params.get('node_id', '')
        runtime = self._apps.get(app_id) if app_id else (list(self._apps.values())[0] if self._apps else None)
        if runtime is None or not node_id:
            return False
        try:
            data = runtime.debug_get_subtree(node_id)
            content = json.dumps(data, ensure_ascii=True)
            comp = clientApi.GetEngineCompFactory().CreateGame(self.mLevelId)
            return comp.SetClipboardContent(content)
        except Exception as e:
            print('=====> PyreactRuntime DebugDumpSubtree failed: %s <=====' % e)
            return False

    def DebugDumpNodeProps(self, params):
        """Write single node props JSON for a given node_id to clipboard."""
        params = params or {}
        app_id = params.get('app_id')
        node_id = params.get('node_id', '')
        runtime = self._apps.get(app_id) if app_id else (list(self._apps.values())[0] if self._apps else None)
        if runtime is None or not node_id:
            return False
        try:
            data = runtime.debug_get_node_props(node_id)
            content = json.dumps(data, ensure_ascii=True)
            comp = clientApi.GetEngineCompFactory().CreateGame(self.mLevelId)
            return comp.SetClipboardContent(content)
        except Exception as e:
            print('=====> PyreactRuntime DebugDumpNodeProps failed: %s <=====' % e)
            return False

    def DebugClickButton(self, params):
        """Simulate a button click by node_id."""
        params = params or {}
        app_id = params.get('app_id')
        node_id = params.get('node_id', '')
        runtime = self._apps.get(app_id) if app_id else (list(self._apps.values())[0] if self._apps else None)
        if runtime is None or not node_id:
            return False
        try:
            runtime._dispatch_click(node_id)
            return True
        except Exception as e:
            print('=====> PyreactRuntime DebugClickButton failed: %s <=====' % e)
            return False

    def DebugSetInput(self, params):
        """Set input text by node_id, then fire onChange diff."""
        params = params or {}
        app_id = params.get('app_id')
        node_id = params.get('node_id', '')
        text = params.get('text', '')
        runtime = self._apps.get(app_id) if app_id else (list(self._apps.values())[0] if self._apps else None)
        if runtime is None or not node_id:
            return False
        try:
            node_path = (getattr(runtime, '_input_paths', None) or {}).get(node_id)
            if not node_path:
                print('=====> PyreactRuntime DebugSetInput: node_id not found: %s <=====' % node_id)
                return False
            runtime._safe_set_edit_text(node_path, text)
            runtime._input_last_values[node_id] = None  # force diff
            runtime._on_any_input_edit_event()
            return True
        except Exception as e:
            print('=====> PyreactRuntime DebugSetInput failed: %s <=====' % e)
            return False

    def Destroy(self):
        app_ids = list(self._apps.keys())
        for app_id in app_ids:
            self.UnmountApp({'app_id': app_id})
        
        

