"""Validate pipeline configuration using SpikeInterface's declared parameters."""

from typing import Annotated, Any

from pydantic import AfterValidator, ConfigDict, TypeAdapter, with_config
from typing_extensions import TypedDict

from .steps_validation import _validate_bad_channel_config


@with_config(ConfigDict(extra="forbid", strict=True))
class PipelineConfig(TypedDict, total=False):
    """Optional pipeline sections; unimplemented sections accept any value."""

    bad_channel_detection: Annotated[
        dict[str, Any], AfterValidator(_validate_bad_channel_config)
    ]
    raw_data_quality_metrics: Any
    artifact_detection: Any
    artifact_curation: Any
    preprocessing: Any
    combine_sessions: Any
    sorting: Any
    postprocessing: Any
    curation: Any


_pipeline_config_adapter = TypeAdapter(PipelineConfig)


def validate_config(config: object) -> PipelineConfig:
    """Return a validated dictionary without adding defaults or coercing values.

    Other allowed sections remain unchanged until their validators are implemented.
    Apart from the unsupported neighborhood_r2 method, constraints absent from SI's
    annotations remain SI's responsibility; unannotated parameters accept any value.
    """
    return _pipeline_config_adapter.validate_python(config)
