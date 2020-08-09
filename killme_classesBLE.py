


class HeartRateService(Service):
    """
    Fake Heart Rate Service that simulates a fake heart beat and control point
    behavior.

    """
    HR_UUID = '0000180d-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.HR_UUID, True)
        self.add_characteristic(HeartRateMeasurementChrc(bus, 0, self))
        self.add_characteristic(BodySensorLocationChrc(bus, 1, self))
        self.add_characteristic(HeartRateControlPointChrc(bus, 2, self))
        self.energy_expended = 0


class HeartRateMeasurementChrc(Characteristic):
    HR_MSRMT_UUID = '00002a37-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.HR_MSRMT_UUID,
                ['notify'],
                service)
        self.notifying = False
        self.hr_ee_count = 0

    def hr_msrmt_cb(self):
        value = []
        value.append(dbus.Byte(0x06))

        value.append(dbus.Byte(randint(90, 130)))

        if self.hr_ee_count % 10 == 0:
            value[0] = dbus.Byte(value[0] | 0x08)
            value.append(dbus.Byte(self.service.energy_expended & 0xff))
            value.append(dbus.Byte((self.service.energy_expended >> 8) & 0xff))

        self.service.energy_expended = \
                min(0xffff, self.service.energy_expended + 1)
        self.hr_ee_count += 1

        print('Updating value: ' + repr(value))

        self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': value }, [])

        return self.notifying

    def _update_hr_msrmt_simulation(self):
        print('Update HR Measurement Simulation')

        if not self.notifying:
            return

        GObject.timeout_add(1000, self.hr_msrmt_cb)

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self._update_hr_msrmt_simulation()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False
        self._update_hr_msrmt_simulation()


class BodySensorLocationChrc(Characteristic):
    BODY_SNSR_LOC_UUID = '00002a38-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.BODY_SNSR_LOC_UUID,
                ['read'],
                service)

    def ReadValue(self, options):
        # Return 'Chest' as the sensor location.
        return [ 0x01 ]

class HeartRateControlPointChrc(Characteristic):
    HR_CTRL_PT_UUID = '00002a39-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.HR_CTRL_PT_UUID,
                ['write'],
                service)

    def WriteValue(self, value, options):
        print('Heart Rate Control Point WriteValue called')

        if len(value) != 1:
            raise InvalidValueLengthException()

        byte = value[0]
        print('Control Point value: ' + repr(byte))

        if byte != 1:
            raise FailedException("0x80")

        print('Energy Expended field reset!')
        self.service.energy_expended = 0


class BatteryService(Service):
    """
    Fake Battery service that emulates a draining battery.

    """
    BATTERY_UUID = '180f'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.BATTERY_UUID, True)
        self.add_characteristic(BatteryLevelCharacteristic(bus, 0, self))


class BatteryLevelCharacteristic(Characteristic):
    """
    Fake Battery Level characteristic. The battery level is drained by 2 points
    every 5 seconds.

    """
    BATTERY_LVL_UUID = '2a19'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.BATTERY_LVL_UUID,
                ['read', 'notify'],
                service)
        self.notifying = False
        self.battery_lvl = 100
        GObject.timeout_add(5000, self.drain_battery)

    def notify_battery_level(self):
        if not self.notifying:
            return
        self.PropertiesChanged(
                GATT_CHRC_IFACE,
                { 'Value': [dbus.Byte(self.battery_lvl)] }, [])

    def drain_battery(self):
        if not self.notifying:
            return True
        if self.battery_lvl > 0:
            self.battery_lvl -= 2
            if self.battery_lvl < 0:
                self.battery_lvl = 0
        print('Battery Level drained: ' + repr(self.battery_lvl))
        self.notify_battery_level()
        return True

    def ReadValue(self, options):
        print('Battery Level read: ' + repr(self.battery_lvl))
        return [dbus.Byte(self.battery_lvl)]

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self.notify_battery_level()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False


