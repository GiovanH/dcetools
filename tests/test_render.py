import json
import os
from unittest import TestCase

from dcetools.formatter.MarkdownNodeWriter import MarkdownNodeWriter
from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter

dir_path = os.path.dirname(os.path.realpath(__file__))

class TestMarkdownText(TestCase):
    maxDiff = None
    def test_render(self):
        with open(f"{dir_path}/test_data.json", "r") as fp:
            test_data = json.load(fp)

        try:
            with open(f"{dir_path}/output_text.md", "r") as fp:
                known_body = fp.read()
        except FileNotFoundError:
            known_body = ""

        rendered = '\n'.join(MarkdownTextWriter([test_data]).format())
        with open(f"{dir_path}/output_text_last.md", "w", encoding='utf-8') as fp:
            fp.write(rendered)

        self.assertEqual(
            rendered,
            known_body
        )

class TestMarkdownNode(TestCase):
    maxDiff = None
    def test_render(self):
        with open(f"{dir_path}/test_data.json", "r") as fp:
            test_data = json.load(fp)

        try:
            with open(f"{dir_path}/output_node.md", "r") as fp:
                known_body = fp.read()
        except FileNotFoundError:
            known_body = ""

        rendered = '\n'.join(MarkdownNodeWriter([test_data]).format())
        with open(f"{dir_path}/output_node_last.md", "w") as fp:
            fp.write(rendered)

        self.assertEqual(
            rendered,
            known_body
        )
