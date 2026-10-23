"""
The pipeline steps `recordings` can be a fairly complex range of input types:
- a SpikeInterface recording
- a dict of SpikeInterface recordings split by shank (e.g. `recordings.split_by("group"))`.
- a tuple of (recording, str) where str is the user-specified name of the session.
Otherwise, the names session_1...n will be automatically used for folder names.

This is for a single session. For multiple-sessions, these datatypes
are stored in a list (where each element is the recording/s from a single session).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from spikeinterface.core import BaseRecording

Recording = str | Path | BaseRecording
SessionRecording = Recording | dict[str | int, BaseRecording]
RecordingInput = SessionRecording | tuple[SessionRecording, str]



def get_num_sessions(recordings: RecordingInput | list[RecordingInput]) -> int:
    """Return the number of sessions in the RecordingInput."""
    if isinstance(recordings, list):
        return len(recordings)
    else:
        return 1


def get_recordings_and_paths(
    recordings: RecordingInput | list[RecordingInput],
    output_path: str | Path, step_name: str
) -> list[tuple[str, str | int | None, Recording, Path]]:
    """Flatten the RecordingInput so that the recording and output path can be iterated over.

    The function handles every possible RecordingInput type and outputs a
    list of tuples containing (session_name, shank_id, spikeinterface_recording, path).
    This can then be iterated over my steps to quickly process individual
    recordings and store the outputs to the relevant path.
    """
    if isinstance(recordings, list):
        sessions = recordings
    else:
        sessions = [recordings]

    step_path = Path(output_path) / step_name
    recordings_and_paths = []

    for session_idx, session_recording in enumerate(sessions):

        # Handle the (recording, session_name) case
        if isinstance(session_recording, tuple):
            session_recording, session_name = session_recording
        else:
            session_name = f"session_{session_idx}"

        if len(sessions) == 1 and not isinstance(sessions[0], tuple):
            session_path = step_path
        else:
            session_path = step_path / session_name

        # Handle multiple shanks. When only one shank is used, `shank_id`
        # is None and data is not stored in a folder called "shank_<id>".
        for shank_id, recording in iter_over_shanks(session_recording):

            if shank_id is None:
                shank_path = session_path
            else:
                shank_path = session_path / f"shank_{shank_id}"

            recordings_and_paths.append(
                (session_name, shank_id, recording, shank_path)
            )

    return recordings_and_paths


def get_recordings_and_paths_by_shank(
    recordings: RecordingInput | list[RecordingInput],
    output_path: str | Path, step_name: str
) -> dict[str | int | None, list[tuple[str, Recording, Path]]]:
    """Group session names, individual recordings and their output paths by shank id.

    This convenience function is useful when we want to perform actions
    over recordings in the same shanks (e.g. union of bad channel detection).
    """
    recordings_by_shank = {}
    for session_name, shank_id, recording, path in get_recordings_and_paths(
        recordings, output_path, step_name
    ):
        recordings_by_shank.setdefault(shank_id, []).append((session_name, recording, path))

    return recordings_by_shank


def iter_over_shanks(
    recording: SessionRecording,
) -> Iterator[tuple[str | int | None, Recording]]:
    """
    A convenience function to handle that a recording could be
    a single recording dict of {shank_id: recording}.
    """
    if isinstance(recording, dict):
        yield from recording.items()
    else:
        yield None, recording
