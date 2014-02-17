##########################################
#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 
##########################################
from PySide.QtCore import Signal
from qtutils.label import LabelWidget
import subprocess as SP
from subprocess import Popen
import thread
from threading import Timer
from twisted.internet import reactor, protocol
from functools import partial
from os import path, environ

PYTHON_FILE='c:/python27/python.exe'
DEFAULT_DIR='z:/creilly/sitzlabexpcontrol'
PROGRAM_ROLE = 32
ENV_VARS = {
    'PYTHONPATH':environ['PYTHONPATH']
}
COUNTER = 0

class StatusLabel(QtGui.QLabel):
    def __init__(self,statusDict,initStatus):
        QtGui.QLabel.__init__(self)
        self.statusDict = statusDict
        self.setStatus(initStatus)
    def setStatus(self,status):
        self.setText(self.statusDict[status])

class LogWidget(QtGui.QTextEdit):
    LIMIT = 100 # at most LIMIT lines in log
    def __init__(self):
        QtGui.QTextEdit.__init__(self)
        self.setReadOnly(True)

    def append(self,line):
        if len(self.toPlainText().split('\n')) is self.LIMIT:
            self.clear()
        QtGui.QTextEdit.append(self,line)

class ProgramWidget(QtGui.QWidget):
    def __init__(self,program,name):
        QtGui.QWidget.__init__(self)

        self.program = program

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        info_layout = QtGui.QHBoxLayout()

        layout.addLayout(info_layout)

        info_layout.addWidget(
            LabelWidget(
                'name',
                QtGui.QLabel(name)
            )
        )

        info_layout.addWidget(
            LabelWidget(
                'script',
                QtGui.QLabel(
                    ' '.join(
                        [path.basename(program.args[2])] + program.args[3:]
                    )
                )
            )
        )
        
        status_label = StatusLabel(
            {
                Program.DEAD:'dead',
                Program.RUNNING:'running'
            },
            program.getState()
        )
        info_layout.addWidget(LabelWidget('status',status_label))

        info_layout.addStretch()

        log_widget = LogWidget()
        layout.addWidget(LabelWidget('log',log_widget),1)

        lower_bar_layout = QtGui.QHBoxLayout()
        layout.addLayout(lower_bar_layout)

        input_widget = QtGui.QLineEdit()
        def on_return_pressed():
            program.write(str(input_widget.text()))
            input_widget.clear()
        input_widget.returnPressed.connect(on_return_pressed)
        lower_bar_layout.addWidget(LabelWidget('input',input_widget),1)

        flush_button = QtGui.QPushButton('flush')
        flush_button.clicked.connect(program.flush)
        lower_bar_layout.addWidget(flush_button)

        clear_button = QtGui.QPushButton('clear')
        clear_button.clicked.connect(log_widget.clear)
        lower_bar_layout.addWidget(clear_button)
        
        def log(label,text):
            log_widget.append('<b>%s</b>:\t%s' % (label,text))

        for signal, label in (
                ('outputReceived','output'),
                ('errorReceived','error'),
                ('inputTransmitted','input')
        ):
            getattr(program,signal).connect(partial(log,label))

        lwi = QtGui.QListWidgetItem()
        lwi.setData(PROGRAM_ROLE,self)
        lwi.setText(name)
        def onStateChanged(state):
            font = QtGui.QFont()
            font.setBold(
                {
                    Program.DEAD:False,
                    Program.RUNNING:True
                }[state]
            )
            lwi.setFont(font)

            status_label.setStatus(state)

            input_widget.setEnabled(
                {
                    Program.DEAD:False,
                    Program.RUNNING:True
                }[state]
            )

        program.stateChanged.connect(onStateChanged)
        onStateChanged(program.getState())
        self.lwi = lwi

    def getListWidgetItem(self): return self.lwi

    def getProgram(self): return self.program

