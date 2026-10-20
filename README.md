# spikesorted

An end-to-end pipeline for spike sorting extracellular electrophysiology recordings.

Pre-alpha: the pipeline is under development. This checkout currently contains
project scaffolding and example modules.

The Python package lives in `src/spikesorted/`, with `tests/` and `docs/` at
repository root. Run development commands from this directory:

```sh
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check --no-fix src tests
```

Activate `.venv` before installing or running these commands.
