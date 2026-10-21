"""Session/shank grouping must use metadata, not directory names or dict order."""

import numpy as np
import pytest
from spikeinterface.core import NumpyRecording

from spikesorted.utils import get_recordings_and_paths_by_shank


def make_recording():
    return NumpyRecording(np.zeros((10, 2), dtype="int16"), 30000)


def test_group_shanks_across_sessions_with_different_dict_order(tmp_path):
    a, b, c, d = [make_recording() for _ in range(4)]
    recordings = [
        ({"left": a, "right": b}, "shank_right"),
        ({"right": d, "left": c}, "shank_left"),
    ]
    root = tmp_path / "bad_channel_detection"

    grouped = get_recordings_and_paths_by_shank(
        recordings, tmp_path, "bad_channel_detection"
    )

    assert grouped == {
        "left": [
            (a, root / "shank_right" / "shank_left"),
            (c, root / "shank_left" / "shank_left"),
        ],
        "right": [
            (b, root / "shank_right" / "shank_right"),
            (d, root / "shank_left" / "shank_right"),
        ],
    }
    assert not root.exists()


@pytest.mark.parametrize("multiple_sessions", [False, True])
def test_unsplit_recordings_group_together_despite_session_path_names(
    tmp_path, multiple_sessions
):
    a, b = make_recording(), make_recording()
    root = tmp_path / "bad_channel_detection"
    if multiple_sessions:
        recordings = [(a, "shank_0"), (b, "shank_1")]
        expected = [(a, root / "shank_0"), (b, root / "shank_1")]
    else:
        recordings = a
        expected = [(a, root)]

    assert get_recordings_and_paths_by_shank(
        recordings, tmp_path, "bad_channel_detection"
    ) == {"none": expected}


def test_single_split_session_omits_session_directory(tmp_path):
    a, b = make_recording(), make_recording()
    root = tmp_path / "bad_channel_detection"

    assert get_recordings_and_paths_by_shank(
        ({"0": a, "1": b}, "named_session"), tmp_path, "bad_channel_detection"
    ) == {
        "0": [(a, root / "shank_0")],
        "1": [(b, root / "shank_1")],
    }


def test_unnamed_sessions_keep_their_numbered_paths(tmp_path):
    a, b = make_recording(), make_recording()
    root = tmp_path / "bad_channel_detection"

    assert get_recordings_and_paths_by_shank(
        [{"0": a}, {"0": b}], tmp_path, "bad_channel_detection"
    ) == {
        "0": [(a, root / "session_0" / "shank_0"),
              (b, root / "session_1" / "shank_0")],
    }
