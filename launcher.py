import argparse
from functools import partial
import importlib.metadata
import sys

from dcetools import validate_logs
from dcetools.formatter import runner as format_runner
from dcetools.util import logfmt
from dcetools import search
from dcetools.util.argparse_helpers import CompactArgparseFormatter

DIST_NAME = 'dcetools'

try:
    version = importlib.metadata.version(DIST_NAME)
except importlib.metadata.PackageNotFoundError:
    version = "dev"


class UsageParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f'error: {message}\n')
        self.print_help()
        sys.exit(2)

def get_parser():
    # Boilerplate
    parser: argparse.ArgumentParser = UsageParser(
        formatter_class=CompactArgparseFormatter,
        description="Launcher for all the dce-tools tools. Choose a command for TOOL and pass --help for tool-specific help."
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {version}')

    # Submodules
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser] = parser.add_subparsers(dest="tool", metavar="TOOL") # type: ignore
    subparsers.required = True

    compact_parser = partial(subparsers.add_parser, formatter_class=CompactArgparseFormatter)

    validate_logs.define_parser(compact_parser("validate"))

    format_runner.define_parser(compact_parser("format"))

    search.define_parser(compact_parser("search"))

    # Usage
    subparsers_fmt = "{" + ', '.join(subparsers._name_parser_map.keys()) + "}"
    subparsers.help = f"{subparsers_fmt}"
    parser.usage = f"{parser.prog} {subparsers_fmt}"

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    logfmt.configure_logging()
    main()
