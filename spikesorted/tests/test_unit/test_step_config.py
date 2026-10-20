"""Tests for loading step configuration without running scientific processing."""

import warnings
from dataclasses import FrozenInstanceError

import numpy as np
import pytest
import yaml
from pydantic import ValidationError
from spikeinterface.core import NumpyRecording

from spikesorted.steps.bad_channel_detection import BadChannelDetectionStep
from spikesorted.steps.base import BaseStep


@pytest.mark.parametrize("step_class", [BaseStep, BadChannelDetectionStep])
def test_configuration_is_loaded_once_and_core_field_can_be_set(
    tmp_path, monkeypatch, step_class
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "detect_bad_channels:\n  method: coherence+psd\n", encoding="utf-8"
    )
    monkeypatch.setattr(step_class, "_resolve_num_cores", lambda self: 2)
    step = step_class("recording", config_path, tmp_path)
    config_path.write_text("changed: true\n", encoding="utf-8")
    assert step.config == {"detect_bad_channels": {"method": "coherence+psd"}}
    assert step.config is step.config
    assert step._resolved_num_cores == 2
    with pytest.raises(FrozenInstanceError):
        step._config = {}


@pytest.mark.parametrize("contents", ["", "null", "- entry", "42", "text"])
def test_configuration_must_be_a_mapping(tmp_path, contents):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        BaseStep("recording", str(config_path), tmp_path)
    assert exc_info.value.errors()[0]["type"] == "dict_type"


@pytest.mark.parametrize(
    "contents", ["broken: [", "!!python/object:builtins.object {}"]
)
def test_invalid_or_unsafe_yaml_is_rejected(tmp_path, contents):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(contents, encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        BaseStep("recording", config_path, tmp_path)


def test_missing_configuration_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        BaseStep("recording", tmp_path / "missing.yaml", tmp_path)


@pytest.mark.parametrize("method", [None, "coherence+psd", "std", "mad", "neighborhood_r2"])
@pytest.mark.parametrize("num_channels", [63, 64, 65])
@pytest.mark.parametrize("layout", ["single", "sessions", "shanks"])
def test_low_channel_count_warning(tmp_path, monkeypatch, num_channels, layout, method):
    config_path = tmp_path / "config.yaml"
    config = {"bad_channel_detection": {}}
    if method is not None:
        config["bad_channel_detection"]["method"] = method
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setattr(BadChannelDetectionStep, "_resolve_num_cores", lambda self: 1)
    recording = NumpyRecording(np.zeros((10, num_channels), dtype="float32"), 30000)
    recordings = recording
    if layout == "sessions":
        recordings = [recording]
    elif layout == "shanks":
        recordings = [{"shank0": recording}]
    step = BadChannelDetectionStep(recordings, config_path, tmp_path)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        step.perform_checks()
    expected = num_channels <= 64 and method in (None, "coherence+psd")
    assert len(caught) == int(expected)
    if caught:
        assert caught[0].category is UserWarning
        assert f"has {num_channels} channels" in str(caught[0].message)
