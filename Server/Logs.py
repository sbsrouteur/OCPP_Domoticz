

def Log(level,msg):
  print (level + '|' + msg)
  return

def LogError(msg):
  Log("Error",msg)
  return

def LogInfo(msg):
  Log("Info",msg)
  return

def LogWarning(msg):
  Log("Warning",msg)
  return