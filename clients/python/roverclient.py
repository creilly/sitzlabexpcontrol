from wsclient import run, sendCommand
from time import sleep
    
def hook(ws):
    sendCommand('set interlock state',{'switch':'2','interlockState':True})

run(hook)