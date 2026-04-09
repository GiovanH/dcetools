from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter


import markdown


import itertools
import textwrap
import xml.etree.ElementTree as etree
import xml.sax.saxutils
from typing import Iterable


class MarkdownNodeWriter(MarkdownTextWriter):
    markdownconverter = PreserveTimeConverter(bullets="-+*")

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

        html = etree.tostring(message_list, encoding='unicode')
        # print(repr(html))
        yield self.markdownconverter.convert(html)
        yield ''

    def formatMessageGroupAuthor(self, msg_group_time_author: list[Message]) -> Iterable[etree.Element]:
        for i, message in enumerate(msg_group_time_author):
            time_fmt_granular: str = self.formatMessageTime(message, "%I:%M %p")

            li = etree.Element("li")
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
            from_md = markdown.markdown(xml.sax.saxutils.escape(message['content']))
            li = etree.fromstring("<li>" + from_md + "</li>")
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