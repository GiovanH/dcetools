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


class PreserveTimeConverter(MarkdownConverter):
    def convert_time(self, el, text, parent_tags):
        # Retrieve original attributes (like datetime) to rebuild the tag
        attrs = "".join([f' {k}="{v}"' for k, v in el.attrs.items()])
        return f'<time{attrs}>{text}</time>'

    def convert_li(self, el, text, parent_tags):
        # handle some early-exit scenarios
        text = (text or "").strip()
        if not text:
            return "\n"

        # determine list item bullet character to use
        parent = el.parent
        if parent is not None and parent.name == "ol":
            if parent.get("start") and str(parent.get("start")).isnumeric():
                start = int(parent.get("start"))
            else:
                start = 1
            # For ordered lists, calculate based on sibling count
            bullet = "%s." % (start + len(el.find_previous_siblings("li")))
        else:
            # For unordered lists, calculate nested depth (if needed)
            depth = -1
            tmp_el = el
            while tmp_el:
                if tmp_el.name == "ul":
                    depth += 1
                tmp_el = tmp_el.parent
            bullets = self.options["bullets"] # type: ignore
            bullet = bullets[depth % len(bullets)]

        # Add a trailing space to the bullet marker
        bullet = bullet + " "

        # Instead of calculating indent from bullet length, use fixed 4 spaces
        fixed_indent = "    "  # 4 spaces, as required by CommonMark
        bullet_indent = fixed_indent

        # Indent the content lines with a fixed indent of 4 spaces
        def _indent_for_li(match):
            line_content = match.group(1)
            return bullet_indent + line_content if line_content else ""

        text = markdownify.re_line_with_content.sub(_indent_for_li, text) # type: ignore

        # Replace the first 4 spaces with the bullet (preserving any extra characters beyond the 4-char indent)
        text = bullet + text[len(fixed_indent) :]

        return "%s\n" % text

def keyfunc_timechangroup(msg) -> tuple:
    return (msg["timestamp"][:10], msg["channel"])


def keyfunc_authorgroup(msg) -> str:
    if msg['type'] == 'RecipientAdd':
        return 'SYS'
    return msg["author"]["id"]


class DiscordWriter():
    QUIRK_EXTRA_LABELS: bool = False
    QUIRK_TRIM: bool = False
    QUIRK_NO_REPEAT_CHANNEL: bool = False

    def __init__(self, json_docs: list[DCEExport]):
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


    def formatMessageTime(self, message: Message, fmt: str) -> str:
        iso_timestamp = message['timestamp'][:19] + 'Z'
        dt = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime(fmt)

    def sectionHeaderBlock(self, members: list[User], message_list: list[Message], title: str | None = None) -> Iterable[str]: ...

    def formatChannelWrapStart(self) -> Iterable[str]: ...

    def formatMessageGroupTime(self, msg_group_time: list[Message], maybe_guild: Guild | None, chanstr: str = '') -> Iterable[str]: ...

    def format(self) -> Iterable[str]:
        for frag in self.formatDocuments():
            yield str(frag)

    def formatDocuments(self) -> Iterable[str]:
        last_channel = None

        printed_header = False

        for msg_group_time in self.time_grouped_messages:

            this_channel = msg_group_time[0]['channel']
            maybe_guild: Guild | None = self.guild_by_channel.get(this_channel)

            chanstr = ''

            # len(channels.keys()) > 1
            if (this_channel != last_channel):
                if not self.QUIRK_NO_REPEAT_CHANNEL:
                    if printed_header:
                        yield from self.formatChannelWrapStart()

                    maybe_name = None
                    if maybe_guild:
                        maybe_name = f"{maybe_guild.get('name')} > {self.channels[this_channel]['name']}"

                    section_members = [message['author'] for message in msg_group_time]

                    for node in self.sectionHeaderBlock(section_members, msg_group_time, maybe_name):
                        yield str(node)

                    printed_header = True
                    chanstr = f", {self.channels[this_channel]['name']}"

            for node in self.formatMessageGroupTime(msg_group_time, maybe_guild, chanstr):
                yield str(node)
            last_channel = this_channel

    def formatMessagePost(self, message: Message) -> Iterable: ...

    def formatMessageRecipientAdd(self, message: Message) -> Iterable: ...

    def formatMessageEmbed(self, message: Message) -> Iterable: ...

    def formatMessageUnknown(self, message: Message) -> Iterable: ...

    def messageToFrags(self, message: Message) -> Iterable:
        # lines = []

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
