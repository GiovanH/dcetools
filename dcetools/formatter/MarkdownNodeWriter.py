import itertools
import re
import sys
import textwrap
import xml.etree.ElementTree as etree
import xml.sax.saxutils
from collections.abc import Iterable

import markdown
import markdownify
from markdownify import MarkdownConverter

from dcetools.formatter.base import keyfunc_authorgroup
from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter
from dcetools.types import Guild, Message


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

        return f"{text}\n"

def protect_ansi_in_code_blocks(html):
    def to_cdata(match):
        return f'<code{match.group(1)}><![CDATA[{match.group(2)}]]></code>'

    return re.sub(
        r'<code([^>]*)>(.*?)</code>',
        to_cdata,
        html,
        flags=re.DOTALL
    )

class MarkdownNodeWriter(MarkdownTextWriter):
    markdownconverter = PreserveTimeConverter(bullets="-+*", heading_style="ATX")
    md = markdown.Markdown(extensions=[
        'fenced_code', 'nl2br'
    ])

    def formatMessageGroupTime(self, msg_group_time: list[Message], maybe_guild: Guild | None, chanstr: str = '') -> Iterable[str]:
        time_fmt: str = self.formatMessageTime(msg_group_time[0], "%B %d, %Y")
        this_channel = msg_group_time[0]['channel']

        time_elem = etree.Element("time")
        time_elem.set("timestamp", msg_group_time[0]["timestamp"])
        time_elem.set("data-guild", maybe_guild.get("id") if maybe_guild else "")
        time_elem.set("data-channel", this_channel)
        time_elem.set("data-id", msg_group_time[0]["id"])
        time_elem.text = time_fmt + chanstr

        yield etree.tostring(time_elem, encoding='unicode')
        yield ('')

        author_grouped_messages: list[list[Message]] = []
        # DON'T SORT
        for _, g in itertools.groupby(msg_group_time, keyfunc_authorgroup):
            author_grouped_messages.append(list(g))

        message_list = etree.Element("ul")
        for msg_group_time_author in author_grouped_messages:
            message_list.extend([*self.formatMessageGroupAuthor(msg_group_time_author)])

        # print("list", repr(message_list))
        html = etree.tostring(message_list, encoding='unicode')
        # print("tostring", repr(html))
        yield self.markdownconverter.convert(html)
        yield ''

    def formatMessageGroupAuthor(self, msg_group_time_author: list[Message]) -> Iterable[etree.Element]:
        li = etree.Element("li")
        li.attrib['class'] = 'group'
        for i, message in enumerate(msg_group_time_author):
            time_fmt_granular: str = self.formatMessageTime(message, "%I:%M %p")

            if i == 0 or self.QUIRK_EXTRA_LABELS:
                if message['type'] == 'RecipientAdd':
                    li.text = "SYS "

                    time_el = etree.SubElement(li, "time", datetime=message["timestamp"])
                    time_el.text = time_fmt_granular
                    # yield li
                else:
                    # li = etree.Element("li")
                    li.text = f'{message["author"]["nickname"]} '

                    time_el = etree.SubElement(li, "time", datetime=message["timestamp"])
                    time_el.text = time_fmt_granular

            subul = etree.SubElement(li, "ul")
            for subli in self.messageToFrags(message):
                subul.append(subli)

        yield li

    def formatMessagePost(self, message: Message) -> Iterable[etree.Element]:
        from_md = None
        try:
            # TODO insert trailing newline in all code blocks
            from_md = self.md.convert(xml.sax.saxutils.escape(message['content']))
            from_md = re.sub(r'(?!<\n)```', r'\n```', from_md)
            li = etree.fromstring("<li class='message'>" + protect_ansi_in_code_blocks(from_md) + "</li>")
        except:
            print(message['content'], file=sys.stderr)
            print(from_md, file=sys.stderr)
            raise

        if message['type'] == 'Reply':
            bq = etree.Element("blockquote")
            reference = self.replied_to_messages.get(message["reference"]["messageId"]) # type: ignore

            if reference:
                bq.text = textwrap.shorten(reference['content'], width=120)
            else:
                bq.text = "???"
            li.insert(0, bq)

        if message['attachments'] and len(message['attachments']) > 0:
            for a in message['attachments']:
                etree.SubElement(li, "img", src=a["url"], title=a["fileName"])

        yield li

    def formatMessageRecipientAdd(self, message: Message) -> Iterable[etree.Element]:
        li = etree.Element("time")
        li.text = f'{message["author"]["nickname"]} added {message["mentions"][0]["nickname"]} to the group.'
        yield li

    def formatMessageEmbed(self, message: Message) -> Iterable[etree.Element]:
        yield etree.Comment(str({"author": message["author"]["nickname"], "embeds": message["embeds"]}))

    def formatMessageUnknown(self, message: Message) -> Iterable[etree.Element]:
        yield etree.Comment(str({"type": message["type"], "author": message["author"]["nickname"], "embeds": message["embeds"]}))