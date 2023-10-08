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
        self.resource = resman.open_resource(self.address, query_delay=0.1)

        self.initialize()

        self._temperature = None
        self._temperature_setpoint = None
        self._temperature_rate = None
        self._temperature_approach_mode = None
        self._mhp = 75.0
        self._temp_stable_time = 1

    def initialize(self):
        self.resource.write(f"SET {self.temperature}") 
        self.resource.write(f"MHP {self._mhp}")
        self.resource.write('MODE 2')
        self.resource.write('CTYP 1')

    @property
    def temperature(self):
        """
        Get the current temperature of the Janis controller.

        Returns:
            float: The current temperature.
        """
        self._temperature = float(self.resource.query("TA?")[3:-2])
        return self._temperature
    
    @property
    def max_heater_power(self):
        return self._mhp
    
    @max_heater_power.setter
    def max_heater_power(self, setpoint):
        setpoint = round(float(setpoint))
        if setpoint < 0.0 or setpoint > 100.0:
            print("Max. heater power must be between 0 and 100 %")
            return
        if setpoint > 75.0:
            print("WARNING: Setting max. heater power higher than 75 % may lead to errors")
        self._mhp = setpoint
        self.resource.write(f"MHP {self._mhp}")

    @property
    def temperature_stable(self):
        """
        This function determines whether the current temperature has stabilized at the setpoint.
        """
        temps = [self._temperature_setpoint]
        for _ in range(3):
            temps.append(self.temperature)
            sleep(self._temp_stable_time)
        return max(temps)-min(temps) < 0.1

    @property
    def temperature_setpoint(self):
        return self._temperature_setpoint

    @temperature_setpoint.setter
    def temperature_setpoint(self, setpoint):
        try:
            self._temperature_setpoint = float(setpoint)
            self.resource.write(f"SET {self._temperature_setpoint}")
        except:
            print("invalid temperature setpoint")
