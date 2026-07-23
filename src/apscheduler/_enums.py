from __future__ import annotations

from enum import Enum, auto


class SchedulerRole(Enum):

    scheduler = auto()
    worker = auto()
    both = auto()


class RunState(Enum):

    starting = auto()
    started = auto()
    stopping = auto()
    stopped = auto()


class JobOutcome(Enum):

    success = auto()
    error = auto()
    missed_start_deadline = auto()
    deserialization_failed = auto()
    cancelled = auto()
    abandoned = auto()


class ConflictPolicy(Enum):

    replace = auto()
    do_nothing = auto()
    exception = auto()


class CoalescePolicy(Enum):

    earliest = auto()
    latest = auto()
    all = auto()
