from pprint import pprint
from enum import Enum, auto
from abc import ABC, abstractmethod

class ImpedanceAnalyzer(ABC):
    @property
    @abstractmethod
    def measurement(self):
        pass

class HP4291A(ImpedanceAnalyzer):
    
    INSTRUMENT_ID = 'HEWLETT-PACKARD,4291A,JP3KA00634,REV3.03'

    DEFAULT_SWEEP_AVERAGE = 1
    DEFAULT_POINT_AVERAGE = 1

    def __init__(self, address, resman):
        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)

    def _reset_trigger(self):
        self.resource.write("TRIG:SOUR INT")
        self.resource.write("INIT:CONT OFF")
        self.resource.write("ABOR")
        self.resource.write("*SRE 4")
        self.resource.write("*CLS")
    
    def trigger(self):
        self.resource.write("*CLS")
        self.resource.write("INIT")

    def measure(self):
        self._reset_trigger()
        self.trigger()
        self.resource.wait_for_srq()
        result = self.resource.query("DATA? RAW")
        print(result)