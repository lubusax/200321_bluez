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
UUID_SERIAL_NUMBER_CHARACTERISTIC   = '5468696e-6773-496e-546f-756368100002'
UUID_DEVICE_TYPE_CHARACTERISTIC     = '5468696e-6773-496e-546f-756368100003'

UUID_BEGIN_THINGSINTOUCH            = '5468696e-6773-496e-546f-756368'

DEVICE_NAME 												= 'ThingsInTouch-Gate-01'

class dBusBluezConnection():
  def __init__(self):
    self.counterTimeToConnect = time.time()
    print("TIMESTAMP __init__ class dBusBluezConnection (ms): ", self.nowInMilliseconds())

    DBusGMainLoop(set_as_default=True)

    self.dictOfDevices ={}
    self.flagToExit = False
    #self.exitFlag = {}

    self.systemBus 	= dbus.SystemBus()

    self.hci0 	= self.systemBus.get_object(BLUEZ, PATH_HCI0)
    self.bluez = self.systemBus.get_object(BLUEZ , "/")
    self.adapterInterface = dbus.Interface( self.hci0,   IFACE_ADAPTER)
    self.objectManagerInterface = dbus.Interface(self.bluez, IFACE_OBJECT_MANAGER_DBUS)

    self.updateRegisteredDevices()

    self.deleteRegisteredDevices()
    self.ServicesResolved = {}

    self.listenToPropertiesChanged()
    self.listenToInterfacesAdded()

    self.exitFlag = threading.Event()
    self.exitFlag.clear()
    self.threadMainLoop = threading.Thread(target=self.enterThreadMainLoopGObject, args=(self.exitFlag,))
    self.threadMainLoop.start()

  def discoverThingsInTouchDevices(self):
    scanFilter = {}
    scanFilter["Transport"] 	= "le" 
    scanFilter['UUIDs'] 			= [UUID_GATESETUP_SERVICE]
    self.adapterInterface.SetDiscoveryFilter(scanFilter)
    self.adapterInterface.StartDiscovery()

  def nowInMilliseconds(self):
    t = time.time()
    return (int((t - int(t/100)*100) *1000))

  def connectDeviceWithoutDiscovery(self,Address, AddressType ="public"):
    connectFilter ={}
    connectFilter["Address"]= str(Address)
    connectFilter["AddressType"]= str(AddressType)
    #self.counterTimeToConnect = time.time()
    print("TIMESTAMP just before asking to connect w/o discovery (ms): ", self.nowInMilliseconds())
    try:
      deviceConnected = self.adapterInterface.ConnectDevice(connectFilter)
      print("TIMESTAMP just after asking to connect w/o discovery (ms): ", self.nowInMilliseconds())
      prettyPrint(deviceConnected)
    except:
      print("TIMESTAMP error (ms): ", self.nowInMilliseconds())
      print("some error while connectDeviceWithoutDiscovery")


  def enterThreadMainLoopGObject(self, exitFlag):
    self.mainloop = GObject.MainLoop()
    self.mainloop.run()

  def exitThreadMainLoopGobject(self):
    self.mainloop.quit()
    self.threadMainLoop.join()

  def deleteRegisteredDevices(self):
    for devicePath in self.registeredDevices:
      self.deleteDevice(devicePath)
    self.updateRegisteredDevices()

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
          #"Connected":        bool(deviceProperties["Connected"]),
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
                characteristicsOfService[str(characteristicProperties['UUID'])]= {
                              "Path":str(c),
                              "Value":characteristicProperties['Value'],
                              "CharacteristicObject": characteristicObject}
            servicesOfDevice[str(uuid)]={"Path":str(path),"ServiceObject": serviceObject,
                                  "Characteristics":characteristicsOfService}

    # print("\n")
    # prettyPrint(servicesOfDevice)
    # print("\n")

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
        self.registeredDevices[str(devicePath)]["Connected"] = bool(changed[dbus.String('Connected')])
        print("DEVÌCE CONNECTED - time ellapsed in seconds since asking to connect: ", int(time.time() - self.counterTimeToConnect))
      if str(key) == "ServicesResolved":
        print("SERVICES RESOLVED - time ellapsed in milliseconds since asking to connect: ", int(1000*(time.time() - self.counterTimeToConnect)))
        print("SERVICES RESOLVED - timestamp (ms): ", self.nowInMilliseconds())
        servicesResolved =  bool(changed[key])
        self.ServicesResolved[path]= servicesResolved
        self.registeredDevices[str(devicePath)]["ServicesResolved"] =  servicesResolved 
        self.registeredDevices[str(devicePath)]["Services"] = self.getServicesOfDevice(devicePath)
        if servicesResolved and self.ensureDeviceKnown(devicePath):
          self.establishBluetoothConnection(devicePath)
        else:
          print ("No Bluetooth Connection Established")
    # print("+#-- "*20)
    # prettyPrint(changed)

  def establishBluetoothConnection(self,devicePath):
    self.readCharacteristicStringValue( devicePath, UUID_GATESETUP_SERVICE, UUID_SERIAL_NUMBER_CHARACTERISTIC) # async answer


  def readCharacteristicStringValue(self,devicePath, uuidService, uuidCharacteristic):
    characteristicObject = self.registeredDevices[str(devicePath)]["Services"][uuidService]["Characteristics"][uuidCharacteristic]["CharacteristicObject"]
    characteristicObject.ReadValue({}, reply_handler= self.showReadStringValue,
        error_handler=self.genericErrorCallback, dbus_interface=IFACE_GATT_CHARACTERISTIC)

  def showReadStringValue(self, value):
    valueString = ''.join([str(v) for v in value])
    print("read Value: ", valueString)

  def genericErrorCallback(self, error):
    print('D-Bus call failed: ' + str(error))

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

    # print("\n")
    # prettyPrint(characteristics)   
    # print("\n")

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
      # print("An interface that was not a Device was added :) (interfacesAdded)")
      # print("it happened on path: ", path, "+- # -+ "*15)
      # prettyPrint(interfaces)
      # print("-"*90)
      pass

  def launchThreadForNewDevice(self,devicePath):
    #prettyPrint(self.updateRegisteredDevices())
    #self.counterTimeToConnect = time.time()
    self.connectToDevice(devicePath)
    #self.flagToExit = True

  def aliasFromThingsInTouch(self, alias):
    if alias.startswith(ALIAS_THINGSINTOUCH_BEGINING):
      return True
    else:
      return False