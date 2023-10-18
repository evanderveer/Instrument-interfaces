import pyvisa

import tkinter
from tkinter import filedialog
import os

from PPMS import PPMS
from LCR import LCR
from Janis import Janis

from exceptions import InstrumentError

device_classes = {'PPMS': PPMS, 'LCR': LCR, 'Janis': Janis}

def increment_filename(filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1

    return new_filename

class MeasurementSetup:
    """Class representing a measurement setup."""

    def __init__(self, addr_lcr=None, addr_ppms=None, addr_janis=None):
        """
        Initialize the Measurement object.

        Args:
            addr_lcr (str): Address of the LCR instrument.
            addr_ppms (str): Address of the PPMS instrument.
        """

        self._resman = pyvisa.ResourceManager()
        self._addresses = {'PPMS': addr_ppms, 
                           'LCR': addr_lcr,
                           'Janis': addr_janis}

        self.connect_to_devices()
        if len(self.devices) == 0:
            raise InstrumentError("no devices connected")     

        self._filename = None
        self._temperature_continuous = True
        self._temperature_points = None
        self._settle_time = 0
        self._bias_points = None
        self._frequency_points = None

        self._tk_root = tkinter.Tk()
        self._tk_root.withdraw()
        
    def connect_to_devices(self):
        self.devices = {}
        for name, addr in self._addresses.items():
            devcls = device_classes[name]
            try:
                self.devices[name] = devcls(addr, self._resman)
            except:
                print(f"Could not connect to device {name} at address {addr}")

    @property
    def supported_devices(self):
        print("Currently supported devices:")
        for dev in device_classes.keys():
            print(dev, '\n')

    @property
    def lcr(self):
        return self.devices["LCR"]
    
    @property
    def ppms(self):
        return self.devices["PPMS"]
    
    @property
    def Janis(self):
        return self.devices["Janis"]

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
            self._filename = increment_filename(filename)

    @property
    def filename(self):
        """
        Get the chosen filename for saving the measurement data.

        Returns:
            str: The chosen filename.
        """

        return self._filename
        
    @filename.setter
    def filename(self, filename):
        """
        Set the filename for saving the measurement data. This will overwrite
        any existing file with that filename.
        """

        
        self._filename = increment_filename(filename)

    @property
    def temperature_mode(self):
        """
        Get the temperature mode.

        Returns:
            str: The temperature mode ('continuous' or 'step').
        """
        
        if self._temperature_continuous == True:
            return 'continuous'
        return 'step'
    
    @temperature_mode.setter
    def temperature_mode(self, mode):
        """
        Set the temperature mode.

        Args:
            mode (str): The temperature mode ('continuous' or 'step').

        Raises:
            ValueError: If the mode is not 'continuous' or 'step'.
        """

        if not mode in ['continuous', 'step']:
            raise ValueError("temperature mode must be 'continuous' or 'step'")
        if mode == 'continuous':
            self._temperature_continuous = True
        else:
            self._temperature_continuous = False

    @property
    def temperature_points(self):
        """
        Get the temperature points.

        Returns:
            tuple: A tuple of tuples representing the temperature points.
        """

        return self._temperature_points

    @temperature_points.setter
    def temperature_points(self, points):
        """
        Set the temperature points.

        Args:
            points (tuple): A tuple of tuples representing the temperature points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not type(points) is tuple:
            raise ValueError("temperature points must be a tuple of tuples (temperature, rate, approach mode)")
        if any((not (type(i) is tuple)) for i in points):
            raise ValueError("temperature points must be a tuple of tuples (temperature, rate, approach mode)")
        if any(i[0]<2 or i[0]>400 for i in points):
            raise ValueError("one or more of the temperature points exceeds the minimum or maximum temperature")
        if any(i[1]<=0 or i[1]>20 for i in points):
            raise ValueError("one or more of the rates exceeds the minimum or maximum value") 
        if not all(i[2] in ['fast settle', 'no overshoot'] for i in points):
            raise ValueError("all approach modes must be either 'fast settle' or 'no overshoot'") 
        self._temperature_points = points

    @property
    def bias_points(self):
        """
        Get the bias points.

        Returns:
            tuple: A tuple of biases representing the bias points.
        """

        return self._bias_points

    @bias_points.setter
    def bias_points(self, points):
        """
        Set the bias points.

        Args:
            points (iterable): An iterable (list, tuple) of biases representing the bias points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("bias points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<0 or i>40 for i in points):
            raise ValueError("one or more of the bias points exceeds the minimum or maximum bias") 
        self._bias_points = points
        
    @property
    def frequency_points(self):
        """
        Get the frequency points.

        Returns:
            tuple: A tuple of biases representing the frequency points.
        """

        return self._frequency_points

    @frequency_points.setter
    def frequency_points(self, points):
        """
        Set the frequency points.

        Args:
            points (iterable): An iterable (list, tuple) of biases representing the frequency points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("frequency points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<20 or i>2_000_000 for i in points):
            raise ValueError("one or more of the frequency points exceeds the minimum or maximum") 
        self._frequency_points = points
        
    @property
    def settle_time(self):
        """
        Get the settle time.

        Returns:
            float: The settle time value.
        """

        return self._settle_time
    
    @settle_time.setter
    def settle_time(self, time):
        """
        Set the settle time.

        Args:
            time (float): The settle time value.

        Raises:
            ValueError: If the time value is invalid.
        """

        if (not (type(time) == int or type(time) == float)) or time < 0:
            raise ValueError("settle time must be a number > 0")
        if self._temperature_continuous == True:
            print("settle time will be ignored in continuous temperature mode")
        self._settle_time = time

        pass

