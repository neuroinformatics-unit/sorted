"""Multipliers of one float64 data chunk for SI 0.105.3 / SciPy 1.18.1.

Assume one recording segment. Budget conservative working-array counts.
Headroom is applied by the step. Exclude resident source data,
process overhead and extractor caches. These are estimates, not universal bounds.
"""

from inspect import signature

import numpy as np
import spikeinterface.preprocessing as spre
from spikeinterface.core import BaseRecording
from spikeinterface.preprocessing.filter import adjust_margin_ms_for_highpass


def _parameter(value, name: str):
    if value is None:
        value = signature(spre.detect_bad_channels).parameters[name].default
    return value


def estimate_filter_memory_usage(
    recording: BaseRecording, chunk_duration_s: float | None = None,
    *, method: str | None = None, num_random_chunks: int | None = None,
) -> float:
    """Return a filter scaling factor relative to one float64 trace chunk.

    Use SI's margin helper for the fixed 300 Hz high-pass filter. Allow 100
    additional samples per side for SciPy padding (default order-5 SOS uses 18).
    Budget six float64 buffers plus stored chunks for non-streaming detection
    methods. No traces are loaded.
    """
    fs = recording.get_sampling_frequency()
    chunk_duration_s = _parameter(chunk_duration_s, "chunk_duration_s")
    random_chunk_samples = int(fs * chunk_duration_s)

    margin_samples = int(adjust_margin_ms_for_highpass(300) * fs / 1000)
    padded_samples = random_chunk_samples + 2 * margin_samples + 2 * 100

    factor = 6 * padded_samples / random_chunk_samples
    if _parameter(method, "method") != "coherence+psd":
        factor += _parameter(num_random_chunks, "num_random_chunks")

    return factor


def estimate_bad_channel_detection_memory_usage(
    recording: BaseRecording, chunk_duration_s: float | None = None,
    *, method: str | None = None, num_random_chunks: int | None = None,
    neighborhood_r2_radius_um: float | None = None,
) -> float:
    """Return a method-specific multiplier of one float64 trace chunk.

    Resolve only the selected method's options. Coherence+PSD budgets the Welch
    spectrogram and trace copies. Std/MAD retain all sampled chunks. Neighbourhood
    medians additionally allocate samples x channels x neighbours working arrays;
    derive neighbour count from probe geometry and the configured radius.
    """
    method = _parameter(method, "method")

    if method == "coherence+psd":
        # Float32/float64 allocation tests measured about 6-10 float64 chunks.
        # Budget 12 as a provisional allowance for spectra and working copies;
        # this is measurement-informed, not a derived universal upper bound.
        return 12.0

    num_random_chunks = _parameter(num_random_chunks, "num_random_chunks")

    if method == "std":
        # Hold all sampled chunks plus an equally sized working copy for std.
        factor = 2 * num_random_chunks
        return float(factor)

    if method == "mad":
        # Includes SciPy's wrapper copy, absolute deviations and median copy.
        factor = 4 * num_random_chunks
        return float(factor)

    if method == "neighborhood_r2":
        radius = _parameter(neighborhood_r2_radius_um, "neighborhood_r2_radius_um")
        locations = recording.get_channel_locations()
        max_neighbors = 0
        for index, location in enumerate(locations):
            distances = np.linalg.norm(locations - location, axis=1)
            neighbors = distances < radius
            neighbors[index] = False
            max_neighbors = max(max_neighbors, int(np.count_nonzero(neighbors)))

        # Retain all sampled chunks. Budget 16 chunk-sized buffers per neighbour
        # and 16 more for other working arrays, including copies and medians.
        # This is a conservative allowance, not an exact allocation count.
        factor = num_random_chunks + 16 * (max_neighbors + 1)
        return float(factor)
