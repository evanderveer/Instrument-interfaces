"""Scientific Instruments Model 9700 temperature controller driver (Janis probe station).

Used to control the cryogenic probe station temperature in the range accessible
by the probe station's cooling system.
"""

from time import sleep

from .base import TemperatureStage


class Janis(TemperatureStage):
    """Driver for the Janis cryogenic probe station temperature controller.

    Communicates over GPIB. Temperature stability is determined by monitoring
    the temperature over a short time window.

    Example usage::

        import pyvisa
        rm = pyvisa.ResourceManager()
        janis = Janis("GPIB0::12::INSTR", rm)
        janis.temperature_setpoint = 200.0
        while not janis.temperature_stable:
            time.sleep(10)
        print(janis.temperature)
    """

    _DEFAULT_MAX_HEATER_POWER = 75.0  # percent
    _STABILITY_WINDOW_K = 0.1          # K — max spread across stability samples
    _STABILITY_SAMPLES = 3
    _STABILITY_SAMPLE_INTERVAL = 1.0   # seconds between samples

    def __init__(self, address: str, resource_manager):
        """Connect to the Janis controller and initialise.

        Args:
            address: VISA resource address (e.g. ``"GPIB0::12::INSTR"``).
            resource_manager: A PyVISA ``ResourceManager`` instance.
        """
        self.address = address
        self.resource = resource_manager.open_resource(address, query_delay=0.1)

        self._temperature: float | None = None
        self._temperature_setpoint: float | None = None
        self._max_heater_power = self._DEFAULT_MAX_HEATER_POWER

        self._initialize()

    def _initialize(self) -> None:
        """Configure the controller operating mode and set heater power limit."""
        self.resource.write(f"SET {self.temperature}")
        self.resource.write(f"MHP {self._max_heater_power}")
        self.resource.write("MODE 2")
        self.resource.write("CTYP 1")

    # ------------------------------------------------------------------
    # TemperatureStage interface
    # ------------------------------------------------------------------

    @property
    def temperature(self) -> float:
        """Current sample temperature in Kelvin."""
        self._temperature = float(self.resource.query("TA?")[3:-2])
        return self._temperature

    @property
    def temperature_stable(self) -> bool:
        """True when temperature spread across three consecutive samples is < 0.1 K."""
        samples = [self._temperature_setpoint]
        for _ in range(self._STABILITY_SAMPLES):
            samples.append(self.temperature)
            sleep(self._STABILITY_SAMPLE_INTERVAL)
        return (max(samples) - min(samples)) < self._STABILITY_WINDOW_K

    @property
    def temperature_setpoint(self) -> float | None:
        """Current temperature setpoint in Kelvin, or ``None`` if not yet set."""
        return self._temperature_setpoint

    @temperature_setpoint.setter
    def temperature_setpoint(self, value: float) -> None:
        """Command the controller to move to a new setpoint.

        Args:
            value: Target temperature in Kelvin.

        Raises:
            ValueError: If ``value`` cannot be converted to float.
        """
        self._temperature_setpoint = float(value)
        self.resource.write(f"SET {self._temperature_setpoint}")

    # ------------------------------------------------------------------
    # Heater power limit
    # ------------------------------------------------------------------

    @property
    def max_heater_power(self) -> float:
        """Maximum heater power limit as a percentage (0–100)."""
        return self._max_heater_power

    @max_heater_power.setter
    def max_heater_power(self, value: float) -> None:
        """Set the maximum heater power limit.

        Args:
            value: Power limit in percent (0–100). Values above 75 % trigger a warning.

        Raises:
            ValueError: If ``value`` is outside 0–100.
        """
        value = round(float(value))
        if not 0.0 <= value <= 100.0:
            raise ValueError("max_heater_power must be between 0 and 100 %")
        if value > 75.0:
            print(f"WARNING: max_heater_power = {value} % — values above 75 % may cause errors")
        self._max_heater_power = value
        self.resource.write(f"MHP {self._max_heater_power}")
