import glob
import json
import os
from unittest import TestCase

from dcetools.formatter.HtmlWriter import HtmlWriter
from dcetools.formatter.MarkdownNodeWriter import MarkdownNodeWriter
from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter
from dcetools.formatter.base import DiscordWriter
from dcetools.types import DCEExport

dir_path: str = os.path.dirname(os.path.realpath(__file__))

def getDocs() -> list[DCEExport]:
    docs = []
    for f in glob.glob(f"{dir_path}/data/*.json"):
        with open(f, "r", encoding='utf-8') as fp:
            docs.append(json.load(fp))
    return docs


class _TestFormatter(TestCase):
    output_name: str
    ext: str
    formatter: type[DiscordWriter]

    def render(self):
        try:
            with open(f"{dir_path}/{self.output_name}.{self.ext}", "r", encoding='utf-8') as fp:
                known_body = fp.read()
        except FileNotFoundError:
            raise

        rendered = '\n'.join(self.formatter(getDocs()).format())
        with open(f"{dir_path}/{self.output_name}_last.{self.ext}", "w", encoding='utf-8') as fp:
            fp.write(rendered)

        self.assertEqual(
            rendered,
            known_body
        )

class TestMarkdownText(_TestFormatter):
    output_name = "output_text"
    ext = "md"
    formatter = MarkdownTextWriter

    def test_render(self): self.render()

class TestMarkdownNode(_TestFormatter):
    output_name = "output_node"
    ext = "md"
    formatter = MarkdownNodeWriter

    def test_render(self): self.render()

class TestMarkdownHtml(_TestFormatter):
    output_name = "output_html"
    ext = "html"
    formatter = HtmlWriter

    def test_render(self): self.render()