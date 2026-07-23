from __future__ import annotations

from datetime import date, timedelta, tzinfo
from enum import Enum
from typing import Any

import attrs
from cbor2 import CBORDecoder, CBOREncoder, CBOREncodeTypeError, CBORTag, dumps, loads

from .. import DeserializationError, SerializationError
from .._marshalling import marshal_object, marshal_timezone, unmarshal_object
from ..abc import Serializer


@attrs.define(kw_only=True, eq=False)
class CBORSerializer(Serializer):

    type_tag: int = 4664
    dump_options: dict[str, Any] = attrs.field(factory=dict)
    load_options: dict[str, Any] = attrs.field(factory=dict)

    def __attrs_post_init__(self) -> None:
        self.dump_options.setdefault("default", self._default_hook)
        self.load_options.setdefault("tag_hook", self._tag_hook)

    def _default_hook(self, encoder: CBOREncoder, value: object) -> None:
        pass

    def _tag_hook(
        self, decoder: CBORDecoder, tag: CBORTag, shareable_index: int | None = None
    ) -> object:
        pass

    def serialize(self, obj: object) -> bytes:
        pass

    def deserialize(self, serialized: bytes):
        pass
