from pprint import pprint
from enum import Enum, auto

class SignalType(Enum):
    CURRENT = auto()
    VOLTAGE = auto()

class MeasurementTime(Enum):
    SHORT = 'SHOR'
    MEDIUM = 'MED'
    LONG = 'LONG'

class MeasurementType(Enum):
    CPD = 'CPD'
    CPQ = 'CPQ'
    CPG = 'CPG'
    CPRP = 'CPRP'
    CSD = 'CSD'
    CSQ = 'CSQ'
    CSRS = 'CSRS'
    LPD = 'LPD'
    LPQ = 'LPQ'
    LPG = 'LPG'
    LPRD = 'LPRD'
    LSD = 'LSD'
    LSQ = 'LSQ'
    LSRD = 'LSRD'
    LSRS = 'LSRS'
    RX = 'RX'
    ZTD = 'ZTD'
    ZTR = 'ZTR'
    GB = 'GB'
    YTD = 'YTD'
    YTR = 'YTR'
    VDID = 'VDID'

class LCR:

    def __init__(self, address, resman):
        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)

        self._measurement_time = MeasurementTime.MEDIUM
        self._averages = 1
        self._bias = 0
        self._frequency = 100
        self._measurement_type = MeasurementType.RX
        self._signal_amplitude = 1
        self.measurement_timeout = 3
        self.instrument_name = 'Agilent E4980A'
        self._signal_type = SignalType.VOLTAGE
        self._alc_enabled = True

        self._initialize()
        self.print_status()

    def _initialize(self):
        self.resource.clear()
        self.resource.write('*RST')
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")
        self.resource.write("BIAS:STAT OFF")
        self.resource.write(f"BIAS:VOLT {self._bias}")
        
        self.resource.write(f"FREQ {self._frequency}")
        self.resource.write(f"VOLT {self._signal_amplitude}")
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type.value}")
        self.resource.write("INIT:CONT ON")
        self.resource.write("AMPL:ALC ON")
        self.resource.write("FORMAT ASCII")

        #Disable all corrections
        self.resource.write("CORR:OPEN:STAT OFF")
        self.resource.write("CORR:SHORT:STAT OFF")
        self.resource.write("CORR:LOAD:STAT OFF")
        self.resource.write(f"CORR:LENG 0")
        
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
        if not isinstance(time, MeasurementTime):
            raise ValueError("measurement time must be SHORT, MEDIUM or LONG")
        self._measurement_time = time
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")
    
    @property
    def averages(self):
        return self._averages

    @averages.setter
    def averages(self, averages):
        if not 1 <= averages <= 256:
            raise ValueError("number of averages must be between 1 and 256")
        self._averages = averages
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")

    @property
    def bias(self):
        return self._bias

    @bias.setter
    def bias(self, bias):
        if self.signal_type == SignalType.VOLTAGE:
            if not -40 <= bias <= 40:
                raise ValueError("bias must be between -40 and 40 V")
            self._bias = bias
            if bias == 0:
                self.resource.write(f"BIAS:STAT OFF")
                self.resource.write(f"BIAS:VOLT {self._bias}")
            else:
                self.resource.write(f"BIAS:VOLT {self._bias}")
                self.resource.write(f"BIAS:STAT ON")
        else:
            if not -0.1 <= bias <= 0.1:
                raise ValueError("bias must be between -0.1 and 0.1 A")
            self._bias = bias
            if bias == 0:
                self.resource.write(f"BIAS:STAT OFF")
                self.resource.write(f"BIAS:CURR {self._bias}")
            else:
                self.resource.write(f"BIAS:CURR {self._bias}")
                self.resource.write(f"BIAS:STAT ON")

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
        if not isinstance(measurement_type, MeasurementType):
            raise ValueError("measurement type invalid")
        self._measurement_type = measurement_type
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type.value}")

    @property
    def signal_amplitude(self):
        return self._signal_amplitude

    @signal_amplitude.setter
    def signal_amplitude(self, signal_amplitude):
        if self.signal_type == SignalType.VOLTAGE:
            if not 0 <= signal_amplitude <= 20:
                raise ValueError("voltage signal amplitude must be between 0 and 20 V")
            self._signal_amplitude = signal_amplitude
            self.resource.write(f"VOLT {self._signal_amplitude}")
        elif self.signal_type == SignalType.CURRENT:
            if not 0 <= signal_amplitude <= 0.1:
                raise ValueError("current signal amplitude must be between 0 and 0.1 A")
            self._signal_amplitude = signal_amplitude
            self.resource.write(f"CURR {self._signal_amplitude}")

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, signal_type):
        if not isinstance(signal_type, SignalType):
            raise ValueError("signal type must be 'voltage' or 'current")
        self._signal_type = signal_type
        self.resource.write(f"CURR 0")

    @property
    def alc_enabled(self):
        return self._alc_enabled

    @alc_enabled.setter
    def alc_enabled(self, alc_enabled):
        if alc_enabled:
            self.resource.write("AMPL:ALC ON")
        else:
            self.resource.write("AMPL:ALC OFF")

    def get_value(self):
        result = self.resource.query("FETCH?").split(',')[0:2]
        return [float(val) for val in result]

    def reset(self):
        self.resource.write("SYSTEM:PRESET")

    def reboot(self):
        self.resource.write("SYSTEM:RESTART")