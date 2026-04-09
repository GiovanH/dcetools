import argparse
import functools
import itertools
import operator
import pprint
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

from dcetools.types import DCEExport, Message

try:
    import ujson as json
except ImportError:
    import json

documents: list[DCEExport] = []

SETTING_DUMP: bool = True
SETTING_CONTEXT: int = 0

def print_message(doc: DCEExport, msg: Message) -> None:
    url = f"https://discord.com/channels/{doc['guild']['id']}/{doc['channel']['id']}/{msg['id']}"

    print()
    if SETTING_DUMP:
        print(json.dumps(msg, indent=2))
    print(url)
    print(f"{msg['author']['name']} ({msg['author']['id']}):")
    print(f"{msg['content']}")

def test_message(query: str, message: Message) -> bool:
    return query.lower() in message['content'].lower()

def do_search(query: str) -> None:
    for doc in documents:
        for ix, message in enumerate(doc['messages']):
            if test_message(query, message):
                for ir in range(SETTING_CONTEXT, 0, -1):
                    try:
                        print_message(doc, doc['messages'][ix-ir])
                    except IndexError:
                        break

                print_message(doc, message)

                for ir in range(1, SETTING_CONTEXT+1):
                    try:
                        print_message(doc, doc['messages'][ix+ir])
                    except IndexError:
                        break



def interactive_search() -> None:
    try:
        while True:
            query = input("Query: ")
            if query:
                do_search(query)
    except KeyboardInterrupt:
        return

def main(args):
    global SETTING_DUMP
    global SETTING_CONTEXT
    SETTING_DUMP = args.dump
    SETTING_CONTEXT = args.context

    documents.clear()

    for input_path in args.input_files:
        try:
            with open(input_path, 'r', encoding='utf-8') as fp:
                documents.append(json.load(fp))
        except json.JSONDecodeError as e:
            print(input_path, file=sys.stderr)
            sys.stderr.flush()
            raise json.JSONDecodeError(msg=e.msg, doc=input_path, pos=e.pos) from e # type: ignore

    if args.query:
        do_search(args.query)
    else:
        interactive_search()

def define_parser(parser):
    parser.add_argument('input_files', help="Input json files", nargs='*')
    parser.add_argument('--query')
    parser.add_argument('--context', type=int, default=0)
    parser.add_argument("--dump",
        action=argparse.BooleanOptionalAction,
        default=True
    )

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
