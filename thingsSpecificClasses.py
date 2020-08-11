class Thing():
  def __init__(self,path, thingInterfaces):
    self.thingInterfaces = thingInterfaces
    self.path = path
    
    self.getListOfServices()
  
  def getListOfServices(self):
    self.services = []