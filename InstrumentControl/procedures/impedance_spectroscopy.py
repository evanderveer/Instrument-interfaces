"""Impedance spectroscopy measurement procedures.

Three procedure variants are provided:

- :class:`ISProcedurePPMS` — temperature-dependent IS using the PPMS cryostat.
- :class:`ISProcedureJanis` — temperature-dependent IS using the Janis probe station.
- :class:`ISProcedureConstTemp` — IS at a fixed temperature (LCR only, no stage).

All procedures inherit from :class:`~nfoinstruments.procedures.base.ConfigurableProcedure`
and follow the standard PyMeasure procedure lifecycle (``startup`` → ``execute``
→ ``shutdown``). Parameters are declared as class-level descriptors so they are
automatically discovered by PyMeasure's GUI infrastructure if needed.

Data columns emitted: ``Time``, ``Bias``, ``Frequency``, ``Temperature``, ``R``, ``X``.

Configuration
-------------
All parameters can be set programmatically or loaded from a TOML file via
:meth:`~nfoinstruments.procedures.base.ConfigurableProcedure.from_config`.
See ``config/examples/is_ppms.toml`` for a reference configuration.
"""

from time import sleep, time

from pymeasure.experiment import (
    BooleanParameter,
    FloatParameter,
    Parameter,
)

from nfoinstruments.instruments.e4980a import E4980A
from nfoinstruments.instruments.janis import Janis
from nfoinstruments.instruments.ppms import PPMS
from nfoinstruments.instruments.setup import MeasurementSetup

from .base import ConfigurableProcedure


class ISProcedurePPMS(ConfigurableProcedure):
    """Temperature-dependent impedance spectroscopy using the PPMS as the cryostat.

    The measurement sweeps through a list of temperatures. At each temperature
    it waits for stabilisation, then sweeps bias and frequency, recording the
    LCR output at every (bias, frequency) point.

    Parameters
    ----------
    All parameters below can be set as attributes or loaded from a TOML file.

    ppms_address : str
        VISA address of the PPMS (e.g. ``"GPIB0::15::INSTR"``).
    lcr_address : str
        VISA address of the LCR meter (e.g. ``"GPIB0::17::INSTR"``).
    start_temperature : float
        Temperature to settle at before beginning the sweep (K).
    temperature_rate : float
        Ramp rate used when moving between temperature setpoints (K/min).
    no_overshoot : bool
        When ``True`` the PPMS uses "no overshoot" approach mode; otherwise
        "fast settle".
    temperature_points : list[float]
        Ordered list of target temperatures in K.
    bias_points : list[float]
        DC bias voltages to apply at each temperature point (V).
    frequency_points : list[float]
        AC frequencies to measure at each (temperature, bias) point (Hz).
    """

    # ------------------------------------------------------------------ #
    # Instrument addresses                                                 #
    # ------------------------------------------------------------------ #
    ppms_address = Parameter("PPMS GPIB address", default="GPIB0::15::INSTR")
    lcr_address = Parameter("LCR GPIB address", default="GPIB0::17::INSTR")

    # ------------------------------------------------------------------ #
    # Scalar PyMeasure parameters (visible in a GUI if one is added)     #
    # ------------------------------------------------------------------ #
    start_temperature = FloatParameter("Start temperature", units="K", default=300.0)
    temperature_rate = FloatParameter("Temperature rate", units="K/min", default=5.0)
    no_overshoot = BooleanParameter("No overshoot approach", default=True)

    # ------------------------------------------------------------------ #
    # List parameters — set as regular attributes or loaded from config  #
    # PyMeasure's ListParameter is for fixed-choice dropdowns, not       #
    # arbitrary point lists, so these use plain Python class attributes. #
    # ------------------------------------------------------------------ #
    temperature_points: list = [300.0]   # K
    bias_points: list = [0.0]            # V
    frequency_points: list = [1000.0]   # Hz

    DATA_COLUMNS = ["Time", "Bias", "Frequency", "Temperature", "R", "X"]

    # ------------------------------------------------------------------ #
    # Procedure lifecycle                                                  #
    # ------------------------------------------------------------------ #

    def startup(self) -> None:
        """Connect to the PPMS and LCR meter.

        Called automatically by PyMeasure before ``execute()``.
        """
        setup = MeasurementSetup()
        setup.connect_to_devices(
            {self.ppms_address: PPMS, self.lcr_address: E4980A}
        )
        self._ppms: PPMS = setup.devices[self.ppms_address]
        self._lcr: E4980A = setup.devices[self.lcr_address]

    def execute(self) -> None:
        """Run the full temperature–bias–frequency sweep.

        Emits one ``results`` row per (temperature, bias, frequency) point.
        Respects :meth:`should_stop` at each temperature step.
        """
        self._settle_at_start_temperature()

        approach = "no overshoot" if self.no_overshoot else "fast settle"
        for temperature in self.temperature_points:
            self._ppms.temperature_setpoint = (temperature, self.temperature_rate, approach)
            self._wait_for_temperature()
            self._scan_bias()
            if self.should_stop():
                break

    def shutdown(self) -> None:
        """Return the LCR to a safe state (zero bias) after the measurement.

        Called automatically by PyMeasure after ``execute()`` completes or is
        stopped.
        """
        if hasattr(self, "_lcr"):
            self._lcr.bias = 0.0

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _settle_at_start_temperature(self) -> None:
        """Ramp quickly to :attr:`start_temperature` and wait for stability."""
        self._ppms.temperature_setpoint = (self.start_temperature, 20.0, "fast settle")
        self._wait_for_temperature()

    def _wait_for_temperature(self) -> None:
        """Block until the PPMS reports a stable temperature."""
        while not self._ppms.temperature_stable:
            sleep(5)

    def _scan_bias(self) -> None:
        """Sweep :attr:`bias_points` and run a frequency scan at each bias."""
        for bias in self.bias_points:
            self._lcr.bias = bias
            sleep(0.1)
            self._scan_frequency()

    def _scan_frequency(self) -> None:
        """Sweep :attr:`frequency_points` and emit one data row per point."""
        for frequency in self.frequency_points:
            self._lcr.frequency = frequency
            sleep(0.1)
            self._emit_data()
            if self.should_stop():
                return

    def _emit_data(self) -> None:
        """Read the LCR and PPMS and emit one result row."""
        r_val, x_val = self._lcr.measurement
        self.emit(
            "results",
            {
                "Time": time(),
                "Bias": self._lcr.bias,
                "Frequency": self._lcr.frequency,
                "Temperature": self._ppms.temperature,
                "R": r_val,
                "X": x_val,
            },
        )


