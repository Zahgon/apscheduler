from __future__ import annotations

from datetime import date, timedelta, tzinfo
from enum import Enum
from json import dumps, loads
from typing import Any
from uuid import UUID

import attrs

from .. import DeserializationError, SerializationError
from .._marshalling import (
    marshal_object,
    marshal_timezone,
    unmarshal_object,
)
from ..abc import Serializer


@attrs.define(kw_only=True, eq=False)
class JSONSerializer(Serializer):

    magic_key: str = "_apscheduler_json"
    dump_options: dict[str, Any] = attrs.field(factory=dict)
    load_options: dict[str, Any] = attrs.field(factory=dict)

    def __attrs_post_init__(self):
        self.dump_options["default"] = self._default_hook
        self.load_options["object_hook"] = self._object_hook

    def _default_hook(self, obj):
        pass

    def _object_hook(self, obj_state: dict[str, Any]):
        pass

    def serialize(self, obj: object) -> bytes:
        pass

    def deserialize(self, serialized: bytes):
        pass
