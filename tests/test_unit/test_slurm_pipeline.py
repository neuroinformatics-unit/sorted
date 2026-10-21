"""Check orchestration ordering without submitting jobs to a real scheduler."""

import pytest

from spikesorted.slurm import slurm_for_pipeline as slurm


def configure_jobs(monkeypatch, config, fail_at=None):
    events = []
    submissions = []
    monkeypatch.setattr(slurm, "load_configs", lambda path: config)

    class Job:
        def __init__(self, stage, index):
            self.stage = stage
            self.index = index

        def result(self):
            events.append(("result", self.stage, self.index))
            if (self.stage, self.index) == fail_at:
                raise RuntimeError("Worker failed")
            return self.stage, self.index

    def submit(**kwargs):
        stage = len(submissions)
        submissions.append(kwargs)
        events.append(("submit", stage))
        return [Job(stage, index) for index in range(2)]

    monkeypatch.setattr(slurm, "_submit_pipeline_jobs", submit)
    monkeypatch.setattr(
        slurm, "create_bad_channel_labels_union",
        lambda recordings, path: events.append(("union",)),
    )
    return events, submissions


def test_union_waits_for_all_detection_jobs_and_preprocessing_precedes_combine(
    monkeypatch, tmp_path
):
    events, submissions = configure_jobs(
        monkeypatch, {"bad_channel_detection": {}, "concatenate_sessions": {}}
    )
    recordings = [object(), object()]
    result = slurm.run_pipeline_with_slurm(
        recordings, "config.yaml", tmp_path, num_cores=4, overwrite=True
    )

    assert events == [
        ("submit", 0), ("result", 0, 0), ("result", 0, 1), ("union",),
        ("submit", 1), ("result", 1, 0), ("result", 1, 1),
        ("submit", 2), ("result", 2, 0), ("result", 2, 1),
    ]
    assert submissions[0]["stop_at_step"] == "raw_data_quality_metrics"
    assert submissions[1]["start_at_step"] == "raw_data_quality_metrics"
    assert submissions[1]["stop_at_step"] == "concatenate_sessions"
    assert submissions[2]["start_at_step"] == "concatenate_sessions"
    assert submissions[2]["split_sessions"] is False
    assert all(call["recordings"] is recordings for call in submissions)
    assert all(call["num_cores"] == 4 for call in submissions)
    assert all(call["overwrite"] is True for call in submissions)
    assert result == [(2, 0), (2, 1)]


def test_concatenation_without_detection_still_waits_before_combining(
    monkeypatch, tmp_path
):
    events, submissions = configure_jobs(monkeypatch, {"concatenate_sessions": {}})
    slurm.run_pipeline_with_slurm([object(), object()], "config.yaml", tmp_path)

    assert events == [
        ("submit", 0), ("result", 0, 0), ("result", 0, 1),
        ("submit", 1), ("result", 1, 0), ("result", 1, 1),
    ]
    assert submissions[0]["start_at_step"] is None
    assert submissions[0]["stop_at_step"] == "concatenate_sessions"
    assert submissions[1]["split_sessions"] is False


@pytest.mark.parametrize("combine,sessions", [(False, 2), (True, 1)])
def test_independent_sessions_run_without_aggregation(
    monkeypatch, tmp_path, combine, sessions
):
    config = {"bad_channel_detection": {}}
    if combine:
        config["concatenate_sessions"] = {}
    events, submissions = configure_jobs(monkeypatch, config)
    slurm.run_pipeline_with_slurm([object()] * sessions, "config.yaml", tmp_path)

    assert events == [("submit", 0), ("result", 0, 0), ("result", 0, 1)]
    assert len(submissions) == 1
    assert "start_at_step" not in submissions[0]
    assert "stop_at_step" not in submissions[0]


@pytest.mark.parametrize("failed_stage", [0, 1])
def test_worker_failure_prevents_dependent_stages(monkeypatch, tmp_path, failed_stage):
    events, submissions = configure_jobs(
        monkeypatch, {"bad_channel_detection": {}, "concatenate_sessions": {}},
        fail_at=(failed_stage, 1),
    )
    with pytest.raises(RuntimeError, match="Worker failed"):
        slurm.run_pipeline_with_slurm([object(), object()], "config.yaml", tmp_path)

    assert len(submissions) == failed_stage + 1
    assert events[-1] == ("result", failed_stage, 1)
    if failed_stage == 0:
        assert ("union",) not in events
