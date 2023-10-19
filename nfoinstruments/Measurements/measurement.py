from pymeasure.experiment import Results
from pymeasure.experiment import Worker

import tkinter
from tkinter import filedialog
import os

def increment_filename(filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1

    return new_filename

class Measurement():

    def __init__(self, setup, procedure):
        self._procedure = procedure()
        self._setup = setup
        self.filename = None
        self.timeout = 3600 

    def run(self):
        if self.filename == None:
            raise Exception("no filename selected")
        
        self._result = Results(self._procedure, increment_filename(self.filename))
        self._worker = Worker(self._result)

        self._worker.start()
        self._worker.join(timeout=self.timeout)

    def choose_filename(self):
        """
        Open a file dialog to choose a filename for saving the measurement data.
        """

        currdir = os.getcwd()
        filename = filedialog.asksaveasfilename(parent=self._tk_root, 
                                                initialdir=currdir, 
                                                title='Please select a filename',
                                                confirmoverwrite=False,
                                                filetypes=[("csv file", ".csv"),
                                                           ("txt file", ".txt")],
                                                defaultextension=".csv")
        if filename:
            self.filename = filename