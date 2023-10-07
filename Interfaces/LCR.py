from pprint import pprint

class LCR:

    valid_measurement_types = ["CPD","CPQ","CPG","CPRP","CSD","CSQ","CSRS","LPD","LPQ",
                               "LPG","LPRP","LPRD","LSD","LSQ","LSRS","LSRD","RX","ZTD",
                               "ZTR","GB","YTD","YTR","VDID"]
    srq = pyvisa.constants.EventType.service_request
    srq_queue = pyvisa.constants.EventMechanism.queue

    def __init__(self, address, resman):
        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)

        self._measurement_time = 'MED'
        self._averages = 1
        self._bias = 0
        self._cable_length = 0
        self._frequency = 100
        self._measurement_type = 'CPD'
        self._signal_amplitude = 1
        self.measurement_timeout = 3
        self.instrument_name = 'Agilent E4980A'

        self._initialize()
        self.print_status()

    def _initialize(self):
        self.resource.clear()
        self.resource.write('*RST')
        self.resource.write(f"APER {self._measurement_time}, {self._averages}")
        self.resource.write("BIAS:STAT OFF")
        self.resource.write(f"BIAS:VOLT {self._bias}")
        self.resource.write(f"CORR:LENG {self._cable_length}")
        
        self.resource.write(f"FREQ {self._frequency}")
        self.resource.write(f"VOLT {self._signal_amplitude}")
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type}")
        self.resource.write("INIT:CONT ON")
        
        self.resource.timeout = self.measurement_timeout * 1000
        self.resource.clear()
        
    def print_status(self):
        """
        Print the current status of the LCR meter.
        """
        
        pprint(vars(self))
    
    @property
    def measurement_time(self):
        return self._measurement_time

    @measurement_time.setter
    def measurement_time(self, time):
        if not time in ['SHORT', 'SHOR', 'MED', 'MEDIUM', 'LONG']:
            raise ValueError("measurement time must be SHORT, MEDIUM or LONG")
        self._measurement_time = time
        self.resource.write(f"APER {self._measurement_time}, {self._averages}")
    
    @property
    def averages(self):
        return self._averages

    @averages.setter
    def averages(self, averages):
        if not 1 <= averages <= 256:
            raise ValueError("number of averages must be between 1 and 256")
        self._averages = averages
        self.resource.write(f"APER {self._measurement_time}, {self._averages}")

    @property
    def bias(self):
        return self._bias

    @bias.setter
    def bias(self, bias):
        if not 0 <= bias <= 40:
            raise ValueError("bias must be between 0 and 40 V")
        self._bias = bias
        if bias == 0:
            self.resource.write(f"BIAS:STAT OFF")
            self.resource.write(f"BIAS:VOLT {self._bias}")
        else:
            self.resource.write(f"BIAS:VOLT {self._bias}")
            self.resource.write(f"BIAS:STAT ON")
        
    
    @property
    def cable_length(self):
        return self._cable_length

    @cable_length.setter
    def cable_length(self, cable_length):
        if not cable_length in [0, 1, 2, 4]:
            raise ValueError("cable_length must be 0, 1, 2 or 4 m")
        self._cable_length = cable_length
        self.resource.write(f"CORR:LENG {self._cable_length}")

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        if not 20 <= frequency <= 2_000_000:
            raise ValueError("frequency must be between 20 Hz and 2 MHz")
        self._frequency = frequency
        #print(f"FREQ {self._frequency}")
        self.resource.write(f"FREQ {self._frequency}")

    @property
    def measurement_type(self):
        return self._measurement_type

    @measurement_type.setter
    def measurement_type(self, measurement_type):
        if not measurement_type in LCR.valid_measurement_types:
            raise ValueError("measurement type invalid")
        self._measurement_type = measurement_type
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type}")

    @property
    def signal_amplitude(self):
        return self._signal_amplitude

    @signal_amplitude.setter
    def signal_amplitude(self, signal_amplitude):
        if not 0 <= signal_amplitude <= 20:
            raise ValueError("signal amplitude must be between 0 and 20 V")
        self._signal_amplitude = signal_amplitude
        self.resource.write(f"VOLT {self._signal_amplitude}")

    def get_value(self):
        result = self.resource.query("FETCH?").split(',')[0:2]
        return [float(val) for val in result]

class InstrumentError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"InstrumentError: {super().__str__()}"