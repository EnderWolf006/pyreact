# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()


class PyreactExampleClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.mPlayerId = clientApi.GetLocalPlayerId()
        self.mLevelId = clientApi.GetLevelId()
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self, self.UiInitFinished)

    def UiInitFinished(self, args):
        clientApi.RegisterUI('PyreactExampleMod', 'PyreactExample', "PyreactExampleScript.PyreactExampleUi.PyreactExampleScreen", "PyreactExample.main")
        # clientApi.CreateUI('PyreactExampleMod', 'PyreactExample', {"isHud": 1, 'data':{},'client':self})
        
        def f():
            clientApi.PushScreen('PyreactExampleMod', 'PyreactExample', {"isHud": 1, 'data':{},'client':self})

        f()
        # comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        # comp.AddTimer(2.0,f)
    def Destroy(self):
        pass
        
        

