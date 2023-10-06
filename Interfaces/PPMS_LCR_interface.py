import pyvisa
import time
from collections import namedtuple
import tkinter
from tkinter import filedialog
import os
import measurements
from pprint import pprint

Status = namedtuple('Status', ['temperature', 'field', 'chamber', 'position'])

def increment_filename(filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1

    return new_filename

class Measurement:
    """Class representing a measurement setup."""

    def __init__(self, addr_lcr='GPIB1::17::INSTR', addr_ppms='GPIB0::15::INSTR'):
        """
        Initialize the Measurement object.

        Args:
            addr_lcr (str): Address of the LCR instrument.
            addr_ppms (str): Address of the PPMS instrument.
        """

        resman = pyvisa.ResourceManager()
        try:
            self.lcr = LCR(addr_lcr, resman)
        except:
            print("could not connect to LCR meter")
            
        try:
            self.ppms = PPMS(addr_ppms, resman)
        except:
            print("could not connect to PPMS")
        

        self._filename = None
        self._temperature_continuous = True
        self._temperature_points = None
        self._settle_time = 0
        self._bias_points = None
        self._frequency_points = None

        self._tk_root = tkinter.Tk()
        self._tk_root.withdraw()
        
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

class PPMS:
    """Class representing a Physical Property Measurement System (PPMS)."""

    def __init__(self, address, resman):
        """
        Initialize the PPMS object.

        Args:
            address (str): Address of the PPMS instrument.
            resman: PyVISA resource manager instance.
        """

        self.address = address
        self.resource = resman.open_resource(self.address, read_termination=';', write_termination=';', query_delay=0.1)

        self._temperature = None
        self._temperature_setpoint = None
        self._temperature_rate = None
        self._temperature_approach_mode = None

        self._field = None
        self._field_setpoint = None
        self._field_rate = None
        self._field_approach_mode = None
        self._magnet_mode = None

        self._position = None
        self._helium_level = None
        self._status = None

        self.print_status()

    def print_status(self):
        """
        Print the current status of the PPMS.
        """

        self._update_status()
        pprint(vars(self))
        
    def _update_status(self):
        for i in range(5):
            try:
                self.resource.clear()
                data = self.resource.query('GETDAT? 15').split(',')
                _, _, status, temp, field, pos = data
                self._temperature = float(temp)
                self._field = float(field)
                self._position = float(pos)
                stat_bin = int(status)
                self._status = Status(temperature=int(stat_bin & 15),
                                      field=round(int(stat_bin & 240)/2**4),
                                      chamber=round(int(stat_bin & 3840)/2**8),
                                      position=round(int(stat_bin & 61440)/2**12)) # Magic
                
                temp_setpt, temp_rate, temp_appr_mode = self.resource.query('TEMP?').split(',')
                self._temperature_setpoint = float(temp_setpt)
                self._temperature_rate = float(temp_rate)
                self._temperature_approach_mode = float(temp_appr_mode)

                field_setpt, field_rate, field_appr_mode, magnet_mode = self.resource.query('FIELD?').split(',')
                self._field_setpoint = float(field_setpt)
                self._field_rate = float(field_rate)
                self._field_approach_mode = float(field_appr_mode)
                self._magnet_mode = float(magnet_mode)

                helium_lev = self.resource.query('LEVEL?').split(',')[0]
                self._helium_level = float(helium_lev)
            except:
                time.sleep(1)
                continue
            else:
                return
        raise IOError("Could not determine PPMS state.")

    @property
    def temperature(self):
        """
        Get the current temperature of the PPMS.

        Returns:
            float: The current temperature.
        """

        self._update_status()
        return self._temperature

    @property
    def temperature_stable(self):
        """
        This function determines whether the current temperature has stabilized at the setpoint.
        """

        self._update_status()
        if self._status[3] in (5, 6, 7) or \
            abs(self._temperature - self._temperature_setpoint) > 0.2: 
            return False
        if self._status[3] in (1, 2):
            return True
        raise IOError("Error in PPMS temperature control.")
    
    @property
    def field_stable(self):
        """This function determines whether the current magnetic field has stabilized at the setpoint."""
        self._update_status()
        if self._status[2] in (2, 3, 5, 6, 7) or \
            abs(self._field - self._field_setpoint) > 2: 
            return False
        if self._status[2] in (1, 4):
            return True
        raise IOError("Error in PPMS field control.")
    
    @property
    def chamber(self):
        """This function returns the status of the sample chamber."""

        self._update_status()
        if self._status[1] in (1, 2, 4, 5, 8, 9): return self._status[1]
        raise IOError("Error in sample chamber status.")

    @chamber.setter
    def chamber(self, chamber_code):
        """Sets a new chamber code."""

        if chamber_code in (0,1,2,3,4):
            self.resource.write(f"CHAMBER {chamber_code}")
            return
        raise ValueError("Invalid chamber code.")
    
    def seal(self): self.chamber = 0
    def purge(self): self.chamber = 1
    def vent_seal(self):
        self._update_status()
        if self._temperature > 320 or self._temperature < 290:
            raise InstrumentError("temperature too high or too low to vent")
        self.chamber = 2
    def pump(self): self.chamber = 3
    def vent_continuous(self): 
        self._update_status()
        if self._temperature > 320 or self._temperature < 290:
            raise InstrumentError("temperature too high or too low to vent")
        self.chamber = 4
    def _force_vent_continuous(self): self.chamber = 4
    
    @property
    def sample_position(self):
        """This function returns the status of the sample chamber."""
        self._update_status()
        if self._status[0] in (1, 5, 8, 9): return self._status[0]
        raise IOError("Error in sample position status.")

    @property
    def temperature_setpoint(self):
        self._update_status()
        return (self._temperature_setpoint, 
                self._temperature_rate, 
                self._temperature_approach_mode)

    @temperature_setpoint.setter
    def temperature_setpoint(self, setpoint):
        if len(setpoint) != 3:
            raise ValueError("setpoint must have three components: value, rate, approach mode")
        if (type(setpoint[2]) == int or type(setpoint[2]) == float) and not setpoint[2] in [0, 1]:
            raise ValueError("approach mode must be 0/'fast settle' or 1/'no overshoot'")
        if (type(setpoint[2]) == str) and not setpoint[2] in ['fast settle', 'no overshoot']:
            raise ValueError("approach mode must be 0/'fast settle' or 1/'no overshoot'")
        if setpoint[2] in ['fast settle', 'no overshoot']:
            appr_mode_dict = {'fast settle': 0, 'no overshoot': 1}
            self.resource.write(f"TEMP {setpoint[0]} {setpoint[1]} {appr_mode_dict[setpoint[2]]}")
            return
        self.resource.write(f"TEMP {setpoint[0]} {setpoint[1]} {setpoint[2]}")

    @property
    def field_setpoint(self):
        self._update_status()
        return (self._field_setpoint, 
                self._field_rate, 
                self._field_approach_mode)

    @field_setpoint.setter
    def field_setpoint(self, setpoint):
        if len(setpoint) != 4:
            raise ValueError("setpoint must have four components: value, rate, approach mode, magnet mode")
        self.resource.write(f"FIELD {setpoint[0]} {setpoint[1]} {setpoint[2]} {setpoint[3]}")

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