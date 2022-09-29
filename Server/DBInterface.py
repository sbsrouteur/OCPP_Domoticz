
from operator import truediv
import mariadb

from secret import *

class DBConnector:
  def __init__(self) -> None:
    self.db=mariadb.connect(
        host = MYSQL_HOST,
        port = MYSQL_PORT,
        user = MYSQL_USER,
        password = MYSQL_PASSWORD,
        database = MYSQL_SCHEMA) 

  def Log( self,Type:str, Msg:str,Src:str='None',SrcIP:str=None):

    sql="insert into Log (Type,Src,LogMsg,SRC_IP) values (?,?,?,?)"
    self.RunSQLStatement (sql,[Type,Src,Msg,SrcIP])

  def CheckClientID(self, ID:str)->bool:
    sql="select count(*) NbCP from OCPP_CLIENT where OCPP_ID=?"
    res= self.RunSQLSelect(sql,[ID])
    if len(res) == 1:
      (NbCP) = res[0][0]
      return NbCP==1
    else:
      return False

  def RunSQLSelect(self,sql:str, params)->dict:
    cur=self.db.cursor()
    cur.execute(sql,params)
    res=cur.fetchall()
    return res

  def RunSQLStatement(self,sql:str, params,AutoCommit:bool=True)->None:
    cur=self.db.cursor()
    cur.execute(sql,params)
    if (AutoCommit):
      self.db.commit()


    