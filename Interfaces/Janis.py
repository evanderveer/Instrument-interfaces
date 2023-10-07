from pprint import pprint
from time import sleep

class Janis:
    """Class representing the Janis probe station temperature controller."""

    def __init__(self, address, resman):
        """
        Initialize the Janis object.

        Args:
            address (str): Address of the Janis instrument.
            resman: PyVISA resource manager instance.
        """

        self.address = address
        self.resource = resman.open_resource(self.address, read_termination=';', write_termination=';', query_delay=0.1)

        self._temperature = None
        self._temperature_setpoint = None
        self._temperature_rate = None
        self._temperature_approach_mode = None

        self.print_status()

    def print_status(self):
        """
        Print the current status of the Janis controller.
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
                sleep(1)
                continue
            else:
                return
        raise IOError("Could not determine temperature controller state.")

    @property
    def temperature(self):
        """
        Get the current temperature of the Janis controller.

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
        raise IOError("Error in Janis temperature control.")

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
