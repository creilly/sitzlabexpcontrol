from wsclient import run, sendCommand

def hook(ws):
    sendCommand('create do task', {'name':'jack'})
    sendCommand(
        'create channel',
        {
            'task':'jack',
            'physicalChannel':'gamma/port0/line0',
            'name':'na'
        }
    )
    sendCommand('virtual channels',{'task':'jack'})
    sendCommand('write state',{'task':'jack','state':True})

run(hook)
