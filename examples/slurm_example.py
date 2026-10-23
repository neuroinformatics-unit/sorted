"""Run from a SLURM login node with spikesorted installed in the active environment."""

from datetime import datetime
from pathlib import Path

import spikeinterface as si

from spikesorted.slurm.slurm_for_pipeline import run_pipeline_with_slurm


def main():
    repo_path = Path(__file__).resolve().parents[1]

    # Recording, config and output paths must be accessible on the compute nodes.
    # Add more saved recording folders to submit multiple sessions in one array.
    recording_paths = [
        repo_path / "tests/data/neuropixels-2010-spikeglx/si_recording",
    ]
    recordings = [si.load(path) for path in recording_paths]

    # This fixture already contains one shank. For multiple shanks, each session
    # can instead be a dictionary: {"0": shank_0_recording, "1": shank_1_recording}.
    run_name = f"{datetime.now():%Y-%m-%d_%H-%M-%S_%f}_{Path(__file__).stem}"
    output_path = repo_path / "examples" / "outputs" / run_name

    job = run_pipeline_with_slurm(
        recordings=recordings,
        config_path=repo_path / "tests/test_integration/bad_channel_detection.yaml",
        output_path=output_path,
        overwrite=False,
        num_cores=1,
        slurm_opts={
            "slurm_partition": "cpu",  # Change to your cluster's partition.
            "mem_gb": 4,
            "timeout_min": 10,
            "slurm_array_parallelism": 4,
        },
        coordinator_slurm_opts={
            "slurm_partition": "cpu",
            "mem_gb": 4,
            "timeout_min": 1440,  # Includes time waiting for workers to start.
        },
    )
    print(f"Coordinator job submitted: {job.job_id}")
    print(f"Results and SLURM logs: {output_path}")
    # job.result()  # Uncomment only if you want this caller to wait.


if __name__ == "__main__":
    main()
