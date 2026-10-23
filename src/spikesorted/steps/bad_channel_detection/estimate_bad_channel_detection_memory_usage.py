"""Multipliers of one float64 data chunk for SI 0.105.3 / SciPy 1.18.1.

Assume one recording segment. Budget conservative working-array counts.
Headroom is applied by the step. Exclude resident source data,
process overhead and extractor caches. These are estimates, not universal bounds.
"""

from inspect import signature

import spikeinterface.preprocessing as spre
from spikeinterface.core import BaseRecording
from spikeinterface.preprocessing.filter import adjust_margin_ms_for_highpass


def _parameter(value, name: str):
    if value is None:
        value = signature(spre.detect_bad_channels).parameters[name].default
    return value


def estimate_filter_memory_usage(
    recording: BaseRecording, chunk_duration_s: float | None = None,
    *, freq_min: float, method: str | None = None, num_random_chunks: int | None = None,
) -> float:
    """Estimate the memory scaling factor of an input data chunk when HP filtering is performed.

    Consider the required margin size, and estimate 6 internal buffers. If another
    other method except IBL is used, increase the factor to account for the fact
    that all chunks are loaded in memory together.
    """
    fs = recording.get_sampling_frequency()
    chunk_duration_s = _parameter(chunk_duration_s, "chunk_duration_s")
    random_chunk_samples = int(fs * chunk_duration_s)

    margin_samples = int(adjust_margin_ms_for_highpass(freq_min) * fs / 1000)
    padded_samples = random_chunk_samples + 2 * margin_samples + 2 * 100

    factor = 6 * padded_samples / random_chunk_samples
    if _parameter(method, "method") != "coherence+psd":
        factor += _parameter(num_random_chunks, "num_random_chunks")

    return factor


def estimate_bad_channel_detection_memory_usage(
    recording: BaseRecording, chunk_duration_s: float | None = None,
    *, method: str | None = None, num_random_chunks: int | None = None,
) -> float:
    """"Estimate the memory scaling factor of an input data chunk when bad channel detection is performed.

    The memory useage per chunk depends on the method. For each, the
    total memory usage expressed as a scaling factor of the input chunk
    memory size is esimtated. This is partly estiamted from the implmenetation
    and partly from benchmarking,s ee benchmark tests.
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
