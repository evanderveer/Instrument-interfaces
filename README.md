# InstrumentControl

A Python package for laboratory instrument control and measurement automation, built on [PyMeasure](https://pymeasure.readthedocs.io) and [PyVISA](https://pyvisa.readthedocs.io). Designed for cryogenic electrical characterisation experiments (impedance spectroscopy, transport measurements, etc.) with clean extension points for new instruments and measurement protocols.

---

## Table of contents

- [Installation](#installation)
- [Package overview](#package-overview)
- [Quick start](#quick-start)
- [Configuration files](#configuration-files)
- [Running a measurement](#running-a-measurement)
- [Extending the package](#extending-the-package)
  - [Adding a new instrument driver](#adding-a-new-instrument-driver)
  - [Adding a new measurement procedure](#adding-a-new-measurement-procedure)
- [Available instruments](#available-instruments)
- [Available procedures](#available-procedures)
- [Project structure](#project-structure)

---

## Installation

**Requirements:** Python 3.11 or later, a working VISA backend (e.g. [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) or [pyvisa-py](https://pyvisa-py.readthedocs.io)).

```bash
# From the repository root
pip install -e .
```

This installs `InstrumentControl` in editable mode along with its dependencies (`pyvisa`, `pymeasure`).

---

## Package overview

```
InstrumentControl/
├── instruments/          # Instrument drivers
│   ├── base.py           # Abstract base classes
│   ├── e4980a.py         # Agilent E4980A LCR meter
│   ├── ppms.py           # Quantum Design PPMS
│   ├── janis.py          # Janis probe station controller
│   ├── hp4291a.py        # HP 4291A impedance analyzer (stub)
│   ├── k4200.py          # Keithley K4200 (stub)
│   └── setup.py          # MeasurementSetup connection helper
├── procedures/           # Measurement procedures
│   ├── base.py           # ConfigurableProcedure (TOML loading)
│   ├── impedance_spectroscopy.py  # IS procedures (PPMS / Janis / constant T)
│   ├── impedance_analyzer.py      # HP 4291A sweep procedure (stub)
│   └── dummy.py          # DummyProcedure for offline testing
├── runner.py             # Measurement runner (Worker + Results)
└── config/
    └── examples/         # Example TOML configuration files
```

**Instruments** wrap a PyVISA resource and expose a clean Python API with validated properties. Each driver implements one of the abstract base classes in `instruments/base.py`, so a new driver for an equivalent piece of hardware can be swapped in without modifying any procedure code.

**Procedures** define a complete experimental protocol using [PyMeasure's `Procedure` class](https://pymeasure.readthedocs.io/en/latest/tutorial/procedure.html). Parameters (instrument addresses, sweep ranges, etc.) are declared at class level and can be set in code or loaded from a TOML config file. Each procedure follows the lifecycle `startup()` → `execute()` → `shutdown()`.

**The runner** (`Measurement`) wraps PyMeasure's `Worker` and `Results` to execute a procedure in a background thread and stream data to a CSV file.

---

## Quick start

### Programmatic configuration

```python
from InstrumentControl.procedures import ISProcedureConstTemp
from InstrumentControl.runner import Measurement

# 1. Create and configure the procedure
proc = ISProcedureConstTemp()
proc.lcr_address = "GPIB0::17::INSTR"
proc.bias_points = [0.0, 0.5, 1.0, 1.5, 2.0]           # V
proc.frequency_points = [100.0, 1e3, 10e3, 100e3, 1e6]  # Hz

# 2. Create the runner and set the output file
m = Measurement(proc)
m.filename = "results/my_measurement.csv"

# 3. Run (blocks until complete)
m.run()
```

### Loading from a config file

```python
from InstrumentControl.procedures import ISProcedurePPMS
from InstrumentControl.runner import Measurement

m = Measurement.from_config(ISProcedurePPMS, "config/examples/is_ppms.toml")
m.filename = "results/run_001.csv"
m.run()
```

### Interactive file picker

```python
m = Measurement.from_config(ISProcedurePPMS, "config/my_run.toml")
m.choose_filename()  # opens a GUI save-file dialog
m.run()
```

### Offline testing (no hardware)

```python
from InstrumentControl.procedures import DummyProcedure
from InstrumentControl.runner import Measurement

proc = DummyProcedure()
proc.number_of_measurements = 20

m = Measurement(proc)
m.filename = "test_output.csv"
m.run()
```

---

## Configuration files

All measurement parameters can be stored in a [TOML](https://toml.io) file and loaded with `Procedure.from_config()`. Config keys map directly to procedure parameter names; unknown keys are silently ignored.

**Example — `config/examples/is_ppms.toml`:**

```toml
[instruments]
ppms_address = "GPIB0::15::INSTR"
lcr_address  = "GPIB0::17::INSTR"

[measurement]
start_temperature  = 300.0        # K — settle here before the sweep
temperature_rate   = 5.0          # K/min
no_overshoot       = true         # PPMS approach mode
temperature_points = [100.0, 150.0, 200.0, 250.0, 300.0]  # K
bias_points        = [0.0, 0.5, 1.0, 1.5, 2.0]            # V
frequency_points   = [100.0, 1000.0, 10000.0, 100000.0, 1000000.0]  # Hz
```

TOML comments (`# ...`) are supported, making config files self-documenting and easy to archive alongside data files.

---

## Running a measurement

The `Measurement` class handles file management and execution:

```python
from InstrumentControl.runner import Measurement

m = Measurement(procedure)
m.filename = "data/run_001.csv"   # set output path directly …
m.choose_filename()                # … or use the GUI file picker
m.timeout = 7200                   # optional: max runtime in seconds (default 10 h)
m.run()                            # blocks until the procedure finishes
```

If the output file already exists, `Measurement` automatically appends `_1`, `_2`, etc., so existing data is never overwritten.

Output files are standard CSV with a PyMeasure header:

```
#Procedure: ISProcedurePPMS
#Parameters:
#   ppms_address: GPIB0::15::INSTR
#   ...
#Data:
Time,Bias,Frequency,Temperature,R,X
1234567890.1,0.0,100.0,100.2,1543.2,-22.4
...
```

---

## Extending the package

### Adding a new instrument driver

1. **Choose the right base class** from `InstrumentControl/instruments/base.py`:
   - `TemperatureStage` — anything that controls sample temperature
   - `LCRMeter` — LCR / impedance meters with per-point measurement
   - `ImpedanceAnalyzer` — swept impedance analyzers
   - If none fits, add a new ABC to `base.py` following the same pattern.

2. **Create a new module** in `InstrumentControl/instruments/`, e.g. `sr830.py`:

```python
# InstrumentControl/instruments/sr830.py
"""Stanford Research SR830 lock-in amplifier driver."""

from .base import LCRMeter  # or whichever ABC fits


class SR830(LCRMeter):
    """Driver for the Stanford Research SR830 lock-in amplifier."""

    INSTRUMENT_ID = "Stanford_Research_Systems,SR830,..."

    def __init__(self, address: str, resource_manager):
        self.address = address
        self.resource = resource_manager.open_resource(address, query_delay=0.1)
        # ... initialise instrument

    @property
    def frequency(self) -> float:
        return float(self.resource.query("FREQ?"))

    @frequency.setter
    def frequency(self, value: float) -> None:
        self.resource.write(f"FREQ {value}")

    @property
    def signal_amplitude(self) -> float:
        return float(self.resource.query("SLVL?"))

    @signal_amplitude.setter
    def signal_amplitude(self, value: float) -> None:
        self.resource.write(f"SLVL {value}")

    @property
    def measurement(self) -> list[float]:
        """Return [X, Y] components."""
        x = float(self.resource.query("OUTP? 1"))
        y = float(self.resource.query("OUTP? 2"))
        return [x, y]
```

3. **Register the driver** in `InstrumentControl/instruments/__init__.py`:

```python
from .sr830 import SR830

__all__ = [..., "SR830"]
```

4. The driver is now available as `from InstrumentControl.instruments import SR830` and can be used directly in any procedure's `startup()`.

---

### Adding a new measurement procedure

1. **Create a new module** in `InstrumentControl/procedures/`, e.g. `transport.py`:

```python
# InstrumentControl/procedures/transport.py
"""Four-wire resistance measurement procedure."""

from time import sleep, time

from pymeasure.experiment import FloatParameter, Parameter

from InstrumentControl.instruments.ppms import PPMS
from InstrumentControl.instruments.sr830 import SR830
from InstrumentControl.instruments.setup import MeasurementSetup

from .base import ConfigurableProcedure


class ResistancePPMS(ConfigurableProcedure):
    """Four-wire resistance vs. temperature using the PPMS and an SR830 lock-in.

    Parameters
    ----------
    ppms_address : str
        VISA address of the PPMS.
    lockin_address : str
        VISA address of the SR830 lock-in amplifier.
    temperature_rate : float
        Ramp rate in K/min.
    temperature_points : list[float]
        Target temperatures in K.
    """

    # --- Instrument addresses (shown in a GUI if one is added later) ---
    ppms_address   = Parameter("PPMS address",   default="GPIB0::15::INSTR")
    lockin_address = Parameter("Lock-in address", default="GPIB0::8::INSTR")

    # --- Scalar parameters ---
    temperature_rate = FloatParameter("Temperature rate", units="K/min", default=2.0)

    # --- List parameters (set directly or loaded from TOML) ---
    temperature_points: list = [300.0]  # K

    DATA_COLUMNS = ["Time", "Temperature", "Resistance"]

    def startup(self) -> None:
        """Connect to instruments."""
        setup = MeasurementSetup()
        setup.connect_to_devices({
            self.ppms_address:   PPMS,
            self.lockin_address: SR830,
        })
        self._ppms   = setup.devices[self.ppms_address]
        self._lockin = setup.devices[self.lockin_address]

    def execute(self) -> None:
        """Sweep temperature and record resistance at each point."""
        for temperature in self.temperature_points:
            self._ppms.temperature_setpoint = (temperature, self.temperature_rate, "no overshoot")
            while not self._ppms.temperature_stable:
                sleep(5)
            x, y = self._lockin.measurement
            resistance = x  # or compute from x, y as appropriate
            self.emit("results", {
                "Time":        time(),
                "Temperature": self._ppms.temperature,
                "Resistance":  resistance,
            })
            if self.should_stop():
                break

    def shutdown(self) -> None:
        """No specific cleanup required."""
```

2. **Register the procedure** in `InstrumentControl/procedures/__init__.py`:

```python
from .transport import ResistancePPMS

__all__ = [..., "ResistancePPMS"]
```

3. **Create a config file** (optional but recommended):

```toml
# config/my_resistance_run.toml
[instruments]
ppms_address   = "GPIB0::15::INSTR"
lockin_address = "GPIB0::8::INSTR"

[measurement]
temperature_rate   = 2.0
temperature_points = [300.0, 250.0, 200.0, 150.0, 100.0]
```

4. **Run it**:

```python
from InstrumentControl.procedures.transport import ResistancePPMS
from InstrumentControl.runner import Measurement

m = Measurement.from_config(ResistancePPMS, "config/my_resistance_run.toml")
m.filename = "results/resistance_run.csv"
m.run()
```

---

## Available instruments

| Class | Hardware | Status |
|---|---|---|
| `E4980A` | Agilent / Keysight E4980A LCR meter | Fully implemented |
| `PPMS` | Quantum Design PPMS (MultiVu GPIB) | Fully implemented |
| `Janis` | Janis / Scientific Instruments 9700 probe station | Fully implemented |
| `HP4291A` | HP 4291A impedance analyzer | Stub — triggers sweep, data parsing TODO |
| `K4200` | Keithley K4200 semiconductor analyzer | Stub — connection only |

All drivers accept `(address: str, resource_manager)` as constructor arguments and expose properties validated at the Python level before any VISA command is sent.

### `E4980A` highlights

```python
lcr = E4980A("GPIB0::17::INSTR", rm)

lcr.measurement_type  = E4980A.MeasurementType.RX   # resistance + reactance
lcr.signal_amplitude  = 0.1                          # V AC
lcr.frequency         = 10_000                       # Hz
lcr.bias              = 1.0                          # V DC

r, x = lcr.measurement  # fetch current reading
```

### `PPMS` highlights

```python
ppms = PPMS("GPIB0::15::INSTR", rm)

ppms.temperature_setpoint = (100.0, 5.0, "no overshoot")  # K, K/min, mode
while not ppms.temperature_stable:
    time.sleep(5)

ppms.field_setpoint = (10000, 100, 0, 0)  # Oe, Oe/s, approach, magnet mode
ppms.seal()   # seal sample chamber
ppms.purge()  # purge sample chamber
```

---

## Available procedures

| Class | Description | Required instruments |
|---|---|---|
| `ISProcedurePPMS` | Temperature-dependent impedance spectroscopy (PPMS) | PPMS + E4980A |
| `ISProcedureJanis` | Temperature-dependent impedance spectroscopy (Janis) | Janis + E4980A |
| `ISProcedureConstTemp` | Impedance spectroscopy at fixed temperature | E4980A only |
| `IAProcedure` | HP 4291A impedance analyzer sweep | HP4291A (stub) |
| `DummyProcedure` | Offline pipeline test (no hardware) | None |

All IS procedures emit CSV columns: `Time, Bias, Frequency, Temperature, R, X`.

---

## Project structure

```
InstrumentControl/
├── __init__.py                        # Top-level exports
├── instruments/
│   ├── __init__.py
│   ├── base.py                        # ABCs: TemperatureStage, LCRMeter, ImpedanceAnalyzer
│   ├── e4980a.py
│   ├── ppms.py
│   ├── janis.py
│   ├── hp4291a.py
│   ├── k4200.py
│   └── setup.py                       # MeasurementSetup, DummyResourceManager, DummyResource
├── procedures/
│   ├── __init__.py
│   ├── base.py                        # ConfigurableProcedure with from_config()
│   ├── impedance_spectroscopy.py
│   ├── impedance_analyzer.py
│   └── dummy.py
├── runner.py                          # Measurement class
└── config/
    └── examples/
        ├── is_ppms.toml
        ├── is_janis.toml
        └── is_const_temp.toml

pyproject.toml
README.md
```
