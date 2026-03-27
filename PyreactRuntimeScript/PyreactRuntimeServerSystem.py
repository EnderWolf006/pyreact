# -*- coding: utf-8 -*-

import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()


class PyreactRuntimeServerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.mlevelId = serverApi.GetLevelId()
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'OnScriptTickServer', self, self.OnScriptTickServer)

    def OnScriptTickServer(self):
        pass

    def Destroy(self):
        pass
