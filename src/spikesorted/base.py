"""Recording input type aliases."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spikeinterface.core import BaseRecording

    Recording = str | Path | BaseRecording
    SessionRecording = Recording | dict[str | int, BaseRecording]
    RecordingInput = SessionRecording | tuple[SessionRecording, str]
