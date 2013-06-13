from sitz import tagger

from twisted.internet.defer import inlineCallbacks, succeed
from twisted.internet import reactor
from abbase import getDigit, log, getListIndex

consoleCommand, consoleMetaclass = tagger('commands')
class ConsoleClient(object):
    __ccname__ = 'console client'
    __metaclass__ = consoleMetaclass
    
    def __init__(self):        
        self.onClose = reactor.stop
        self.onOpen = self.initializeConsoleClient().addCallback(lambda _:log('console client initialized'))
        
    @consoleCommand('quit','exits program')
    @inlineCallbacks
    def quit(self):
        yield self.onClose()

    @consoleCommand('help','prints list of available commands')
    def help(self):
        return '\n'.join('%d:\t%s\t->\t%s' % (index, command[tagger.NAME], command[tagger.DESCRIPTION]) for index, command in enumerate(self.commands))
 
    @inlineCallbacks
    def inputLoop(self):
        commandIndex = yield getListIndex([command[tagger.NAME] for command in self.commands],'select command')
        try:
            response = yield self.commands[commandIndex][tagger.CALLABLE](self)
            response = str(response)
        except Exception, e:
            response = 'ERROR: %s' % repr(e)
        print '\n' + response + '\n'
        if reactor.running: self.inputLoop()

    def initializeConsoleClient(self):
        return succeed(None)

def runConsoleClient(CC,*args,**kwargs):
    import os
    os.system('title %s' % CC.__ccname__)
    cc = CC(*args,**kwargs)
    cc.onOpen.addCallback(lambda _:cc.inputLoop())

if __name__ == '__main__': 
    runConsoleClient(ConsoleClient)
    reactor.run()



