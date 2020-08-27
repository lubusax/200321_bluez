import time
from dBusBluezConnection import dBusBluezConnection

from pprint import PrettyPrinter

prettyPrint = PrettyPrinter(indent=1).pprint

myBluezConnection = dBusBluezConnection()

prettyPrint(myBluezConnection.pathsOfRegisteredDevices)

print("status connected beginning: ")
print(myBluezConnection.isDeviceConnected(myBluezConnection.pathsOfRegisteredDevices[0]["path"]))


myBluezConnection.connectToDevice(myBluezConnection.pathsOfRegisteredDevices[0]["path"])

time.sleep(40)

print("status connected after attempting connection: ")
print(myBluezConnection.isDeviceConnected(myBluezConnection.pathsOfRegisteredDevices[0]["path"]))

myBluezConnection.disconnectDevice(myBluezConnection.pathsOfRegisteredDevices[0]["path"])

#time.sleep(6)

print("status connected after attempting disconnection: ")
print(myBluezConnection.isDeviceConnected(myBluezConnection.pathsOfRegisteredDevices[0]["path"]))

myBluezConnection.exitThreadMainLoopGobject()