"""Base class for all InstrumentControl measurement procedures.

All procedures should subclass :class:`ConfigurableProcedure` instead of
:class:`pymeasure.experiment.Procedure` directly. This adds TOML-based
configuration loading on top of PyMeasure's standard procedure lifecycle.

Procedure lifecycle (PyMeasure)
--------------------------------
1. Instantiate the procedure class.
2. Set parameter values (manually or via :meth:`from_config`).
3. Pass the procedure to a :class:`~InstrumentControl.runner.Measurement` and call
   :meth:`~InstrumentControl.runner.Measurement.run`.
4. PyMeasure calls ``startup()`` → ``execute()`` → ``shutdown()`` in a worker thread.

Adding a new procedure
-----------------------
1. Subclass :class:`ConfigurableProcedure`.
2. Declare all parameters as **class-level** attributes using PyMeasure parameter
   types (``FloatParameter``, ``ListParameter``, etc.).
3. Define ``DATA_COLUMNS`` as a list of column name strings.
4. Implement ``startup()``, ``execute()``, and ``shutdown()``.
5. Inside ``execute()`` call ``self.emit('results', {...})`` with a dict whose
   keys match ``DATA_COLUMNS``.
6. Check ``self.should_stop()`` periodically to support graceful cancellation.

Example::

    class MyProcedure(ConfigurableProcedure):
        frequency = FloatParameter('Frequency', units='Hz', default=1000.0)
        DATA_COLUMNS = ['Time', 'Frequency', 'Value']

        def startup(self):
            self._instrument = MyInstrument(self.address, resource_manager)

        def execute(self):
            self._instrument.frequency = self.frequency
            value = self._instrument.measure()
            self.emit('results', {'Time': time(), 'Frequency': self.frequency, 'Value': value})

        def shutdown(self):
            self._instrument.reset()
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError as exc:
        raise ImportError(
            "Python < 3.11 requires the 'tomli' package: pip install tomli"
        ) from exc

from pymeasure.experiment import Procedure


class ConfigurableProcedure(Procedure):
    """PyMeasure :class:`~pymeasure.experiment.Procedure` with TOML config loading.

    All measurement procedures in InstrumentControl inherit from this class.
    It does not define any parameters itself; those are declared by each
    concrete subclass.
    """

    @classmethod
    def from_config(cls, config_path: str | Path) -> "ConfigurableProcedure":
        """Create a procedure instance and populate its parameters from a TOML file.

        The TOML file may contain multiple sections (e.g. ``[instruments]``,
        ``[measurement]``). Every key that matches a parameter name on the
        procedure class will be set automatically. Unknown keys are silently
        ignored, making it safe to add comments and extra fields to config files.

        Args:
            config_path: Path to the TOML configuration file.

        Returns:
            A fully configured instance of the calling procedure class.

        Raises:
            FileNotFoundError: If ``config_path`` does not exist.
            tomllib.TOMLDecodeError: If the file is not valid TOML.

        Example::

            procedure = ISProcedurePPMS.from_config("config/my_run.toml")
            measurement = Measurement(procedure)
            measurement.run()
        """
        config_path = Path(config_path)
        with config_path.open("rb") as f:
            config = tomllib.load(f)

        procedure = cls()
        for section in config.values():
            if isinstance(section, dict):
                for key, value in section.items():
                    if hasattr(procedure, key):
                        setattr(procedure, key, value)
        return procedure
