import time
from dBusBluezConnection_03 import dBusBluezConnection

from pprint import PrettyPrinter

prettyPrint = PrettyPrinter(indent=1).pprint

myBluezConnection = dBusBluezConnection()

myBluezConnection.discoverThingsInTouchDevices()

while not myBluezConnection.flagToExit: time.sleep(0.5)

myBluezConnection.exitThreadMainLoopGobject()