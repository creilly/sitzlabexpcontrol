from config.filecreation import POOHDATAPATH
import os
from os import path
from datetime import datetime

def get_filename(folders=None,description=None):
    if folders is None: 
        folders = []
    filepath = path.join(
        POOHDATAPATH,
        datetime.now().strftime("%Y-%m-%d"),
        *folders
    )
    if not path.exists(filepath):
        os.makedirs(filepath)
    time = datetime.now().strftime("%H%M")
    return os.path.join(
        filepath,
        (
            '_'.join(
                (
                    time,
                    description
                )
            ) if description is not None else time
        )
    )
def get_file_dialog():
    import Tkinter, tkFileDialog

    root = Tkinter.Tk()
    root.withdraw()

    return tkFileDialog.askopenfilename()
    
