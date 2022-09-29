
class DBLogger:
  def __init__(self,DB) -> None:
    self.db = DB

  def Log(self,level,msg):
    print (level + '|' + msg)
    self.db.Log(level,msg)
    return

  def LogError(self,msg):
    self.Log("Error",msg)
    return

  def LogInfo(self,msg):
    self.Log("Info",msg)
    return

  def LogWarning(self,msg):
    self.Log("Warning",msg)
    return