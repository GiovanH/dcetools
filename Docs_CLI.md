## CLI Utilities


════════════════════════════════════════════════════════════
  launcher.py
════════════════════════════════════════════════════════════

usage: launcher.py [-h] [--version] TOOL ...

positional arguments:
  TOOL        Options are ['validate', 'format', 'search']

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit


════════════════════════════════════════════════════════════
  validate
════════════════════════════════════════════════════════════

usage: launcher.py validate [-h] query_glob baseline_glob

Validate a set of unknown discord logs against a set of known logs. This looks
for signs of tampering, namely out-of-order messages.

positional arguments:
  query_glob     Input json files
  baseline_glob  Input json files

options:
  -h, --help     show this help message and exit


════════════════════════════════════════════════════════════
  format
════════════════════════════════════════════════════════════

usage: launcher.py format [-h] [--format {MarkdownNode,MarkdownText}]
                          [input_files ...]

positional arguments:
  input_files           Input json files

options:
  -h, --help            show this help message and exit
  --format {MarkdownNode,MarkdownText}


════════════════════════════════════════════════════════════
  search
════════════════════════════════════════════════════════════

usage: launcher.py search [-h] [--query QUERY] [--context CONTEXT]
                          [--dump | --no-dump]
                          [input_files ...]

positional arguments:
  input_files        Input json files

options:
  -h, --help         show this help message and exit
  --query QUERY
  --context CONTEXT
  --dump, --no-dump

