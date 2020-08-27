from bluepy import btle

# peripheral = "E7:E7:EE:61:22:8F" 
# peripheral = "74:40:BB:59:C5:6E" 
# peripheral = "57:82:68:EF:F4:A6"
# peripheral = "77:CC:44:5E:D3:01"
peripheral = "5c:f9:38:db:c0:b0"

print ("Connecting to peripheral: ", peripheral)
dev = btle.Peripheral(peripheral)

print ("Services...")
for svc in dev.services:
    print (str(svc))
    characteristics = svc.getCharacteristics()
    for ch in characteristics:
        print (str(ch))