"""Canonical pipeline step names accepted in configuration files."""

ALLOWED_STEPS = [
    "bad_channel_detection",
    "raw_data_quality_metrics",
    "artifact_detection",
    "artifact_curation",
    "preprocessing",
    "combine_sessions",
    "sorting",
    "postprocessing",
    "curation",
]



