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
ALIAS_THINGSINTOUCH_BEGINING				= 'ThingsInTouch'
# ThingsInTouch Services        go from 0x001000 to 0x001FFF
# ThingsInTouch Characteristics go from 0x100000 to 0x1FFFFF

UUID_READ_WRITE_TEST_CHARACTERISTIC = '5468696e-6773-496e-546f-756368100000'
UUID_NOTIFY_TEST_CHARACTERISTIC     = '5468696e-6773-496e-546f-756368100001'
UUID_BEGIN_THINGSINTOUCH            = '5468696e-6773-496e-546f-756368'

DEVICE_NAME 												= 'ThingsInTouch-Gate-01'

class dBusBluezConnection():
  def __init__(self):
    DBusGMainLoop(set_as_default=True)

    self.dictOfDevices ={}
    self.flagToExit = False

    self.systemBus 	= dbus.SystemBus()

    self.hci0 	= self.systemBus.get_object(BLUEZ, PATH_HCI0)
    self.bluez = self.systemBus.get_object(BLUEZ , "/")
    self.adapterInterface = dbus.Interface( self.hci0,   IFACE_ADAPTER)
    self.objectManagerInterface = dbus.Interface(self.bluez, IFACE_OBJECT_MANAGER_DBUS)

    self.updateRegisteredDevices()

    self.deleteRegisteredDevices()
    self.ServicesResolved = False

    self.listenToPropertiesChanged()
    self.listenToInterfacesAdded()

    self.exitFlag = threading.Event()
    self.exitFlag.clear()
    self.threadMainLoop = threading.Thread(target=self.enterThreadMainLoopGObject, args=(self.exitFlag,))
    self.threadMainLoop.start()

  def discoverThingsInTouchDevices(self):
    scan_filter = {}
    scan_filter["Transport"] 	= "le"
    scan_filter['UUIDs'] 			= [UUID_GATESETUP_SERVICE]
    self.adapterInterface.SetDiscoveryFilter(scan_filter)
    self.adapterInterface.StartDiscovery()

  def enterThreadMainLoopGObject(self, exitFlag):
    self.mainloop = GObject.MainLoop()
    self.mainloop.run()

  def exitThreadMainLoopGobject(self):
    self.mainloop.quit()
    self.threadMainLoop.join()

  def deleteRegisteredDevices(self):
    for devicePath in self.registeredDevices:
      self.deleteDevice(devicePath)

  def deleteDevice(self, devicePath):
    self.objects = self.objectManagerInterface.GetManagedObjects()
    for path in self.objects:
      if IFACE_ADAPTER in self.objects[path]:
        adapterObject =  self.systemBus.get_object(BLUEZ , path)
        adapterProperties = adapterObject.GetAll(IFACE_ADAPTER, dbus_interface=IFACE_PROPERTIES_DBUS)
        adapterAddress = adapterProperties["Address"]
        deviceAddress = self.registeredDevices[devicePath]["Address"]
        print("Device Address: ",deviceAddress)
        print("Adapter Address: ",adapterAddress)
        adapterInterface = dbus.Interface(adapterObject, IFACE_ADAPTER)
        adapterInterface.RemoveDevice(devicePath)
        print("Device removed - Address: ",deviceAddress)

    return True

  def updateRegisteredDevices(self):
    self.objects = self.objectManagerInterface.GetManagedObjects()
    self.registeredDevices = {}
    for path in self.objects:
      if IFACE_DEVICE in self.objects[path]:
        deviceObject = self.systemBus.get_object(BLUEZ , path)
        deviceProperties = deviceObject.GetAll(IFACE_DEVICE, dbus_interface=IFACE_PROPERTIES_DBUS)
        self.registeredDevices[str(path)]= {
          "Alias":            self.alias(path),
          "Address":          str(deviceProperties["Address"]),
          "Connected":        bool(deviceProperties["Connected"]),
          #"Adapter":          deviceProperties["Adapter"],
          "ServicesResolved": False,
          "Services":         None,
          "deviceInterface":  self.getDeviceInterface(path),
          "SerialNumber":     None}
    return self.registeredDevices
  
  def isDeviceConnected(self, path):
    return bool(self.objects[path][IFACE_DEVICE]["Connected"])
  
  def alias(self, path):
    return str(self.objects[path][IFACE_DEVICE]["Alias"])

  def isServiceOfThingsInTouch(self, uuid):
    if str(uuid).startswith(UUID_BEGIN_THINGSINTOUCH):
      return True
    else:
      return False
  
  def getDeviceInterface(self, path):
    deviceObject = self.systemBus.get_object( BLUEZ, path)
    return dbus.Interface( deviceObject, IFACE_DEVICE)


  def getServicesOfDevice(self, devicePath):
    servicesOfDevice = {}

    characteristicsOfDevice = self.getCharacteristicsOfDevice(devicePath)

    for path in self.objects:
      if str(path).startswith(str(devicePath)):
        if IFACE_GATT_SERVICE in self.objects[path]:
          serviceObject = self.systemBus.get_object(BLUEZ , path)
          serviceProperties = serviceObject.GetAll(IFACE_GATT_SERVICE, dbus_interface=IFACE_PROPERTIES_DBUS)
          uuid = serviceProperties['UUID']
          if self.isServiceOfThingsInTouch(uuid):
            characteristicsOfService = {}
            for c in characteristicsOfDevice:
              if c.startswith(str(path)):
                characteristicObject = self.systemBus.get_object(BLUEZ , c)
                characteristicProperties = characteristicObject.GetAll(IFACE_GATT_CHARACTERISTIC, dbus_interface=IFACE_PROPERTIES_DBUS)
                characteristicsOfService[str(c)]= {"UUID": str(characteristicProperties['UUID']),
                                                  "CharacteristicObject": characteristicObject}
            servicesOfDevice[str(uuid)]={"Path":str(path),"ServiceObject": serviceObject,
                                  "Characteristics":characteristicsOfService}

    print("\n")
    prettyPrint(servicesOfDevice)
    print("\n")

    return servicesOfDevice

  def connectToDevice(self,path):
    self.registeredDevices[str(path)]["deviceInterface"].Connect(path, dbus_interface=IFACE_DEVICE)

  def pairToDevice(self,path):
    self.registeredDevices[str(path)]["deviceInterface"].Pair(path, dbus_interface=IFACE_DEVICE)
  
  def disconnectDevice(self, path):
    self.registeredDevices[str(path)]["deviceInterface"].Disconnect(path, dbus_interface=IFACE_DEVICE)

  def propertiesChanged(self, interface, changed, invalidated, path):
    self.updateRegisteredDevices()
    devicePath = path
    for key in changed:
      if str(key) == "Connected":
        self.registeredDevices[str(devicePath)]["Connected"] = bool(changed[key])
        print("DEVOÌCE CONNECTED - time ellapsed in seconds since asking to connect: ", int(time.time() - self.counterTimeToConnect))
      if str(key) == "ServicesResolved":
        print("SERVICES RESOLVED - time ellapsed in seconds since asking to connect: ", int(time.time() - self.counterTimeToConnect))
        self.ServicesResolved = True
        servicesResolved =  bool(changed[key])
        self.registeredDevices[str(devicePath)]["ServicesResolved"] =  servicesResolved 
        self.registeredDevices[str(devicePath)]["Services"] = self.getServicesOfDevice(devicePath)
        if servicesResolved and self.ensureDeviceKnown(devicePath):
          self.establishBluetoothConnection(devicePath)
        else:
          print ("No Bluetooth Connection Established")
    print("+#-- "*20)
    #print("properties changed -            Alias: ", deviceChanged["Alias"])
    #print("properties changed - device connected: ", bool(deviceChanged["Connected"]))
    prettyPrint(changed)

  def establishBluetoothConnection(self,path):
    self.registeredDevices[str(path)]["SerialNumber"] = str(self.getSerialNumber(path))
    pass

  def getSerialNumber(self,path):
    return "007"


  def ensureDeviceKnown(self,path):
    # look into a list of known devices , checking the serial number
    # if it is not known, make it known .  Get approval from Odoo for a new device
    # and then make a new entry on the list of local known devices
    # if there is no approval from Odoo, this Method returns False
    return True

  def getCharacteristicsOfDevice(self, devicePath):
    self.objects = self.objectManagerInterface.GetManagedObjects()
    characteristics = []
    for path in self.objects:
      if str(path).startswith(str(devicePath)):
        if IFACE_GATT_CHARACTERISTIC in self.objects[path]:
          characteristics.append(str(path))

    print("\n")
    prettyPrint(characteristics)   
    print("\n")
    
    return characteristics

  def updateRegisteredServices(self,devicePath):
    self.updateCharacteristics()

  def listenToPropertiesChanged(self):
    self.systemBus.add_signal_receiver(self.propertiesChanged, dbus_interface = IFACE_PROPERTIES_DBUS,
                        signal_name = "PropertiesChanged", arg0 = IFACE_DEVICE, path_keyword = "path")

  def listenToInterfacesAdded(self):
    self.systemBus.add_signal_receiver(self.interfacesAdded, dbus_interface = IFACE_OBJECT_MANAGER_DBUS,
                        signal_name = "InterfacesAdded")

  def interfacesAdded(self, path, interfaces):
    try:
      if interfaces[IFACE_DEVICE]: self.launchThreadForNewDevice(path)
    except:
      print("An interface that was not a Device was added :) (interfacesAdded)")
      print("it happened on path: ", path, "+- # -+ "*15)
      prettyPrint(interfaces)
      print("-"*90)

  def launchThreadForNewDevice(self,devicePath):
    prettyPrint(self.updateRegisteredDevices())
    self.counterTimeToConnect = time.time()
    self.connectToDevice(devicePath)
    #self.flagToExit = True

  def aliasFromThingsInTouch(self, alias):
    if alias.startswith(ALIAS_THINGSINTOUCH_BEGINING):
      return True
    else:
      return False