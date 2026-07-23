from __future__ import annotations

from collections import defaultdict
from collections.abc import AsyncGenerator, Iterable, Mapping, Sequence
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timedelta, timezone
from functools import partial
from logging import Logger
from typing import Any, cast
from uuid import UUID

import anyio
import attrs
import tenacity
from anyio import CancelScope, to_thread
from attr.validators import instance_of
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    Interval,
    LargeBinary,
    MetaData,
    SmallInteger,
    Table,
    TypeDecorator,
    Unicode,
    Uuid,
    and_,
    bindparam,
    create_engine,
    false,
    or_,
    select,
)
from sqlalchemy.engine import URL, Dialect, Result
from sqlalchemy.exc import (
    CompileError,
    IntegrityError,
    InterfaceError,
    InvalidRequestError,
    ProgrammingError,
)
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.future import Connection, Engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql import Executable
from sqlalchemy.sql.ddl import DropTable
from sqlalchemy.sql.elements import BindParameter, literal
from sqlalchemy.sql.type_api import TypeEngine

from .._enums import CoalescePolicy, ConflictPolicy, JobOutcome
from .._events import (
    DataStoreEvent,
    Event,
    JobAcquired,
    JobAdded,
    JobDeserializationFailed,
    JobReleased,
    ScheduleAdded,
    ScheduleDeserializationFailed,
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
from .._utils import create_repr, current_async_library
from ..abc import EventBroker
from .base import BaseExternalDataStore


class EmulatedTimestampTZ(TypeDecorator[datetime]):
    impl = Unicode(32)
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> str | None:
        pass

    def process_result_value(
        self, value: str | None, dialect: Dialect
    ) -> datetime | None:
        pass


class EmulatedInterval(TypeDecorator[timedelta]):
    impl = BigInteger()
    cache_ok = True

    def process_bind_param(
        self, value: timedelta | None, dialect: Dialect
    ) -> float | None:
        pass

    def process_result_value(
        self, value: int | None, dialect: Dialect
    ) -> timedelta | None:
        pass


def marshal_timestamp(timestamp: datetime | None, key: str) -> Mapping[str, Any]:
    pass


@attrs.define(eq=False, frozen=True)
class _JobDiscard:
    job_id: UUID
    outcome: JobOutcome
    task_id: str
    schedule_id: str | None
    scheduled_fire_time: datetime | None
    result_expires_at: datetime
    exception: Exception | None = None


@attrs.define(eq=False, repr=False)
class SQLAlchemyDataStore(BaseExternalDataStore):

    engine_or_url: str | URL | Engine | AsyncEngine = attrs.field(
        validator=instance_of((str, URL, Engine, AsyncEngine))
    )
    schema: str | None = attrs.field(kw_only=True, default=None)

    _engine: Engine | AsyncEngine = attrs.field(init=False)
    _close_on_exit: bool = attrs.field(init=False, default=False)
    _supports_update_returning: bool = attrs.field(init=False, default=False)
    _supports_tzaware_timestamps: bool = attrs.field(init=False, default=False)
    _supports_native_interval: bool = attrs.field(init=False, default=False)
    _metadata: MetaData = attrs.field(init=False)
    _t_metadata: Table = attrs.field(init=False)
    _t_tasks: Table = attrs.field(init=False)
    _t_schedules: Table = attrs.field(init=False)
    _t_jobs: Table = attrs.field(init=False)
    _t_job_results: Table = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        if isinstance(self.engine_or_url, (str, URL)):
            try:
                self._engine = create_async_engine(self.engine_or_url)
            except InvalidRequestError:
                self._engine = create_engine(self.engine_or_url)

            self._close_on_exit = True
        else:
            self._engine = self.engine_or_url

        prefix = f"{self.schema}." if self.schema else ""
        self._supports_tzaware_timestamps = self._engine.dialect.name in (
            "postgresql",
            "oracle",
        )
        self._supports_native_interval = self._engine.dialect.name == "postgresql"
        self._metadata = self.get_table_definitions()
        self._t_metadata = self._metadata.tables[prefix + "metadata"]
        self._t_tasks = self._metadata.tables[prefix + "tasks"]
        self._t_schedules = self._metadata.tables[prefix + "schedules"]
        self._t_jobs = self._metadata.tables[prefix + "jobs"]
        self._t_job_results = self._metadata.tables[prefix + "job_results"]

    def __repr__(self) -> str:
        return create_repr(self, url=repr(self._engine.url), schema=self.schema)

    def _retry(self) -> tenacity.AsyncRetrying:
        pass

    @asynccontextmanager
    async def _begin_transaction(
        self,
    ) -> AsyncGenerator[Connection | AsyncConnection, None]:
        pass

    async def _create_metadata(self, conn: Connection | AsyncConnection) -> None:
        pass

    async def _execute(
        self,
        conn: Connection | AsyncConnection,
        statement: Executable,
        parameters: Sequence | Mapping | None = None,
    ):
        pass

    @property
    def _temporary_failure_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    def _convert_incoming_fire_times(self, data: dict[str, Any]) -> dict[str, Any]:
        pass

    def _convert_outgoing_fire_times(self, data: dict[str, Any]) -> dict[str, Any]:
        pass

    def get_table_definitions(self) -> MetaData:
        pass

    async def start(
        self, exit_stack: AsyncExitStack, event_broker: EventBroker, logger: Logger
    ) -> None:
        pass

    async def _deserialize_schedules(self, result: Result) -> list[Schedule]:
        pass

    async def _deserialize_jobs(self, result: Result) -> list[Job]:
        pass

    async def add_task(self, task: Task) -> None:
        pass

    async def remove_task(self, task_id: str) -> None:
        pass

    async def get_task(self, task_id: str) -> Task:
        pass

    async def get_tasks(self) -> list[Task]:
        pass

    async def add_schedule(
        self, schedule: Schedule, conflict_policy: ConflictPolicy
    ) -> None:
        pass

    async def remove_schedules(self, ids: Iterable[str]) -> None:
        pass

    async def get_schedules(self, ids: set[str] | None = None) -> list[Schedule]:
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
        conn: Connection | AsyncConnection,
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
