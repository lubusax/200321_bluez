import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject
from thingsSpecificClasses import Thing
import time
import threading

from pprint import PrettyPrinter

prettyPrint = PrettyPrinter(indent=1).pprint

BLUEZ 															= 'org.bluez'
IFACE_OBJECT_MANAGER_DBUS						= 'org.freedesktop.DBus.ObjectManager'
IFACE_PROPERTIES_DBUS								= "org.freedesktop.DBus.Properties"
IFACE_LE_ADVERTISING_MANAGER 				= 'org.bluez.LEAdvertisingManager1'
IFACE_GATT_MANAGER 									= 'org.bluez.GattManager1'
IFACE_GATT_CHARACTERISTIC 					= 'org.bluez.GattCharacteristic1'
IFACE_GATT_SERVICE                  = 'org.bluez.GattService1'
IFACE_ADAPTER 											= 'org.bluez.Adapter1'
IFACE_DEVICE                        = 'org.bluez.Device1'

PATH_HCI0 													= '/org/bluez/hci0'

UUID_GATESETUP_SERVICE      				= '5468696e-6773-496e-546f-756368000100'
ALIAS_BEGINS_WITH										= 'ThingsInTouch'
# ThingsInTouch Services        go from 0x001000 to 0x001FFF
# ThingsInTouch Characteristics go from 0x100000 to 0x1FFFFF

UUID_READ_WRITE_TEST_CHARACTERISTIC = '5468696e-6773-496e-546f-756368100000'
UUID_NOTIFY_TEST_CHARACTERISTIC     = '5468696e-6773-496e-546f-756368100001'

DEVICE_NAME 												= 'ThingsInTouch-Gate-01'

class dBusBluezConnection():
  def __init__(self):
    DBusGMainLoop(set_as_default=True)

    self.systemBus 	= dbus.SystemBus()

    self.hci0 	= self.systemBus.get_object(BLUEZ, PATH_HCI0)
    self.bluez = self.systemBus.get_object(BLUEZ , "/")
    self.adapterInterface = dbus.Interface( self.hci0,   IFACE_ADAPTER)
    self.objectManagerInterface = dbus.Interface(self.bluez, IFACE_OBJECT_MANAGER_DBUS)
    self.updatePathsOfRegisteredDevices()
    self.listenToPropertiesChanged()

    self.exitFlag = threading.Event()
    self.exitFlag.clear()
    self.threadMainLoop = threading.Thread(target=self.enterThreadMainLoopGObject, args=(self.exitFlag,))
    self.threadMainLoop.start()


  def enterThreadMainLoopGObject(self, exitFlag):
    self.mainloop = GObject.MainLoop()
    self.mainloop.run()

  def exitThreadMainLoopGobject(self):
    self.mainloop.quit()
    self.threadMainLoop.join()

  
  # def getManagedObjects(self):
  #   return  self.objectManagerInterface.GetManagedObjects()

  def updatePathsOfRegisteredDevices(self):
    self.objects = self.objectManagerInterface.GetManagedObjects()
    self.pathsOfRegisteredDevices = []
    for path in self.objects:
      if "org.bluez.Device1" in self.objects[path]:
        self.pathsOfRegisteredDevices.append({"path":str(path), "connected":self.isDeviceConnected(path)})
    return self.pathsOfRegisteredDevices
  
  def isDeviceConnected(self, path):
    return bool(self.objects[path][IFACE_DEVICE]["Connected"])

  def connectToDevice(self,path):
    deviceObject = self.systemBus.get_object( BLUEZ, path)
    deviceInterface = dbus.Interface( deviceObject, IFACE_DEVICE)
    deviceInterface.Connect(path, dbus_interface=IFACE_DEVICE)
    # if not deviceInterface.Connected:
    #   time.sleep(1)
    #   print('waiting...')
    # print("connected -+ "*10)
    print(self.isDeviceConnected(path))
  
  def disconnectDevice(self, path):
    deviceObject = self.systemBus.get_object( BLUEZ, path)
    deviceInterface = dbus.Interface( deviceObject, IFACE_DEVICE)
    deviceInterface.Disconnect(path, dbus_interface=IFACE_DEVICE)

  def propertiesChanged(self, interface, changed, invalidated, path):
    deviceChanged = self.objects[path][IFACE_DEVICE]
    print("+#-- "*20)
    print("properties changed -            Alias: ", deviceChanged["Alias"])
    print("properties changed - device connected: ", bool(deviceChanged["Connected"]))
    prettyPrint(changed)

  def listenToPropertiesChanged(self):
    self.systemBus.add_signal_receiver(self.propertiesChanged, dbus_interface = IFACE_PROPERTIES_DBUS, signal_name = "PropertiesChanged", arg0 = IFACE_DEVICE, path_keyword = "path")

  def aliasFromThingsInTouch(self, alias):
    if alias[:13] == ALIAS_BEGINS_WITH:
      return True
    else:
      return False