import sys
import array
import dbus, dbus.mainloop.glib
from gi.repository import GLib
from example_advertisement import Advertisement

from example_gatt_server import Service, Characteristic


BLUEZ =           'org.bluez'
DBUS =        'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING = 'org.bluez.LEAdvertisingManager1'
GATT =           'org.bluez.GattManager1'
CHRC =              'org.bluez.GattCharacteristic1'
mainloop = None

def register_ad_cb():
    print('Advertisement registered')

def register_ad_error_cb(error):
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()

def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()

#############################################################
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
                ['write'],
                service)
        self.value = []
        self.notifying = False
        self.index = index
        #self.service= service

    def ReadValue(self, options):
        print('TestCharacteristic Read: ' + repr(self.value))
        return self.value

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

###############################################################

class TestService(Service):
	"""
	Dummy test service that provides characteristics and descriptors that
	exercise various API functionality.
	"""
	def __init__(self, bus, index):
		Service.__init__(self, bus, index,'12345678-1234-5678-1234-56789abcdfff', True)
		charUUID     = '12345678-1234-5678-1234-56789abcd800'
		print('characteristic added: '+ charUUID )
		self.add_characteristic(TestCharacteristic(bus, 0, charUUID,self))
##################################################################
class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)
        # print('appended service --- - ', service)
        # print('  service properties - ', service.get_properties())

    @dbus.service.method(DBUS, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        return response

###################################################################
class IoTApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(TestService(bus, 0))

####################################################################
class IoTAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('12345678-1234-5678-1234-56789abcdfff')
        self.add_local_name('thingsintouch-RAS3')
        self.include_tx_power = True

#########################################################################
def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ, '/'),
                               DBUS)
    objects = remote_om.GetManagedObjects()
    for o, props in objects.items():
        if LE_ADVERTISING in props and GATT in props:
            return o
        print('Skip adapter:', o)
    return None


########################################################################


def main():
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)

    # print('bus - ', bus)
    # print('adapter - ',adapter)

    if not adapter:
        print('BLE adapter not found')
        return

    service_manager = dbus.Interface(
                                bus.get_object(BLUEZ, adapter),
                                GATT)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ, adapter),
                                LE_ADVERTISING)

    # print('service_manager - ',service_manager)
    # print('ad_manager', ad_manager)

    appPath = '/'
    app = dbus.service(bus,'/')
    
    servicePath = '/org/bluez/example/service0'
    serviceUUID = '12345678-1234-5678-1234-56789abcdfff'
    servicePrimary = True
    service = dbus.service.Object(bus, servicePath)

    appServices = []
    appServices.append([servicePath,serviceUUID,servicePrimary])
    
    #app = IoTApplication(bus)
    adv = IoTAdvertisement(bus, 0)

    mainloop = GLib.MainLoop()

    # print('mainloop - ', mainloop)
    # print('IoTApp Services - ',app.services)


    service_manager.RegisterApplication('/', {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
		# the error handler quits the mainloop: mainloop.quit

    ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
    try:
        mainloop.run()
    except KeyboardInterrupt:
        adv.Release()

if __name__ == '__main__':
    main()
