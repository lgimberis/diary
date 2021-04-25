from collections import OrderedDict
import os
import sys

from .diary import Diary

def main():
    """Use a CLI to the Diary module.
    """

    COMMANDS = OrderedDict[
        ("Help", [["help", "h"], "Show this help", None, None]),
        ("Exit", [["exit", "e"], "Stop Execution", None, None]),
        ("Today", [["today", "t"], "Open today's entry", "today", 0]),
        ("Date", [["date", "d"], "Open an entry corresponding to the given date", "get_entry", 1]),
        ("Open", [["open", "o"], "Open a file of the given name", "get_file", 1]),
    ]

    def help():
        """List all the commands.
        """
        for command in COMMANDS:
            alias_list = str(COMMANDS[command][0])[1:-1] #Remove '[' and ']' from string representation
            print(f"{command} ({alias_list}) - {COMMANDS[command][1]}")

    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = os.getcwd()
    with Diary(root) as d:
        main_command = None
        while main_command not in COMMANDS["Exit"][0]:
            response = [word for word in input("Enter command:\n").lower().split(" ") if word]
            call_found = False
            print_help = False

            if len(response > 0):
                main_command = response[0]
                for command in COMMANDS:
                    if main_command in COMMANDS[command][0]:
                        call_found = True
                        if command == "Help":
                            print_help = True
                        if COMMANDS[command][2]:
                            if len(response) == 1+COMMANDS[command][3]:
                                func = getattr(d, COMMANDS[command][2])
                                func(*response[1:])
                            else:
                                print(f"Expected {COMMANDS[command][3]} arguments, got {len(response)-1}")
            else:
                main_command = None
            if not call_found:
                print("Command not recognised")
                print_help = True
            if print_help:
                help()
            
if __name__=="__main__":
    main()
