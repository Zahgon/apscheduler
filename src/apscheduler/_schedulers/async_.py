from __future__ import annotations

import os
import platform
import random
import sys
from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from contextlib import AsyncExitStack
from datetime import datetime, timedelta, timezone
from functools import partial
from inspect import isbuiltin, isclass, ismethod, ismodule
from logging import Logger, getLogger
from types import TracebackType
from typing import Any, Literal, TypeAlias, TypeVar, cast, overload
from uuid import UUID, uuid4

import anyio
import attrs
from anyio import (
    TASK_STATUS_IGNORED,
    CancelScope,
    create_task_group,
    get_cancelled_exc_class,
    move_on_after,
    sleep,
)
from anyio.abc import TaskGroup, TaskStatus
from attr.validators import instance_of, optional

from .. import JobAdded, SerializationError, TaskLookupError
from .._context import current_async_scheduler, current_job
from .._converters import as_enum, as_timedelta
from .._decorators import TaskParameters, get_task_params
from .._enums import CoalescePolicy, ConflictPolicy, JobOutcome, RunState, SchedulerRole
from .._events import (
    Event,
    JobReleased,
    ScheduleAdded,
    SchedulerStarted,
    SchedulerStopped,
    ScheduleUpdated,
    T_Event,
)
from .._exceptions import (
    CallableLookupError,
    DeserializationError,
    JobCancelled,
    JobDeadlineMissed,
    JobLookupError,
    ScheduleLookupError,
)
from .._marshalling import callable_from_ref, callable_to_ref
from .._structures import (
    Job,
    JobResult,
    MetadataType,
    Schedule,
    ScheduleResult,
    Task,
    TaskDefaults,
)
from .._utils import UnsetValue, create_repr, merge_metadata, unset
from .._validators import non_negative_number
from ..abc import DataStore, EventBroker, JobExecutor, Subscription, Trigger
from ..datastores.memory import MemoryDataStore
from ..eventbrokers.local import LocalEventBroker
from ..executors.async_ import AsyncJobExecutor
from ..executors.subprocess import ProcessPoolJobExecutor
from ..executors.thread import ThreadPoolJobExecutor

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

_microsecond_delta = timedelta(microseconds=1)
_zero_timedelta = timedelta()

TaskType: TypeAlias = "Task | str | Callable[..., Any]"
T = TypeVar("T")


