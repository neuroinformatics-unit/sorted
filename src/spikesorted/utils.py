"""Shared pipeline utilities."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import TypeAdapter

if TYPE_CHECKING:
    from .steps.base import RecordingInput


def load_configs(config_path: str | Path) -> dict:
    """Read YAML and validate its top-level dictionary with Pydantic."""
    with Path(config_path).open(encoding="utf-8") as file:
        loaded_config = yaml.safe_load(file)

    return TypeAdapter(dict).validate_python(loaded_config, strict=True)


def get_recordings_and_paths(
    recordings: RecordingInput | list[RecordingInput],
    project_path: str | Path, step_name: str
) -> list[tuple[str, str, RecordingInput, Path]]:
    """Return session name, shank ID, recording and output path for each input."""
    if isinstance(recordings, list):
        sessions = recordings
    else:
        sessions = [recordings]

    step_path = Path(project_path) / step_name
    recordings_and_paths = []

    for session_idx, session_recording in enumerate(sessions):

        if isinstance(session_recording, tuple):
            session_recording, session_name = session_recording
        else:
            session_name = f"session_{session_idx}"

        if len(sessions) == 1:
            session_path = step_path
        else:
            session_path = step_path / session_name

        if isinstance(session_recording, dict):
            shank_recordings = session_recording
        else:
            shank_recordings = {"none": session_recording}

        for shank_id, recording in shank_recordings.items():

            shank_path = (
                session_path if shank_id == "none"
                else
                session_path / f"shank_{shank_id}"
            )
            recordings_and_paths.append((session_name, shank_id, recording, shank_path))

    return recordings_and_paths


def get_recordings_and_paths_by_shank(
    recordings: RecordingInput | list[RecordingInput],
    project_path: str | Path, step_name: str
) -> dict[str, list[tuple[RecordingInput, Path]]]:
    """Group recording/output-directory pairs by shank ID, preserving session order.

    Unsplit recordings use the existing "none" shank key. Group by the explicit
    shank ID rather than directory names, which may instead identify sessions.
    No directories are created.
    """
    recordings_by_shank = {}
    for _, shank_id, recording, path in get_recordings_and_paths(
        recordings, project_path, step_name
    ):
        recordings_by_shank.setdefault(shank_id, []).append((recording, path))
    return recordings_by_shank


def get_num_sessions(recordings: RecordingInput | list[RecordingInput]) -> int:
    """Return the session count; shank dictionaries and named tuples count as one."""
    if isinstance(recordings, list):
        return len(recordings)
    else:
        return 1
