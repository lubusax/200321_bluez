# connectDeviceWithoutDiscovery needs flag --experimental on the bluetooth service (daemon bluetoothd)
# https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation#enable-bluetooth-low-energy-features
# https://pythonhosted.org/txdbus/dbus_overview.html

import time
from dBusBluezConnection_04 import dBusBluezConnection
from pprint import PrettyPrinter

def printVersionPython():
  import sys
  print("Python version")
  print (sys.version)
  print("Version info.")
  print (sys.version_info)

printVersionPython()

prettyPrint = PrettyPrinter(indent=1).pprint

myBluezConnection = dBusBluezConnection()

myBluezConnection.connectDeviceWithoutDiscovery("B8:27:EB:4D:68:70")


#myBluezConnection.discoverThingsInTouchDevices()

#while not myBluezConnection.flagToExit: time.sleep(0.5)

time.sleep(6)

print("client Gate Things exit")

myBluezConnection.exitThreadMainLoopGobject()