@attrs.define(eq=False, repr=False)
class AsyncScheduler:

    data_store: DataStore = attrs.field(
        validator=instance_of(DataStore), factory=MemoryDataStore
    )
    event_broker: EventBroker = attrs.field(
        validator=instance_of(EventBroker), factory=LocalEventBroker
    )
    identity: str = attrs.field(kw_only=True, validator=instance_of(str), default="")
    role: SchedulerRole = attrs.field(
        kw_only=True, converter=as_enum(SchedulerRole), default=SchedulerRole.both
    )
    task_defaults: TaskDefaults = attrs.field(kw_only=True, factory=TaskDefaults)
    max_concurrent_jobs: int = attrs.field(
        kw_only=True, validator=non_negative_number, default=100
    )
    job_executors: MutableMapping[str, JobExecutor] = attrs.field(
        kw_only=True, validator=instance_of(MutableMapping), factory=dict
    )
    cleanup_interval: timedelta | None = attrs.field(
        kw_only=True,
        converter=as_timedelta,
        validator=optional(instance_of(timedelta)),
        default=timedelta(minutes=15),
    )
    lease_duration: timedelta = attrs.field(converter=as_timedelta, default=30)
    logger: Logger = attrs.field(kw_only=True, default=getLogger(__name__))

    _state: RunState = attrs.field(init=False, default=RunState.stopped)
    _services_task_group: TaskGroup | None = attrs.field(init=False, default=None)
    _exit_stack: AsyncExitStack = attrs.field(init=False)
    _services_initialized: bool = attrs.field(init=False, default=False)
    _scheduler_cancel_scope: CancelScope | None = attrs.field(init=False, default=None)
    _running_jobs: set[Job] = attrs.field(init=False, factory=set)
    _task_callables: dict[str, Callable] = attrs.field(init=False, factory=dict)

    def __attrs_post_init__(self) -> None:
        if not self.identity:
            self.identity = f"{platform.node()}-{os.getpid()}-{id(self)}"

        if not self.job_executors:
            self.job_executors = {
                "async": AsyncJobExecutor(),
                "threadpool": ThreadPoolJobExecutor(),
                "processpool": ProcessPoolJobExecutor(),
            }

        if self.task_defaults.job_executor is unset:
            self.task_defaults.job_executor = next(iter(self.job_executors))
        elif self.task_defaults.job_executor not in self.job_executors:
            valid_executors = ", ".join(self.job_executors)
            raise ValueError(
                f"the default job executor must be one of the given job executors "
                f"({valid_executors})"
            )

        if self.task_defaults.max_running_jobs is unset:
            self.task_defaults.max_running_jobs = 1

        if self.task_defaults.misfire_grace_time is unset:
            self.task_defaults.misfire_grace_time = None

    async def __aenter__(self) -> Self:
        async with AsyncExitStack() as exit_stack:
            await self._ensure_services_initialized(exit_stack)
            self._services_task_group = await exit_stack.enter_async_context(
                create_task_group()
            )
            exit_stack.callback(setattr, self, "_services_task_group", None)
            exit_stack.push_async_callback(self.stop)
            self._exit_stack = exit_stack.pop_all()

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    def __repr__(self) -> str:
        return create_repr(self, "identity", "role", "data_store", "event_broker")

    async def _ensure_services_initialized(self, exit_stack: AsyncExitStack) -> None:
        pass

    def _check_initialized(self) -> None:
        pass

    async def _cleanup_loop(self) -> None:
        pass

    @property
    def state(self) -> RunState:
        pass

    async def cleanup(self) -> None:
        pass

    @overload
    def subscribe(
        self,
        callback: Callable[[T_Event], Any],
        event_types: type[T_Event],
        *,
        one_shot: bool = ...,
        is_async: bool = ...,
    ) -> Subscription: ...

    @overload
    def subscribe(
        self,
        callback: Callable[[Event], Any],
        event_types: Iterable[type[Event]] | None = None,
        *,
        one_shot: bool = False,
        is_async: bool = True,
    ) -> Subscription: ...

    def subscribe(
        self,
        callback: Callable[[T_Event], Any],
        event_types: type[T_Event] | Iterable[type[T_Event]] | None = None,
        *,
        one_shot: bool = False,
        is_async: bool = True,
    ) -> Subscription:
        pass

    @overload
    async def get_next_event(self, event_types: type[T_Event]) -> T_Event: ...

    @overload
    async def get_next_event(self, event_types: Iterable[type[Event]]) -> Event: ...

    async def get_next_event(
        self, event_types: type[Event] | Iterable[type[Event]]
    ) -> Event:
        pass

    async def configure_task(
        self,
        func_or_task_id: TaskType,
        *,
        func: Callable[..., Any] | UnsetValue = unset,
        job_executor: str | UnsetValue = unset,
        misfire_grace_time: float | timedelta | None | UnsetValue = unset,
        max_running_jobs: int | None | UnsetValue = unset,
        metadata: MetadataType | UnsetValue = unset,
    ) -> Task:
        pass

    async def get_tasks(self) -> Sequence[Task]:
        pass

    async def add_schedule(
        self,
        func_or_task_id: TaskType,
        trigger: Trigger,
        *,
        id: str | None = None,
        args: Iterable[Any] | None = None,
        kwargs: Mapping[str, Any] | None = None,
        paused: bool = False,
        coalesce: CoalescePolicy = CoalescePolicy.latest,
        job_executor: str | UnsetValue = unset,
        misfire_grace_time: float | timedelta | None | UnsetValue = unset,
        metadata: MetadataType | UnsetValue = unset,
        max_jitter: float | timedelta | None = None,
        job_result_expiration_time: float | timedelta = 0,
        conflict_policy: ConflictPolicy = ConflictPolicy.do_nothing,
    ) -> str:
        pass

    async def get_schedule(self, id: str) -> Schedule:
        pass

    async def get_schedules(self) -> list[Schedule]:
        pass

    async def remove_schedule(self, id: str) -> None:
        pass

    async def pause_schedule(self, id: str) -> None:
        pass

    async def unpause_schedule(
        self,
        id: str,
        *,
        resume_from: datetime | Literal["now"] | None = None,
    ) -> None:
        pass

    async def add_job(
        self,
        func_or_task_id: TaskType,
        *,
        args: Iterable[Any] | None = None,
        kwargs: Mapping[str, Any] | None = None,
        job_executor: str | UnsetValue = unset,
        metadata: MetadataType | UnsetValue = unset,
        result_expiration_time: timedelta | float = 0,
    ) -> UUID:
        pass

    async def get_jobs(self) -> Sequence[Job]:
        pass

    async def get_job_result(
        self, job_id: UUID, *, wait: bool = True
    ) -> JobResult | None:
        pass

    async def run_job(
        self,
        func_or_task_id: str | Callable[..., Any],
        *,
        args: Iterable[Any] | None = None,
        kwargs: Mapping[str, Any] | None = None,
        job_executor: str | UnsetValue = unset,
        metadata: MetadataType | UnsetValue = unset,
    ) -> Any:
        pass

    async def stop(self) -> None:
        pass

    async def wait_until_stopped(self) -> None:
        pass

    async def start_in_background(self) -> None:
        pass

    async def run_until_stopped(
        self, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED
    ) -> None:
        pass

    async def _process_schedules(self, *, task_status: TaskStatus[None]) -> None:
        pass

    def _get_task_callable(self, task: Task) -> Callable:
        pass

    async def _process_jobs(self, *, task_status: TaskStatus[None]) -> None:
        pass

    async def _run_job(self, job: Job, func: Callable[..., Any], executor: str) -> None:
        pass
