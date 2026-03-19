"""Instrument connection management.

``MeasurementSetup`` discovers available VISA resources and connects to
instrument driver instances by address. ``DummyResourceManager`` and
``DummyResource`` provide hardware-free substitutes for unit testing and
offline development.
"""

import pyvisa


class InstrumentError(Exception):
    """Raised when an instrument reports an error or cannot be reached."""

    def __str__(self) -> str:
        return f"InstrumentError: {super().__str__()}"


class MeasurementSetup:
    """Manages VISA resource discovery and instrument connections.

    Usage::

        from nfoinstruments.instruments.setup import MeasurementSetup
        from nfoinstruments.instruments.e4980a import E4980A

        setup = MeasurementSetup()
        setup.connect_to_devices({"GPIB0::17::INSTR": E4980A})
        lcr = setup.devices["GPIB0::17::INSTR"]
    """

    def __init__(self, debug: bool = False):
        """Initialise and discover available VISA resources.

        Args:
            debug: When ``True`` a :class:`DummyResourceManager` is used so
                the class can be instantiated without any hardware attached.

        Raises:
            InstrumentError: If no VISA resources are found in normal mode.
        """
        self.resources: list[str] = []
        self.devices: dict = {}

        if debug:
            self._resman = DummyResourceManager()
            return

        self._resman = pyvisa.ResourceManager()
        self._discover_resources()

        if not self.resources:
            raise InstrumentError("No VISA devices found")

        print("Available VISA resources:", self.resources)

    def _discover_resources(self) -> None:
        """Probe each listed VISA address to confirm it is reachable."""
        for addr in self._resman.list_resources():
            try:
                self._resman.open_resource(addr).close()
                self.resources.append(addr)
            except pyvisa.errors.VisaIOError:
                continue

    def connect_to_devices(self, address_map: dict) -> None:
        """Instantiate instrument drivers for the given address → class mapping.

        Args:
            address_map: Dict mapping VISA address strings to driver classes,
                e.g. ``{"GPIB0::17::INSTR": E4980A}``.

        Any address that fails to connect is reported but does not raise; the
        corresponding key will be absent from :attr:`devices`.
        """
        for addr, driver_cls in address_map.items():
            try:
                self.devices[addr] = driver_cls(addr, self._resman)
            except Exception as exc:
                print(f"Could not connect to {driver_cls.__name__} at {addr}: {exc}")


class DummyResourceManager:
    """Drop-in replacement for :class:`pyvisa.ResourceManager` for offline testing.

    Returns :class:`DummyResource` instances and reports no physical resources.
    """

    def list_resources(self) -> tuple:
        """Return an empty resource list."""
        return ()

    def open_resource(self, addr: str, **kwargs) -> "DummyResource":
        """Return a :class:`DummyResource` regardless of address.

        Args:
            addr: Ignored.
            **kwargs: Ignored.
        """
        return DummyResource(addr, self)


class DummyResource:
    """Minimal stand-in for a PyVISA resource, useful for testing procedures.

    ``read()`` returns the current ``time.time()`` value so that timing-based
    logic can be exercised without real hardware.
    """

    def __init__(self, address: str, resource_manager: DummyResourceManager, **kwargs):
        """Create a DummyResource.

        Args:
            address: Stored for reference.
            resource_manager: The manager that created this resource.
            **kwargs: Absorbed and ignored.
        """
        self.address = address
        self._resman = resource_manager

    def read(self) -> float:
        """Return the current wall-clock time as a float.

        Returns:
            ``time.time()`` value in seconds since the epoch.
        """
        from time import time
        return time()

    def write(self, command: str) -> None:
        """Silently discard a write command.

        Args:
            command: SCPI command string (ignored).
        """

    def query(self, command: str) -> str:
        """Return an empty string for any query.

        Args:
            command: SCPI query string (ignored).

        Returns:
            Empty string.
        """
        return ""

    def close(self) -> None:
        """No-op close."""
