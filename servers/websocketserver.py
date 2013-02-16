import signal
import tornado
import tornado.websocket
import tornado.httpserver
import tornado.web

import json
import sys

DEBUG = len(sys.argv) > 1 and sys.argv[1] == '-debug'

#TAGS METHOD AS COMMAND
def command (command):
    def foo (bar):
        bar.__command__ = command
        return bar
    return foo

#BUILDS COMMANDS DICT
class _get_commands (type):
    def __new__(cls,name,bases,attrs):        
        attrs['commands'] = bases[0].__dict__.get('commands',{})
        for value in attrs.values():        
            if hasattr(value,'__command__'):
                attrs['commands'][value.__command__] = value
        return type.__new__(cls, name, bases, attrs)

#WORKAROUND FOR UNICODE ISSUE
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv
def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
           key = key.encode('utf-8')
        if isinstance(value, unicode):
           value = value.encode('utf-8')
        elif isinstance(value, list):
           value = _decode_list(value)
        elif isinstance(value, dict):
           value = _decode_dict(value)
        rv[key] = value
    return rv

#FUTURE SERVERS INHERIT FROM THIS CLASS
class WebSocketServer(tornado.web.Application):
    __metaclass__ = _get_commands

    handler = None

    class WebSocketHandler(tornado.websocket.WebSocketHandler):
        
        def initialize(self):
            self.application.sockets.append(self)
            
        def on_message(self, message):
            self.application.handle_message(self,message)
                    
        def on_close(self):
            self.application.sockets.remove(self)
    
    def __init__(self):
        self.sockets = []
        tornado.web.Application.__init__(self,[(r'/ws', WebSocketServer.WebSocketHandler if self.handler is None else self.handler), ])
        self.initialize()

    def initialize(self):
        pass

    def terminate(self):
        pass

    def handle_message(self,socket,message):
        command, data, callback, valid = self.parse_message(message)
        if not valid:
            self.error(socket,'not valid message')
            return
        try:
            response = self.commands[command](self,socket,**data)
            if callback is None: return
            socket.write_message(
                json.dumps(
                    {
                        'callback':{
                            'id':callback,
                            'data':response
                        }
                    }
                )
            )
        except Exception as e:
            print e
            self.error(socket,str(e))
            if DEBUG: raise

    def parse_message(self,message):
        try:
            message = json.loads(message,object_hook = _decode_dict)
            return message['command'], message['data'], message['callback'], True
        except (ValueError, KeyError, AttributeError):
            return None, None, None, False        

    def broadcast(self,message):
        for socket in self.sockets:
            socket.write_message(message)

    def error(self,socket,message):
        socket.write_message(json.dumps({'error':message}))

def runServer(server,port):
    from datetime import timedelta
    server.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    def checkForInterrupt():
        ioloop.add_timeout(timedelta(seconds = 1), checkForInterrupt)
    checkForInterrupt()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        server.terminate()
        ioloop.stop()

        
