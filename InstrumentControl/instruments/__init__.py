"""Instrument drivers for nfoinstruments.

Each module in this package contains a driver for a specific piece of
laboratory equipment. All drivers implement one of the abstract base classes
defined in :mod:`nfoinstruments.instruments.base`.

Available drivers
-----------------
- :class:`~nfoinstruments.instruments.e4980a.E4980A` — Agilent E4980A LCR meter (fully implemented)
- :class:`~nfoinstruments.instruments.ppms.PPMS` — Quantum Design PPMS (fully implemented)
- :class:`~nfoinstruments.instruments.janis.Janis` — Janis probe station controller (fully implemented)
- :class:`~nfoinstruments.instruments.hp4291a.HP4291A` — HP 4291A impedance analyzer (stub)
- :class:`~nfoinstruments.instruments.k4200.K4200` — Keithley K4200 (stub)

Connection helpers
------------------
- :class:`~nfoinstruments.instruments.setup.MeasurementSetup` — VISA resource discovery and connection
- :class:`~nfoinstruments.instruments.setup.DummyResourceManager` — offline testing
- :class:`~nfoinstruments.instruments.setup.DummyResource` — offline testing
"""

from .base import TemperatureStage, LCRMeter, ImpedanceAnalyzer
from .e4980a import E4980A
from .ppms import PPMS
from .janis import Janis
from .hp4291a import HP4291A
from .k4200 import K4200
from .setup import MeasurementSetup, DummyResourceManager, DummyResource, InstrumentError

__all__ = [
    "TemperatureStage",
    "LCRMeter",
    "ImpedanceAnalyzer",
    "E4980A",
    "PPMS",
    "Janis",
    "HP4291A",
    "K4200",
    "MeasurementSetup",
    "DummyResourceManager",
    "DummyResource",
    "InstrumentError",
]
