#!/usr/bin/python

from __future__ import absolute_import, print_function, unicode_literals

from optparse import OptionParser, make_option
import sys
import time
import dbus
import bluezutils

bus = dbus.SystemBus()

# option_list = [
# 		make_option("-i", "--device", action="store",
# 				type="string", dest="dev_id"),
# 		]
# parser = OptionParser(option_list=option_list)

# (options, args) = parser.parse_args()

# print(options.dev_id)

adapter_path = bluezutils.find_adapter().object_path
adapter = dbus.Interface(bus.get_object("org.bluez", adapter_path),
					"org.freedesktop.DBus.Properties")
print ('adapter ', adapter)


addr = adapter.Get("org.bluez.Adapter1", "Address")
print(addr)

name = adapter.Get("org.bluez.Adapter1", "Name")
print(name)

alias = adapter.Get("org.bluez.Adapter1", "Alias")
print(alias)
#adapter.Set("org.bluez.Adapter1", "Alias", args[1])

om = dbus.Interface(bus.get_object("org.bluez", "/"),
		"org.freedesktop.DBus.ObjectManager")
objects = om.GetManagedObjects()
for path, interfaces in objects.items():
	if "org.bluez.Adapter1" in interfaces:
		print("PATH [ %s ]" % (path))
		props = interfaces["org.bluez.Adapter1"]

		for (key, value) in props.items():
			if (key == "Class"):
				print("    %s = 0x%06x" % (key, value))
			else:
				print("    %s = %s" % (key, value))
		print()

powered = adapter.Get("org.bluez.Adapter1", "Powered")
print(powered)
value = dbus.Boolean(1)
#value = dbus.Boolean(0)
#value = dbus.Boolean(args[1])
adapter.Set("org.bluez.Adapter1", "Powered", value)

pairable = adapter.Get("org.bluez.Adapter1", "Pairable")
print(pairable)
value = dbus.Boolean(1)
#value = dbus.Boolean(0)
#value = dbus.Boolean(args[1])
adapter.Set("org.bluez.Adapter1", "Pairable", value)

pt = adapter.Get("org.bluez.Adapter1", "PairableTimeout")
print(pt)
timeout = dbus.UInt32(123) # timeout is 123msec ?
adapter.Set("org.bluez.Adapter1", "PairableTimeout", timeout)

discoverable = adapter.Get("org.bluez.Adapter1", "Discoverable")
print(discoverable)
value = dbus.Boolean(1)
#value = dbus.Boolean(0)
# value = dbus.Boolean(args[1])
adapter.Set("org.bluez.Adapter1", "Discoverable", value)

dt = adapter.Get("org.bluez.Adapter1", "DiscoverableTimeout")
print(dt)
to = dbus.UInt32(1234) # timeout 1234msec
adapter.Set("org.bluez.Adapter1", "DiscoverableTimeout", to)

discovering = adapter.Get("org.bluez.Adapter1", "Discovering")
print(discovering)

