from sys import stdout

lastline = ''
def write(text):
    global lastline
    lastline = text
    stdout.write(text)

def overwrite(text):
    whitespace = ' ' * len(lastline)
    write('\r' + whitespace)
    write('\r')
    write(text)

def writeLine(text):
    write('\n')
    write(text)
    write('\n')

def newLine():
    write('\n')
    
