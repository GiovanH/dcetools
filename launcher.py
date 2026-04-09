import argparse
import importlib.metadata

from dcetools import validate_logs
from dcetools.formatter import runner as format_runner
from dcetools.util import logfmt
from dcetools import search

try:
    version = importlib.metadata.version('dcetools')
except importlib.metadata.PackageNotFoundError:
    version = "dev"

def get_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument('--version', action='version', version=f'%(prog)s {version}')
    subparsers = parser.add_subparsers(dest="tool", metavar="TOOL")
    subparsers.required = True

    parser_validate = subparsers.add_parser("validate")
    validate_logs.define_parser(parser_validate)

    parser_format = subparsers.add_parser("format")
    format_runner.define_parser(parser_format)

    parser_search = subparsers.add_parser("search")
    search.define_parser(parser_search)

    subparsers.help = f"Options are {[*subparsers._name_parser_map.keys()]}"

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    logfmt.configure_logging()
    main()
