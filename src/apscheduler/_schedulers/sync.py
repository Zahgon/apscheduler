from __future__ import annotations

import atexit
import sys
import threading
from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from datetime import datetime, timedelta
from functools import partial
from logging import Logger
from types import TracebackType
from typing import Any, Literal, overload
from uuid import UUID

import attrs
from anyio.from_thread import BlockingPortal, start_blocking_portal

from .. import current_scheduler
from .._enums import CoalescePolicy, ConflictPolicy, RunState, SchedulerRole
from .._events import Event, T_Event
from .._structures import Job, JobResult, MetadataType, Schedule, Task, TaskDefaults
from .._utils import UnsetValue, create_repr, unset
from ..abc import DataStore, EventBroker, JobExecutor, Subscription, Trigger
from .async_ import AsyncScheduler, TaskType

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


@attrs.define(init=False, repr=False)
class Scheduler:

    _async_scheduler: AsyncScheduler
    _exit_stack: ExitStack = attrs.field(init=False, factory=ExitStack)
    _portal: BlockingPortal | None = attrs.field(init=False, default=None)
    _lock: threading.Lock = attrs.field(init=False, factory=threading.Lock)

    def __init__(
        self,
        data_store: DataStore | None = None,
        event_broker: EventBroker | None = None,
        *,
        identity: str = "",
        role: SchedulerRole = SchedulerRole.both,
        max_concurrent_jobs: int = 100,
        cleanup_interval: float | timedelta | None = None,
        lease_duration: timedelta = timedelta(seconds=30),
        job_executors: MutableMapping[str, JobExecutor] | None = None,
        task_defaults: TaskDefaults | None = None,
        logger: Logger | None = None,
    ):
        kwargs: dict[str, Any] = {}
        if data_store is not None:
            kwargs["data_store"] = data_store

        if event_broker is not None:
            kwargs["event_broker"] = event_broker

        if logger is not None:
            kwargs["logger"] = logger

        if task_defaults is None:
            task_defaults = TaskDefaults()

        if task_defaults.job_executor is unset:
            task_defaults.job_executor = "threadpool"

        async_scheduler = AsyncScheduler(
            identity=identity,
            role=role,
            task_defaults=task_defaults,
            max_concurrent_jobs=max_concurrent_jobs,
            job_executors=job_executors or {},
            cleanup_interval=cleanup_interval,
            lease_duration=lease_duration,
            **kwargs,
        )
        self.__attrs_init__(async_scheduler=async_scheduler)

    @property
    def logger(self) -> Logger:
        pass

    @property
    def data_store(self) -> DataStore:
        pass

    @property
    def event_broker(self) -> EventBroker:
        pass

    @property
    def identity(self) -> str:
        pass

    @property
    def role(self) -> SchedulerRole:
        pass

    @property
    def max_concurrent_jobs(self) -> int:
        pass

    @property
    def cleanup_interval(self) -> timedelta | None:
        pass

    @property
    def lease_duration(self) -> timedelta:
        pass

    @property
    def job_executors(self) -> MutableMapping[str, JobExecutor]:
        pass

    @property
    def task_defaults(self) -> TaskDefaults:
        pass

    @property
    def state(self) -> RunState:
        pass

    def __enter__(self: Self) -> Self:
        self._ensure_services_ready(self._exit_stack)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._exit_stack.__exit__(exc_type, exc_val, exc_tb)

    def _ensure_services_ready(
        self, exit_stack: ExitStack | None = None
    ) -> BlockingPortal:
        pass

    def __repr__(self) -> str:
        return create_repr(self, "identity", "role", "data_store", "event_broker")

    def cleanup(self) -> None:
        pass

    @overload
    def subscribe(
        self,
        callback: Callable[[T_Event], Any],
        event_types: type[T_Event],
        *,
        one_shot: bool = ...,
    ) -> Subscription: ...

    @overload
    def subscribe(
        self,
        callback: Callable[[Event], Any],
        event_types: Iterable[type[Event]] | None = None,
        *,
        one_shot: bool = False,
    ) -> Subscription: ...

    def subscribe(
        self,
        callback: Callable[[T_Event], Any],
        event_types: type[T_Event] | Iterable[type[T_Event]] | None = None,
        *,
        one_shot: bool = False,
    ) -> Subscription:
        pass

    @overload
    def get_next_event(self, event_types: type[T_Event]) -> T_Event: ...

    @overload
    def get_next_event(self, event_types: Iterable[type[Event]]) -> Event: ...

    def get_next_event(self, event_types: type[Event] | Iterable[type[Event]]) -> Event:
        pass

    def configure_task(
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

    def get_tasks(self) -> Sequence[Task]:
        pass

    def add_schedule(
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

    def get_schedule(self, id: str) -> Schedule:
        pass

    def get_schedules(self) -> list[Schedule]:
        pass

    def remove_schedule(self, id: str) -> None:
        pass

    def pause_schedule(self, id: str) -> None:
        pass

    def unpause_schedule(
        self,
        id: str,
        *,
        resume_from: datetime | Literal["now"] | None = None,
    ) -> None:
        pass

    def add_job(
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

    def get_jobs(self) -> Sequence[Job]:
        pass

    def get_job_result(self, job_id: UUID, *, wait: bool = True) -> JobResult | None:
        pass

    def run_job(
        self,
        func_or_task_id: str | Callable[..., Any],
        *,
        args: Iterable[Any] | None = None,
        kwargs: Mapping[str, Any] | None = None,
        job_executor: str | UnsetValue = unset,
        metadata: MetadataType | UnsetValue = unset,
    ) -> Any:
        pass

    def start_in_background(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def wait_until_stopped(self) -> None:
        pass

    def run_until_stopped(self) -> None:
        pass


for attrname in dir(AsyncScheduler):
    if attrname.startswith("_"):
        continue

    value = getattr(AsyncScheduler, attrname)
    if callable(value):
        sync_method = getattr(Scheduler, attrname, None)
        if sync_method and not sync_method.__doc__:
            sync_method.__doc__ = value.__doc__
