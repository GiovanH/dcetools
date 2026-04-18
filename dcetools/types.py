
# from typing import get_origin, get_args, Any
from typing import NotRequired, TypedDict


class Channel(TypedDict):
    id: str
    name: str

class Guild(TypedDict):
    id: str

class User(TypedDict):
    name: str
    id: str
    nickname: str
    avatarUrl: str
    color: str

# class Reference(TypedDict):
#     messageId: str
#     content: str


class Attachment(TypedDict):
    fileName: str
    url: str

class Message(TypedDict):
    id: str
    type: str
    author: User
    reference: NotRequired['Message']
    timestamp: str
    channel: str
    content: str
    attachments: list[Attachment]
    embeds: list[dict] # todo
    mentions: list[User]
    timestampEdited: str | None
    isPinned: bool


class DCEExport(TypedDict):
    channel: Channel
    guild: Guild
    messages: list[Message]

