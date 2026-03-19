"""Abstract base classes for instrument drivers.

To add support for a new instrument, subclass the appropriate ABC and implement
all abstract properties/methods. Register the concrete class in instruments/__init__.py.
"""

from abc import ABC, abstractmethod


class TemperatureStage(ABC):
    """Interface for any instrument that controls sample temperature."""

    @property
    @abstractmethod
    def temperature(self) -> float:
        """Current temperature in Kelvin."""

    @property
    @abstractmethod
    def temperature_stable(self) -> bool:
        """True when temperature has settled at the setpoint."""

    @property
    @abstractmethod
    def temperature_setpoint(self):
        """Current temperature setpoint."""

    @temperature_setpoint.setter
    @abstractmethod
    def temperature_setpoint(self, setpoint):
        """Command the stage to move to a new temperature setpoint."""


class LCRMeter(ABC):
    """Interface for LCR / impedance meters."""

    @property
    @abstractmethod
    def frequency(self) -> float:
        """Measurement frequency in Hz."""

    @frequency.setter
    @abstractmethod
    def frequency(self, value: float):
        """Set measurement frequency in Hz."""

    @property
    @abstractmethod
    def signal_amplitude(self) -> float:
        """AC signal amplitude (V or A depending on signal_type)."""

    @signal_amplitude.setter
    @abstractmethod
    def signal_amplitude(self, value: float):
        """Set AC signal amplitude."""

    @property
    @abstractmethod
    def measurement(self) -> list[float]:
        """Return the two measured parameters as [primary, secondary]."""


class ImpedanceAnalyzer(ABC):
    """Interface for swept impedance analyzers (e.g. HP 4291A)."""

    @abstractmethod
    def measure(self):
        """Trigger a sweep and return raw result data."""
