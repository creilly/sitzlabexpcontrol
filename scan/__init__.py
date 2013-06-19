from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
"""

Scan(input,output,callback)

input:
a callable that receives no arguments and \
returns the input (or deferred input) of \
the next scan step or None if the scan \
is finished.

output:
a callable that receives no arguments and \
returns the output (or deferred output) \
of the next scan step.

callback:
a callable that receives the most recent \
input and output and returns either True \
to continue the scan or False to stop \
the scan.

"""
class Scan:
    def __init__(self,input,output,callback):
        self.input = input
        self.output = output
        self.callback = callback

    def start(self):
        d  = Deferred()
        self._loop(d)
        return d

    @inlineCallbacks
    def _loop(self,deferred):
        input = yield self.input()
        if input is None:
            deferred.callback(True) 
            returnValue(None)
        output = yield self.output()
        onwards = yield self.callback(input,output)
        if onwards:
            self._loop(deferred)
        else:
            deferred.callback(False)

