import argparse
import itertools
import re
import textwrap
from typing import Iterable, Literal

from dcetools.formatter.base import DiscordWriter, keyfunc_authorgroup

from dcetools.types import Attachment, Channel, DCEExport, Guild, Message, User


class MarkdownOutputWriter(DiscordWriter):
    QUIRK_EXTRA_LABELS: bool = False
    QUIRK_TRIM: bool = False
    QUIRK_NO_REPEAT_CHANNEL: bool = False

    FENCE_FORMAT: Literal['cb', 'mdx', 'none']

    @classmethod
    def define_parser(cls, parser):
        parser.set_defaults(factory=cls)

        parser.add_argument("-f", "--format",
            choices=['cb', 'mdx', 'ticks', 'none'],
            default='mdx',
            help="Fence to use. Customblocks, mdx, ticks, or none."
        )
        return parser

    def parse_args(self, args):
        self.FENCE_FORMAT = args.format

        return

    def file_header(self) -> str:
        return """---
Title: discordlogs
Status: draft
Date: 1970-01-01
Category: todo
Tags: todo
---
"""

    # Division, channel

    def formatChannelWrapStart(
        self,
        message_list: list[Message],
    ) -> Iterable[str]:
        members = [message['author'] for message in message_list]

        # title
        this_channel = message_list[0]['channel']
        maybe_guild: Guild | None = self.guild_by_channel.get(this_channel)
        if maybe_guild:
            title = f"{maybe_guild.get('name')} > {self.channels[this_channel]['name']}"
        else:
            title = repr({message['author']["nickname"] for message in message_list})

        # Discord block header
        mdheader = (title) + \
            " " + self.formatMessageTime(message_list[0], "%B %d, %Y")

        # Format-dependant block output
        if self.FENCE_FORMAT == 'cb':
            args: list[str] = sorted({
                f'avatar_{author["nickname"]}="{author["avatarUrl"]}"'
                for author in
                members
            })
            yield (f"## {mdheader}\n\n::: discord {' '.join(args)}")
        elif self.FENCE_FORMAT == 'mdx':
            avatars = {
                author["nickname"]: author["avatarUrl"]
                for author in
                members
            }
            yamloptsstr = '\n' + '\n'.join(
                ["    avatars: " + repr(avatars)]
            ) + '\n'
            yield (f"## {mdheader}\n\n/// discord{yamloptsstr}")
        elif self.FENCE_FORMAT == 'ticks':
            yield (f"## {mdheader}\n\n```discord")
        else:
            yield (f"## {mdheader}\n\n")

    def formatChannelWrapEnd(
        self,
        message_list: list[Message],
    ) -> Iterable[str]:
        if self.FENCE_FORMAT == 'cb':
            yield ""
        elif self.FENCE_FORMAT == 'mdx':
            yield ("///\n")
        elif self.FENCE_FORMAT == 'ticks':
            yield ("```")
        else:
            yield ''

class MarkdownTextWriter(MarkdownOutputWriter, DiscordWriter):
    # Division, top-level

    def formatDocuments(self) -> Iterable[str]:
        for line in super().formatDocuments():
            # print(line, file=sys.stderr)
            if line is None:
                if self.QUIRK_TRIM:
                    print()
                    continue
                else:
                    line = ''

            if self.FENCE_FORMAT == 'cb':
                yield ("    " + line)
            else:
                yield (line)

    # Division, message group

    def formatMessageGroupTime(
        self,
        msg_group_time: list[Message],
        maybe_guild: Guild | None,
        channel: str
    ) -> Iterable[str]:
        time_fmt: str = self.formatMessageTime(msg_group_time[0], "%B %d, %Y")

        this_channel = channel

        chanstr = f", {self.channels[this_channel]['name']}"
        yield (
            f'<time timestamp="{msg_group_time[0]["timestamp"]}" data-guild="{maybe_guild.get("id") if maybe_guild else ""} "'
            f'data-channel="{this_channel}" data-id="{msg_group_time[0]["id"]}">\n{time_fmt}{chanstr}</time>'
        )
        yield ('')

        author_grouped_messages: list[list[Message]] = []

        # DON'T SORT
        for _, g in itertools.groupby(msg_group_time, keyfunc_authorgroup):
            author_grouped_messages.append(list(g))

        for msg_group_time_author in author_grouped_messages:
            yield from self.formatMessageGroupAuthor(msg_group_time_author)
        yield ('')

    # Division, merged author

    def formatMessageGroupAuthor(self, msg_group_time_author: list[Message]) -> Iterable:
        for i, message in enumerate(msg_group_time_author):
            time_fmt_granular: str = self.formatMessageTime(message, "%I:%M %p")

            # If this is the first, add L1 name/date format line
            # before subsequent l2 lines
            if i == 0 or self.QUIRK_EXTRA_LABELS:
                if message['type'] == 'RecipientAdd':
                    yield (
                        f'- SYS <time datetime="{message["timestamp"]}">{time_fmt_granular}</time>'
                    )
                else:
                    yield (
                        f'- {message["author"]["nickname"]} <time datetime="{message["timestamp"]}">{time_fmt_granular}</time>'
                    )

            yield from self.formatMessage(message)

    # Individual messages

    def formatMessagePost(self, message: Message) -> Iterable[str]:
        # Posts
        if message['type'] == 'Reply':
            reference = self.replied_to_messages.get(message["reference"]["messageId"]) # type: ignore
            if reference:
                preview = textwrap.shorten(reference['content'], width=120)
            else:
                preview = "???"
            yield (
                f'    + > {preview}'
            )

        # Hack: Treat "paragraphs" within message as separate messages
        for separate_message in message['content'].split("\n\n"):
            msg_lines: list[str] = re.split(r'\n|```', separate_message)

            block_lines = []
            block_lines.append("    + " + msg_lines[0])
            block_lines.extend(msg_lines[1:])

            # Special line returns on multiline blocks
            if block_lines != ["    + "]:
                try:
                    yield from "<br>\n     ".join(block_lines).split("\n")
                except:
                    print(block_lines, msg_lines, separate_message)
                    raise

        if message['attachments'] and len(message['attachments']) > 0:
            for a in message['attachments']:
                name_label = a["fileName"].replace("_", r"\_")
                url = a["url"].replace('\\', '/')
                yield (f'    + ![{name_label}]({url})')

    def formatMessageRecipientAdd(self, message: Message) -> Iterable[str]:
        yield (
            f'    + {message["author"]["nickname"]} added {message["mentions"][0]["nickname"]} to the group.'
        )

    def formatMessageEmbed(self, message: Message) -> Iterable[str]:
        yield (
            f'<!-- { {"author": message["author"]["nickname"], "embeds": message["embeds"] } } -->'
        )

    def formatMessageUnknown(self, message: Message) -> Iterable[str]:
        yield (
            f'<!-- { {"author": message["author"]["nickname"], "type": message["type"], "content": message["content"], "embeds": message["embeds"]} } -->'
        )
