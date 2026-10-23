"""Submit Python calls to SLURM, optionally waiting for batch results."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import submitit


def _get_executor(project_path, num_cores, slurm_opts):
    executor = submitit.AutoExecutor(
        folder=Path(project_path) / "slurm_logs" / "%j", cluster="slurm"
    )
    executor.update_parameters(
        **{"cpus_per_task": num_cores, **(slurm_opts or {})}
    )
    return executor


def submit_slurm(
    function: Callable,
    args: tuple,
    kwargs: dict,
    project_path: str | Path,
    num_cores: int = 1,
    slurm_opts: dict | None = None,
) -> submitit.Job:
    """Submit a call and return its job handle without waiting for completion."""
    executor = _get_executor(project_path, num_cores, slurm_opts)
    return executor.submit(function, *args, **kwargs)


def run_slurm_batch(
    calls: list[tuple[Callable, tuple, dict]],
    project_path: str | Path,
    num_cores: int = 1,
    slurm_opts: dict | None = None,
) -> list[Any]:
    """Submit (function, args, kwargs) calls as an array and return ordered results.

    All calls share executor settings. Results are awaited after submission;
    a worker error is propagated when its result is retrieved.
    """
    executor = _get_executor(project_path, num_cores, slurm_opts)

    jobs = []
    with executor.batch():
        for function, args, kwargs in calls:
            jobs.append(executor.submit(function, *args, **kwargs))

    return [job.result() for job in jobs]
