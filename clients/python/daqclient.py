import websocket
import json
import thread
import time
import sys

TASK = sys.argv[1]
CHANNEL = sys.argv[2]
PHYS_CHANNEL = 'gamma/ai0'

commandTup = (
    ('create task',{'name':TASK}),
    ('tasks',{}),
    ('create channel',{'task':TASK, 'name':CHANNEL,'physicalChannel':PHYS_CHANNEL}),
    ('virtual channels',{'task':TASK}),
    ('read sample',{'task':TASK}),
)

def ws_command(command, data):
    return json.dumps({'command':command, 'data':data})

def on_message(ws, message):
    print message

def on_error(ws, error):
    print error

def on_close(ws):
    print "### closed ###"

def on_open(ws):
    def run(*args):
        for command in [ws_command(command,data) for command, data in commandTup]:
            time.sleep(.1)
            ws.send(command)
        time.sleep(.1)
        ws.close()
        print "thread terminating..."
    thread.start_new_thread(run, ())


if __name__ == "__main__":
    ws = websocket.WebSocketApp("ws://localhost:8888/ws",
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open

    ws.run_forever()