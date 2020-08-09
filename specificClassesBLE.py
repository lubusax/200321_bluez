import sys
# import array
import dbus, dbus.mainloop.glib
from gi.repository import GLib
from genericClassesBLE import Application, Advertisement, Service, Characteristic
from pprint import PrettyPrinter
import time
#from array import array

prettyPrint = PrettyPrinter(indent=1).pprint

BLUEZ =                        'org.bluez'
DBUS_OM_IFACE =                'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE =           'org.bluez.GattManager1'
GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
ADAPTER_IFACE =                'org.Bluez.Adapter1'

HCI0_PATH =                    '/org/bluez/hci0'

GATESETUP_SERVICE_UUID = '5468696e-6773-496e-546f-756368000100' # ThingsInTouch - Gate Setup Service

DEVICE_NAME = 'ThingsInTouch-Gate-01'

class TestCharacteristic(Characteristic):
    """
    Dummy test characteristic. Allows writing arbitrary bytes to its value, and
    contains "extended properties", as well as a test descriptor.
    """

    def __init__(self, bus, index, uuid, service):

        Characteristic.__init__(
                self, bus, index,
                uuid,
                #['read', 'write', 'writable-auxiliaries', 'notify'],
                ['read','write'],
                service)
        self.value = []
        self.notifying = False
        self.index = index
        #self.service= service

    def ReadValue(self, options):
        self.value= time.asctime()
        print('TestCharacteristic Read: ' + repr(self.value))
        returnValue = bytearray()
        returnValue.extend(map(ord, self.value))
        print(returnValue)
        print(type(returnValue))
        return returnValue

    def WriteValue(self, value, options):
        valueString = ""
        for i in range(0,len(value)):
            valueString+= str(value[i])
        print('TestCharacteristic on index ' +
        str(self.index) + ' was written : '+valueString)
       
        self.value = value
        self.valueString = valueString
        # if (self.index % 2) == 0:
        #     self.service.keysList.insert(self.index/2) = valueString
        # else:
        #     self.service.valuesList.insert((self.index-1)/2) = valueString

class GateSetupService(Service):
	"""
    Service that exposes Gate Device Information and allows for the Setup
	"""
	def __init__(self, bus, index):
		Service.__init__(self, bus, index, GATESETUP_SERVICE_UUID, True)
		charUUID     = '12345678-1234-5678-1234-56789abcd800'
		#print('characteristic added: '+ charUUID )
		self.add_characteristic(TestCharacteristic(bus, 0, charUUID,self))

class GateSetupApplication(Application):
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        Application.__init__(self, bus)
        self.add_service(GateSetupService(bus, 0))

class GateSetupAdvertisement(Advertisement):
    def __init__(self):
        bus = dbus.SystemBus()
        index = 0
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid( GATESETUP_SERVICE_UUID) 
        self.add_local_name( DEVICE_NAME)
        self.include_tx_power = True

