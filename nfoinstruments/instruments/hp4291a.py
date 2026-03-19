"""Hewlett-Packard HP 4291A impedance analyzer driver.

.. note::
    This driver is a functional stub. The ``measure()`` method triggers a sweep
    and retrieves raw data, but parsing of that data into physical quantities is
    not yet implemented. Contributions welcome.

TODO: Parse raw sweep data into frequency, Z, phase arrays.
TODO: Add frequency sweep configuration (start, stop, number of points).
"""

from .base import ImpedanceAnalyzer


class HP4291A(ImpedanceAnalyzer):
    """Driver for the HP 4291A impedance/material analyzer.

    Communicates over GPIB using SCPI commands. Measurement is triggered
    via a service request (SRQ) handshake to ensure data is ready before
    reading.

    Example usage::

        import pyvisa
        rm = pyvisa.ResourceManager()
        ia = HP4291A("GPIB0::18::INSTR", rm)
        raw_data = ia.measure()
    """

    INSTRUMENT_ID = "HEWLETT-PACKARD,4291A,JP3KA00634,REV3.03"

    DEFAULT_SWEEP_AVERAGES = 1
    DEFAULT_POINT_AVERAGES = 1

    def __init__(self, address: str, resource_manager):
        """Connect to the HP 4291A.

        Args:
            address: VISA resource address (e.g. ``"GPIB0::18::INSTR"``).
            resource_manager: A PyVISA ``ResourceManager`` instance.
        """
        self.address = address
        self.resource = resource_manager.open_resource(address, query_delay=0.1)

    # ------------------------------------------------------------------
    # ImpedanceAnalyzer interface
    # ------------------------------------------------------------------

    def measure(self) -> str:
        """Trigger a single sweep and return the raw ASCII data string.

        The instrument is first reconfigured for a triggered single-shot
        acquisition, then an SRQ is awaited to confirm completion.

        Returns:
            Raw ASCII response from ``DATA? RAW``. Parsing into physical
            values is not yet implemented.

        TODO: Parse the returned string into structured (frequency, Z, phase) data.
        """
        self._reset_trigger()
        self._trigger()
        self.resource.wait_for_srq()
        return self.resource.query("DATA? RAW")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _reset_trigger(self) -> None:
        """Configure the instrument for a single triggered acquisition."""
        self.resource.write("TRIG:SOUR INT")
        self.resource.write("INIT:CONT OFF")
        self.resource.write("ABOR")
        self.resource.write("*SRE 4")
        self.resource.write("*CLS")

    def _trigger(self) -> None:
        """Arm and fire the trigger."""
        self.resource.write("*CLS")
        self.resource.write("INIT")
