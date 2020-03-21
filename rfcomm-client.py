import bluetooth

bd_addr = "C0:5E:2B:42:E2:76"

port = 1

sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
sock.connect((bd_addr, port))

sock.send("hello!!")

sock.close()