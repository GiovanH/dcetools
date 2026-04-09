from argparse import ArgumentParser
import argparse
import os
import pprint
import sys
import textwrap
from collections import defaultdict

import launcher

def print_full_help(parser: ArgumentParser, prefix: str = "") -> None:
    label = prefix if prefix else parser.prog
    print(f"\n{'═' * 60}")
    print(f"  {label}")
    print(f"{'═' * 60}\n")
    parser.print_help()
    print()

    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        for sub_name, sub_parser in action.choices.items():
            child_prefix = f"{prefix} {sub_name}".strip() if prefix else sub_name
            print_full_help(sub_parser, prefix=child_prefix)

sys.argv = ["launcher.py", '--help']
parser = launcher.get_parser()

print("CLI Utilities", file=sys.stderr)
print("## CLI Utilities\n")
print_full_help(parser)
