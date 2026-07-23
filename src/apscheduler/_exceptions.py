from __future__ import annotations

from uuid import UUID


class TaskLookupError(LookupError):

    def __init__(self, task_id: str):
        super().__init__(f"No task by the id of {task_id!r} was found")


class ScheduleLookupError(LookupError):

    def __init__(self, schedule_id: str):
        super().__init__(f"No schedule by the id of {schedule_id!r} was found")


class JobLookupError(LookupError):

    def __init__(self, job_id: UUID):
        super().__init__(f"No job by the id of {job_id} was found")


class CallableLookupError(LookupError):
    pass


class JobResultNotReady(Exception):

    def __init__(self, job_id: UUID):
        super().__init__(f"No job by the id of {job_id} was found")


class JobCancelled(Exception):
    pass


class JobDeadlineMissed(Exception):
    pass


class ConflictingIdError(KeyError):

    def __init__(self, schedule_id):
        super().__init__(
            f"This data store already contains a schedule with the identifier "
            f"{schedule_id!r}"
        )


class SerializationError(Exception):
    pass


class DeserializationError(Exception):
    pass


class MaxIterationsReached(Exception):
    pass
