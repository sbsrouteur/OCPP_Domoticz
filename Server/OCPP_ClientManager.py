import asyncio
import hashlib
from inspect import getmembers
from logging import exception
from operator import truediv
from xmlrpc.client import Boolean
import websockets
import json
import random
import uuid

from datetime import datetime

from Logs import DBLogger

class OCPP_ClientManager:

  
  def __init__(self,ID:str,ws:websockets, DB, Logs:DBLogger)  -> None:
    self.ID = ID
    self.ws = ws
    self.DB = DB
    self.Logs = Logs
    self.SupportedMessages_2 = {
    "Authorize": self.HandleAuthorize,
    "BootNotification": self.HandleBootNotification,
    "Heartbeat": self.HandleHeartBeat,
    "MeterValues": self.HandleMeterValues,
    "StatusNotification": self.HandleStatusNotification ,
    "StartTransaction": self.HandleStartTransaction ,
    "StopTransaction": self.HandleStopTransaction ,
    }

    self.IsConfigured = False
    self.LastRequestID = None

    if not self.DB.CheckClientID(ID):
      self.Logs.LogError(f"unknown client ID {ID}. Closing Connexion")
      self.ws.close()
      raise exception ("Invalid ID. Dying...")
    return

  async def CheckAndHandleWSMessage(self,DataStr)->Boolean:
    Data = json.loads(DataStr)
    if isinstance(Data,list):
      if len(Data) == 4 and Data[0]==2:
        if self.SupportedMessages_2.get(Data[2],None):
          status= await self.SupportedMessages_2[Data[2]](Data[1],Data[3])
          if status:
            return True
        else:
            self.Logs.LogError(f"Unsupported message type {Data[2]}") 
      elif len (Data)== 3 and Data[0] == 3:
        status= await self.HandleCode3Response(Data[1],Data[2])
        return True

      else:
        self.Logs.LogError(f"unexpected data length is not  : {len(Data)} or message type")
    else:
      self.Logs.LogError("Data is not a list")

    self.Logs.LogError(f"Invalid Data Structure {Data}")
    return 

  async def GetChargeAuth(self, TagID)->str:
    return "Blocked"

  def GetRequestID(self)->str:
    self.LastRequestID =  str(uuid.uuid4())
    return self.LastRequestID

  async def HandleAuthorize(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Authorize Msg UID {UID} received : {Msg}")

    h = hashlib.sha256((Msg["idTag"]+'9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08').encode()).hexdigest()

    if h=='174415da35b9489cf42bebf18e0222767a15f1de4a8dcbaf6fc91d9fe93f49dc' or h == '44edd6d784be7a1c9c768d442f2814c825d80ca88615a0b9d32ca872b04fac7a':
      Status="Accepted"
    else:
      self.Logs.LogError('Invalid ID hashed to '+h)
      Status='Invalid'

    #TODO Check ID
    Payload={
      "status":Status,      
    }
    reply=json.dumps([3,UID,Payload])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")

    self.RequestStartTransaction(Msg["idTag"])

    return True
  async def HandleBootNotification(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Boot Notification Msg UID {UID} received : {Msg}")
    BootMessage={
      "status":"Accepted",
      "currentTime": datetime.utcnow().replace(microsecond=0).isoformat()+'Z',
      "interval":60,
      
    }
    reply=json.dumps([3,UID,BootMessage])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")

    #getconf =json.dumps( [2,UID,"GetConfiguration",{}])
    #await self.ws.send(getconf)
    #self.Logs.LogInfo(f"Sent : {getconf}")

    return True

  async def HandleCode3Response(self,UID,Msg):
    if (UID != self.LastRequestID):
      self.Logs.LogError(f' Invalid reply ID got {UID} expected {self.LastRequestID}')
      await self.ws.close()
    self.Logs.LogInfo(f"Response to Msg UID {UID} received : {Msg}")
    self.LastRequestID = None
    self.IsConfigured = True
  
  async def HandleHeartBeat(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Heartbeat Msg UID {UID} received : {Msg}")
    Message={
      "currentTime": datetime.utcnow().replace(microsecond=0).isoformat()+'Z',      
    }
    reply=json.dumps([3,UID,Message])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")

    if self.IsConfigured:
      await self.RequestMeterValues()
      
    else:
      #'Init set all to operative'
      await self.RequestConfiguration()
      
    return True
  async def HandleMeterValues(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Meter Msg UID {UID} received : {Msg}")
    reply=json.dumps([3,UID,{}])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")
    
    return True

  async def HandleStatusNotification(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Status Notification Msg UID {UID} received : {Msg}")
    reply=json.dumps([3,UID,{}])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")
    
    return True

  async def HandleStartTransaction(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Start Transaction Msg UID {UID} received : {Msg}")
    tid=random.randint(1,100000)
    reply=json.dumps([3,UID,
          {
            "transactionId":tid,
            "idTagInfo" : {"status":self.GetChargeAuth(Msg.idTag)}
          }])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")
    
    return True

  async def HandleStopTransaction(self,UID,Msg)->bool:
    self.Logs.LogInfo(f"Stop Transaction Msg UID {UID} received : {Msg}")
    tid=random.randint(1,100000)
    reply=json.dumps([3,UID,
          {}])

    await self.ws.send(reply)
    self.Logs.LogInfo(f"replied : {reply}")
    
    return True

  async def RequestConfiguration(self):
    ID = self.GetRequestID()
    GetConfigurationRequest =json.dumps( [2,ID,"GetConfiguration",{"key":[]}])
    await self.ws.send(GetConfigurationRequest)
    self.Logs.LogInfo(f"Sent : {GetConfigurationRequest}")

  async def RequestLocalList(self):
    ID = self.GetRequestID()
    Payload =json.dumps( [2,ID,"TriggerMessage",{"requestedMessage":"SendLocalList"}])
    await self.ws.send(Payload)
    self.Logs.LogInfo(f"Sent : {Payload}")

  async def RequestMeterValues(self):
    ID = self.GetRequestID()
    Payload =json.dumps( [2,ID,"TriggerMessage",{"requestedMessage":"MeterValues"}])
    await self.ws.send(Payload)
    self.Logs.LogInfo(f"Sent : {Payload}")


  async def RequestStartTransaction(self,ID):
    ID = self.GetRequestID()
    Payload =json.dumps( [2,ID,"RemoteStartTransaction",{"idTag":ID}])
    await self.ws.send(Payload)
    self.Logs.LogInfo(f"Sent : {Payload}")
    

  async def SetAvailability(self, ConnectorID,Availability):
    ID = self.GetRequestID()
    Payload =json.dumps( [2,ID,"ChangeAvailability",{"connectorId":ConnectorID , "type":Availability}])
    await self.ws.send(Payload)
    self.Logs.LogInfo(f"Sent : {Payload}")

  async def RunManager(self)-> None:

    while True:
      data = await self.ws.recv()
      await self.CheckAndHandleWSMessage(data)

