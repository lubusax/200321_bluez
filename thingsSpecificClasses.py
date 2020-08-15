import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject
import time

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

class Thing():
  def __init__(self,thingPath, thingInterfaces):
    self.thingInterfaces = thingInterfaces
    self.thingPath = thingPath
    self.services = {}
    self.characteristics = {}

    self.thingsInTouchUUIDbeginning = UUID_GATESETUP_SERVICE[:30]
    self.bus = dbus.SystemBus()
    self.objectManager = dbus.Interface(self.bus.get_object(BLUEZ, '/'), IFACE_OBJECT_MANAGER_DBUS)
    self.getServices()

  def getServices(self):
    objects = self.objectManager.GetManagedObjects()
    chrcs = []
    
    # List characteristics found
    for path, interfaces in objects.items():
      if IFACE_GATT_CHARACTERISTIC in interfaces.keys(): chrcs.append(path)

    # List services found
    for path, interfaces in objects.items():
      if IFACE_GATT_SERVICE not in interfaces.keys():
        continue

      chrc_paths = [[str(d), self.process_chrc(d)] for d in chrcs if d.startswith(path + "/")]
      for d in chrcs:
        if d.startswith(path+"/"):
          characteristicObject, characteristicProperties = self.process_chrc(d)
          characteristicUUID = str(characteristicProperties['UUID'])
          self.characteristics[characteristicUUID]= [characteristicObject, characteristicProperties]
      service = self.bus.get_object(BLUEZ , path)
      service_props = service.GetAll(IFACE_GATT_SERVICE, dbus_interface=IFACE_PROPERTIES_DBUS)
      uuid = str(service_props['UUID'])
      serviceDict={"path": str(path), "characteristics": chrc_paths}
      self.services[uuid]= serviceDict
      print("\n")

    print("#----"*25)

  def process_chrc(self, chrc_path):
      characteristicObject = self.bus.get_object(BLUEZ, chrc_path)
      characteristicProperties = characteristicObject.GetAll(IFACE_GATT_CHARACTERISTIC, dbus_interface=IFACE_PROPERTIES_DBUS)
      return (characteristicObject, characteristicProperties)
  
  def startNotify(self, characteristicUUID):
    if characteristicUUID in self.characteristics:
      characteristicPropertiesInterface = dbus.Interface(self.characteristics[characteristicUUID][0], IFACE_PROPERTIES_DBUS)
      characteristicPropertiesInterface.connect_to_signal("PropertiesChanged", self.characteristicChangedCallback)
      self.characteristics[characteristicUUID][0].StartNotify(reply_handler=self.startNotifyCallback, error_handler=self.genericErrorCallback, dbus_interface=IFACE_GATT_CHARACTERISTIC)
    else:
      print("this UUID is not in the characteristics dict: ", self.characteristics)
  
  def readValue(self, characteristicUUID):
    if characteristicUUID in self.characteristics:
      self.characteristics[characteristicUUID][0].ReadValue({}, reply_handler=self.showReadValue, error_handler=self.genericErrorCallback, dbus_interface=IFACE_GATT_CHARACTERISTIC)
    else:
      print("this UUID is not in the characteristics dict: ", self.characteristics)

  def startNotifyCallback(self):
    print('notifications enabled')

  def genericErrorCallback(self, error):
    print('D-Bus call failed: ' + str(error))

  def characteristicChangedCallback(self, iface, changed_props, invalidated_props):
    value = changed_props.get('Value', None)
    if value: print("new value: ", int.from_bytes(value, byteorder='big', signed=True))
      # valueString =""
      # for i in range(0,len(value)):
      #   valueString+= str(value[i])
      # print("new value: ", valueString)      
  
  def showReadValue(self, value):
    valueString =""
    valueToRead = value[0]
    for i in range(0,len(valueToRead)):
      valueString+= str(valueToRead[i])
    print("read Value: ", valueString)
