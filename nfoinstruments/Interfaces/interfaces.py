import pyvisa

import tkinter
from tkinter import filedialog
import os

class MeasurementSetup:
    """Class representing a measurement setup."""

    def __init__(self):
        """Initialize the Measurement object."""

        self._resman = pyvisa.ResourceManager()
        self._resource = self._get_resources()

        if len(self._resources) == 0:
            raise InstrumentError("no devices found") 

    def _get_resources(self):
        addresses = self._resman.list_resources()
        self.resources = []
        for addr in addresses:
            try:
                #Try to open the resource, them immediately close it again
                self._resman.open_resource(addr).close()
                self.resources.append(addr)
            except pyvisa.errors.VisaIOError:
                continue
        
    def connect_to_devices(self, addresses):
        self.devices = {}
        for addr, devcls in addresses.items():
            try:
                self.devices[addr] = devcls(addr, self._resman)
            except:
                print(f"Could not connect to device {devcls} at address {addr}")

class InstrumentError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"InstrumentError: {super().__str__()}"