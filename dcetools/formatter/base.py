from abc import ABC, abstractmethod
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

from dcetools.types import Attachment, Channel, DCEExport, Guild, Message, User

try:
    import ujson as json
except ImportError:
    import json


def keyfunc_timechangroup(msg) -> tuple:
    return (msg["timestamp"][:10], msg["channel"])


def keyfunc_authorgroup(msg) -> str:
    if msg['type'] == 'RecipientAdd':
        return 'SYS'
    return msg["author"]["id"]

Frag = TypeVar('Frag')

class DiscordWriter(ABC, Generic[Frag]):
    QUIRK_NO_REPEAT_CHANNEL: bool = False

    @classmethod
    def define_parser(cls, parser):
        parser.set_defaults(factory=cls)

        return parser

    def parse_args(self, args):
        return

    def __init__(self, json_docs: list[DCEExport]):
        self.json_docs: list[DCEExport] = json_docs

        self.channels: Mapping[str, Channel] = {
            json_doc['channel']['id']: json_doc['channel']
            for json_doc in json_docs
        }
        self.guild_by_channel: Mapping[str, Guild] = {
            json_doc['channel']['id']: json_doc['guild']
            for json_doc in json_docs
        }

        self.all_messages: list[Message] = functools.reduce(operator.iadd, [
            [
                {**m, "channel": json_doc['channel']['id']}
                for m in json_doc['messages']
            ]
            for json_doc in json_docs
        ], [])

        self.messages_by_id: dict[str, Message] = {
            m['id']: m
            for m in self.all_messages
        }

        self.replied_to_ids: set[str] = {
            m["reference"]["messageId"] # type: ignore
            for m in self.all_messages
            if m['type'] == 'Reply'
        }
        self.replied_to_messages: dict[str, Message] = {
            m["id"]: m
            for m in self.all_messages
            if m['id'] in self.replied_to_ids
        }

        self.members: list[User] = [message['author'] for message in self.all_messages]

        self.time_grouped_messages: list[list[Message]] = []
        for _, g in itertools.groupby(sorted(self.all_messages, key=keyfunc_timechangroup), keyfunc_timechangroup):
            self.time_grouped_messages.append(list(g))

    # Formatters
    def formatMessageTime(self, message: Message, fmt: str) -> str:
        iso_timestamp = message['timestamp'][:19] + 'Z'
        dt = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime(fmt)

    # def formatChannelTitle(self):
    #     return f"{maybe_guild.get('name')} > {self.channels[this_channel]['name']}"

    # Entrypoint
    def format(self) -> Iterable[str]:
        """Format the document and yield final strings"""
        for frag in self.formatDocuments():
            yield str(frag)

    # Division, top-level

    def formatDocuments(self) -> Iterable[Frag]:
        key = lambda msg_group: msg_group[0]["channel"]

        for _, g in itertools.groupby(sorted(self.time_grouped_messages, key=key), key):
            yield from self.formatChannel([*g])

    # Division, channel

    def formatChannelWrapStart(
        self,
        message_list: list[Message],
    ) -> Iterable[Frag]:
        return
        yield

    # section_members = [message['author'] for message in chan_messages]

    def formatChannelWrapEnd(
        self,
        message_list: list[Message],
    ) -> Iterable[Frag]:
        return
        yield

    def formatChannel(self, channel_time_groups: list[list[Message]]) -> Iterable[Frag]:
        this_channel = channel_time_groups[0][0]['channel']
        maybe_guild: Guild | None = self.guild_by_channel.get(this_channel)

        chan_messages = [m for l in channel_time_groups for m in l]

        yield from self.formatChannelWrapStart(chan_messages)

        for msg_group_time in channel_time_groups:
            yield from self.formatMessageGroupTime(msg_group_time, maybe_guild, this_channel)

        yield from self.formatChannelWrapEnd(chan_messages)

    # Division, message group

    @abstractmethod
    def formatMessageGroupTime(
        self,
        msg_group_time: list[Message],
        maybe_guild: Guild | None,
        channel: str
    ) -> Iterable[Frag]:
        raise NotImplementedError()


    # Division, merged author

    def formatMessageGroupAuthor(self, msg_group_time_author: list[Message]) -> Iterable[Frag]:
        raise NotImplementedError()

    # chanstr = f", {self.channels[this_channel]['name']}"

    # Individual message

    def formatMessagePost(self, message: Message) -> Iterable[Frag]:
        raise NotImplementedError()

    def formatMessageRecipientAdd(self, message: Message) -> Iterable[Frag]:
        raise NotImplementedError()

    def formatMessageEmbed(self, message: Message) -> Iterable[Frag]:
        raise NotImplementedError()

    def formatMessageUnknown(self, message: Message) -> Iterable[Frag]:
        raise NotImplementedError()

    def formatMessage(self, message: Message) -> Iterable[Frag]:
        if message['type'] == 'Default' or message['type'] == 'Reply':
            try:
                yield from self.formatMessagePost(message)
            except Exception as e:
                print(e)
                yield from self.formatMessageUnknown(message)

        elif message['type'] == "RecipientAdd":
            yield from self.formatMessageRecipientAdd(message)
        elif message['type'] == "24":
            yield from self.formatMessageEmbed(message)
            # Some kind of embed-only format
        else:
            print(f"Unknown message type {message['type']}", file=sys.stderr)
            yield from self.formatMessageUnknown(message)
