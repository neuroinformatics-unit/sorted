from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from spikeinterface.core import BaseRecording

from ..utils.recordings_structure import get_recordings_and_paths
from ..utils.utils import load_pipeline_config
from ..validation.steps_validation import _BaseStepArguments

if TYPE_CHECKING:
    from ..utils.recordings_structure import RecordingInput
    from ..validation.config_validation import PipelineConfig


@dataclass(frozen=True)
class BasePipelineStep:
    """The base PipelineStep that defines methods and sets up shared attributes.

    A frozen dataclass is used, to ensure attributes cannot easily be mutated.

    Parameters
    ----------

    recordings
        A RecordingsInput (either a recording, (recording, str), or {str: recording}
        object, or list thereof).
    config_path
        The path to a YAML PipelineConfig.
    output_path
        The output path for the pipeline step. Outputs for every
        session / shank in RecordingsInput will be saved here.
    overwrite
        If `True`, existing outputs found in `output_path`
        will be deleted and overwritten.
    num_cores
        Number of cores to parallelize the step. Passed
        to SpikeInterface's `job_kwargs`.
    """

    recordings: RecordingInput | list[RecordingInput]
    config_path: str | Path
    output_path: str | Path
    overwrite: bool = False
    num_cores: int = 1

    _highpass_freq_min: ClassVar[float] = 300

    _config: PipelineConfig = field(init=False, repr=False, compare=False)
    _resolved_num_cores: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate all attributes and store loaded / computed attributes."""
        _BaseStepArguments.model_validate(
            {
                "recordings": self.recordings,
                "config_path": self.config_path,
                "output_path": self.output_path,
                "overwrite": self.overwrite,
                "num_cores": self.num_cores,
            }
        )
        loaded_config = load_pipeline_config(self.config_path)
        object.__setattr__(self, "_config", loaded_config)

        resolved_num_cores = self._resolve_num_cores()
        object.__setattr__(self, "_resolved_num_cores", resolved_num_cores)

    @property
    def config(self) -> PipelineConfig:
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
                self.recordings, self.output_path, step_name
            )
        ]
