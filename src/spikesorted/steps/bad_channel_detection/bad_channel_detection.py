"""Bad-channel detection step (not implemented yet)."""

import warnings
from dataclasses import dataclass
from math import ceil
from pathlib import Path

import pandas as pd

# Preload SciPy signal so its one-time import allocations are process baseline,
# rather than part of the first bad-channel detection chunk.
import scipy.signal  # noqa: F401
import spikeinterface.preprocessing as spre

from ...utils.recordings_structure import get_num_sessions
from ..base import BasePipelineStep
from .bad_channel_union import create_bad_channel_labels_union
from .estimate_bad_channel_detection_memory_usage import (
    estimate_bad_channel_detection_memory_usage,
    estimate_filter_memory_usage,
    _parameter,
)


@dataclass(frozen=True)
class BadChannelDetectionStep(BasePipelineStep):
    """Detect bad channels. Inherits from BasePipelineStep
    including  all standard attributes (recordings, pipeline config, etc).

    The step wraps SpikeInterface's `bad_channel_detection` in it's `run()`
    function. It stores to disk for each session / shank in `recordings`:

    "bad_channel_ids.csv"
        The SpikeInterface channel_id of every bad channel in the recording.
        A single column containing channel ID.

    "bad_channel_labels.csv"
        A label indicating whether the channel is good, bad noise etc.
        See SpikeInterface detect_bad_channels() documentation for details
        on labels. Two columns, the first is channel ID and the second the label.
    """
    def run(self, verbose: bool = True) -> None:
        """Check inputs, high-pass at 300 Hz, and run IBL bad-channel detection.

        Save channel IDs, labels, detection metrics, and associated plots.
        """
        self.perform_checks()

        kwargs = self.config["bad_channel_detection"]

        for shank_recording, shank_path in self._get_recordings_and_paths(
            "bad_channel_detection"
        ):
            bad_ids_path = self.get_bad_channel_ids_filepath(shank_path)
            labels_path = self.get_bad_channel_labels_filepath(shank_path)

            shank_path.mkdir(parents=True, exist_ok=True)

            filtered_recording = spre.highpass_filter(shank_recording, freq_min=self._highpass_freq_min)

            bad_channel_ids, channel_labels = spre.detect_bad_channels(
                filtered_recording, **kwargs
            )

            bad_ids_df = pd.DataFrame({"channel_id": bad_channel_ids})
            labels_df = pd.DataFrame(
                {
                    "channel_id": shank_recording.get_channel_ids(),
                    "label": channel_labels,
                }
            )
            bad_ids_df.to_csv(bad_ids_path, index=False)
            labels_df.to_csv(labels_path, index=False)

        if "combine_sessions" in self.config and get_num_sessions(self.recordings) > 1:
            create_bad_channel_labels_union(self.recordings, self.output_path)

    def perform_checks(self) -> None:
        """This function performs the following checks on the bad channel detction intput:

        - checks required bad channel detection method is passed
        - throw a warning for low-coutn channels
        - raise if `overwrite=False` and output already exists.
        """
        method = self.config["bad_channel_detection"].get("method")
        if method is None:
            raise ValueError("bad_channel_detection.method must be explicitly provided")

        for recording, shank_path in self._get_recordings_and_paths(
            "bad_channel_detection"
        ):

            num_channels = recording.get_num_channels()
            if method == "coherence+psd" and num_channels <= 64:
                warnings.warn(
                    f"Recording for {shank_path} has {num_channels} channels "
                    "(64 or fewer). IBL bad-channel detection was developed for "
                    "Neuropixels probes; review its suitability and thresholds "
                    "for low-channel-count recordings.",
                    UserWarning,
                    stacklevel=2,
                )

            bad_ids_path = self.get_bad_channel_ids_filepath(shank_path)
            labels_path = self.get_bad_channel_labels_filepath(shank_path)

            if not self.overwrite:
                for output_path in (bad_ids_path, labels_path):
                    if output_path.exists():
                        raise FileExistsError(
                            "Bad-channel detection output already exists: "
                            f"{output_path}. "
                            "Set overwrite=True to replace existing outputs, "
                            "or choose a different output_path."
                        )

    def get_bad_channel_ids_filepath(self, shank_path: Path) -> Path:
        """Return the bad-channel IDs CSV path for a shank output directory."""
        return shank_path / "bad_channel_ids.csv"

    def get_bad_channel_labels_filepath(self, shank_path: Path) -> Path:
        """Return the all-channel labels CSV path for a shank output directory."""
        return shank_path / "bad_channel_labels.csv"

    def mem_required_per_core(self) -> int:
        """Estimate the memory usage for applying bad channel to a single recording.

        Bad channels are detected by first generating random chunks of data
        from the recording before estimating channel data quality from the chunks.
        When n_jobs>1 each chunk is handled in a separate core. This function estimates
        the memory requirement for each function.

        This is very much a conservative estimate. The key features for the memory used
        is chunk size in bytes (affected by chunk length in seconds and datatype)
        as well as the number of copies made internally. For each step, the number
        of copies is estimated from the implementation.

        This estimate is *very* rough. In reality, these scalars are largely determined
        by our benchmark tests, choosing values that work as close to, but within, all
        measured memory limits across systems.
        """
        config = self.config["bad_channel_detection"]

        recording = self.get_first_recording()

        chunk_duration_s = _parameter(config.get("chunk_duration_s"), "chunk_duration_s")

        num_samples_per_chunk = int(
            recording.get_sampling_frequency() * chunk_duration_s
        )

        float64_bytes = 8

        chunk_bytes = num_samples_per_chunk * recording.get_num_channels() * float64_bytes

        filter_factor = estimate_filter_memory_usage(
            recording, chunk_duration_s=config.get("chunk_duration_s"),
            freq_min=self._highpass_freq_min,
            method=config.get("method"),
            num_random_chunks=config.get("num_random_chunks"),
        )

        detection_factor = estimate_bad_channel_detection_memory_usage(
            recording,
            chunk_duration_s=config.get("chunk_duration_s"),
            method=config.get("method"),
            num_random_chunks=config.get("num_random_chunks"),
        )

        # Add 10% headroom for small allocations beyond the estimated arrays.
        headroom_multiplier = 1.1

        return ceil(headroom_multiplier * chunk_bytes * max(filter_factor, detection_factor))

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False

