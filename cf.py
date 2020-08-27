from concurrent import futures
import math
import time
import sys

def calc(val):
    time.sleep(1)
    result = math.sqrt(float(val))
    return result

def use_threads(num, values):
    t1 = time.time()
    with futures.ThreadPoolExecutor(num) as tex:
        results = tex.map(calc, values)
    t2 = time.time()
    return t2 - t1

def use_processes(num, values):
    t1 = time.time()
    with futures.ProcessPoolExecutor(num) as pex:
        results = pex.map(calc, values)
    t2 = time.time()
    return t2 - t1

def main(workers, values):
    print("Using %s workers for %s  values" % (workers, len(values)) )
    t_sec = use_threads(workers, values)
    print("Threads took  seconds", t_sec)
    p_sec = use_processes(workers, values)
    print("Processes took seconds", p_sec)

if __name__ == '__main__':
    workers = int(sys.argv[1])
    values = list(range(1, 31)) # 1 .. 5
    main(workers, values)
