from collections import OrderedDict
import os
import sys

from .diary import Diary

class Command:
    def __init__(self, aliases, help, function, numargs):
        self.aliases = aliases
        self.help = help
        self.function = function
        self.numargs = numargs

def main():
    """Use a CLI to the Diary module.
    """

    HELP_NAME = "Help"
    EXIT_NAME = "Exit"

    COMMANDS = OrderedDict([
        (HELP_NAME, Command(["help", "h"], "Show this help", None, None)),
        (EXIT_NAME, Command(["exit", "e"], "Stop Execution", None, None)),
        ("Today", Command(["today", "t"], "Open today's entry", "today", 0)),
        ("Date", Command(["date", "d"], "Open an entry corresponding to the given date", "get_entry", 1)),
        ("Open", Command(["open", "o"], "Open a file of the given name", "get_file", 1)),
    ])

    def help():
        """List all the commands.
        """
        for command in COMMANDS:
            alias_list = str(COMMANDS[command].aliases)[1:-1] #Remove '[' and ']' from string representation
            print(f"{command} ({alias_list}) - {COMMANDS[command].help}")

    if len(sys.argv) > 1:
        root = os.path.abspath(sys.argv[1])
    else:
        root = os.getcwd()
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
                            if len(response) == 1+COMMANDS[command].numargs:
                                func = getattr(d, COMMANDS[command].function)
                                func(*response[1:])
                            else:
                                print(f"Expected {COMMANDS[command].numargs} arguments, got {len(response)-1}")
            else:
                main_command = None
            if not call_found:
                print("Command not recognised")
                print_help = True
            if print_help:
                help()
            
if __name__=="__main__":
    main()