class ISProcedureJanis(ConfigurableProcedure):
    """Temperature-dependent impedance spectroscopy using the Janis probe station.

    Identical sweep logic to :class:`ISProcedurePPMS` but uses the Janis
    temperature controller instead of the PPMS.

    Parameters
    ----------
    janis_address : str
        VISA address of the Janis controller.
    lcr_address : str
        VISA address of the LCR meter.
    temperature_points : list[float]
        Ordered list of target temperatures in K.
    bias_points : list[float]
        DC bias voltages (V).
    frequency_points : list[float]
        AC frequencies (Hz).
    """

    janis_address = Parameter("Janis GPIB address", default="GPIB0::12::INSTR")
    lcr_address = Parameter("LCR GPIB address", default="GPIB0::17::INSTR")

    temperature_points: list = [300.0]   # K
    bias_points: list = [0.0]            # V
    frequency_points: list = [1000.0]   # Hz

    DATA_COLUMNS = ["Time", "Bias", "Frequency", "Temperature", "R", "X"]

    def startup(self) -> None:
        """Connect to the Janis controller and LCR meter."""
        setup = MeasurementSetup()
        setup.connect_to_devices(
            {self.janis_address: Janis, self.lcr_address: E4980A}
        )
        self._janis: Janis = setup.devices[self.janis_address]
        self._lcr: E4980A = setup.devices[self.lcr_address]

    def execute(self) -> None:
        """Run the full temperature–bias–frequency sweep."""
        for temperature in self.temperature_points:
            self._janis.temperature_setpoint = temperature
            self._wait_for_temperature()
            self._scan_bias()
            if self.should_stop():
                break

    def shutdown(self) -> None:
        """Return the LCR to zero bias."""
        if hasattr(self, "_lcr"):
            self._lcr.bias = 0.0

    def _wait_for_temperature(self) -> None:
        """Block until the Janis controller reports a stable temperature."""
        while not self._janis.temperature_stable:
            sleep(10)

    def _scan_bias(self) -> None:
        for bias in self.bias_points:
            self._lcr.bias = bias
            sleep(0.1)
            self._scan_frequency()

    def _scan_frequency(self) -> None:
        for frequency in self.frequency_points:
            self._lcr.frequency = frequency
            sleep(0.1)
            self._emit_data()
            if self.should_stop():
                return

    def _emit_data(self) -> None:
        r_val, x_val = self._lcr.measurement
        self.emit(
            "results",
            {
                "Time": time(),
                "Bias": self._lcr.bias,
                "Frequency": self._lcr.frequency,
                "Temperature": self._janis.temperature,
                "R": r_val,
                "X": x_val,
            },
        )


class ISProcedureConstTemp(ConfigurableProcedure):
    """Impedance spectroscopy at constant temperature (LCR only, no stage).

    Performs a bias–frequency sweep without controlling temperature. Useful
    when the sample environment is handled externally, or when room-temperature
    measurements are sufficient.

    Parameters
    ----------
    lcr_address : str
        VISA address of the LCR meter.
    bias_points : list[float]
        DC bias voltages (V).
    frequency_points : list[float]
        AC frequencies (Hz).
    """

    lcr_address = Parameter("LCR GPIB address", default="GPIB0::17::INSTR")

    bias_points: list = [0.0]          # V
    frequency_points: list = [1000.0]  # Hz

    DATA_COLUMNS = ["Time", "Bias", "Frequency", "R", "X"]

    def startup(self) -> None:
        """Connect to the LCR meter."""
        setup = MeasurementSetup()
        setup.connect_to_devices({self.lcr_address: E4980A})
        self._lcr: E4980A = setup.devices[self.lcr_address]

    def execute(self) -> None:
        """Run the bias–frequency sweep at the current (fixed) temperature."""
        self._scan_bias()

    def shutdown(self) -> None:
        """Return the LCR to zero bias."""
        if hasattr(self, "_lcr"):
            self._lcr.bias = 0.0

    def _scan_bias(self) -> None:
        for bias in self.bias_points:
            self._lcr.bias = bias
            sleep(0.1)
            self._scan_frequency()

    def _scan_frequency(self) -> None:
        for frequency in self.frequency_points:
            self._lcr.frequency = frequency
            sleep(0.1)
            self._emit_data()
            if self.should_stop():
                return

    def _emit_data(self) -> None:
        r_val, x_val = self._lcr.measurement
        self.emit(
            "results",
            {
                "Time": time(),
                "Bias": self._lcr.bias,
                "Frequency": self._lcr.frequency,
                "R": r_val,
                "X": x_val,
            },
        )
