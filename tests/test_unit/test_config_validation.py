"""Check signature-derived fields and validation during YAML loading."""

from copy import deepcopy
from inspect import signature

import pytest
from pydantic import ValidationError
from spikeinterface.preprocessing import detect_bad_channels

from spikesorted.utils import load_configs
from spikesorted.validation.canonical_values import ALLOWED_STEPS
from spikesorted.validation.config_validation import (
    BadChannelDetectionConfig,
    validate_config,
)


def test_fields_and_defaults_match_spikeinterface():
    parameters = dict(signature(detect_bad_channels).parameters)
    parameters.pop("recording")
    assert set(BadChannelDetectionConfig.model_fields) == set(parameters)
    for name, parameter in parameters.items():
        field = BadChannelDetectionConfig.model_fields[name]
        assert field.annotation == parameter.annotation
        assert field.default == parameter.default


@pytest.mark.parametrize("config", [
    {},
    {"bad_channel_detection": {}, "combine_sessions": {}},
    {"bad_channel_detection": {"seed": None, "std_mad_threshold": 5}},
])
def test_validation_returns_none_without_changing_config(config):
    original = deepcopy(config)
    assert validate_config(config) is None
    assert config == original
    if "std_mad_threshold" in config.get("bad_channel_detection", {}):
        assert type(config["bad_channel_detection"]["std_mad_threshold"]) is int


def test_all_allowed_steps_are_accepted():
    config = {step: {} for step in ALLOWED_STEPS}
    assert validate_config(config) is None


@pytest.mark.parametrize("step", [
    "raw_data_quality_metrics", "bad_channel_detection", "artifact_detection",
    "artifact_curation", "preprocessing", "sorting", "postprocessing", "curation",
    "combine_sessions",
])
def test_specification_steps_are_accepted(step):
    assert validate_config({step: {}}) is None


@pytest.mark.parametrize("step", [
    "detect_bad_channels", "unknown", "concatenate_sessions", "data_loading",
    "project_path",
])
def test_unknown_steps_are_rejected(step):
    with pytest.raises(ValidationError) as error:
        validate_config({"bad_channel_detection": {}, step: {}})
    assert error.value.errors()[0]["type"] == "extra_forbidden"
    assert error.value.errors()[0]["loc"] == (step,)


@pytest.mark.parametrize("options", [
    {"num_random_chunk": 5},
    {"recording": "not a config option"},
    {"num_random_chunks": "5"},
    {"num_random_chunks": 1.5},
    {"direction": "diagonal"},
    {"chunk_duration_s": None},
    None,
    [],
])
def test_invalid_bad_channel_options_are_rejected(options):
    with pytest.raises(ValidationError):
        validate_config({"bad_channel_detection": options})


def test_yaml_loader_validates_bad_channel_options(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("bad_channel_detection:\n  seed: wrong\n")
    with pytest.raises(ValidationError):
        load_configs(config_path)

    config_path.write_text(
        "bad_channel_detection:\n  seed: 42\n  chunk_duration_s: 0.1\n"
    )
    assert load_configs(config_path) == {
        "bad_channel_detection": {"seed": 42, "chunk_duration_s": 0.1},
    }
