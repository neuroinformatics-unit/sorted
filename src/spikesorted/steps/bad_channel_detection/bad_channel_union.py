from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from ...utils.recordings_structure import get_recordings_and_paths_by_shank


def create_bad_channel_labels_union(recordings, output_path):
    """Create a CSV which contains the union of all bad channel IDs across sessions.

    When working with multiple sessions, and concatenating or unit-matching, the
    same set of channels must be included on all used recordings. This function
    uses the individual sessions bad channel detection outputs on disk to create
    a union of all bad channel labels.

    The outputs are stored in a "session_unions" folder in the "bad_channel_detection" folder.
    A sessions.yaml beside each CSV records the contributing session names and date.

    This step will throw an error if the set of sessions / shanks on disk
    does not exactly match those in `recordings`, as this may indicate the
    project has gotten out of sync.
    """
    recordings_by_shank = get_recordings_and_paths_by_shank(
        recordings, output_path, "bad_channel_detection"
    )

    _confirm_all_and_only_specified_bad_channel_files_exist(
        recordings_by_shank, output_path
    )

    # For each session / shank, load the bad channel ids and save their
    # union in the shared output folder
    generation_date = date.today().isoformat()
    union_path = Path(output_path) / "bad_channel_detection" / "session_unions"

    for shank_id, recordings_and_paths in recordings_by_shank.items():

        bad_channel_ids = set()
        session_names = []

        for session_name, _, path in recordings_and_paths:
            session_names.append(session_name)
            labels = pd.read_csv(
                path / "bad_channel_ids.csv",
                dtype={"channel_id": str}, keep_default_na=False,
            )
            bad_channel_ids.update(labels["channel_id"])

        if shank_id is None:
            output_path = union_path
        else:
            output_path = union_path / f"shank_{shank_id}"

        output_path.mkdir(parents=True, exist_ok=True)

        pd.DataFrame({"channel_id": sorted(bad_channel_ids)}).to_csv(
            output_path / "bad_channel_ids.csv", index=False
        )
        with (output_path / "sessions.yaml").open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                {"sessions": session_names, "date": generation_date},
                file, sort_keys=False,
            )


def _confirm_all_and_only_specified_bad_channel_files_exist(recordings_by_shank, output_path):
    """Require the discovered CSVs to match the supplied sessions/shanks exactly."""
    expected_files = sorted(
        path / "bad_channel_ids.csv"
        for recordings_and_paths in recordings_by_shank.values()
        for _, _, path in recordings_and_paths
    )

    step_path = Path(output_path) / "bad_channel_detection"

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
