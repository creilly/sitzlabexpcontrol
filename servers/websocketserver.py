import signal
import tornado
import tornado.websocket
import tornado.httpserver
import tornado.web

import json
import sys

from sitz import SitzException, _decode_dict

DEBUG = len(sys.argv) > 1 and sys.argv[1] == '-debug'

#TAGS METHOD AS COMMAND
def command (command):
    def foo (bar):
        bar.__command__ = command
        return bar
    return foo

def message (message):
    def foo (bar):
        def baz(self,*args,**kwargs):
            result = bar(self,*args,**kwargs)
            self.sendMessage(message,result)
            return result
        baz.__message__ = message
        return baz
    return foo

#BUILDS COMMANDS DICT
class _get_commands (type):
    def __new__(cls,name,bases,attrs):        
        attrs['commands'] = bases[0].__dict__.get('commands',{})
        attrs['messages'] = bases[0].__dict__.get('messages',{})
        if '_messages' in attrs:
            for message in attrs['_messages']:
                attrs['messages'][message] = []
        for value in attrs.values():        
            if hasattr(value,'__command__'):
                attrs['commands'][value.__command__] = value
            if hasattr(value,'__message__'):
                attrs['messages'][value.__message__] = []
        return type.__new__(cls, name, bases, attrs)

#FUTURE SERVERS INHERIT FROM THIS CLASS
class WebSocketServer(tornado.web.Application):
    __metaclass__ = _get_commands

    handler = None

    class WebSocketHandler(tornado.websocket.WebSocketHandler):
        
        def initialize(self):
            self.application.sockets.append(self)
            self.subscriptions = []
            
        def on_message(self, message):
            self.application.handle_message(self,message)
                    
        def on_close(self):
            for message in self.subscriptions:
                self.application.messages[message].remove(self)
    
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
        except SitzException as e:
            socket.write_message(
                json.dumps(
                    {
                        'error':{
                            'id':callback,
                            'message':e.message
                        }
                    }
                )
            )

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

    @command('commands')
    def getCommands(self,socket):
        return self.commands.keys()

    def sendMessage(self,name,data):
        message = json.dumps(        
            {
                'message':name,
                'data':data
            }        
        )
        for subscriber in self.messages[name]:
            subscriber.write_message(message)
        

    @command('messages')
    def getMessages(self,socket):
        return self.messages.keys()

    @command('subscribe')
    def subscribeToMessage(self,socket,name):
        self.messages[name].append(socket)
        socket.subscriptions.append(name)

    @command('unsubscribe')
    def unsubscribeFromMessage(self,socket,name):
        self.messages[name].remove(socket)
        socket.subscriptions.append(remove)

    @command('subscriptions')
    def getSubscriptions(self,socket):
        return socket.subscriptions()

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

        
