from __future__ import annotations

import operator
from collections.abc import (
    Callable,
    Iterable,
    Mapping,
    Sequence,
)
from contextlib import AsyncExitStack
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Any, ClassVar, TypeVar, cast
from uuid import UUID

import attrs
import pymongo
from attrs.validators import instance_of
from bson import CodecOptions, UuidRepresentation
from bson.codec_options import TypeEncoder, TypeRegistry
from pymongo import ASCENDING, DeleteOne, UpdateOne
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

from .._enums import CoalescePolicy, ConflictPolicy, JobOutcome
from .._events import (
    DataStoreEvent,
    JobAcquired,
    JobAdded,
    JobReleased,
    ScheduleAdded,
    ScheduleRemoved,
    ScheduleUpdated,
    TaskAdded,
    TaskRemoved,
    TaskUpdated,
)
from .._exceptions import (
    ConflictingIdError,
    DeserializationError,
    SerializationError,
    TaskLookupError,
)
from .._structures import Job, JobResult, Schedule, ScheduleResult, Task
from .._utils import create_repr
from ..abc import EventBroker
from .base import BaseExternalDataStore

T = TypeVar("T", bound=Mapping[str, Any])


class CustomEncoder(TypeEncoder):
    def __init__(self, python_type: type, encoder: Callable):
        self._python_type = python_type
        self._encoder = encoder

    @property
    def python_type(self) -> type:
        pass

    def transform_python(self, value: Any) -> Any:
        pass


def marshal_timestamp(timestamp: datetime | None, key: str) -> Mapping[str, Any]:
    pass


def marshal_document(document: dict[str, Any]) -> None:
    pass


def unmarshal_timestamps(document: dict[str, Any]) -> None:
    pass


@attrs.define(eq=False, repr=False)
class MongoDBDataStore(BaseExternalDataStore):

    client_or_uri: AsyncMongoClient | str = attrs.field(
        validator=instance_of((AsyncMongoClient, str))
    )
    database: str = attrs.field(
        default="apscheduler", kw_only=True, validator=instance_of(str)
    )

    _client: AsyncMongoClient = attrs.field(init=False)
    _close_on_exit: bool = attrs.field(init=False, default=False)
    _task_attrs: ClassVar[list[str]] = [field.name for field in attrs.fields(Task)]
    _schedule_attrs: ClassVar[list[str]] = [
        field.name for field in attrs.fields(Schedule)
    ]
    _job_attrs: ClassVar[list[str]] = [field.name for field in attrs.fields(Job)]
    _tasks: AsyncCollection = attrs.field(init=False)
    _schedules: AsyncCollection = attrs.field(init=False)
    _jobs: AsyncCollection = attrs.field(init=False)
    _jobs_results: AsyncCollection = attrs.field(init=False)

    @property
    def _temporary_failure_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    def __attrs_post_init__(self) -> None:
        if isinstance(self.client_or_uri, str):
            self._client = AsyncMongoClient(self.client_or_uri)
            self._close_on_exit = True
        else:
            self._client = self.client_or_uri

        type_registry = TypeRegistry(
            [
                CustomEncoder(timedelta, timedelta.total_seconds),
                CustomEncoder(ConflictPolicy, operator.attrgetter("name")),
                CustomEncoder(CoalescePolicy, operator.attrgetter("name")),
                CustomEncoder(JobOutcome, operator.attrgetter("name")),
            ]
        )
        codec_options: CodecOptions = CodecOptions(
            type_registry=type_registry,
            uuid_representation=UuidRepresentation.STANDARD,
        )
        database = self._client.get_database(self.database, codec_options=codec_options)
        self._tasks = database["tasks"]
        self._schedules = database["schedules"]
        self._jobs = database["jobs"]
        self._jobs_results = database["job_results"]

    def __repr__(self) -> str:
        server_descriptions = self._client.topology_description.server_descriptions()
        return create_repr(self, host=list(server_descriptions))

    async def _initialize(self) -> None:
        pass

    async def start(
        self, exit_stack: AsyncExitStack, event_broker: EventBroker, logger: Logger
    ) -> None:
        pass

    async def add_task(self, task: Task) -> None:
        pass

    async def remove_task(self, task_id: str) -> None:
        pass

    async def get_task(self, task_id: str) -> Task:
        pass

    async def get_tasks(self) -> list[Task]:
        pass

    async def get_schedules(self, ids: set[str] | None = None) -> list[Schedule]:
        pass

    async def add_schedule(
        self, schedule: Schedule, conflict_policy: ConflictPolicy
    ) -> None:
        pass

    async def remove_schedules(self, ids: Iterable[str]) -> None:
        pass

    async def acquire_schedules(
        self, scheduler_id: str, lease_duration: timedelta, limit: int
    ) -> list[Schedule]:
        pass

    async def release_schedules(
        self, scheduler_id: str, results: Sequence[ScheduleResult]
    ) -> None:
        pass

    async def get_next_schedule_run_time(self) -> datetime | None:
        pass

    async def add_job(self, job: Job) -> None:
        pass

    async def get_jobs(self, ids: Iterable[UUID] | None = None) -> list[Job]:
        pass

    async def acquire_jobs(
        self, scheduler_id: str, lease_duration: timedelta, limit: int | None = None
    ) -> list[Job]:
        pass

    async def _release_job(
        self,
        session: AsyncClientSession,
        result: JobResult,
        scheduler_id: str,
        task_id: str,
        schedule_id: str | None = None,
        scheduled_fire_time: datetime | None = None,
        *,
        decrement_running_job_count: bool = True,
    ) -> JobReleased:
        pass

    async def release_job(self, scheduler_id: str, job: Job, result: JobResult) -> None:
        pass

    async def get_job_result(self, job_id: UUID) -> JobResult | None:
        pass

    async def extend_acquired_schedule_leases(
        self, scheduler_id: str, schedule_ids: set[str], duration: timedelta
    ) -> None:
        pass

    async def extend_acquired_job_leases(
        self, scheduler_id: str, job_ids: set[UUID], duration: timedelta
    ) -> None:
        pass

    async def reap_abandoned_jobs(self, scheduler_id: str) -> None:
        pass

    async def cleanup(self) -> None:
        pass
