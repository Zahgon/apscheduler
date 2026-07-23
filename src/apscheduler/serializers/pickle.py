from __future__ import annotations

from pickle import dumps, loads

import attrs

from .. import DeserializationError, SerializationError
from ..abc import Serializer


@attrs.define(kw_only=True, eq=False)
class PickleSerializer(Serializer):

    protocol: int = 4

    def serialize(self, obj: object) -> bytes:
        pass

    def deserialize(self, serialized: bytes):
        pass
