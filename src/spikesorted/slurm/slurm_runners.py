from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import submitit


def _get_executor(log_path: Path, slurm_opts: dict) -> submitit.AutoExecutor:
    """Return the executor defining requested SLURM node parameters and log path.

    Parameters
    ----------
    log_path
        Path to log the SLURM output to.

    slurm_opts
        The slurm options to run.

    Returns
    -------
    executor
        submitit executor object defining requested SLURM node parameters.

    """
    executor = submitit.AutoExecutor(
        folder=log_path, cluster="slurm"
    )

    executor.update_parameters(**slurm_opts)

    return executor


def submit_slurm(
    function: Callable,
    args: tuple,
    kwargs: dict,
    output_path: str | Path,
    num_cores: int = 1,
    slurm_opts: dict | None = None,
) -> submitit.Job:
    """Submit a call and return its job handle without waiting for completion."""
    executor = _get_executor(
        Path(output_path) / "slurm_logs" / "%j",
        {"cpus_per_task": num_cores, **(slurm_opts or {})},
    )
    return executor.submit(function, *args, **kwargs)


def run_slurm_batch(
    calls: list[tuple[Callable, tuple, dict]],
    output_path: str | Path,
    num_cores: int = 1,
    slurm_opts: dict | None = None,
) -> list[Any]:
    """Submit (function, args, kwargs) calls as an array and return ordered results.

    All calls share executor settings. Results are awaited after submission;
    a worker error is propagated when its result is retrieved.
    """
    executor = _get_executor(
        Path(output_path) / "slurm_logs" / "%j",
        {"cpus_per_task": num_cores, **(slurm_opts or {})},
    )

    jobs = []
    with executor.batch():
        for function, args, kwargs in calls:
            jobs.append(executor.submit(function, *args, **kwargs))

    return [job.result() for job in jobs]
