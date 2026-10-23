"""Helpers for preparing SLURM worker inputs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils.recordings_structure import iter_over_shanks

if TYPE_CHECKING:
    from ..utils.recordings_structure import RecordingInput


def split_recordings_by_shank(
    recordings: RecordingInput | list[RecordingInput],
) -> list[RecordingInput]:
    """Prepare individual session/shank inputs to run the pipeline in parallel.

    The function takes the RecordingInput and returns a list of inputs that
    can be passed one at a time to the pipeline on separate SLURM workers.

    For example, two sessions with two shanks each::

        [
            ({"0": session_a_shank_0, "1": session_a_shank_1}, "session_a"),
            ({"0": session_b_shank_0, "1": session_b_shank_1}, "session_b"),
        ]

    become four inputs::

        [
            ({"0": session_a_shank_0}, "session_a"),
            ({"1": session_a_shank_1}, "session_a"),
            ({"0": session_b_shank_0}, "session_b"),
            ({"1": session_b_shank_1}, "session_b"),
        ]
    """
    sessions = recordings if isinstance(recordings, list) else [recordings]
    split_recordings = []
    for session_idx, session_recording in enumerate(sessions):

        if isinstance(session_recording, tuple):
            session_recording, session_name = session_recording
        else:
            session_name = f"session_{session_idx}" if len(sessions) > 1 else None

        for shank_id, recording in iter_over_shanks(session_recording):
            if shank_id is None:
                shank_recording = recording
            else:
                shank_recording = {shank_id: recording}

            if session_name is None:
                split_recordings.append(shank_recording)
            else:
                split_recordings.append((shank_recording, session_name))

    return split_recordings
