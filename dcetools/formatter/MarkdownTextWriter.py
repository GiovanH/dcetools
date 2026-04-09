import itertools
import re
import textwrap
from typing import Iterable

from dcetools.formatter.base import DiscordWriter, keyfunc_authorgroup

from dcetools.types import Attachment, Channel, DCEExport, Guild, Message, User

class MarkdownTextWriter(DiscordWriter):
    MODE_CUSTOMBLOCKS = False

    def file_header(self) -> str:
        return """---
Title: discordlogs
Status: draft
Date: 1970-01-01
Category: todo
Tags: todo
---
"""

    def sectionHeaderBlock(self, members: list[User], message_list: list[Message], title: str | None = None) -> Iterable[str]:
        mdheader = (title or repr({message['author']["nickname"] for message in message_list})) + \
            " " + self.formatMessageTime(message_list[0], "%B %d, %Y")
        if self.MODE_CUSTOMBLOCKS:
            args: list[str] = sorted({
                f'avatar_{author["nickname"]}="{author["avatarUrl"]}"'
                for author in
                members
            })
            yield (f"## {mdheader}\n\n::: discord {' '.join(args)}")
        else:
            avatars = {
                author["nickname"]: author["avatarUrl"]
                for author in
                members
            }
            yamloptsstr = '\n' + '\n'.join(
                ["    avatars: " + repr(avatars)]
            ) + '\n'
            yield (f"## {mdheader}\n\n/// discord{yamloptsstr}")


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

    def formatDocuments(self) -> Iterable[str]:
        if self.QUIRK_NO_REPEAT_CHANNEL:
            yield from self.sectionHeaderBlock(self.members, self.all_messages)

        for line in super().formatDocuments():
            # print(line, file=sys.stderr)
            if line is None:
                if self.QUIRK_TRIM:
                    print()
                    continue
                else:
                    line = ''

            if self.MODE_CUSTOMBLOCKS:
                yield ("    " + line)
            else:
                yield (line)

        if self.MODE_CUSTOMBLOCKS:
            yield ""
        else:
            yield ("///\n")

    def formatChannelWrapStart(self) -> Iterable[str]:
        if not self.MODE_CUSTOMBLOCKS:
            yield ("///\n")

    def formatMessageGroupTime(self, msg_group_time: list[Message], maybe_guild: Guild | None, chanstr: str = '') -> Iterable[str]:
        time_fmt: str = self.formatMessageTime(msg_group_time[0], "%B %d, %Y")

        this_channel = msg_group_time[0]['channel']

        yield (
            f'<time timestamp="{msg_group_time[0]["timestamp"]}" data-guild="{maybe_guild.get("id") if maybe_guild else ""}"'
            f'data-channel="{this_channel}" data-id="{msg_group_time[0]["id"]}">\n{time_fmt}{chanstr}</time>'
        )
        yield ('')

        author_grouped_messages: list[list[Message]] = []
        # DON'T SORT
        for _, g in itertools.groupby(msg_group_time, keyfunc_authorgroup):
            author_grouped_messages.append(list(g))

        # print("author_grouped_messages", estimate_type(author_grouped_messages), file=sys.stderr)

        for msg_group_time_author in author_grouped_messages:
            yield from self.formatMessageGroupAuthor(msg_group_time_author)
        yield ('')

    def formatMessageGroupAuthor(self, msg_group_time_author: list[Message]) -> Iterable:
        for i, message in enumerate(msg_group_time_author):
            time_fmt_granular: str = self.formatMessageTime(message, "%I:%M %p")

            if i == 0 or self.QUIRK_EXTRA_LABELS:
                if message['type'] == 'RecipientAdd':
                    yield (
                        f'- SYS <time datetime="{message["timestamp"]}">{time_fmt_granular}</time>'
                    )
                else:
                    yield (
                        f'- {message["author"]["nickname"]} <time datetime="{message["timestamp"]}">{time_fmt_granular}</time>'
                    )

            yield from self.messageToFrags(message)