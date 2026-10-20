"""Shared step inputs from the SPEC's implementation interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import yaml
from pydantic import TypeAdapter
from spikeinterface.core import BaseRecording

if TYPE_CHECKING:
    RecordingInput = str | Path | BaseRecording | dict[str, BaseRecording]

# TODO: set up pydantic validation
# TODO: reject multi-segment recordings; only one segment per recording is
# supported. Memory estimates may assume one segment (not one session).
# TODO: validate that sampling frequency and channel count match across all
# recordings/shanks; memory estimation currently assumes they are identical.
# TODOC: the convention is that each step will loop over all sessions and
# shanks provided. To parallelize, handle this at the level above.
# TODO: for low channel count config e..g 32 don't use this bad channel detction method

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
        loaded_config = self._load_config_from_path()
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

    def _load_config_from_path(self) -> dict:
        """Read YAML and validate its top-level dictionary with Pydantic."""
        with Path(self.config_path).open(encoding="utf-8") as file:
            loaded_config = yaml.safe_load(file)

        return TypeAdapter(dict).validate_python(loaded_config, strict=True)

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
        """
        """
        if isinstance(self.recordings, list):
            sessions = self.recordings
        else:
            sessions = [self.recordings]

        step_path = Path(self.project_path) / step_name
        recordings_and_paths = []

        for session_idx, session_recording in enumerate(sessions):

            if isinstance(session_recording, tuple):
                session_recording, session_name = session_recording
            else:
                session_name = f"session_{session_idx}"

            session_path = (
                step_path if len(sessions) == 1
                else
                step_path / session_name
            )

            if isinstance(session_recording, dict):
                shank_recordings = session_recording
            else:
                shank_recordings = {"none": session_recording}

            for shank_id, recording in shank_recordings.items():

                shank_path = (
                    session_path if shank_id == "none"
                    else
                    session_path / f"shank_{shank_id}"
                )
                recordings_and_paths.append((recording, shank_path))

        return recordings_and_paths
