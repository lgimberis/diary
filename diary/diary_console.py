import datetime
import re

import diary


def relative_day_name(days_ago:int) -> str:
    """Return the name of a day relative to today."""

    if days_ago == 0:
        return "Today"
    elif days_ago == 1:
        return "Yesterday"
    elif days_ago == -1:
        return "Tomorrow"
    elif days_ago > 0:
        return f"{days_ago} days ago"
    else:
        return f"In {days_ago} days"


def relative_timestamp(timestamp: str, leniency=3) -> str:
    target = datetime.datetime.fromisoformat(timestamp)
    today = datetime.datetime.today()
    days_difference = today.day - target.day
    if abs(days_difference) > leniency:
        return target.strftime("%Y/%m/%d %H:%M")
    else:
        return f"{relative_day_name(days_difference)} {target.strftime('%H:%M')}"

class ConsoleDiary:
    def __init__(self, root):
        self.__diary = diary.diary_handler.Diary(root)
        self.running = True
        self.category = ''

    def get_day(self, days=None, print_count=0):
        categories = {categoryid: category for categoryid, category in list(self.__diary.get_categories())}
        #category_padding = max([len(category) for category in categories.values()])
        entries = self.__diary.get_entries(days, print_count=print_count)
        for rowid, timestamp, entry, categoryid in entries:
            if days is not None:
                time = datetime.datetime.fromisoformat(timestamp)
                time_display = time.strftime("%H:%M")
            else:
                time_display = relative_timestamp(timestamp)
            category_display = f"[{categories[categoryid]}]" if (
                categories[categoryid] and categories[categoryid] != diary.DEFAULT_CATEGORY) else ''
            print(f"[{time_display}]{category_display} {entry}")

    def interpret_input(self, command):
        if not command.strip():
            # Blank enter
            return
        if command == 'h':
            COMMANDS = [
                ('h', 'Help'),
                ('t', 'Today\'s entries'),
                ('y', 'Yesterday\'s entries'),
                ('q', 'Quit'),
                (': (any text)', 'Change category to given text. \n\t'
                'Categories can later be used to easily find specific entries from a long time ago.\n\t'
                'Categories are not created until an entry is submitted under them. \n\t'
                'Omit all text (just enter ":") to return to default category.\n\t')
                ('# (any number)', 'Send the last # entries. Can be combined with "t" and "y".')
            ]
            for command_key, command_explanation in COMMANDS:
                print(f"{command_key} - {command_explanation}")
        if match := re.match(r'^([ty]?)(\d*)$', command):
            count = int(match.group(2)) if match.group(2) else 0
            if match.group(1):
                days = 1 if match.group(1) == 'y' else 0


                print(f"{relative_day_name(days)}'s entries:")
                self.get_day(days, count)
            else:
                # Number only ('#')
                self.get_day(None, print_count=count)
        elif command == 'q':
            self.running = False
        elif command[0] == ':':
            self.category = command[1:].strip()
        else:
            # Assume the user wants to submit the command as an entry
            category = self.category or diary.DEFAULT_CATEGORY
            self.__diary.add_entry(command, category)
    
    def run(self):
        command = ""
        print("Welcome to the Diary. Type your message and press Enter to create an entry. Enter 'h' to look up commands.")
        try:
            while self.running:
                prompt = f"[{self.category}]>" if self.category else ">"
                command = input(prompt)
                self.interpret_input(command)
        except (KeyboardInterrupt, EOFError):
            self.running = False
            print("")  # Print newline (end='\n')
    

def run(storage_location):
    ConsoleDiary(storage_location).run()
