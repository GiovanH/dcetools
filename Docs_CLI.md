## CLI Utilities

### `launcher.py`

`launcher.py {validate, format, search}`

Launcher for all the dce-tools tools. Choose a command for TOOL and pass --help for tool-specific help.

```text
usage: launcher.py [-h] [--version] TOOL ...

positional arguments:
  TOOL        {validate, format, search}

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

### `validate`

Validate a set of unknown discord logs against a set of known logs. The purpose of this is to look for signs of tampering, namely out-of-order messages.
Use query_glob to match the json logfiles to validate and baseline_glob for known good logs.

The more messages in baseline chronologically close to the messages in query, the more accurate this check will be.

```text
usage: launcher.py validate [-h] query_glob baseline_glob

positional arguments:
  query_glob     Input json files
  baseline_glob  Input json files

options:
  -h, --help     show this help message and exit
```

Glob values can be a quoted glob, like "*.json".

Example usage: `validate "query/*.json" "baseline/*.json"`


### `format`

Format json log files into a new output. This new output is written to stdout, so redirect this to a file to capture it. 

```text
usage: launcher.py format [-h] [--format {MarkdownNode,MarkdownText}]
                          [input_files ...]

positional arguments:
  input_files           Input json files (default: None)

options:
  -h, --help            show this help message and exit
  [-f | --format] {MarkdownNode,MarkdownText}
                        Which formatter to use. This defines what the output
                        format will be. (default: MarkdownNode)
```

Formatters:
- MarkdownText: Outputs markdown using the old text implementation.
- MarkdownNode: Outputs markdown using the new node implementation.


### `search`

Loads multiple logs from json files and searches through them. This loads the entire contents into memory.

```text
usage: launcher.py search [-h] [--query QUERY] [--context CONTEXT]
                          [--dump | --no-dump]
                          [input_files ...]

positional arguments:
  input_files        Input json files (default: None)

options:
  -h, --help         show this help message and exit
  --query QUERY      If this is set, run a single search matching this query.
                     Otherwise, give the user an interactive prompt. (default:
                     None)
  --context CONTEXT  How much context to display around match results, in
                     whole messages. (default: 0)
  --dump, --no-dump  Show the entire json object for each message matched, not
                     just the human-readable contents. (default: False)
```

