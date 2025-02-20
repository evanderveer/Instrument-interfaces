from time import sleep, time
from pymeasure.experiment import Procedure,\
                                 IntegerParameter,\
                                 FloatParameter,\
                                 ListParameter,\
                                 BooleanParameter

from nfoinstruments.Interfaces.Stage import PPMS
from nfoinstruments.Interfaces.LCR import E4890A

class K4200Procedure(Procedure):

    def __init__(self, setup):
        pass

    def _emit_measurement_data(self):
        pass

    def execute(self):
        pass