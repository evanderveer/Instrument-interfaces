"""Measurement procedures for nfoinstruments.

Each module in this package contains one or more :class:`~pymeasure.experiment.Procedure`
subclasses that implement a specific measurement protocol. All procedures
inherit from :class:`~nfoinstruments.procedures.base.ConfigurableProcedure`,
which adds TOML-based configuration loading.

Available procedures
--------------------
- :class:`~nfoinstruments.procedures.impedance_spectroscopy.ISProcedurePPMS`
  — Temperature-dependent IS with PPMS cryostat.
- :class:`~nfoinstruments.procedures.impedance_spectroscopy.ISProcedureJanis`
  — Temperature-dependent IS with Janis probe station.
- :class:`~nfoinstruments.procedures.impedance_spectroscopy.ISProcedureConstTemp`
  — IS at fixed temperature (LCR only).
- :class:`~nfoinstruments.procedures.impedance_analyzer.IAProcedure`
  — HP 4291A impedance analyzer sweep (stub).
- :class:`~nfoinstruments.procedures.dummy.DummyProcedure`
  — Offline test procedure (no hardware required).

Adding a new procedure
-----------------------
1. Create a new module in this directory.
2. Subclass :class:`~nfoinstruments.procedures.base.ConfigurableProcedure`.
3. Declare class-level PyMeasure parameters and ``DATA_COLUMNS``.
4. Implement ``startup()``, ``execute()``, ``shutdown()``.
5. Import and expose the class in this ``__init__.py``.
"""

from .base import ConfigurableProcedure
from .impedance_spectroscopy import ISProcedurePPMS, ISProcedureJanis, ISProcedureConstTemp
from .impedance_analyzer import IAProcedure
from .dummy import DummyProcedure

__all__ = [
    "ConfigurableProcedure",
    "ISProcedurePPMS",
    "ISProcedureJanis",
    "ISProcedureConstTemp",
    "IAProcedure",
    "DummyProcedure",
]
