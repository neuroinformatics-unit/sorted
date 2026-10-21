"""Bad-channel detection step (not implemented yet)."""

import warnings
from dataclasses import dataclass
from inspect import signature
from math import ceil
from pathlib import Path

import pandas as pd

# Preload SciPy signal so its one-time import allocations are process baseline,
# rather than part of the first bad-channel detection chunk.
import scipy.signal  # noqa: F401
import spikeinterface.preprocessing as spre

from ...utils import get_num_sessions
from ..base import BaseStep
from .bad_channel_union import create_bad_channel_labels_union
from .estimate_bad_channel_detection_memory_usage import (
    estimate_bad_channel_detection_memory_usage,
    estimate_filter_memory_usage,
    _parameter,
)


@dataclass(frozen=True)
class BadChannelDetectionStep(BaseStep):
    """Detect bad channels using the shared pipeline step inputs.

    Configuration loading and resource resolution are inherited from BaseStep.
    Optional shank splitting belongs to the data loader, before this step.
    Scientific operations and resource estimation remain unimplemented.
    """

    def perform_checks(self) -> None:
        """Check output paths and warn about low channel counts for the IBL method."""
        method = self.config["bad_channel_detection"].get("method")
        if method is None:
            method = signature(spre.detect_bad_channels).parameters["method"].default

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
                            "or choose a different project_path."
                        )

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

            filtered_recording = spre.highpass_filter(shank_recording, freq_min=300)

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

        if "concatenate_sessions" in self.config and get_num_sessions(self.recordings) > 1:
            create_bad_channel_labels_union(self.recordings, self.project_path)

    def get_bad_channel_ids_filepath(self, shank_path: Path) -> Path:
        """Return the bad-channel IDs CSV path for a shank output directory."""
        return shank_path / "bad_channel_ids.csv"

    def get_bad_channel_labels_filepath(self, shank_path: Path) -> Path:
        """Return the all-channel labels CSV path for a shank output directory."""
        return shank_path / "bad_channel_labels.csv"

    def mem_required_per_core(self) -> int:
        """Use the first recording, assuming matching sampling rates/channel counts."""
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
            method=config.get("method"),
            num_random_chunks=config.get("num_random_chunks"),
        )

        detection_factor = estimate_bad_channel_detection_memory_usage(
            recording,
            chunk_duration_s=config.get("chunk_duration_s"),
            method=config.get("method"),
            num_random_chunks=config.get("num_random_chunks"),
            neighborhood_r2_radius_um=config.get("neighborhood_r2_radius_um"),
        )

        # Add 10% headroom for small allocations beyond the estimated arrays.
        headroom_multiplier = 1.1

        return ceil(headroom_multiplier * chunk_bytes * max(filter_factor, detection_factor))

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False

