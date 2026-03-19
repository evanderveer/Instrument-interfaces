"""Impedance analyzer measurement procedure (HP 4291A).

.. note::
    This procedure is a stub. The ``execute()`` method triggers a sweep but
    does not yet parse or emit any data. Contributions welcome.

TODO: Parse the raw sweep data returned by :meth:`~nfoinstruments.instruments.hp4291a.HP4291A.measure`
      into (frequency, Z, phase) arrays and emit them row by row.
TODO: Add parameters for sweep range and averaging.
"""

from pymeasure.experiment import Parameter

from nfoinstruments.instruments.hp4291a import HP4291A
from nfoinstruments.instruments.setup import MeasurementSetup

from .base import ConfigurableProcedure


class IAProcedure(ConfigurableProcedure):
    """Swept impedance measurement using the HP 4291A impedance analyzer.

    TODO: Implement data emission once raw sweep data parsing is complete.

    Parameters
    ----------
    ia_address : str
        VISA address of the HP 4291A (e.g. ``"GPIB0::18::INSTR"``).
    """

    ia_address = Parameter("HP 4291A GPIB address", default="GPIB0::18::INSTR")

    # TODO: Add DATA_COLUMNS once the output format is defined.
    DATA_COLUMNS: list[str] = []

    def startup(self) -> None:
        """Connect to the HP 4291A impedance analyzer."""
        setup = MeasurementSetup()
        setup.connect_to_devices({self.ia_address: HP4291A})
        self._ia: HP4291A = setup.devices[self.ia_address]

    def execute(self) -> None:
        """Trigger a sweep. Data parsing and emission not yet implemented.

        TODO: Parse ``raw_data`` and emit rows matching ``DATA_COLUMNS``.
        """
        raw_data = self._ia.measure()
        # TODO: parse raw_data and call self.emit('results', {...})

    def shutdown(self) -> None:
        """No-op shutdown placeholder."""
