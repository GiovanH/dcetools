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

from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter

try:
    import ujson as json
except ImportError:
    import json

from dcetools.formatter.MarkdownNodeWriter import MarkdownNodeWriter

formatters = {
    'MarkdownNode': MarkdownNodeWriter,
    'MarkdownText': MarkdownTextWriter
}

def main(args):
    documents = []
    for input_path in args.input_files:
        try:
            with open(input_path, 'r', encoding='utf-8') as fp:
                documents.append(json.load(fp))
        except json.JSONDecodeError as e:
            print(input_path, file=sys.stderr)
            sys.stderr.flush()
            raise json.JSONDecodeError(msg=e.msg, doc=input_path, pos=e.pos) from e # type: ignore

    formatter = formatters[args.format]

    for line in formatter(documents).format():
        print(line)


def define_parser(parser):
    parser.add_argument('input_files', help="Input json files", nargs='*')
    parser.add_argument('--format', choices=formatters.keys(), default='MarkdownNode')

    parser.set_defaults(func=main)

    return parser

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="()",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    define_parser(parser)
    args = parser.parse_args()
    args.func(args)
