import sys

from specificClassesBLE import GateSetupApplication, GateSetupAdvertisement

def main():

    application     = GateSetupApplication()
    application.registerApplication()

    advertisement   = GateSetupAdvertisement()
    advertisement.makeDeviceDiscoverable()
    advertisement.registerAdvertisement()
    advertisement.infiniteLoop()

if __name__ == '__main__':
    main()
