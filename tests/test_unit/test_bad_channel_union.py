"""Verify session bad-channel unions and their per-shank output layout."""

import numpy as np
import pandas as pd
import pytest
from spikeinterface.core import NumpyRecording

from spikesorted.steps.bad_channel_detection.bad_channel_union import (
    create_bad_channel_labels_union,
)


def recording():
    return NumpyRecording(np.zeros((10, 4)), 30000)


def write_ids(path, ids):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"channel_id": ids}).to_csv(path, index=False)


def read_ids(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)["channel_id"].tolist()


def test_union_keeps_shanks_separate_and_preserves_text_ids(tmp_path):
    rec = recording()
    recordings = [
        ({"left": rec, "right": rec}, "first"),
        ({"right": rec, "left": rec}, "second"),
    ]
    root = tmp_path / "bad_channel_detection"
    inputs = {
        "first/shank_left": ["001", "NA"],
        "second/shank_left": ["NA", "002"],
        "first/shank_right": ["3"],
        "second/shank_right": ["4", "3"],
    }
    for folder, ids in inputs.items():
        write_ids(root / folder / "bad_channel_ids.csv", ids)

    create_bad_channel_labels_union(recordings, tmp_path)

    assert read_ids(root / "session_unions/shank_left/bad_channel_ids.csv") == [
        "001", "002", "NA"
    ]
    assert read_ids(root / "session_unions/shank_right/bad_channel_ids.csv") == [
        "3", "4"
    ]
    for folder, ids in inputs.items():
        assert read_ids(root / folder / "bad_channel_ids.csv") == ids


@pytest.mark.parametrize("ids_a,ids_b,expected", [
    ([1, 2], [2, 3], ["1", "2", "3"]),
    ([], [2], ["2"]),
    ([], [], []),
])
def test_unsplit_sessions_write_union_without_shank_folder(
    tmp_path, ids_a, ids_b, expected
):
    root = tmp_path / "bad_channel_detection"
    write_ids(root / "session_0/bad_channel_ids.csv", ids_a)
    write_ids(root / "session_1/bad_channel_ids.csv", ids_b)

    create_bad_channel_labels_union([recording(), recording()], tmp_path)

    assert read_ids(root / "session_unions/bad_channel_ids.csv") == expected
    assert not (root / "session_unions/shank_none").exists()


def test_single_session_union(tmp_path):
    root = tmp_path / "bad_channel_detection"
    write_ids(root / "bad_channel_ids.csv", [2, 2, 1])

    create_bad_channel_labels_union(recording(), tmp_path)

    assert read_ids(root / "session_unions/bad_channel_ids.csv") == ["1", "2"]


def test_union_rerun_replaces_previous_union(tmp_path):
    rec = recording()
    root = tmp_path / "bad_channel_detection"
    write_ids(root / "bad_channel_ids.csv", [1])
    create_bad_channel_labels_union(rec, tmp_path)
    write_ids(root / "bad_channel_ids.csv", [2])
    create_bad_channel_labels_union(rec, tmp_path)
    assert read_ids(root / "session_unions/bad_channel_ids.csv") == ["2"]


@pytest.mark.parametrize("unexpected", [False, True])
def test_file_mismatch_creates_no_union(tmp_path, unexpected):
    root = tmp_path / "bad_channel_detection"
    write_ids(root / "session_0/bad_channel_ids.csv", [1])
    if unexpected:
        write_ids(root / "session_1/bad_channel_ids.csv", [2])
        write_ids(root / "unrelated/bad_channel_ids.csv", [3])

    with pytest.raises(ValueError, match="do not match"):
        create_bad_channel_labels_union([recording(), recording()], tmp_path)

    assert not (root / "session_unions").exists()
