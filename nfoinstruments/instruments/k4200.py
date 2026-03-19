"""Keithley K4200 semiconductor characterization system driver.

.. note::
    This driver is a stub. Only the VISA connection is established;
    no measurement commands are implemented yet.

TODO: Implement SMU channel configuration and IV-sweep commands.
TODO: Implement CV measurement commands.
"""


class K4200:
    """Driver stub for the Keithley K4200 semiconductor parameter analyzer.

    Example usage (once implemented)::

        import pyvisa
        rm = pyvisa.ResourceManager()
        k4200 = K4200("GPIB0::22::INSTR", rm)
        # TODO: call measurement methods here

    TODO: Implement full driver inheriting from a suitable base class.
    """

    def __init__(self, address: str, resource_manager):
        """Connect to the K4200.

        Args:
            address: VISA resource address (e.g. ``"GPIB0::22::INSTR"``).
            resource_manager: A PyVISA ``ResourceManager`` instance.
        """
        self.address = address
        self.resource = resource_manager.open_resource(address, query_delay=0.1)
