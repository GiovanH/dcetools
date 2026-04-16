import argparse
import sys
from argparse import ArgumentParser

import launcher


def print_full_help(parser: ArgumentParser, prefix: str = "") -> None:
    label = prefix if prefix else parser.prog

    print(label, file=sys.stderr)

    epilog = None

    print(f"### `{label}`\n")
    # Print strings as text outside the --help invocation
    if parser.usage:
        print(f"`{parser.usage}`" + "\n")
        parser.usage = None
    if parser.description:
        print(parser.description + "\n")
        parser.description = None
    if parser.epilog:
        epilog = parser.epilog
        parser.epilog = None

    print("```text")
    parser.print_help()
    print("```\n")

    if epilog:
        print(epilog + "\n")

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
