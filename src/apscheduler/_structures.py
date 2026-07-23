from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Any, TypeAlias
from uuid import UUID, uuid4

import attrs
from attr.setters import frozen
from attrs.validators import and_, gt, instance_of, matches_re, min_len, optional

from ._converters import as_aware_datetime, as_enum, as_timedelta
from ._enums import CoalescePolicy, JobOutcome
from ._utils import UnsetValue, unset
from ._validators import if_not_unset, valid_metadata
from .abc import Serializer, Trigger

MetadataType: TypeAlias = dict[
    str, str | int | bool | None | list["MetadataType"] | dict[str, "MetadataType"]
]


def serialize(inst: Any, field: attrs.Attribute, value: Any) -> Any:
    pass


@attrs.define(kw_only=True, order=False)
class Task:

    id: str = attrs.field(validator=[instance_of(str), min_len(1)], on_setattr=frozen)
    func: str | None = attrs.field(
        validator=optional(and_(instance_of(str), matches_re(r".+:.+"))),
        on_setattr=frozen,
    )
    job_executor: str = attrs.field(validator=instance_of(str), on_setattr=frozen)
    max_running_jobs: int | None = attrs.field(
        default=None,
        validator=optional(and_(instance_of(int), gt(0))),
        on_setattr=frozen,
    )
    misfire_grace_time: timedelta | None = attrs.field(
        default=None,
        converter=as_timedelta,
        validator=optional(instance_of(timedelta)),
        on_setattr=frozen,
    )
    metadata: MetadataType = attrs.field(validator=valid_metadata, factory=dict)
    running_jobs: int = attrs.field(default=0)

    def marshal(self, serializer: Serializer) -> dict[str, Any]:
        pass

    @classmethod
    def unmarshal(cls, serializer: Serializer, marshalled: dict[str, Any]) -> Task:
        pass

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Task):
            return self.id == other.id

        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Task):
            return self.id < other.id

        return NotImplemented


@attrs.define(kw_only=True)
class TaskDefaults:

    job_executor: str | UnsetValue = attrs.field(
        validator=if_not_unset(instance_of(str)), default=unset
    )
    max_running_jobs: int | None | UnsetValue = attrs.field(
        validator=optional(instance_of(int)), default=1
    )
    misfire_grace_time: timedelta | None = attrs.field(
        converter=as_timedelta,
        validator=optional(instance_of(timedelta)),
        default=None,
    )
    metadata: MetadataType = attrs.field(validator=valid_metadata, factory=dict)


@attrs.define(kw_only=True, order=False)
class Schedule:

    id: str = attrs.field(validator=[instance_of(str), min_len(1)], on_setattr=frozen)
    task_id: str = attrs.field(
        validator=[instance_of(str), min_len(1)], on_setattr=frozen
    )
    trigger: Trigger = attrs.field(
        validator=instance_of(Trigger),  # type: ignore[type-abstract]
        on_setattr=frozen,
    )
    args: tuple = attrs.field(converter=tuple, default=())
    kwargs: dict[str, Any] = attrs.field(converter=dict, default=())
    paused: bool = attrs.field(default=False)
    coalesce: CoalescePolicy = attrs.field(
        default=CoalescePolicy.latest,
        converter=as_enum(CoalescePolicy),
        validator=instance_of(CoalescePolicy),
        on_setattr=frozen,
    )
    misfire_grace_time: timedelta | None = attrs.field(
        default=None,
        converter=as_timedelta,
        validator=optional(instance_of(timedelta)),
        on_setattr=frozen,
    )
    max_jitter: timedelta | None = attrs.field(
        converter=as_timedelta,
        default=None,
        validator=optional(instance_of(timedelta)),
        on_setattr=frozen,
    )
    job_executor: str = attrs.field(validator=instance_of(str), on_setattr=frozen)
    job_result_expiration_time: timedelta = attrs.field(
        default=0,
        converter=as_timedelta,
        validator=optional(instance_of(timedelta)),
        on_setattr=frozen,
    )
    metadata: MetadataType = attrs.field(validator=valid_metadata, factory=dict)
    next_fire_time: datetime | None = attrs.field(
        converter=as_aware_datetime,
        default=None,
    )
    last_fire_time: datetime | None = attrs.field(
        converter=as_aware_datetime,
        default=None,
    )
    acquired_by: str | None = attrs.field(default=None)
    acquired_until: datetime | None = attrs.field(
        converter=as_aware_datetime, default=None
    )

    def marshal(self, serializer: Serializer) -> dict[str, Any]:
        pass

    @classmethod
    def unmarshal(cls, serializer: Serializer, marshalled: dict[str, Any]) -> Schedule:
        pass

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Schedule):
            return self.id == other.id

        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Schedule):
            if self.next_fire_time is not None and other.next_fire_time is not None:
                return self.next_fire_time < other.next_fire_time
            elif self.next_fire_time is None:
                return False
            elif other.next_fire_time is None:
                return True

            return self.id < other.id

        return NotImplemented


