import sys
import os

from specificClassesBLE_03 import GateSetupApplication, GateSetupAdvertisement

DEVICE_NAME = 'ThingsInTouch-Gate-03'
IP_HOSTNAME = '127.0.1.1'

def changeDeviceHostname(): # the bluetooth device listening reads the DeviceHostname instead of the Alias of the Advertisement
    # https://wiki.debian.org/Hostname?action=show&redirect=HowTo%2FChangeHostname
    # http://pitown.blogspot.com/2013/11/change-raspberry-pis-hostname-without.html
    # https://thepihut.com/blogs/raspberry-pi-tutorials/19668676-renaming-your-raspberry-pi-the-hostname

    file1='/etc/hostname' 
    with open(file1, 'w') as f:
        f.write(DEVICE_NAME)

    file2='/etc/hosts'
    with open(file2, "r") as f:
        lines = f.readlines()
    with open(file2, "w") as f:
        for line in lines:
            #print(repr(line))
            if IP_HOSTNAME in line:
                f.write(IP_HOSTNAME+'\t'+DEVICE_NAME+'\n')
            elif repr(line) == "\n":
                pass
            else:
                f.write(line)
    
    os.system("invoke-rc.d hostname.sh start")
    os.system("invoke-rc.d networking force-reload")
    os.system("invoke-rc.d dhcpcd force-reload")


def main():
    #changeDeviceHostname()
    application     = GateSetupApplication()
    application.registerApplication()

    advertisement   = GateSetupAdvertisement()
    advertisement.makeDeviceDiscoverable()
    advertisement.registerAdvertisement()
    advertisement.infiniteLoop()

if __name__ == '__main__':
    main()
