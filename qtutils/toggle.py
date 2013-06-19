from PySide import QtGui
from PySide.QtCore import Signal, QTimer, QObject
from functools import partial
from sitz import compose

"""

convenient object for starting and stopping tasks with startup/shutdown procedures.

methods :

    requestToggle() :
        request task to toggle startup or shutdown.
        
    toggle() :
        notify ToggleObject of completion of toggle request.
        
    isToggled() :
        returns toggle state
        
signals :

    toggleRequested / activationRequested / deactivationRequested :
        emitted upon call to requestToggle.  notifies agents \
        that a startup (activationRequested)/ shutdown (deactivationRequested) has \
        been requested.  agents responding to this signal are to perform the \
        requested startup / shutdown and then call toggle() to finish request.
        
    toggled / activated / deactivated :
        emitted upon completion of toggle request.  agents responding to this signal \
        can proceed knowing that the rest of the application is prepared for task \
        initiation/abortion.
"""
class ToggleObject(QObject):
    
    toggled = Signal()
    activated = Signal()
    deactivated = Signal()
    
    toggleRequested = Signal()
    activationRequested = Signal()
    deactivationRequested = Signal()
    
    def __init__(self,initialState=False):
        QObject.__init__(self)
        self._toggled = initialState
        self.isToggled = partial(getattr,self,'_toggled')

    def toggle(self):
        state = not self._toggled
        self._toggled = state
        self.toggled.emit()
        getattr(self,'activated' if state else 'deactivated').emit()

    def requestToggle(self):
        self.toggleRequested.emit()
        getattr(self,'deactivationRequested' if self.isToggled() else 'activationRequested').emit()

"""

Simply a ToggleObject with the toggleRequested signal \
internally connected to the toggle method.  For tasks \
that don't require any setup / tearing down.

"""
class ClosedToggle(ToggleObject):
    def __init__(self,initialState=False):
        ToggleObject.__init__(self,initialState)
        self.toggleRequested.connect(self.toggle)
        
"""

A widget that takes in a ToggleObject and connects its \
buttons to the ToggleObject's requestToggle method and \
subscribes to the toggled signal to provide appropriate \
enabling/disabling of buttons

"""
class ToggleWidget(QtGui.QWidget):
    def __init__(self,toggleObject,labels=('start','stop')):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)
        
        def toggle(state):
            self.setEnabled(True)
            for toggle, button in buttons.items():
                button.setEnabled(state is not toggle)
                
        toggleObject.toggled.connect(compose(toggle,toggleObject.isToggled))
                
        buttons = {}
        for label, state in zip(labels,(True,False)):
            button = QtGui.QPushButton(label)
            button.clicked.connect(partial(self.setEnabled,False))
            button.clicked.connect(partial(toggleObject.requestToggle))
            layout.addWidget(button)
            buttons[state] = button

        toggle(toggleObject.isToggled())

"""

Leverages the ToggleObject capabilities to provide start/stoppable \
looping behavior.  Internally it has wired the activationRequested signal \
to the toggle method, and has wired the deactivationRequested signal to \
set an abort flag.

Upon activation, Looper begins issuing loop requests. \
Subscribers to the loopRequested signal receive a Looper.LoopRequest object \
that has a method completeRequest(state) that will stop looping if state is False or \
if the Looper has in the meantime received a stop request.

"""
class Looper(ToggleObject):
    class LoopRequest:
        def __init__(self,looper):
            self.alive = True
            self.looper = looper

        def completeRequest (self,state):
            if not self.alive: raise SitzException('loop request already completed')
            self.alive = False
            if self.looper.aborted or not state:
                self.looper.aborted = False
                self.looper.toggle()
            else:
                self.looper.loopRequested.emit(Looper.LoopRequest(self.looper))
    loopRequested = Signal(object)
    def __init__(self):
        ToggleObject.__init__(self,False)
        self.activationRequested.connect(self.toggle)
        self.activated.connect(
            compose(
                self.loopRequested.emit,
                partial(
                    Looper.LoopRequest,
                    self
                )
            )
        )
        self.deactivationRequested.connect(partial(setattr,self,'aborted',True))
        self.aborted = False
     
if __name__ == '__main__':
    import sys
    from qled import LEDWidget
    app = QtGui.QApplication(sys.argv)
    toggleObject = Looper()
    toggleWidget = ToggleWidget(toggleObject)
    led = LEDWidget(False)
    led.show()
    toggleWidget.show()
    l = range(20)
    def onLoopRequested(loopRequest):
        print 'l: ', l
        if l:
            l.pop()
            led.toggle(not led.isToggled())
        ledTimer = QTimer(toggleObject)
        ledTimer.setSingleShot(True)
        ledTimer.setInterval(200)
        ledTimer.timeout.connect(
            partial(
                loopRequest.completeRequest,
                True if l else False
            )
        )
        ledTimer.start()
        if not l: l.extend(range(20))
    toggleObject.loopRequested.connect(onLoopRequested)
    app.exec_()