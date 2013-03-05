from sitz import _decode_dict
import websocket
import json
import thread
import time
import sys

ws = None

def log(x): print 'log:', x

handlers = {}

def message(name):
    def foo(bar):
        handlers[name] = bar
        return bar
    return foo

class Callback(object):
    def __init__(self,callback,errback):
        self.callback = callback
        self.errback = errback
        self.id = id(self)

callbacks = {}

def sendCommand(command, data={}, callback=log, errback=log):
    callback = Callback(callback,errback)
    callbacks[callback.id] = callback
    ws.send(
        json.dumps(
            {
            'command':command,
                'data':data,
                'callback':callback.id
            }
        )
    )
    onMessage(ws.recv())
    
def onMessage(message):
    message = json.loads(message,object_hook=_decode_dict)
    for key, data in message.items():
        handlers[key](data)

@message('callback')
def onCallback(data):
    callbacks.pop(data['id']).callback(data['data'])

@message('error')
def onError(data):
    callbacks.pop(data['id']).errback(data['message'])

def run(hook):
    global ws
    ws = websocket.create_connection('ws://localhost:8888/ws')
    hook(ws)

if __name__ == '__main__':
    def hook(ws):
        from functools import partial
        def printList(title,l):
            print title, ':'
            for i in l:
                print '\t', i        
        sendCommand('commands',{},partial(printList,'commands'))
        sendCommand('messages',{},partial(printList,'messages'))

    run(hook)




        