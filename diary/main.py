from collections import OrderedDict
from pathlib import Path
import sys

from .diary import Diary

HELP_NAME = "Help"
EXIT_NAME = "Exit"


class Command:
    def __init__(self, aliases, help_text, function, num_arguments):
        self.aliases = aliases
        self.help = help_text
        self.function = function
        self.num_arguments = num_arguments


COMMANDS = OrderedDict([
    (HELP_NAME, Command(["help", "h"], "Show this help", None, None)),
    (EXIT_NAME, Command(["exit", "e"], "Stop Execution", None, None)),
    ("Today", Command(["today", "t"], "Open today's entry", "today", 0)),
    ("Date", Command(["date", "d"], "Open an entry corresponding to the given date", "get_entry", 1)),
    ("Open", Command(["open", "o"], "Open a file of the given name", "get_file", 1)),
    ("Config", Command(["config", "c"], "Open the config file for editing", "edit_config", 0))
])


def main():
    """Use a CLI to the Diary module.
    """

    def help_text():
        """List all the commands.
        """
        for command_to_explain in COMMANDS:
            # Remove '[' and ']' from string representation
            alias_list = str(COMMANDS[command_to_explain].aliases)[1:-1]
            print(f"{command_to_explain} ({alias_list}) - {COMMANDS[command_to_explain].help}")

    if len(sys.argv) > 1:
        root = Path(sys.argv[1:]).absolute()
    else:
        root = Path().absolute()
    with Diary(root) as d:
        main_command = None
        while main_command not in COMMANDS[EXIT_NAME].aliases:
            response = [word for word in input("Enter command:\n").lower().split(" ") if word]
            call_found = False
            print_help = False

            if len(response) > 0:
                main_command = response[0]
                for command in COMMANDS:
                    if main_command in COMMANDS[command].aliases:
                        call_found = True
                        if command == HELP_NAME:
                            print_help = True
                        if COMMANDS[command].function:
                            if len(response) == 1+COMMANDS[command].num_arguments:
                                func = getattr(d, COMMANDS[command].function)
                                func(*response[1:])
                            else:
                                print(f"Expected {COMMANDS[command].num_arguments} "
                                      f"arguments, got {len(response) - 1}")
            else:
                main_command = None
            if not call_found:
                print("Command not recognised")
                print_help = True
            if print_help:
                help_text()


if __name__ == "__main__":
    main()
