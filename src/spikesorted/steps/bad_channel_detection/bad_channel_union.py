"""Create per-shank unions of session bad-channel outputs."""

from pathlib import Path

import pandas as pd

from ...utils import get_recordings_and_paths_by_shank


def create_bad_channel_labels_union(recordings, project_path):
    """Validate session CSVs and save their bad-channel ID union per shank.

    Unsplit recordings save directly in session_unions. Channel IDs are read as
    text to preserve identifiers such as "001" and "NA", then sorted as text.
    """
    recordings_by_shank = get_recordings_and_paths_by_shank(
        recordings, project_path, "bad_channel_detection"
    )

    _confirm_all_and_only_specified_bad_channel_files_exist(
        recordings_by_shank, project_path
    )

    union_path = Path(project_path) / "bad_channel_detection" / "session_unions"

    for shank_id, recordings_and_paths in recordings_by_shank.items():
        bad_channel_ids = set()
        for _, path in recordings_and_paths:
            labels = pd.read_csv(
                path / "bad_channel_ids.csv",
                dtype={"channel_id": str}, keep_default_na=False,
            )
            bad_channel_ids.update(labels["channel_id"])

        if shank_id == "none":
            output_path = union_path
        else:
            output_path = union_path / f"shank_{shank_id}"

        output_path.mkdir(parents=True, exist_ok=True)

        pd.DataFrame({"channel_id": sorted(bad_channel_ids)}).to_csv(
            output_path / "bad_channel_ids.csv", index=False
        )


def _confirm_all_and_only_specified_bad_channel_files_exist(recordings_by_shank, project_path):
    """Require the discovered CSVs to match the supplied sessions/shanks exactly."""
    expected_files = sorted(
        path / "bad_channel_ids.csv"
        for recordings_and_paths in recordings_by_shank.values()
        for _, path in recordings_and_paths
    )

    step_path = Path(project_path) / "bad_channel_detection"
    existing_files = sorted(
        path for path in step_path.rglob("bad_channel_ids.csv")
        if not path.is_relative_to(step_path / "session_unions")
    )

    if expected_files != existing_files:
        missing = sorted(set(expected_files) - set(existing_files))
        unexpected = sorted(set(existing_files) - set(expected_files))
        raise ValueError(
            "Cannot create the bad-channel union: files in the project path "
            "do not match the supplied recordings.\n"
            f"Missing files: {missing}\n"
            f"Unexpected files: {unexpected}\n"
            "Remove folders for sessions or shanks that are not part of this run, "
            "and generate any missing bad-channel files before trying again."
        )
