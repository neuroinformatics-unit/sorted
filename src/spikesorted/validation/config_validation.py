"""Validate pipeline configuration using SpikeInterface's declared parameters."""

from inspect import Parameter, signature
from typing import Any

from pydantic import ConfigDict, TypeAdapter, create_model
from spikeinterface.preprocessing import detect_bad_channels

from .canonical_values import ALLOWED_STEPS


BadChannelDetectionConfig = create_model(
    "BadChannelDetectionConfig",
    __config__=ConfigDict(extra="forbid", strict=True),
    **{
        name: (
            parameter.annotation if parameter.annotation is not Parameter.empty else Any,
            parameter.default if parameter.default is not Parameter.empty else ...,
        )
        for name, parameter in signature(detect_bad_channels, eval_str=True).parameters.items()
        if name != "recording"
        and parameter.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    },
)

PipelineConfig = create_model(
    "PipelineConfig",
    __config__=ConfigDict(extra="forbid"),
    **{step: (Any, None) for step in ALLOWED_STEPS},
)


def validate_config(config: object) -> None:
    """Raise on invalid configuration without changing the supplied values.

    Other allowed sections remain unchanged until their validators are implemented.
    Constraints absent from SI's annotations (such as method names) remain SI's
    responsibility; unannotated parameters accept any value.
    """
    TypeAdapter(dict).validate_python(config, strict=True)
    PipelineConfig.model_validate(config)

    if "bad_channel_detection" in config:
        BadChannelDetectionConfig.model_validate(config["bad_channel_detection"])
