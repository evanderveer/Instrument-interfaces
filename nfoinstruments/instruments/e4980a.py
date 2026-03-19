"""Agilent / Keysight E4980A LCR meter driver."""

from enum import Enum, auto
from pprint import pprint

from .base import LCRMeter


class E4980A(LCRMeter):
    """Driver for the Agilent E4980A precision LCR meter.

    Connects via PyVISA. All instrument settings are validated before being
    written to the hardware and cached locally to avoid unnecessary queries.

    Example usage::

        import pyvisa
        rm = pyvisa.ResourceManager()
        lcr = E4980A("GPIB0::17::INSTR", rm)
        lcr.frequency = 10_000        # 10 kHz
        lcr.bias = 1.0                # 1 V DC bias
        r, x = lcr.measurement        # read R and X
    """

    INSTRUMENT_ID = r"Agilent Technologies,E4980A,.+"

    class SignalType(Enum):
        VOLTAGE = auto()
        CURRENT = auto()

    class MeasurementTime(Enum):
        SHORT = "SHOR"
        MEDIUM = "MED"
        LONG = "LONG"

    class MeasurementType(Enum):
        CPD = "CPD"
        CPQ = "CPQ"
        CPG = "CPG"
        CPRP = "CPRP"
        CSD = "CSD"
        CSQ = "CSQ"
        CSRS = "CSRS"
        LPD = "LPD"
        LPQ = "LPQ"
        LPG = "LPG"
        LPRD = "LPRD"
        LSD = "LSD"
        LSQ = "LSQ"
        LSRD = "LSRD"
        LSRS = "LSRS"
        RX = "RX"
        ZTD = "ZTD"
        ZTR = "ZTR"
        GB = "GB"
        YTD = "YTD"
        YTR = "YTR"
        VDID = "VDID"

    # Defaults applied on every reset
    DEFAULT_AVERAGES = 1
    DEFAULT_BIAS = 0.0
    DEFAULT_FREQUENCY = 100.0
    DEFAULT_SIGNAL_AMPLITUDE = 1.0
    DEFAULT_MEASUREMENT_TIMEOUT = 3       # seconds
    DEFAULT_ALC_ENABLED = True
    DEFAULT_MEASUREMENT_TYPE = MeasurementType.RX
    DEFAULT_SIGNAL_TYPE = SignalType.VOLTAGE
    DEFAULT_MEASUREMENT_TIME = MeasurementTime.MEDIUM

    def __init__(self, address: str, resource_manager):
        self.address = address
        self.resource = resource_manager.open_resource(address, query_delay=0.1)
        self.reset()
        self.print_status()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def reset(self, keep_settings: bool = False) -> None:
        """Reset the instrument to default (or current) settings.

        Args:
            keep_settings: When True the cached parameter values are kept and
                only the hardware state is re-applied. Useful after a power
                cycle without changing the measurement configuration.
        """
        if not keep_settings:
            self._measurement_time = self.DEFAULT_MEASUREMENT_TIME
            self._averages = self.DEFAULT_AVERAGES
            self._bias = self.DEFAULT_BIAS
            self._frequency = self.DEFAULT_FREQUENCY
            self._measurement_type = self.DEFAULT_MEASUREMENT_TYPE
            self._signal_amplitude = self.DEFAULT_SIGNAL_AMPLITUDE
            self._measurement_timeout = self.DEFAULT_MEASUREMENT_TIMEOUT
            self._signal_type = self.DEFAULT_SIGNAL_TYPE
            self._alc_enabled = self.DEFAULT_ALC_ENABLED
        self._apply_settings()

    def _apply_settings(self) -> None:
        """Write all cached settings to the hardware."""
        self.resource.clear()
        self.resource.write("*RST")
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")
        self.resource.write("BIAS:STAT OFF")
        self.resource.write(f"BIAS:VOLT {self._bias}")
        self.resource.write(f"FREQ {self._frequency}")
        self.resource.write(f"VOLT {self._signal_amplitude}")
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type.value}")
        self.resource.write("INIT:CONT ON")
        self.resource.write("AMPL:ALC ON")
        self.resource.write("FORMAT ASCII")
        # Disable all corrections
        self.resource.write("CORR:OPEN:STAT OFF")
        self.resource.write("CORR:SHORT:STAT OFF")
        self.resource.write("CORR:LOAD:STAT OFF")
        self.resource.write("CORR:LENG 0")
        self.resource.timeout = self._measurement_timeout * 1000  # s → ms

    def print_status(self) -> None:
        """Print the current instrument state to stdout."""
        pprint(vars(self))

    # ------------------------------------------------------------------
    # Measurement time & averaging
    # ------------------------------------------------------------------

    @property
    def measurement_time(self) -> MeasurementTime:
        return self._measurement_time

    @measurement_time.setter
    def measurement_time(self, value: MeasurementTime) -> None:
        if not isinstance(value, E4980A.MeasurementTime):
            raise ValueError("measurement_time must be a MeasurementTime enum value")
        self._measurement_time = value
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")

    @property
    def averages(self) -> int:
        return self._averages

    @averages.setter
    def averages(self, value: int) -> None:
        if not 1 <= value <= 256:
            raise ValueError("averages must be between 1 and 256")
        self._averages = value
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")

    # ------------------------------------------------------------------
    # Bias
    # ------------------------------------------------------------------

    @property
    def bias(self) -> float:
        return self._bias

    @bias.setter
    def bias(self, value: float) -> None:
        if self._signal_type == E4980A.SignalType.VOLTAGE:
            if not -40.0 <= value <= 40.0:
                raise ValueError("voltage bias must be between -40 V and +40 V")
            self._bias = value
            if value == 0.0:
                self.resource.write("BIAS:STAT OFF")
                self.resource.write(f"BIAS:VOLT {self._bias}")
            else:
                self.resource.write(f"BIAS:VOLT {self._bias}")
                self.resource.write("BIAS:STAT ON")
        else:
            if not -0.1 <= value <= 0.1:
                raise ValueError("current bias must be between -0.1 A and +0.1 A")
            self._bias = value
            if value == 0.0:
                self.resource.write("BIAS:STAT OFF")
                self.resource.write(f"BIAS:CURR {self._bias}")
            else:
                self.resource.write(f"BIAS:CURR {self._bias}")
                self.resource.write("BIAS:STAT ON")

    # ------------------------------------------------------------------
    # Frequency
    # ------------------------------------------------------------------

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        if not 20.0 <= value <= 2_000_000.0:
            raise ValueError("frequency must be between 20 Hz and 2 MHz")
        self._frequency = value
        self.resource.write(f"FREQ {self._frequency}")

    # ------------------------------------------------------------------
    # Measurement type
    # ------------------------------------------------------------------

    @property
    def measurement_type(self) -> MeasurementType:
        return self._measurement_type

    @measurement_type.setter
    def measurement_type(self, value: MeasurementType) -> None:
        if not isinstance(value, E4980A.MeasurementType):
            raise ValueError("measurement_type must be a MeasurementType enum value")
        self._measurement_type = value
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type.value}")

    # ------------------------------------------------------------------
    # Signal amplitude & type
    # ------------------------------------------------------------------

    @property
    def signal_amplitude(self) -> float:
        return self._signal_amplitude

    @signal_amplitude.setter
    def signal_amplitude(self, value: float) -> None:
        if self._signal_type == E4980A.SignalType.VOLTAGE:
            if not 0.0 <= value <= 20.0:
                raise ValueError("voltage signal amplitude must be between 0 and 20 V")
            self._signal_amplitude = value
            self.resource.write(f"VOLT {self._signal_amplitude}")
        else:
            if not 0.0 <= value <= 0.1:
                raise ValueError("current signal amplitude must be between 0 and 0.1 A")
            self._signal_amplitude = value
            self.resource.write(f"CURR {self._signal_amplitude}")

    @property
    def signal_type(self) -> SignalType:
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value: SignalType) -> None:
        if not isinstance(value, E4980A.SignalType):
            raise ValueError("signal_type must be a SignalType enum value")
        self._signal_type = value

    # ------------------------------------------------------------------
    # ALC
    # ------------------------------------------------------------------

    @property
    def alc_enabled(self) -> bool:
        return self._alc_enabled

    @alc_enabled.setter
    def alc_enabled(self, value: bool) -> None:
        self._alc_enabled = bool(value)
        self.resource.write("AMPL:ALC ON" if self._alc_enabled else "AMPL:ALC OFF")

    # ------------------------------------------------------------------
    # Measurement
    # ------------------------------------------------------------------

    @property
    def measurement(self) -> list[float]:
        """Fetch the current measurement result.

        Returns:
            [primary, secondary] as floats, matching the active MeasurementType.
        """
        raw = self.resource.query("FETCH?").split(",")[:2]
        return [float(v) for v in raw]
