"""Quantum Design PPMS (Physical Property Measurement System) driver.

The PPMS controls cryogenic sample temperature (2–400 K) and magnetic field
via a proprietary MultiVu GPIB interface.
"""

from collections import namedtuple
from pprint import pprint
from time import sleep

from .base import TemperatureStage
from .setup import InstrumentError


class PPMS(TemperatureStage):
    """Driver for the Quantum Design Physical Property Measurement System.

    Communicates over GPIB using the MultiVu command set. Temperature and
    field values are polled on demand; no background thread is used.

    Example usage::

        import pyvisa
        rm = pyvisa.ResourceManager()
        ppms = PPMS("GPIB0::15::INSTR", rm)
        ppms.temperature_setpoint = (100.0, 5.0, "no overshoot")
        while not ppms.temperature_stable:
            time.sleep(5)
        print(ppms.temperature)
    """

    # Named tuple for readable status decoding
    PPMSStatus = namedtuple("PPMSStatus", ["temperature", "field", "chamber", "position"])

    # Bit-field masks for the status word returned by GETDAT? 15
    _TEMP_STATUS_MASK = 0x000F
    _FIELD_STATUS_MASK = 0x00F0
    _CHAMBER_STATUS_MASK = 0x0F00
    _POSITION_STATUS_MASK = 0xF000

    _APPROACH_MODES = {"fast settle": 0, "no overshoot": 1}

    def __init__(self, address: str, resource_manager):
        """Connect to a PPMS and read its current state.

        Args:
            address: VISA resource address (e.g. ``"GPIB0::15::INSTR"``).
            resource_manager: A PyVISA ``ResourceManager`` instance.
        """
        self.address = address
        self.resource = resource_manager.open_resource(
            address,
            read_termination=";",
            write_termination=";",
            query_delay=0.1,
        )

        self._temperature: float | None = None
        self._temperature_setpoint: float | None = None
        self._temperature_rate: float | None = None
        self._temperature_approach_mode: float | None = None

        self._field: float | None = None
        self._field_setpoint: float | None = None
        self._field_rate: float | None = None
        self._field_approach_mode: float | None = None
        self._magnet_mode: float | None = None

        self._position: float | None = None
        self._helium_level: float | None = None
        self._status: PPMS.PPMSStatus | None = None

        self.print_status()

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def print_status(self) -> None:
        """Print the current PPMS state to stdout."""
        self._update_status()
        pprint(vars(self))

    def _update_status(self) -> None:
        """Query the PPMS and refresh all cached state values.

        Retries up to 5 times with a 1-second delay before raising.

        Raises:
            IOError: If the PPMS cannot be queried after 5 attempts.
        """
        for _ in range(5):
            try:
                self.resource.clear()
                _, _, status, temp, field, pos = self.resource.query("GETDAT? 15").split(",")
                self._temperature = float(temp)
                self._field = float(field)
                self._position = float(pos)
                stat = int(status)
                self._status = self.PPMSStatus(
                    temperature=stat & self._TEMP_STATUS_MASK,
                    field=(stat & self._FIELD_STATUS_MASK) >> 4,
                    chamber=(stat & self._CHAMBER_STATUS_MASK) >> 8,
                    position=(stat & self._POSITION_STATUS_MASK) >> 12,
                )

                t_setpt, t_rate, t_mode = self.resource.query("TEMP?").split(",")
                self._temperature_setpoint = float(t_setpt)
                self._temperature_rate = float(t_rate)
                self._temperature_approach_mode = float(t_mode)

                f_setpt, f_rate, f_mode, magnet = self.resource.query("FIELD?").split(",")
                self._field_setpoint = float(f_setpt)
                self._field_rate = float(f_rate)
                self._field_approach_mode = float(f_mode)
                self._magnet_mode = float(magnet)

                self._helium_level = float(self.resource.query("LEVEL?").split(",")[0])
            except Exception:
                sleep(1)
                continue
            else:
                return
        raise IOError("Could not read PPMS state after 5 attempts.")

    # ------------------------------------------------------------------
    # TemperatureStage interface
    # ------------------------------------------------------------------

    @property
    def temperature(self) -> float:
        """Current sample temperature in Kelvin."""
        self._update_status()
        return self._temperature

    @property
    def temperature_stable(self) -> bool:
        """True when the temperature has settled at the setpoint (within 0.2 K).

        Raises:
            IOError: If the PPMS reports an unexpected temperature-control status.
        """
        self._update_status()
        approaching = self._status.temperature in (5, 6, 7)
        far_from_setpoint = abs(self._temperature - self._temperature_setpoint) > 0.2
        if approaching or far_from_setpoint:
            return False
        if self._status.temperature in (1, 2):
            return True
        raise IOError(f"Unexpected PPMS temperature status: {self._status.temperature}")

    @property
    def temperature_setpoint(self) -> tuple[float, float, float]:
        """Current temperature setpoint as ``(value_K, rate_K_per_min, approach_mode)``."""
        self._update_status()
        return self._temperature_setpoint, self._temperature_rate, self._temperature_approach_mode

    @temperature_setpoint.setter
    def temperature_setpoint(self, setpoint: tuple) -> None:
        """Command the PPMS to ramp to a new temperature.

        Args:
            setpoint: A 3-tuple of ``(target_K, rate_K_per_min, approach_mode)``.
                ``approach_mode`` can be the integer ``0``/``1`` or the strings
                ``"fast settle"`` / ``"no overshoot"``.

        Raises:
            ValueError: If the tuple length or approach mode is invalid.
        """
        if len(setpoint) != 3:
            raise ValueError("setpoint must be (target_K, rate_K_per_min, approach_mode)")
        target, rate, mode = setpoint
        if isinstance(mode, str):
            if mode not in self._APPROACH_MODES:
                raise ValueError(f"approach_mode must be one of {list(self._APPROACH_MODES)}")
            mode = self._APPROACH_MODES[mode]
        elif mode not in (0, 1):
            raise ValueError("approach_mode integer must be 0 (fast settle) or 1 (no overshoot)")
        self.resource.write(f"TEMP {target} {rate} {mode}")

    # ------------------------------------------------------------------
    # Field control
    # ------------------------------------------------------------------

    @property
    def field(self) -> float:
        """Current magnetic field in Oersted."""
        self._update_status()
        return self._field

    @property
    def field_stable(self) -> bool:
        """True when the magnetic field has settled at the setpoint (within 2 Oe).

        Raises:
            IOError: If the PPMS reports an unexpected field-control status.
        """
        self._update_status()
        approaching = self._status.field in (2, 3, 5, 6, 7)
        far_from_setpoint = abs(self._field - self._field_setpoint) > 2
        if approaching or far_from_setpoint:
            return False
        if self._status.field in (1, 4):
            return True
        raise IOError(f"Unexpected PPMS field status: {self._status.field}")

    @property
    def field_setpoint(self) -> tuple[float, float, float, float]:
        """Current field setpoint as ``(value_Oe, rate, approach_mode, magnet_mode)``."""
        self._update_status()
        return self._field_setpoint, self._field_rate, self._field_approach_mode, self._magnet_mode

    @field_setpoint.setter
    def field_setpoint(self, setpoint: tuple) -> None:
        """Command the PPMS to ramp to a new magnetic field.

        Args:
            setpoint: A 4-tuple of ``(target_Oe, rate, approach_mode, magnet_mode)``.

        Raises:
            ValueError: If the tuple length is not 4.
        """
        if len(setpoint) != 4:
            raise ValueError("setpoint must be (target_Oe, rate, approach_mode, magnet_mode)")
        self.resource.write(f"FIELD {setpoint[0]} {setpoint[1]} {setpoint[2]} {setpoint[3]}")

    # ------------------------------------------------------------------
    # Chamber control
    # ------------------------------------------------------------------

    @property
    def chamber(self) -> int:
        """Sample chamber status code.

        Raises:
            IOError: If the status code is not a recognised chamber state.
        """
        self._update_status()
        if self._status.chamber in (1, 2, 4, 5, 8, 9):
            return self._status.chamber
        raise IOError(f"Unexpected chamber status: {self._status.chamber}")

    @chamber.setter
    def chamber(self, code: int) -> None:
        """Send a chamber command.

        Args:
            code: Integer chamber command (0–4).

        Raises:
            ValueError: If the code is out of range.
        """
        if code not in range(5):
            raise ValueError("Chamber command must be 0, 1, 2, 3, or 4")
        self.resource.write(f"CHAMBER {code}")

    def seal(self) -> None:
        """Seal the sample chamber."""
        self.chamber = 0

    def purge(self) -> None:
        """Purge the sample chamber."""
        self.chamber = 1

    def vent_seal(self) -> None:
        """Vent and seal the chamber. Only safe near room temperature.

        Raises:
            InstrumentError: If temperature is outside 290–320 K.
        """
        self._update_status()
        if not 290 <= self._temperature <= 320:
            raise InstrumentError("Temperature must be 290–320 K to vent the chamber")
        self.chamber = 2

    def pump(self) -> None:
        """Pump the sample chamber."""
        self.chamber = 3

    def vent_continuous(self) -> None:
        """Continuously vent the sample chamber. Only safe near room temperature.

        Raises:
            InstrumentError: If temperature is outside 290–320 K.
        """
        self._update_status()
        if not 290 <= self._temperature <= 320:
            raise InstrumentError("Temperature must be 290–320 K to vent the chamber")
        self.chamber = 4

    # ------------------------------------------------------------------
    # Sample position
    # ------------------------------------------------------------------

    @property
    def sample_position(self) -> int:
        """Sample position status code.

        Raises:
            IOError: If the status code is not a recognised position state.
        """
        self._update_status()
        if self._status.position in (1, 5, 8, 9):
            return self._status.position
        raise IOError(f"Unexpected sample position status: {self._status.position}")
