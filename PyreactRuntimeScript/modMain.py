# -*- coding: utf-8 -*-

from mod.common.mod import Mod
import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi

@Mod.Binding(name="PyreactRuntimeMod", version="1.0.0")
class PyreactRuntimeClient(object):
    @Mod.InitClient()
    def PyreactRuntimeClientInit(self):
        clientApi.RegisterSystem("PyreactRuntimeMod", "PyreactRuntimeClientSystem", "PyreactRuntimeScript.PyreactRuntimeClientSystem.PyreactRuntimeClientSystem")
        print('=====> PyreactRuntime Init <=====')
        
    @Mod.DestroyClient()
    def PyreactRuntimeClientDestroy(self):
        print('=====> PyreactRuntime Destroy <=====')
        
    @Mod.InitServer()
    def PyreactRuntimeServerInit(self):
        serverApi.RegisterSystem('PyreactRuntimeMod', 'PyreactRuntimeServerSystem', 'PyreactRuntimeScript.PyreactRuntimeServerSystem.PyreactRuntimeServerSystem')
        print('=====> PyreactRuntime(Server Side) Init <=====')

    @Mod.DestroyServer()
    def PyreactRuntimeServerDestroy(self):
        print('=====> PyreactRuntime(Server Side) Destroy <=====')
