#!/usr/bin/python

#from __future__ import absolute_import, print_function, unicode_literals

#from optparse import OptionParser, make_option
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject
from thingsSpecificClasses import Thing
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
  if alias[:13] == ALIAS_BEGINS_WITH:
    return True
  else:
    return False

def signalRemoved():
  print("signal Removed")

def connectDeviceIfThingsInTouch(path, interfaces):
  interfaces_added(path,interfaces)


def interfaces_added(path, interfaces):
  #prettyPrint(interfaces)
  try: 
    newDevice = interfaces[IFACE_DEVICE]

    if aliasFromThingsInTouch(newDevice["Alias"]):
      print("-#"*56)
      #print(path)
      #prettyPrint(interfaces)
      newThingInstance=Thing(path, interfaces)
      prettyPrint(newThingInstance.characteristics)
      newThingInstance.startNotify(UUID_NOTIFY_TEST_CHARACTERISTIC)
      thingsDetected.append(newThingInstance)
      print("interfaces added -- "*6)
      now = time.asctime()
      print("interfaces added: {}".format(now))
      bus 							= dbus.SystemBus()
      #prettyPrint(interfaces)
      #printInfo("NEW -->", newDevice)

      thing 					= bus.get_object( BLUEZ, path)
      #help(thing)
      deviceInterface  = dbus.Interface( thing,   IFACE_DEVICE)
      #deviceProps = thing.GetAll(IFACE_DEVICE, dbus_interface=IFACE_PROPERTIES_DBUS)
      #print("Device Properties")
      #prettyPrint(deviceProps)
      
      #print("path:", path)

      #thingsDetected.append(Thing(path, interfaces))
    # print("connect ------------------")
      deviceInterface.Connect(path, dbus_interface=IFACE_DEVICE)
      #bus.remove_signal_receiver(signalRemoved, signal_name="InterfacesAdded", dbus_interface = IFACE_OBJECT_MANAGER_DBUS)
      time.sleep(1)
      print("connected - connected - "*5)
    
      #printInfo("NEW -->", newDevice)
      #getChrcsAndServices()

      #print( newDevice["Alias"])
      #printManagedObjects()
  except:
    print("no interface device")

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
    service = bus.get_object(BLUEZ , path)
    service_props = service.GetAll(IFACE_GATT_SERVICE, dbus_interface=IFACE_PROPERTIES_DBUS)

    uuid = service_props['UUID']
    print("\n")
    print("service uuid ", uuid)
    print("service path ", path)
    print("characteristics of this service: ")
    prettyPrint(chrc_paths)
    print("\n")

  print("#----"*25)
  #prettyPrint(chrcs)

def properties_changed(interface, changed, invalidated, path):
  print('properties changed '+'#'*120+ '\n')
  #device = interface["org.bluez.Device1"]
  #device[path]["Alias"]
  prettyPrint(path)
  prettyPrint(changed)
  # if aliasFromThingsInTouch(device[path]["Alias"]):
  #   print("-#"*56)
  #   print("properties changed -- "*6)
  #   now = time.asctime()
  #   print("properties changed: {}".format(now))
  om = dbus.Interface(bus.get_object(BLUEZ , "/"), IFACE_OBJECT_MANAGER_DBUS)
  objects = om.GetManagedObjects()
  interfaceChanged = objects[path]
  deviceChanged = interfaceChanged[IFACE_DEVICE]
  #prettyPrint(interfaceChanged)
  if aliasFromThingsInTouch(deviceChanged["Alias"]):
    prettyPrint(deviceChanged)

def readValue():
  thingsDetected[0].readValue(UUID_READ_WRITE_TEST_CHARACTERISTIC)

def printManagedObjects():
  om = dbus.Interface(bus.get_object(BLUEZ , "/"), IFACE_OBJECT_MANAGER_DBUS)
  objects = om.GetManagedObjects()
  prettyPrint(objects)

if __name__ == '__main__':
  DBusGMainLoop(set_as_default=True)

  bus 							= dbus.SystemBus()

  hci0 							= bus.get_object( BLUEZ, PATH_HCI0)
  adapter_interface = dbus.Interface( hci0,   IFACE_ADAPTER)

  #help(bus)

  om = dbus.Interface(bus.get_object(BLUEZ , "/"), IFACE_OBJECT_MANAGER_DBUS)

  objects = om.GetManagedObjects()
  #prettyPrint(objects)
  for path, interfaces in objects.items():
    if "org.bluez.Device1" in interfaces:
      connectDeviceIfThingsInTouch(path, interfaces)

  
  bus.add_signal_receiver(interfaces_added, dbus_interface = IFACE_OBJECT_MANAGER_DBUS, signal_name = "InterfacesAdded")
  bus.add_signal_receiver(properties_changed, dbus_interface = "org.freedesktop.DBus.Properties", signal_name = "PropertiesChanged", arg0 = "org.bluez.Device1", path_keyword = "path")


  scan_filter = dict()
  scan_filter["Transport"] 	= "le"
  #scan_filter['UUIDs'] 			= [UUID_GATESETUP_SERVICE]
  #help(adapter_interface)
  
  adapter_interface.SetDiscoveryFilter(scan_filter)
  #adapter_interface.SetDiscoveryFilter(scan_filter)
  #adapter_interface.StartDiscovery()

  time.sleep(4)


  objects = om.GetManagedObjects()
  #prettyPrint(objects)
  for path, interfaces in objects.items():
    if "org.bluez.Device1" in interfaces:
      connectDeviceIfThingsInTouch(path, interfaces)
  
  GObject.timeout_add(2000, readValue)


  mainloop = GObject.MainLoop()
  mainloop.run()