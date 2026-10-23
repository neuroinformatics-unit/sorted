"""Validation for shared step constructor arguments."""

from inspect import Parameter, signature
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, create_model
from spikeinterface.preprocessing import detect_bad_channels

from ..utils.recordings_structure import RecordingInput


class _BaseStepArguments(BaseModel):
    """Validate shared constructor arguments without inspecting recording data."""

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    recordings: RecordingInput | list[RecordingInput]
    config_path: str | Path
    output_path: str | Path
    overwrite: bool
    num_cores: int


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

def _validate_bad_channel_config(config: dict[str, Any]) -> dict[str, Any]:
    """Check SI options without inserting defaults or returning a model."""
    BadChannelDetectionConfig.model_validate(config)
    if config.get("method") == "neighborhood_r2":
        raise ValueError("neighborhood_r2 is not supported as it is developed for LFP stream.")
    return config
