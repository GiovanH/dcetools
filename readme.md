# DCE-tools

Tools for working with exported json files from [Discord Chat Exporter](https://github.com/Tyrrrz/DiscordChatExporter) or similar.

Current features:

- Format JSON logs
    - As Markdown
        - This is designed to render as rich text for embedding, and interactive support is limited.
        - The syntax used for markdown is list-based with support for the formatting syntax provided by my [Custom blocks](https://github.com/GiovanH/mdexts/tree/master/gio_blocks). 
    - As HTML
        - WIP, currently using implementation from [jsmsj/DCE-JSONtoHTML](https://github.com/jsmsj/DCE-JSONtoHTML)
- Validate
    - Confirm that a query file "fits" within existing data, validating it to check for signs of tampering
- Search

See [Docs_CLI.md](./Docs_CLI.md) for tool usage and documentation.

## Roadmap

- Format: Rewritten HTML formatter
- Format: Write output to multiple pages

## Thanks

Test data from [slatinsky](https://github.com/slatinsky)

