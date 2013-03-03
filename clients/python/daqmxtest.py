from daqmx import *
import time

start()

SLEEP = 1

def write(value):
    print 'writing %d' % value
    time.sleep(SLEEP)
    task.writeState(value)
    time.sleep(SLEEP)

createDOTask('chris')
task = getTask('chris')
task.createChannel('gamma/port0/line2','na')
write(0)
write(1)

stop()