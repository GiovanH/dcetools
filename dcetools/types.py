
import argparse
import functools
import itertools
import operator
import re
import sys
import textwrap
import xml.etree.ElementTree as etree
import xml.sax.saxutils
from datetime import datetime

# from typing import get_origin, get_args, Any
from typing import Generic, Iterable, Mapping, Optional, TypedDict, TypeVar

import markdown
import markdownify
from markdownify import MarkdownConverter
from typing_extensions import NotRequired

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


class DCEExport(TypedDict):
    channel: Channel
    guild: Guild
    messages: list[Message]

