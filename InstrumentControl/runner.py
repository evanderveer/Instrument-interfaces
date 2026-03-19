"""Measurement runner — executes a procedure and saves results to disk.

:class:`Measurement` wraps PyMeasure's :class:`~pymeasure.experiment.Worker`
and :class:`~pymeasure.experiment.Results` to run a
:class:`~InstrumentControl.procedures.base.ConfigurableProcedure` in a background
thread and stream data to a CSV file.

Typical usage::

    from InstrumentControl.procedures import ISProcedureConstTemp
    from InstrumentControl.runner import Measurement

    # Option A: configure manually
    proc = ISProcedureConstTemp()
    proc.lcr_address = "GPIB0::17::INSTR"
    proc.bias_points = [0.0, 1.0, 2.0]
    proc.frequency_points = [100.0, 1000.0, 10000.0]
    m = Measurement(proc)
    m.filename = "my_measurement.csv"
    m.run()

    # Option B: load everything from a TOML config file
    m = Measurement.from_config(ISProcedureConstTemp, "config/my_run.toml")
    m.choose_filename()   # opens a GUI file-picker dialog
    m.run()
"""

from __future__ import annotations

import os
from pathlib import Path

import tkinter
from tkinter import filedialog

from pymeasure.experiment import Results, Worker

from InstrumentControl.procedures.base import ConfigurableProcedure


def _increment_filename(path: str) -> str:
    """Return ``path`` (or a suffixed variant) that does not already exist.

    If ``path`` is ``"data.csv"`` and that file exists, returns
    ``"data_1.csv"``, ``"data_2.csv"``, etc.

    Args:
        path: Desired output file path.

    Returns:
        A file path string guaranteed not to exist on disk.
    """
    base, ext = os.path.splitext(path)
    candidate = path
    counter = 1
    while os.path.exists(candidate):
        candidate = f"{base}_{counter}{ext}"
        counter += 1
    return candidate


class Measurement:
    """Runs a :class:`~InstrumentControl.procedures.base.ConfigurableProcedure` and saves results.

    The procedure executes in a background :class:`~pymeasure.experiment.Worker`
    thread; this object blocks in :meth:`run` until the worker finishes or the
    timeout elapses.

    Args:
        procedure: A fully configured procedure instance ready to execute.

    Attributes:
        filename: Output CSV path. Must be set before calling :meth:`run`.
        timeout: Maximum time in seconds to wait for the worker (default 10 h).
    """

    DEFAULT_TIMEOUT = 36_000  # 10 hours in seconds

    def __init__(self, procedure: ConfigurableProcedure):
        self._procedure = procedure
        self.filename: str | None = None
        self.timeout: int = self.DEFAULT_TIMEOUT

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def from_config(
        procedure_cls: type[ConfigurableProcedure],
        config_path: str | Path,
    ) -> "Measurement":
        """Create a :class:`Measurement` with parameters loaded from a TOML file.

        Args:
            procedure_cls: The procedure class to instantiate
                (e.g. :class:`~InstrumentControl.procedures.ISProcedurePPMS`).
            config_path: Path to the TOML configuration file.

        Returns:
            A :class:`Measurement` instance ready for :meth:`choose_filename`
            and :meth:`run`.

        Example::

            m = Measurement.from_config(ISProcedurePPMS, "config/my_run.toml")
            m.filename = "results/run_001.csv"
            m.run()
        """
        procedure = procedure_cls.from_config(config_path)
        return Measurement(procedure)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def choose_filename(self) -> None:
        """Open a GUI file-picker dialog to select the output CSV path.

        The chosen path is stored in :attr:`filename`. If the user cancels the
        dialog without choosing a file, :attr:`filename` is left unchanged.
        """
        root = tkinter.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            parent=root,
            initialdir=os.getcwd(),
            title="Select output file",
            confirmoverwrite=False,
            filetypes=[("CSV file", ".csv"), ("Text file", ".txt")],
            defaultextension=".csv",
        )
        root.destroy()
        if path:
            self.filename = path

    def run(self) -> None:
        """Execute the procedure and block until it finishes.

        The output file path is auto-incremented if a file with :attr:`filename`
        already exists, so existing data is never overwritten.

        Raises:
            RuntimeError: If :attr:`filename` has not been set.
        """
        if self.filename is None:
            raise RuntimeError(
                "No output filename set. Assign `measurement.filename` or call "
                "`measurement.choose_filename()` first."
            )
        output_path = _increment_filename(self.filename)
        results = Results(self._procedure, output_path)
        worker = Worker(results)
        worker.start()
        worker.join(timeout=self.timeout)
