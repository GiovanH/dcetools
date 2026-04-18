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

from dcetools.formatter.HtmlWriter import HtmlWriter
from dcetools.formatter.MarkdownTextWriter import MarkdownTextWriter
from dcetools.util.argparse_helpers import CompactArgparseFormatter

try:
    import ujson as json
except ImportError:
    import json

from dcetools.formatter.MarkdownNodeWriter import HTMLNodeWriter, MarkdownNodeWriter

formatters = {
    'md': MarkdownNodeWriter,
    'mdtext': MarkdownTextWriter,
    # 'NodeHtml': HTMLNodeWriter,
    'html': HtmlWriter
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

    formatter = args.factory(documents)

    formatter.parse_args(args)

    for line in formatter.format():
        print(line)

def define_parser(parser: argparse.ArgumentParser):
    parser.description = "Format json log files into a new output. This new output is written to stdout, so redirect this to a file to capture it. "
    parser.add_argument('input_files', help="Input json files", nargs='+')

    # parser.add_argument('-o', '--output', help="Directory to save output files. '-' to write all output to stdout.", default='-')

    subparsers = parser.add_subparsers(dest="formatter", metavar="FORMATTER", help="Which formatter to use. This defines what the output format will be. Options: {%(choices)s}")

    # parser.add_argument('--format', '-f', choices=formatters.keys(), default='MarkdownNode', )

    compact_parser = functools.partial(subparsers.add_parser, formatter_class=CompactArgparseFormatter)

    for k, formatter in formatters.items():
        formatter.define_parser(compact_parser(
            k,
            # aliases=[k.lower(), k.upper(), k.capitalize()]
        ))

#     parser.epilog = """Formatters:
# - MarkdownText: Outputs markdown using the old text implementation.
# - MarkdownNode: Outputs markdown using the new node implementation.
# - Html: Straight port of `jsmsj/DCE-JSONtoHTML`. Lacking support.
# """

    parser.set_defaults(factory=MarkdownNodeWriter)
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
