import gevent
from gevent import socket

def printVersionPython():
  import sys
  print("Python version")
  print (sys.version)
  print("Version info.")
  print (sys.version_info)

printVersionPython()

hosts = ['www.crappytaxidermy.com', 'www.walterpottertaxidermy.com',
         'www.antique-taxidermy.com']
jobs = [gevent.spawn(gevent.socket.gethostbyname, host) for host in hosts]
gevent.joinall(jobs, timeout=5)
for job in jobs:
    print(job.value)
    #help(job)



