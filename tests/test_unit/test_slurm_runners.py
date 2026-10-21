"""Check generic callable arguments and result ordering without SLURM."""

from contextlib import contextmanager

from spikesorted.slurm import slurm_runners


def test_batch_forwards_arguments_and_waits_after_submission(monkeypatch, tmp_path):
    events = []

    class Job:
        def __init__(self, function, args, kwargs):
            self.function = function
            self.args = args
            self.kwargs = kwargs

        def result(self):
            assert "submitted" in events
            return self.function(*self.args, **self.kwargs)

    class Executor:
        def __init__(self, **kwargs):
            pass

        def update_parameters(self, **kwargs):
            pass

        @contextmanager
        def batch(self):
            yield
            events.append("submitted")

        def submit(self, function, *args, **kwargs):
            assert "submitted" not in events
            return Job(function, args, kwargs)

    monkeypatch.setattr(slurm_runners.submitit, "AutoExecutor", Executor)

    def scale(value, *, factor):
        return value * factor

    results = slurm_runners.run_slurm_batch(
        [(scale, (3,), {"factor": 4}), (str, (7,), {})], tmp_path,
    )
    assert results == [12, "7"]
