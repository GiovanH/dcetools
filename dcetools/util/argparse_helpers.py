import argparse

class CompactArgparseFormatter(
   argparse.RawDescriptionHelpFormatter,
   argparse.ArgumentDefaultsHelpFormatter
):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s | --long ARGS
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                if len(action.option_strings) > 1:
                    opts = sorted(action.option_strings, key=len)
                    parts.append(f"[{' | '.join(opts)}] {args_string}")
                else:
                    for option_string in action.option_strings:
                        parts.append(f'{option_string} {args_string}')

            return ', '.join(parts)
