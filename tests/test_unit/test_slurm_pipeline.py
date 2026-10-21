"""Check synchronization and session/shank grouping between pipeline stages."""

import pytest

from spikesorted.slurm import slurm_for_pipeline as slurm


def configure_jobs(monkeypatch, fail_at=None):
    events, batches = [], []
    monkeypatch.setattr(slurm, "load_configs", lambda path: {
        "bad_channel_detection": {}, "combine_sessions": {},
    })

    def run_batch(calls, project_path, num_cores, slurm_opts):
        stage = len(batches)
        pipelines = [function.__self__ for function, args, kwargs in calls]
        batches.append(pipelines)
        events.append(("submit", stage))
        for index in range(len(pipelines)):
            events.append(("result", stage, index))
            if (stage, index) == fail_at:
                raise RuntimeError("Worker failed")
        return list(range(len(pipelines)))

    monkeypatch.setattr(slurm, "run_slurm_batch", run_batch)
    monkeypatch.setattr(
        slurm, "create_bad_channel_labels_union",
        lambda recordings, path: events.append(("union", recordings, path)),
    )
    return events, batches


def test_detection_union_preprocessing_then_combination(monkeypatch, tmp_path):
    events, batches = configure_jobs(monkeypatch)
    a, b, c, d = [object() for _ in range(4)]
    recordings = [
        ({"left": a, "right": b}, "first"),
        ({"right": d, "left": c}, "second"),
    ]
    result = slurm.run_pipeline_with_slurm(
        recordings, "config.yaml", tmp_path, overwrite=True, num_cores=4,
    )

    assert events == [
        ("submit", 0), *(("result", 0, i) for i in range(4)),
        ("union", recordings, tmp_path),
        ("submit", 1), *(("result", 1, i) for i in range(4)),
        ("submit", 2), ("result", 2, 0), ("result", 2, 1),
    ]
    assert all(p.start_at_step is None for p in batches[0])
    assert all(p.stop_after_step == "bad_channel_detection" for p in batches[0])
    assert all(p.start_at_step == "preprocessing" for p in batches[1])
    assert all(p.stop_after_step == "preprocessing" for p in batches[1])
    assert [p.recordings for p in batches[1]] == [p.recordings for p in batches[0]]
    assert all(p.start_at_step == "combine_sessions" for p in batches[2])
    assert all(p.stop_after_step is None for p in batches[2])
    assert [p.recordings for p in batches[2]] == [
        [({"left": a}, "first"), ({"left": c}, "second")],
        [({"right": b}, "first"), ({"right": d}, "second")],
    ]
    for batch in batches:
        assert all(p.project_path == tmp_path for p in batch)
        assert all(p.num_cores == 4 and p.overwrite for p in batch)
    assert result == [0, 1]


@pytest.mark.parametrize("failed_stage", [0, 1, 2])
def test_worker_failure_prevents_dependent_stages(monkeypatch, tmp_path, failed_stage):
    events, batches = configure_jobs(monkeypatch, fail_at=(failed_stage, 0))
    with pytest.raises(RuntimeError, match="Worker failed"):
        slurm.run_pipeline_with_slurm([object(), object()], "config.yaml", tmp_path)

    assert len(batches) == failed_stage + 1
    assert events[-1] == ("result", failed_stage, 0)
    if failed_stage == 0:
        assert not any(event[0] == "union" for event in events)


def test_union_failure_prevents_preprocessing(monkeypatch, tmp_path):
    _, batches = configure_jobs(monkeypatch)

    def fail_union(recordings, project_path):
        raise ValueError("Missing detection outputs")

    monkeypatch.setattr(slurm, "create_bad_channel_labels_union", fail_union)
    with pytest.raises(ValueError, match="Missing detection outputs"):
        slurm.run_pipeline_with_slurm([object(), object()], "config.yaml", tmp_path)
    assert len(batches) == 1


def test_unsplit_sessions_combine_in_original_order(monkeypatch, tmp_path):
    _, batches = configure_jobs(monkeypatch)
    a, b = object(), object()
    slurm.run_pipeline_with_slurm([a, b], "config.yaml", tmp_path)
    assert len(batches[2]) == 1
    assert batches[2][0].recordings == [
        ({"none": a}, "session_0"), ({"none": b}, "session_1"),
    ]
