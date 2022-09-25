import asyncio
 
import websockets

import  Logs
import OCPP_ClientManager 
# create handler for each connection
 
cp = None
async def handler(websocket, path):
    try:
        requested_protocols = websocket.request_headers[
            'Sec-WebSocket-Protocol']
    except KeyError:
        Logs.LogError("Client hasn't requested any Subprotocol. "
                "Closing Connection")
    if websocket.subprotocol:
        Logs.LogInfo(f"Websocket connection successfull Protocols Matched: {websocket.subprotocol}" )
        Logs.LogInfo(f"Websocket connection successfull Protocols Matched: {websocket.remote_address}" )
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        Logs.LogWarning(f'Protocols Mismatched | Expected Subprotocols: {websocket.available_subprotocols}, but client supports  {requested_protocols} | Closing connection ')
        return await websocket.close()
        pass 
    charge_point_id = path.strip('/')
    cp = OCPP_ClientManager.OCPP_ClientManager(charge_point_id,websocket)
        
    await cp.RunManager()
   
 
 

start_server = websockets.serve(handler, None, 8000,subprotocols=['ocpp1.6','ocpp_server'])
 
 
 
asyncio.get_event_loop().run_until_complete(start_server)
 
asyncio.get_event_loop().run_forever()