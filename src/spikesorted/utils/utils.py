"""Shared pipeline utilities."""

from __future__ import annotations

from pathlib import Path

import yaml

from ..validation.config_validation import PipelineConfig, validate_config


def load_pipeline_config(config_path: str | Path) -> PipelineConfig:
    """Read the PIPELINE_CONFIG from disk."""
    with Path(config_path).open(encoding="utf-8") as file:
        loaded_config = yaml.safe_load(file)

    return validate_config(loaded_config)
