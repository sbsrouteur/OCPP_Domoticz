import asyncio
 
import websockets

import  Logs
import OCPP_ClientManager
from DBInterface import DBConnector
from Logs import DBLogger 
# create handler for each connection

class Server:

    def __init__(self) -> None:
        self.db = DBConnector()
        self.Logs = DBLogger(self.db)
        self.Logs.LogInfo('OCCP Server starting...')


        pass 
    cp = None
    async def handler(self,websocket, path):
        try:
            requested_protocols = websocket.request_headers[
                'Sec-WebSocket-Protocol']
        except KeyError:
            self.Logs.LogError("Client hasn't requested any Subprotocol. "
                    "Closing Connection")
        if websocket.subprotocol:
            self.Logs.LogInfo(f"Websocket connection successfull Protocols Matched: {websocket.subprotocol}" )
            self.Logs.LogInfo(f"Websocket connection successfull Protocols Matched: {websocket.remote_address}" )
        else:
            # In the websockets lib if no subprotocols are supported by the
            # client and the server, it proceeds without a subprotocol,
            # so we have to manually close the connection.
            self.Logs.LogWarning(f'Protocols Mismatched | Expected Subprotocols: {websocket.available_subprotocols}, but client supports  {requested_protocols} | Closing connection ')
            return await websocket.close()
            pass 
        
        charge_point_id = path.strip('/')
        cp = OCPP_ClientManager.OCPP_ClientManager(charge_point_id,websocket,self.db,self.Logs)
        await cp.RunManager()

    def Run(self):
        start_server = websockets.serve(self.handler, None, 8000,subprotocols=['ocpp1.6','ocpp_server'])
        
        asyncio.get_event_loop().run_until_complete(start_server)
        
        asyncio.get_event_loop().run_forever()
    
S = Server()
S.Run()
