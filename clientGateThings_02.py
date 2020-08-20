import time
from dBusBluezConnection_02 import dBusBluezConnection

from pprint import PrettyPrinter

prettyPrint = PrettyPrinter(indent=1).pprint

myBluezConnection = dBusBluezConnection()

while not myBluezConnection.ServicesResolved: time.sleep(0.5)

prettyPrint(myBluezConnection.registeredDevices)

for key in myBluezConnection.registeredDevices:
  firstPath = key
  break


myBluezConnection.connectToDevice(firstPath)

time.sleep(40)

prettyPrint(myBluezConnection.registeredDevices)

myBluezConnection.disconnectDevice(firstPath)

myBluezConnection.exitThreadMainLoopGobject()