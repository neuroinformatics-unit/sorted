"""SLURM execution for the pipeline."""


def run_pipeline_with_slurm(
    recordings: RecordingInput | list[RecordingInput],
    config_path: str | Path,
    project_path: str | Path,
    overwrite: bool = False,
    num_cores: int = 1,
    verbose: bool = True,
):
  # if we are not concatenating sessions, or we are concatenating but not bad
  # channel detection, then run all sessions / shanks in different slurm nodes

  # however, if we are running with concatentation things get more complex

  # 1) run pipeline from 0 to detect bad channels in slurm, wait.
  # 2) collect all into union
  # run from bad channel detection to preprocessing in slurm
  # 3) collect all and concatenate / combine
  # 4) postprocessing on single recording.
