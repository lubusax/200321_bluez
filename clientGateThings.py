#!/usr/bin/python

#from __future__ import absolute_import, print_function, unicode_literals

from optparse import OptionParser, make_option
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject
from thingsSpecificClasses import Thing

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

compact = True
device 	= {}
thingsDetected =[]

def printInfo(prefix, properties, compact=False):
	
	address = properties.get("Address")
	if address is None:
		address = "    address unknown"

	if compact:	
		name = properties.get("Name")
		if name is None:
			name = "    name unknown"
		print("%s %s %s" % (prefix, address, name))
	else:
		print(prefix+"[ " + address + " ]")
		for key in properties:
			if (key == "Class"):
				print("    %s = 0x%06x" % (key, properties[key]))
			else:
				print("    %s = %s" % (key, properties[key]))

def aliasFromThingsInTouch(alias):
	if alias[:len(ALIAS_BEGINS_WITH)] == ALIAS_BEGINS_WITH:
		return True
	else:
		return False

def interfaces_added(path, interfaces):
  newDevice = interfaces["org.bluez.Device1"]
  #prettyPrint(interfaces)
  #printInfo("NEW -->", newDevice)

  thing 					= bus.get_object( BLUEZ, path)
  deviceInterface  = dbus.Interface( thing,   IFACE_DEVICE)
  deviceProps = thing.GetAll(IFACE_DEVICE, dbus_interface=IFACE_PROPERTIES_DBUS)
  print("Device Properties")
  prettyPrint(deviceProps)
  
  #print("path:", path)

  if aliasFromThingsInTouch(newDevice["Alias"]):
    thingsDetected.append(Thing(path, interfaces))
    print("connect ------------------")
    deviceInterface.Pair()
    print("connected - connected - "*5)
  
  printInfo("NEW -->", newDevice)
  getChrcsAndServices()

  #print( newDevice["Alias"])
  #printManagedObjects()
def getChrcsAndServices():
  om = dbus.Interface(bus.get_object(BLUEZ, '/'), IFACE_OBJECT_MANAGER_DBUS)
  objects = om.GetManagedObjects()
  chrcs = []

  # List characteristics found
  for path, interfaces in objects.items():
    if IFACE_GATT_CHARACTERISTIC not in interfaces.keys():
      continue
    chrcs.append(path)

  # List services found
  for path, interfaces in objects.items():
    if IFACE_GATT_SERVICE not in interfaces.keys():
      continue

    chrc_paths = [d for d in chrcs if d.startswith(path + "/")]

  print("List Characteristics #########################################")
  prettyPrint(chrcs)



def printManagedObjects():
  om = dbus.Interface(bus.get_object(BLUEZ , "/"), IFACE_OBJECT_MANAGER_DBUS)
  objects = om.GetManagedObjects()
  prettyPrint(objects)

if __name__ == '__main__':
  DBusGMainLoop(set_as_default=True)

  bus 							= dbus.SystemBus()

  hci0 							= bus.get_object( BLUEZ, PATH_HCI0)
  adapter_interface = dbus.Interface( hci0,   IFACE_ADAPTER)

  bus.add_signal_receiver(interfaces_added, dbus_interface = IFACE_OBJECT_MANAGER_DBUS, signal_name = "InterfacesAdded")

  om = dbus.Interface(bus.get_object(BLUEZ , "/"), IFACE_OBJECT_MANAGER_DBUS)

  objects = om.GetManagedObjects()
  for path, interfaces in objects.items():
    if "org.bluez.Device1" in interfaces:
      print("known")
      #adapter_interface.RemoveDevice(path)

  scan_filter = dict()
  scan_filter["Transport"] 	= "le"
  scan_filter['UUIDs'] 			= [UUID_GATESETUP_SERVICE]

  adapter_interface.SetDiscoveryFilter(scan_filter)
  adapter_interface.StartDiscovery()

  mainloop = GObject.MainLoop()
  mainloop.run()