# class TestService(Service):
    #     """
    #     Dummy test service that provides characteristics and descriptors that
    #     exercise various API functionality.

    #     """
    #     TEST_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    #     def __init__(self, bus, index):
    #         Service.__init__(self, bus, index, self.TEST_SVC_UUID, True)
    #         self.add_characteristic(TestCharacteristic(bus, 0, self))
    #         self.add_characteristic(TestEncryptCharacteristic(bus, 1, self))
    #         self.add_characteristic(TestSecureCharacteristic(bus, 2, self))

    # class TestCharacteristic(Characteristic):
    #     """
    #     Dummy test characteristic. Allows writing arbitrary bytes to its value, and
    #     contains "extended properties", as well as a test descriptor.

    #     """
    #     TEST_CHRC_UUID = '12345678-1234-5678-1234-56789abcdef1'

    #     def __init__(self, bus, index, service):
    #         Characteristic.__init__(
    #                 self, bus, index,
    #                 self.TEST_CHRC_UUID,
    #                 ['read', 'write', 'writable-auxiliaries'],
    #                 service)
    #         self.value = []
    #         self.add_descriptor(TestDescriptor(bus, 0, self))
    #         self.add_descriptor(
    #                 CharacteristicUserDescriptionDescriptor(bus, 1, self))

    #     def ReadValue(self, options):
    #         print('TestCharacteristic Read: ' + repr(self.value))
    #         return self.value

    #     def WriteValue(self, value, options):
    #         print('TestCharacteristic Write: ' + repr(value))
    #         self.value = value


    # class TestDescriptor(Descriptor):
    #     """
    #     Dummy test descriptor. Returns a static value.

    #     """
    #     TEST_DESC_UUID = '12345678-1234-5678-1234-56789abcdef2'

    #     def __init__(self, bus, index, characteristic):
    #         Descriptor.__init__(
    #                 self, bus, index,
    #                 self.TEST_DESC_UUID,
    #                 ['read', 'write'],
    #                 characteristic)

    #     def ReadValue(self, options):
    #         return [
    #                 dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')
    #         ]


    # class CharacteristicUserDescriptionDescriptor(Descriptor):
    #     """
    #     Writable CUD descriptor.

    #     """
    #     CUD_UUID = '2901'

    #     def __init__(self, bus, index, characteristic):
    #         self.writable = 'writable-auxiliaries' in characteristic.flags
    #         self.value = array.array('B', b'This is a characteristic for testing')
    #         self.value = self.value.tolist()
    #         Descriptor.__init__(
    #                 self, bus, index,
    #                 self.CUD_UUID,
    #                 ['read', 'write'],
    #                 characteristic)

    #     def ReadValue(self, options):
    #         return self.value

    #     def WriteValue(self, value, options):
    #         if not self.writable:
    #             raise NotPermittedException()
    #         self.value = value

    # class TestEncryptCharacteristic(Characteristic):
    #     """
    #     Dummy test characteristic requiring encryption.

    #     """
    #     TEST_CHRC_UUID = '12345678-1234-5678-1234-56789abcdef3'

    #     def __init__(self, bus, index, service):
    #         Characteristic.__init__(
    #                 self, bus, index,
    #                 self.TEST_CHRC_UUID,
    #                 ['encrypt-read', 'encrypt-write'],
    #                 service)
    #         self.value = []
    #         self.add_descriptor(TestEncryptDescriptor(bus, 2, self))
    #         self.add_descriptor(
    #                 CharacteristicUserDescriptionDescriptor(bus, 3, self))

    #     def ReadValue(self, options):
    #         print('TestEncryptCharacteristic Read: ' + repr(self.value))
    #         return self.value

    #     def WriteValue(self, value, options):
    #         print('TestEncryptCharacteristic Write: ' + repr(value))
    #         self.value = value

    # class TestEncryptDescriptor(Descriptor):
    #     """
    #     Dummy test descriptor requiring encryption. Returns a static value.

    #     """
    #     TEST_DESC_UUID = '12345678-1234-5678-1234-56789abcdef4'

    #     def __init__(self, bus, index, characteristic):
    #         Descriptor.__init__(
    #                 self, bus, index,
    #                 self.TEST_DESC_UUID,
    #                 ['encrypt-read', 'encrypt-write'],
    #                 characteristic)

    #     def ReadValue(self, options):
    #         return [
    #                 dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')
    #         ]


    # class TestSecureCharacteristic(Characteristic):
    #     """
    #     Dummy test characteristic requiring secure connection.

    #     """
    #     TEST_CHRC_UUID = '12345678-1234-5678-1234-56789abcdef5'

    #     def __init__(self, bus, index, service):
    #         Characteristic.__init__(
    #                 self, bus, index,
    #                 self.TEST_CHRC_UUID,
    #                 ['secure-read', 'secure-write'],
    #                 service)
    #         self.value = []
    #         self.add_descriptor(TestSecureDescriptor(bus, 2, self))
    #         self.add_descriptor(
    #                 CharacteristicUserDescriptionDescriptor(bus, 3, self))

    #     def ReadValue(self, options):
    #         print('TestSecureCharacteristic Read: ' + repr(self.value))
    #         return self.value

    #     def WriteValue(self, value, options):
    #         print('TestSecureCharacteristic Write: ' + repr(value))
    #         self.value = value


    # class TestSecureDescriptor(Descriptor):
    #     """
    #     Dummy test descriptor requiring secure connection. Returns a static value.

    #     """
    #     TEST_DESC_UUID = '12345678-1234-5678-1234-56789abcdef6'

    #     def __init__(self, bus, index, characteristic):
    #         Descriptor.__init__(
    #                 self, bus, index,
    #                 self.TEST_DESC_UUID,
    #                 ['secure-read', 'secure-write'],
    #                 characteristic)

    #     def ReadValue(self, options):
    #         return [
    #                 dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')
    #         ]