class Program(QtCore.QObject):
    outputReceived = Signal(str)
    errorReceived = Signal(str)
    inputTransmitted = Signal(str)
    stateChanged = Signal(int)

    DEAD, RUNNING = 0, 1
    STATES = (DEAD,RUNNING)

    def __init__(self,args):
        QtCore.QObject.__init__(self)
        self.args = args
        self.process = None
        self.state = self.DEAD
        self._RESTART = False
        this = self
        class ProgramProtocol(protocol.ProcessProtocol):
            STD_IN, STD_OUT, STD_ERR = 0,1,2
            PIPES = (STD_IN,STD_OUT,STD_ERR)
            def __init__(self):
                self.remainders = {
                    pipe:'' for pipe in self.PIPES
                }

            def write(self,data):
                self.transport.write(data)
                self.handleTransmission(data,self.STD_IN)

            def outReceived(self,data):
                self.handleTransmission(data,self.STD_OUT)
            def errReceived(self,data):
                self.handleTransmission(data,self.STD_ERR)

            def handleTransmission(self,data,pipe):
                lines = data.split('\n')
                lines[0] = self.remainders[pipe] + lines[0]
                self.remainders[pipe] = lines[-1]
                signal = getattr(
                    this,
                    {
                        self.STD_IN:'inputTransmitted',
                        self.STD_OUT:'outputReceived',
                        self.STD_ERR:'errorReceived',
                    }[pipe]
                )
                for line in lines[:-1]:
                    signal.emit(line)

            def processEnded(self,status):
                this.setState(this.DEAD)

            def connectionMade(self):
                this.setState(this.RUNNING)

            def flushOutput(self):                
                line = self.remainders[self.STD_OUT]
                self.remainders[self.STD_OUT] = ''
                this.outputReceived.emit(line)

        self.ProgramProtocol = ProgramProtocol

    def write(self,data):
        if self.state is self.DEAD:
            raise Exception('can not write to dead process')
        self.process.write(data + '\n')

    def flush(self):
        if self.state is self.DEAD:
            raise Exception('can not flush dead process')
        self.process.flushOutput()
    
    def run(self):
        if self.state is self.RUNNING:
            raise Exception('process already running')
        self.process = self.ProgramProtocol()
        reactor.spawnProcess(
            self.process,
            self.args[0],
            self.args,
            env=ENV_VARS
        )

    def setState(self,state):
        self.state = state
        self.stateChanged.emit(state)
        if not state: 
            self.process = None
        if self._RESTART:
            self._RESTART = False
            self.run()

    def terminate(self):
        if self.state is self.DEAD:
            raise Exception('process already terminated')
        self.process.transport.signalProcess('KILL')
        self.process = None

    def restart(self):
        if self.state is self.DEAD:
            raise Exception('attempted restart of dead process')
        self._RESTART = True
        self.terminate()

    def getState(self):
        return self.state

def main(container):
    widget = QtGui.QWidget()

    # VOODOO
    container.append(widget)

    layout = QtGui.QHBoxLayout()
    
    widget.setLayout(layout)

    left_layout = QtGui.QVBoxLayout()

    layout.addLayout(left_layout)

    tool_layout = QtGui.QHBoxLayout()

    left_layout.addLayout(tool_layout)

    def on_add():
        args = [PYTHON_FILE]
        args.append('-u')
        file_name, _ = QtGui.QFileDialog.getOpenFileName(
            parent=widget,
            caption='pick script',
            dir=DEFAULT_DIR,
            filter='*.py'
        )
        if not file_name: return
        args.append(file_name)
        opt_arg, _ = QtGui.QInputDialog.getText(
            widget,
            'optional argument?',
            'specify any optional argument'
        )
        if opt_arg:
            args.append(opt_arg)        
        program = Program(args)

        name, _ = QtGui.QInputDialog.getText(
            widget,
            'enter name',
            'enter name for program',
            text=path.basename(file_name)
        )
        programWidget = ProgramWidget(program,name)
        stack_widget.addWidget(programWidget)
        lwi = programWidget.getListWidgetItem()
        list_widget.addItem(lwi)
        list_widget.setCurrentItem(lwi)
        
    def on_remove():
        list_item = list_widget.currentItem()
        program = list_item.data(PROGRAM_ROLE).getProgram()
        list_widget.takeItem(list_widget.row(list_item))
        if program.getState() is program.RUNNING:
            program.terminate()
        
    def on_run():
        list_widget.currentItem().data(PROGRAM_ROLE).getProgram().run()
    def on_kill():
        list_widget.currentItem().data(PROGRAM_ROLE).getProgram().terminate()
    def on_restart(): 
        list_widget.currentItem().data(PROGRAM_ROLE).getProgram().restart()

    for name, callback in (
            ('add',on_add),
#            ('remove',on_remove),
            ('run',on_run),
            ('kill',on_kill),
            ('restart',on_restart)
    ):
        button = QtGui.QPushButton(name)
        button.clicked.connect(callback)
        tool_layout.addWidget(button)

    tool_layout.addStretch()

    list_widget = QtGui.QListWidget()

    def on_item_selection_changed():
        list_item = list_widget.currentItem()
        if list_item is None:
            stack_widget.setCurrentWidget(null_widget)
        else:
            stack_widget.setCurrentWidget(list_widget.currentItem().data(PROGRAM_ROLE))

    list_widget.itemSelectionChanged.connect(on_item_selection_changed)

    left_layout.addWidget(list_widget,1)

    stack_widget = QtGui.QStackedWidget()

    null_widget = QtGui.QLabel('nothing selected')

    stack_widget.addWidget(null_widget)

    layout.addWidget(stack_widget,1)

    widget.show()

if __name__ == '__main__':
    container = []
    main(container)
    reactor.run()
