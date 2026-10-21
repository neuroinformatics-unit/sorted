"""SLURM execution for the pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..pipeline.pipeline import Pipeline
from ..steps.bad_channel_detection.bad_channel_union import create_bad_channel_labels_union
from ..utils import load_configs, split_recordings_by_shank
from .slurm_runners import run_slurm_batch

if TYPE_CHECKING:
    from ..steps.base import RecordingInput

# TODO: we need a unitmatching option here in which we will need to
# take the union of bad channels even if we are not concatenating
def run_pipeline_with_slurm(
    recordings: RecordingInput | list[RecordingInput],
    config_path: str | Path,
    project_path: str | Path,
    overwrite: bool = False,
    num_cores: int = 1,
    verbose: bool = True,
    slurm_opts: dict | None = None,
):
    """Run independent session/shank pipelines as an array and await results.

    Each job retains the project root and its session/shank identity.
    slurm_opts are passed to Submitit's executor.update_parameters().
    Combined sessions synchronize after detection and preprocessing.
    """
    def run_pipeline_in_slurm_batch(inputs, start_at_step=None, stop_after_step=None):
        calls = []
        for recording in inputs:
            pipeline = Pipeline(
                recordings=recording,
                config_path=config_path,
                project_path=project_path,
                overwrite=overwrite,
                num_cores=num_cores,
                verbose=verbose,
                start_at_step=start_at_step,
                stop_after_step=stop_after_step,
            )
            calls.append((pipeline.run, (), {}))

        # TODO: set SLURM GPU resources based on the pipeline's needs_gpu().
        return run_slurm_batch(calls, project_path, num_cores, slurm_opts)

    configs = load_configs(config_path)
    split_recordings = split_recordings_by_shank(recordings)

    if "combine_sessions" not in configs or "bad_channel_detection" not in configs:
        return run_pipeline_in_slurm_batch(split_recordings)
    else:
        # First we run bad channel detection across separate nodes before
        # creating the union of all bad channels for later combination
        run_pipeline_in_slurm_batch(
            split_recordings, stop_after_step="bad_channel_detection"
        )
        create_bad_channel_labels_union(
            recordings, project_path
        )
