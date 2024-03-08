from time import sleep, time
from pymeasure.experiment import Procedure,\
                                 IntegerParameter,\
                                 FloatParameter,\
                                 ListParameter,\
                                 BooleanParameter

from nfoinstruments.Interfaces.ImpedanceAnalyzer import HP4291A

class IAProcedure(Procedure):
    """
    Procedure for doing impedance spectroscopy at different temperatures
    and bias offsets using the HP 4291A impedance analyzer. 
    """

    # a list defining the order and appearance of columns in our data file
    DATA_COLUMNS = ['Frequency','Bias', 'R', 'X', 'Rraw', 'Xraw']

    def __init__(self, setup, ia_addr):

        self._setup = setup
        self._setup.connect_to_devices({
                                        ia_addr: HP4291A
                                        })

        self._ia = self._setup.devices[ia_addr]

        super().__init__()

    def execute(self):
        self._emit_measurement_data()

    def _emit_measurement_data(self):
        self._ia.measure()
        """
        self.emit('results', {
                'Time': time(),
                'Bias': self._lcr.bias,
                'Frequency': self._lcr.frequency,
                'R': cap_res[0],
                'X': cap_res[1],
            })
            """
        pass