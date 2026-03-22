from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChatMessage(_message.Message):
    __slots__ = ("message", "username")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    message: str
    username: str
    def __init__(self, message: _Optional[str] = ..., username: _Optional[str] = ...) -> None: ...

class ChatMessagesList(_message.Message):
    __slots__ = ("messages",)
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[ChatMessage]
    def __init__(self, messages: _Optional[_Iterable[_Union[ChatMessage, _Mapping]]] = ...) -> None: ...
