from bluetooth.ble import DiscoveryService

service = DiscoveryService()
devices = service.discover()

for address, name in devices.items():
    print("name: {}, address: {}".format(name, address))
    if address=="C0:5E:2B:42:E2:76":
        print()