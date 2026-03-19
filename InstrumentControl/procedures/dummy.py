"""Dummy procedure for offline testing of the measurement pipeline.

:class:`DummyProcedure` connects to a :class:`~InstrumentControl.instruments.setup.DummyResource`
(no real hardware) and emits timestamps, making it easy to verify that the
:class:`~InstrumentControl.runner.Measurement` worker pipeline works end-to-end
without any instruments attached.
"""

from time import sleep

from pymeasure.experiment import IntegerParameter

from InstrumentControl.instruments.setup import DummyResource, MeasurementSetup

from .base import ConfigurableProcedure

_DUMMY_ADDR = "dummy://0"


class DummyProcedure(ConfigurableProcedure):
    """Offline test procedure that emits timing data without real hardware.

    Useful for verifying that the full ``Measurement`` → ``Worker`` →
    ``Results`` pipeline is functioning.

    Example::

        from InstrumentControl.procedures.dummy import DummyProcedure
        from InstrumentControl.runner import Measurement

        proc = DummyProcedure()
        proc.number_of_measurements = 10
        m = Measurement(proc)
        m.filename = "test_output.csv"
        m.run()

    Parameters
    ----------
    number_of_measurements : int
        Number of data rows to emit (default 10).
    """

    number_of_measurements = IntegerParameter("Number of measurements", default=10)

    DATA_COLUMNS = ["Number", "Time_since_init", "Time_since_start"]

    def startup(self) -> None:
        """Connect to the dummy resource and record the init time."""
        setup = MeasurementSetup(debug=True)
        setup.connect_to_devices({_DUMMY_ADDR: DummyResource})
        self._resource: DummyResource = setup.devices[_DUMMY_ADDR]
        self._init_time: float = self._resource.read()

    def execute(self) -> None:
        """Emit ``number_of_measurements`` rows of timing data."""
        start_time = self._resource.read()
        for i in range(self.number_of_measurements):
            current_time = self._resource.read()
            self.emit(
                "results",
                {
                    "Number": i,
                    "Time_since_init": current_time - self._init_time,
                    "Time_since_start": current_time - start_time,
                },
            )
            sleep(0.01)
            if self.should_stop():
                break

    def shutdown(self) -> None:
        """No-op shutdown placeholder."""
