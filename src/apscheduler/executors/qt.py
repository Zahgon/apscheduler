from __future__ import annotations

import sys
from collections.abc import Callable
from concurrent.futures import Future
from contextlib import AsyncExitStack
from typing import Any, TypeVar

import anyio
import attrs
from anyio.from_thread import BlockingPortal

from apscheduler import Job, current_job
from apscheduler.abc import JobExecutor

if "PySide6" in sys.modules:
    from PySide6.QtCore import QObject, Signal
elif "PyQt6" in sys.modules:
    from PyQt6.QtCore import QObject
    from PyQt6.QtCore import pyqtSignal as Signal
else:
    try:
        from PySide6.QtCore import QObject, Signal
    except ImportError:
        from PyQt6.QtCore import QObject
        from PyQt6.QtCore import pyqtSignal as Signal

T_Retval = TypeVar("T_Retval")


class _SchedulerSignals(QObject):
    run_job = Signal(tuple)


@attrs.define(eq=False)
class QtJobExecutor(JobExecutor):
    _signals: _SchedulerSignals = attrs.field(init=False, factory=_SchedulerSignals)
    _portal: BlockingPortal = attrs.field(init=False)

    def __attrs_post_init__(self):
        self._signals.run_job.connect(self.run_in_qt_thread)

    async def start(self, exit_stack: AsyncExitStack) -> None:
        pass

    async def run_job(self, func: Callable[..., T_Retval], job: Job) -> Any:
        pass

    def run_in_qt_thread(
        self,
        parameters: tuple[Callable[..., T_Retval], Job, Future[T_Retval], anyio.Event],
    ) -> Any:
        pass
