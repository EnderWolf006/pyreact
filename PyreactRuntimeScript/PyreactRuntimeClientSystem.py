# -*- coding: utf-8 -*-

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
        
        

