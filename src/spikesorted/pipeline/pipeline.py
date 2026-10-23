"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..steps.bad_channel_detection.bad_channel_detection import BadChannelDetectionStep
from ..utils.utils import load_pipeline_config

if TYPE_CHECKING:
    from ..utils.recordings_structure import RecordingInput


class Pipeline:
    """Electrophysiology analysis pipeline."""

    def __init__(
        self,
        recordings: RecordingInput | list[RecordingInput],
        config_path: str | Path,
        output_path: str | Path,
        start_at_step: str | None = None,
        stop_after_step: str | None = None,
        overwrite: bool = False,
        num_cores: int = 1,
        verbose: bool = True,
    ) -> None:
        """Store recordings, configuration path, output root, and execution options."""
        self.recordings = recordings
        self.config_path = config_path
        self.output_path = output_path
        self.start_at_step = start_at_step
        self.stop_after_step = stop_after_step
        self.overwrite = overwrite
        self.num_cores = num_cores
        self.verbose = verbose

    def run(self):
        """Run from start_at_step, stopping after stop_after_step executes."""

        configs = load_pipeline_config(self.config_path)

        if "bad_channel_detection" in configs and self.start_at_step in [None, "bad_channel_detection"]:

            bad_channel_detection = BadChannelDetectionStep(
                recordings=self.recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
                num_cores=self.num_cores,
            )
            bad_channel_detection.run(self.verbose)

        if self.stop_after_step == "bad_channel_detection":
            return

