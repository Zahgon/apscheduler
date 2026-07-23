from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from traceback import format_tb
from typing import Any, TypeVar
from uuid import UUID

import attrs
from attrs.converters import optional

from ._converters import as_aware_datetime, as_enum, as_uuid
from ._enums import JobOutcome
from ._structures import Job, JobResult
from ._utils import qualified_name

T_Event = TypeVar("T_Event", bound="Event")


@attrs.define(kw_only=True, frozen=True)
class Event:

    timestamp: datetime = attrs.field(
        factory=partial(datetime.now, timezone.utc), converter=as_aware_datetime
    )

    def marshal(self) -> dict[str, Any]:
        pass

    @classmethod
    def unmarshal(cls, marshalled: dict[str, Any]) -> Event:
        pass




@attrs.define(kw_only=True, frozen=True)
class DataStoreEvent(Event):
    pass


@attrs.define(kw_only=True, frozen=True)
class TaskAdded(DataStoreEvent):

    task_id: str


@attrs.define(kw_only=True, frozen=True)
class TaskUpdated(DataStoreEvent):

    task_id: str


@attrs.define(kw_only=True, frozen=True)
class TaskRemoved(DataStoreEvent):

    task_id: str


@attrs.define(kw_only=True, frozen=True)
class ScheduleAdded(DataStoreEvent):

    schedule_id: str
    task_id: str
    next_fire_time: datetime | None = attrs.field(converter=optional(as_aware_datetime))


@attrs.define(kw_only=True, frozen=True)
class ScheduleUpdated(DataStoreEvent):

    schedule_id: str
    task_id: str
    next_fire_time: datetime | None = attrs.field(converter=optional(as_aware_datetime))


@attrs.define(kw_only=True, frozen=True)
class ScheduleRemoved(DataStoreEvent):

    schedule_id: str
    task_id: str
    finished: bool


@attrs.define(kw_only=True, frozen=True)
class JobAdded(DataStoreEvent):

    job_id: UUID = attrs.field(converter=as_uuid)
    task_id: str
    schedule_id: str | None


@attrs.define(kw_only=True, frozen=True)
class JobRemoved(DataStoreEvent):

    job_id: UUID = attrs.field(converter=as_uuid)
    task_id: str


@attrs.define(kw_only=True, frozen=True)
class ScheduleDeserializationFailed(DataStoreEvent):

    schedule_id: str
    exception: BaseException


@attrs.define(kw_only=True, frozen=True)
class JobDeserializationFailed(DataStoreEvent):

    job_id: UUID = attrs.field(converter=as_uuid)
    exception: BaseException




@attrs.define(kw_only=True, frozen=True)
class SchedulerEvent(Event):
    pass


@attrs.define(kw_only=True, frozen=True)
class SchedulerStarted(SchedulerEvent):
    pass


@attrs.define(kw_only=True, frozen=True)
class SchedulerStopped(SchedulerEvent):

    exception: BaseException | None = None


@attrs.define(kw_only=True, frozen=True)
class JobAcquired(SchedulerEvent):

    job_id: UUID = attrs.field(converter=as_uuid)
    scheduler_id: str
    task_id: str
    schedule_id: str | None = None
    scheduled_start: datetime | None = attrs.field(converter=as_aware_datetime)

    @classmethod
    def from_job(cls, job: Job, scheduler_id: str) -> JobAcquired:
        pass


@attrs.define(kw_only=True, frozen=True)
class JobReleased(SchedulerEvent):

    job_id: UUID = attrs.field(converter=as_uuid)
    scheduler_id: str
    task_id: str
    schedule_id: str | None = None
    scheduled_start: datetime | None = attrs.field(converter=as_aware_datetime)
    started_at: datetime | None = attrs.field(converter=as_aware_datetime)
    outcome: JobOutcome = attrs.field(converter=as_enum(JobOutcome))
    exception_type: str | None = None
    exception_message: str | None = None
    exception_traceback: list[str] | None = None

    @classmethod
    def from_result(
        cls,
        result: JobResult,
        scheduler_id: str,
        task_id: str,
        schedule_id: str | None,
        scheduled_fire_time: datetime | None = None,
    ) -> JobReleased:
        pass

    def marshal(self) -> dict[str, Any]:
        pass
