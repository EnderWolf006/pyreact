# -*- coding: utf-8 -*-

from mod.common.mod import Mod
import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi

@Mod.Binding(name="PyreactExampleMod", version="1.0.0")
class PyreactExampleClient(object):
    @Mod.InitClient()
    def PyreactExampleClientInit(self):
        clientApi.RegisterSystem("PyreactExampleMod", "PyreactExampleClientSystem", "PyreactExampleScript.PyreactExampleClientSystem.PyreactExampleClientSystem")
        print('=====> PyreactExample Init <=====')
        
    @Mod.DestroyClient()
    def PyreactExampleClientDestroy(self):
        print('=====> PyreactExample Destroy <=====')
        
    @Mod.InitServer()
    def PyreactExampleServerInit(self):
        serverApi.RegisterSystem('PyreactExampleMod', 'PyreactExampleServerSystem', 'PyreactExampleScript.PyreactExampleServerSystem.PyreactExampleServerSystem')
        print('=====> PyreactExample(Server Side) Init <=====')

    @Mod.DestroyServer()
    def PyreactExampleServerDestroy(self):
        print('=====> PyreactExample(Server Side) Destroy <=====')