@attrs.define(kw_only=True, frozen=True)
class ScheduleResult:

    schedule_id: str
    task_id: str
    trigger: Trigger
    last_fire_time: datetime
    next_fire_time: datetime | None


@attrs.define(kw_only=True, order=False)
class Job:

    id: UUID = attrs.field(factory=uuid4, on_setattr=frozen)
    task_id: str = attrs.field(on_setattr=frozen)
    args: tuple = attrs.field(
        converter=tuple, default=(), repr=False, on_setattr=frozen
    )
    kwargs: dict[str, Any] = attrs.field(
        converter=dict, factory=dict, repr=False, on_setattr=frozen
    )
    schedule_id: str | None = attrs.field(default=None, on_setattr=frozen)
    scheduled_fire_time: datetime | None = attrs.field(
        converter=as_aware_datetime, default=None, on_setattr=frozen
    )
    executor: str = attrs.field(on_setattr=frozen)
    jitter: timedelta = attrs.field(
        converter=as_timedelta, factory=timedelta, repr=False, on_setattr=frozen
    )
    start_deadline: datetime | None = attrs.field(
        converter=as_aware_datetime, default=None, repr=False, on_setattr=frozen
    )
    result_expiration_time: timedelta = attrs.field(
        converter=as_timedelta, default=timedelta(), repr=False, on_setattr=frozen
    )
    metadata: MetadataType = attrs.field(validator=valid_metadata, factory=dict)
    created_at: datetime = attrs.field(
        converter=as_aware_datetime,
        factory=partial(datetime.now, timezone.utc),
        on_setattr=frozen,
    )
    acquired_by: str | None = attrs.field(default=None, repr=False)
    acquired_until: datetime | None = attrs.field(
        converter=as_aware_datetime, default=None, repr=False
    )

    @property
    def original_scheduled_time(self) -> datetime | None:
        pass

    def marshal(self, serializer: Serializer) -> dict[str, Any]:
        pass

    @classmethod
    def unmarshal(cls, serializer: Serializer, marshalled: dict[str, Any]) -> Job:
        pass

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Job):
            return self.id == other.id

        return NotImplemented


@attrs.define(kw_only=True, frozen=True, eq=False)
class JobResult:

    job_id: UUID
    outcome: JobOutcome = attrs.field(converter=as_enum(JobOutcome))
    started_at: datetime | None = attrs.field(converter=as_aware_datetime, default=None)
    finished_at: datetime = attrs.field(converter=as_aware_datetime)
    expires_at: datetime = attrs.field(converter=as_aware_datetime, repr=False)
    exception: BaseException | None = attrs.field(default=None, repr=False)
    return_value: Any = attrs.field(default=None, repr=False)

    @classmethod
    def from_job(
        cls,
        job: Job,
        outcome: JobOutcome,
        *,
        finished_at: datetime | None = None,
        started_at: datetime | None = None,
        exception: BaseException | None = None,
        return_value: Any = None,
    ) -> JobResult:
        pass

    def marshal(self, serializer: Serializer) -> dict[str, Any]:
        pass

    @classmethod
    def unmarshal(cls, serializer: Serializer, marshalled: dict[str, Any]) -> JobResult:
        pass

    def __hash__(self) -> int:
        return hash(self.job_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, JobResult):
            return self.job_id == other.job_id

        return NotImplemented
