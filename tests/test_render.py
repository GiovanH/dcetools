import json
import os
from unittest import TestCase

from dcetools.formatter.MarkdownNodeWriter import MarkdownNodeWriter
from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter

dir_path = os.path.dirname(os.path.realpath(__file__))

class TestMarkdownText(TestCase):
    def test_render(self):
        with open(f"{dir_path}/test_data.json", "r") as fp:
            test_data = json.load(fp)

        try:
            with open(f"{dir_path}/output_text.md", "r") as fp:
                known_body = fp.read()
        except FileNotFoundError:
            known_body = ""

        self.assertEqual(
            '\n'.join(MarkdownTextWriter([test_data]).format()),
            known_body
        )

class TestMarkdownNode(TestCase):
    def test_render(self):
        with open(f"{dir_path}/test_data.json", "r") as fp:
            test_data = json.load(fp)

        try:
            with open(f"{dir_path}/output_text.md", "r") as fp:
                known_body = fp.read()
        except FileNotFoundError:
            known_body = ""

        self.assertEqual(
            '\n'.join(MarkdownNodeWriter([test_data]).format()),
            known_body
        )
