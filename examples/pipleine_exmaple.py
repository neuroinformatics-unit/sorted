"""Run bad-channel detection on the local Neuropixels test recording."""

from datetime import datetime
from pathlib import Path
import spikeinterface as si
from spikesorted.pipeline.pipeline import Pipeline


def main():

    repo_path = Path(__file__).resolve().parents[1]
    recording = si.load(
        repo_path / "tests/data/neuropixels-2010-spikeglx/si_recording"
    )
    run_name = f"{datetime.now():%Y-%m-%d_%H-%M-%S_%f}_{Path(__file__).stem}"
    output_path = repo_path / "examples" / "outputs" / run_name

    Pipeline(
        recordings=recording,
        config_path=repo_path / "tests/test_integration/bad_channel_detection.yaml",
        output_path=output_path,
        stop_after_step="bad_channel_detection",
        overwrite=False,
    ).run()

    print(f"Results saved to: {output_path / 'bad_channel_detection'}")


if __name__ == "__main__":
    main()
