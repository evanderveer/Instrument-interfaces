"""nfoinstruments — laboratory instrument control and measurement automation.

This package provides:

- **Instrument drivers** (:mod:`nfoinstruments.instruments`) — PyVISA-based
  drivers for scientific instruments, built on abstract base classes so new
  hardware can be added without touching existing code.
- **Measurement procedures** (:mod:`nfoinstruments.procedures`) — PyMeasure
  ``Procedure`` subclasses that implement specific experimental protocols.
  Each procedure can be configured programmatically or via a TOML file.
- **Measurement runner** (:mod:`nfoinstruments.runner`) — wraps PyMeasure's
  ``Worker`` / ``Results`` pipeline to execute procedures and save CSV data.

Quick-start example::

    from nfoinstruments.procedures import ISProcedureConstTemp
    from nfoinstruments.runner import Measurement

    # Load parameters from a config file and run
    m = Measurement.from_config(ISProcedureConstTemp, "config/examples/is_const_temp.toml")
    m.filename = "results/my_run.csv"
    m.run()
"""

from nfoinstruments.instruments import (
    E4980A,
    HP4291A,
    ImpedanceAnalyzer,
    InstrumentError,
    Janis,
    K4200,
    LCRMeter,
    MeasurementSetup,
    PPMS,
    TemperatureStage,
)
from nfoinstruments.procedures import (
    ConfigurableProcedure,
    DummyProcedure,
    IAProcedure,
    ISProcedureConstTemp,
    ISProcedureJanis,
    ISProcedurePPMS,
)
from nfoinstruments.runner import Measurement

__all__ = [
    # Instruments
    "TemperatureStage",
    "LCRMeter",
    "ImpedanceAnalyzer",
    "E4980A",
    "PPMS",
    "Janis",
    "HP4291A",
    "K4200",
    "MeasurementSetup",
    "InstrumentError",
    # Procedures
    "ConfigurableProcedure",
    "ISProcedurePPMS",
    "ISProcedureJanis",
    "ISProcedureConstTemp",
    "IAProcedure",
    "DummyProcedure",
    # Runner
    "Measurement",
]
