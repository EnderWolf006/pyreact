# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi

from examples.BedwarStoreApp import BedwarStoreApp
from examples.FriendApp import FriendApp

from pyreact import *

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()


class PyreactExampleScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.app_id = None

    def Create(self):
        print('=====> PyreactExampleUi Created <=====')
        self.app_id = 'pyreact_example_counter'
        self._mount_pyreact_app()

    def _mount_pyreact_app(self):
        bind = {
            'screen': self,
            'root': '/root',
            'app_id': self.app_id,
            'base_namespace': 'PyreactBase',
        }
        # 可以在此切换挂载展示不同的app示例
        # render_app(root=FriendApp, bind=bind)
        render_app(root=BedwarStoreApp, bind=bind)

    def Destroy(self):
        runtime_system = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime_system is not None:
            runtime_system.UnmountApp({'app_id': self.app_id})
        print('=====> PyreactExampleUi Destroyed <=====')


