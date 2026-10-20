"""Check estimates against traced NumPy/SciPy allocations, not process RSS."""

import json
import tracemalloc
from importlib.metadata import version

import numpy as np
import pytest

# Exclude one-time SciPy signal import allocations from per-chunk measurements.
import scipy.signal  # noqa: F401
import spikeinterface.preprocessing as spre
from spikeinterface.core import NumpyRecording
from spikeinterface.preprocessing.detect_bad_channels import detect_bad_channels_ibl

from spikesorted.steps.bad_channel_detection import BadChannelDetectionStep
from spikesorted.steps.bad_channel_detection import (
    estimate_bad_channel_detection_memory_usage as memory,
)


def measure_peak(operation):
    tracemalloc.start()
    try:
        operation()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


@pytest.mark.parametrize(
    "channels,samples,dtype", [
        (64, 9000, "int16"), (384, 9000, "float32"), (128, 9000, "float64"),
        (384, 60000, "float32"), (768, 30000, "float64"),
    ]
)
def test_filter_estimate_covers_measured_allocations(
    channels, samples, dtype, record_property
):
    assert version("scipy") == "1.18.1"
    recording = NumpyRecording(np.zeros((samples + 6000, channels), dtype=dtype), 30000)
    filtered = spre.highpass_filter(recording, freq_min=300)
    factor = memory.estimate_filter_memory_usage(
        recording, chunk_duration_s=samples / 30000
    )
    estimate = factor * samples * channels * 8
    peak = measure_peak(
        lambda: filtered.get_traces(start_frame=1000, end_frame=1000 + samples)
    )
    record_property("estimated_bytes", estimate)
    record_property("measured_peak_bytes", peak)
    assert isinstance(factor, float)
    assert np.isfinite(factor) and factor > 1
    assert estimate > samples * channels * 8
    assert peak <= estimate, f"Measured {peak} bytes exceeds estimate {estimate}"


@pytest.mark.parametrize(
    "channels,samples,window_ms", [(64, 3000, 10), (384, 9000, 10), (128, 9000, 20),
     (64, 3000, 0.2), (64, 3000, 100), (384, 60000, 10), (768, 30000, 20)]
)
@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_detection_estimate_covers_measured_allocations(
    channels, samples, window_ms, dtype, record_property
):
    assert version("scipy") == "1.18.1"
    source = (
        np.random.default_rng(42).normal(size=(samples, channels)).astype(dtype)
    )
    recording = NumpyRecording(source, 30000)
    factor = memory.estimate_bad_channel_detection_memory_usage(
        recording, chunk_duration_s=samples / 30000
    )
    estimate = factor * samples * channels * 8

    def detect():
        chunk = source.copy()
        ordered = chunk[:, np.arange(channels)[::-1]]
        return detect_bad_channels_ibl(
            raw=ordered,
            fs=30000,
            psd_hf_threshold=0.02,
            dead_channel_thr=-0.5,
            noisy_channel_thr=1.0,
            outside_channel_thr=-0.75,
            n_neighbors=11,
            nyquist_threshold=0.8,
            welch_window_ms=window_ms,
            outside_channels_location="top",
        )

    peak = measure_peak(detect)
    record_property("estimated_bytes", estimate)
    record_property("measured_peak_bytes", peak)
    assert isinstance(factor, float)
    assert np.isfinite(factor) and factor > 1
    assert source.nbytes < estimate
    assert peak <= estimate, f"Measured {peak} bytes exceeds estimate {estimate}"


def check_method_allocations(method, channels, samples, num_random_chunks, dtype,
                             tmp_path, record_property):
    """Measure the full SI detector, including filtering, against the step budget."""
    traces = np.random.default_rng(42).normal(
        size=(samples * 3, channels)
    ).astype(dtype)
    recording = NumpyRecording(traces, 30000)
    recording.set_dummy_probe_from_locations(
        np.column_stack((np.zeros(channels), np.arange(channels) * 20))
    )
    config = {
        "method": method, "chunk_duration_s": samples / 30000,
        "num_random_chunks": num_random_chunks,
        "neighborhood_r2_radius_um": 60,
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(json.dumps({"bad_channel_detection": config}))
    step = BadChannelDetectionStep(recording, config_path, tmp_path, num_cores=1)
    estimate = step.mem_required_per_core()
    filtered = spre.highpass_filter(recording, freq_min=300)
    peak = measure_peak(lambda: spre.detect_bad_channels(filtered, seed=42, **config))
    record_property("estimated_bytes", estimate)
    record_property("measured_peak_bytes", peak)
    assert peak <= estimate, f"Measured {peak} bytes exceeds estimate {estimate}"


@pytest.mark.parametrize("channels,samples,num_random_chunks", [
    (64, 3000, 5), (384, 9000, 20),
])
@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_std_estimate_covers_measured_allocations(
    channels, samples, num_random_chunks, dtype, tmp_path, record_property
):
    check_method_allocations(
        "std", channels, samples, num_random_chunks, dtype, tmp_path, record_property
    )


@pytest.mark.parametrize("channels,samples,num_random_chunks", [
    (64, 3000, 5), (384, 9000, 20),
])
@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_mad_estimate_covers_measured_allocations(
    channels, samples, num_random_chunks, dtype, tmp_path, record_property
):
    check_method_allocations(
        "mad", channels, samples, num_random_chunks, dtype, tmp_path, record_property
    )


@pytest.mark.parametrize("channels,samples,num_random_chunks", [
    (64, 3000, 5), (384, 9000, 5),
])
@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_neighborhood_r2_estimate_covers_measured_allocations(
    channels, samples, num_random_chunks, dtype, tmp_path, record_property
):
    check_method_allocations(
        "neighborhood_r2", channels, samples, num_random_chunks, dtype,
        tmp_path, record_property
    )
