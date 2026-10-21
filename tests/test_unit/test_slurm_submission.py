"""Check independent pipeline array submission without a SLURM cluster."""

from contextlib import contextmanager

import pytest

from spikesorted.slurm import slurm_for_pipeline as slurm
from spikesorted.slurm import slurm_runners
from spikesorted.utils import get_recordings_and_paths


@pytest.fixture
def scheduler(monkeypatch):
    events = []
    pipelines = []
    settings = {}

    class Job:
        def result(self):
            assert events[-1] in ("batch submitted", "result")
            events.append("result")
            return "finished"

    class Executor:
        def __init__(self, **kwargs):
            settings.update(kwargs)

        def update_parameters(self, **kwargs):
            settings.update(kwargs)

        @contextmanager
        def batch(self):
            events.append("batch started")
            yield
            events.append("batch submitted")

        def submit(self, function):
            assert events[-1] in ("batch started", "submit")
            pipelines.append(function.__self__)
            events.append("submit")
            return Job()

    monkeypatch.setattr(slurm_runners.submitit, "AutoExecutor", Executor)
    return events, pipelines, settings


@pytest.mark.parametrize("config", [
    {"bad_channel_detection": {}},
    {"combine_sessions": {}},
])
def test_sessions_and_shanks_submit_together(monkeypatch, tmp_path, scheduler, config):
    monkeypatch.setattr(slurm, "load_configs", lambda path: config)
    a, b, c = object(), object(), object()
    events, pipelines, settings = scheduler

    results = slurm.run_pipeline_with_slurm(
        [({"left": a, "right": b}, "day_one"), {"left": c}],
        "config.yaml", tmp_path, overwrite=True, num_cores=4, verbose=False,
        slurm_opts={"slurm_partition": "cpu", "mem_gb": 8},
    )

    assert [pipeline.recordings for pipeline in pipelines] == [
        ({"left": a}, "day_one"), ({"right": b}, "day_one"),
        ({"left": c}, "session_1"),
    ]
    assert [pipeline.project_path for pipeline in pipelines] == [
        tmp_path, tmp_path, tmp_path,
    ]
    assert [
        get_recordings_and_paths(pipeline.recordings, pipeline.project_path, "step")[0][3]
        for pipeline in pipelines
    ] == [
        tmp_path / "step" / "day_one" / "shank_left",
        tmp_path / "step" / "day_one" / "shank_right",
        tmp_path / "step" / "session_1" / "shank_left",
    ]
    assert all(pipeline.config_path == "config.yaml" for pipeline in pipelines)
    assert all(pipeline.overwrite for pipeline in pipelines)
    assert all(pipeline.num_cores == 4 for pipeline in pipelines)
    assert all(pipeline.verbose is False for pipeline in pipelines)
    assert settings["cluster"] == "slurm"
    assert settings["cpus_per_task"] == 4
    assert settings["slurm_partition"] == "cpu"
    assert settings["mem_gb"] == 8
    assert events == [
        "batch started", "submit", "submit", "submit", "batch submitted",
        "result", "result", "result",
    ]
    assert results == ["finished"] * 3


def test_single_unsplit_recording_keeps_project_root(monkeypatch, tmp_path, scheduler):
    monkeypatch.setattr(slurm, "load_configs", lambda path: {})
    recording = object()
    slurm.run_pipeline_with_slurm(recording, "config.yaml", tmp_path)
    _, pipelines, _ = scheduler
    assert len(pipelines) == 1
    assert pipelines[0].recordings == {"none": recording}
    assert pipelines[0].project_path == tmp_path


def test_worker_failure_is_propagated(monkeypatch, tmp_path, scheduler):
    monkeypatch.setattr(slurm, "load_configs", lambda path: {})

    class FailedJob:
        def result(self):
            raise RuntimeError("Worker failed")

    monkeypatch.setattr(
        slurm_runners.submitit.AutoExecutor, "submit", lambda self, function: FailedJob()
    )
    with pytest.raises(RuntimeError, match="Worker failed"):
        slurm.run_pipeline_with_slurm(object(), "config.yaml", tmp_path)


