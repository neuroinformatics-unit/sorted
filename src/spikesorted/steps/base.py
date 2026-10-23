"""Shared step inputs from the SPEC's implementation interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict
from spikeinterface.core import BaseRecording

from ..utils import get_recordings_and_paths, load_configs

if TYPE_CHECKING:
    RecordingInput = str | Path | BaseRecording | dict[str, BaseRecording]

# TODO: reject multi-segment recordings; only one segment per recording is
# supported. Memory estimates may assume one segment (not one session).
# TODO: validate that sampling frequency and channel count match across all
# recordings/shanks; memory estimation currently assumes they are identical.
# TODOC: the convention is that each step will loop over all sessions and
# shanks provided. To parallelize, handle this at the level above.
# TODO: for low channel count config e..g 32 don't use this bad channel detction method


class _BaseStepArguments(BaseModel):
    """Validate shared constructor arguments without inspecting recordings."""

    model_config = ConfigDict(strict=True)

    config_path: str | Path
    project_path: str | Path
    overwrite: bool
    num_cores: int


@dataclass(frozen=True)
class BaseStep:
    """Load configuration and resolve resources once during construction.

    The cached configuration is a mutable dictionary despite the frozen step.
    File changes after construction do not update it. Automatic core resolution
    remains unimplemented.
    """

    recordings: RecordingInput | list[RecordingInput]
    config_path: str | Path
    project_path: str | Path
    overwrite: bool = False
    num_cores: int = 1

    _config: dict = field(init=False, repr=False, compare=False)
    _resolved_num_cores: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Cache validated configuration and resolved resources."""
        _BaseStepArguments.model_validate(
            {
                "config_path": self.config_path,
                "project_path": self.project_path,
                "overwrite": self.overwrite,
                "num_cores": self.num_cores,
            }
        )
        loaded_config = load_configs(self.config_path)
        object.__setattr__(self, "_config", loaded_config)

        resolved_num_cores = self._resolve_num_cores()
        object.__setattr__(self, "_resolved_num_cores", resolved_num_cores)

    @property
    def config(self) -> dict:
        """Return the dictionary loaded at construction, without rereading disk."""
        return self._config

    def perform_checks(self) -> None:
        """Check inputs, configuration, and scientific assumptions before running."""
        raise NotImplementedError

    def run(self, verbose: bool = True) -> None:
        """Perform checks, execute the step, and save its outputs."""
        raise NotImplementedError

    def mem_required_per_core(self) -> int:
        """Estimate peak working RAM in bytes for one worker."""
        raise NotImplementedError

    def mem_required_total(self) -> int:
        """Estimate worker RAM in bytes, excluding already-resident shared data."""
        return self.mem_required_per_core() * self._resolved_num_cores

    def needs_gpu(self) -> bool:
        """Report whether the configured operation requires a GPU."""
        raise NotImplementedError

    def _resolve_num_cores(self) -> int:
        """TODO: add "auto" feature"""
        if self.num_cores != "auto":
            return self.num_cores

    def get_first_recording(self) -> BaseRecording:
        """Return the first loaded recording from session/shank containers."""
        recording = self.recordings

        while not isinstance(recording, BaseRecording):

            if isinstance(recording, (list, tuple)):
                if not recording:
                    raise ValueError("At least one recording is required")
                recording = recording[0]

            elif isinstance(recording, dict):
                if not recording:
                    raise ValueError("At least one recording is required")
                recording = next(iter(recording.values()))

            else:
                raise TypeError("Load recording paths before accessing a recording")

        return recording

    def _get_recordings_and_paths(
        self, step_name: str
    ) -> list[tuple[RecordingInput, Path]]:
        """Return recording/path pairs using the shared session/shank helper."""
        return [
            (recording, path)
            for _, _, recording, path in get_recordings_and_paths(
                self.recordings, self.project_path, step_name
            )
        ]
