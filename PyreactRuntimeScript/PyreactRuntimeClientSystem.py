# -*- coding: utf-8 -*-

import time

import mod.client.extraClientApi as clientApi
from PyreactRuntimeScript.PyreactNativeRuntime import PyreactNativeRuntime

ClientSystem = clientApi.GetClientSystemCls()


class PyreactRuntimeClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.mPlayerId = clientApi.GetLocalPlayerId()
        self.mLevelId = clientApi.GetLevelId()
        self._apps = {}
        self._tick_event_registered = False
        self._tick_count = 0
        self._tick_first_logged = False
        self._tick_last_log_time = 0.0
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self, self.UiInitFinished)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'ScreenSizeChangedClientEvent', self, self.ScreenSizeChangedClientEvent)
        try:
            self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'GameRenderTickEvent', self, self.GameRenderTickEvent)
            self._tick_event_registered = True
            print('[PyreactAnim] GameRenderTickEvent 监听注册成功')
        except Exception as err:
            print('[PyreactAnim] GameRenderTickEvent 监听注册失败: %s' % err)

    def UiInitFinished(self, args):
       print('=====> PyreactRuntime UiInitFinished <=====')

    def ScreenSizeChangedClientEvent(self, args):
        args = args or {}
        before_x = args.get('beforeX')
        before_y = args.get('beforeY')
        after_x = args.get('afterX')
        after_y = args.get('afterY')

        # Only rerender when width/height actually changed.
        if before_x == after_x and before_y == after_y:
            return

        app_ids = list(self._apps.keys())
        if not app_ids:
            return

        for app_id in app_ids:
            runtime = self._apps.get(app_id)
            if runtime is None:
                continue
            try:
                runtime.request_render()
            except Exception as e:
                print('=====> PyreactRuntime resize rerender failed: %s, %s <=====' % (app_id, e))

    def GameRenderTickEvent(self, args):
        self._tick_count += 1
        if not self._tick_first_logged:
            self._tick_first_logged = True
            print('[PyreactAnim] GameRenderTickEvent 首次触发 (apps=%d)' % len(self._apps))
        # 每 2 秒汇报一次频率（只在有 app 的前提下，避免空刷屏）
        if self._apps:
            now = time.time()
            if now - self._tick_last_log_time >= 2.0:
                print('[PyreactAnim] GameRenderTickEvent 最近2秒触发 %d 次 (累计 %d)' % (
                    self._tick_count, self._tick_count,
                ))
                self._tick_last_log_time = now

        if not self._apps:
            return
        for app_id in list(self._apps.keys()):
            runtime = self._apps.get(app_id)
            if runtime is None:
                continue
            try:
                runtime.tick_animations()
            except Exception as err:
                print('[PyreactAnim] tick_animations 异常 app=%s: %s' % (app_id, err))

    def MountApp(self, params):
        params = params or {}
        app_id = params.get('app_id') or params.get('appId')
        screen = params.get('screen')
        root_path = params.get('root_path') or params.get('root') or '/root'
        app_fn = params.get('app_fn') or params.get('appFn')
        base_namespace = params.get('base_namespace') or params.get('baseNamespace') or 'PyreactBase'
        log_perf = bool(params.get('log_perf'))

        if not app_id or screen is None or not callable(app_fn):
            print('=====> PyreactRuntime MountApp failed: invalid params <=====')
            return False

        self.UnmountApp({'app_id': app_id})

        runtime = PyreactNativeRuntime(app_id, screen, root_path, app_fn, base_namespace, log_perf=log_perf)
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

    def Destroy(self):
        app_ids = list(self._apps.keys())
        for app_id in app_ids:
            self.UnmountApp({'app_id': app_id})
