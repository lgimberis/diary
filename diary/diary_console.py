import datetime
import re

import diary

COMMAND_PREFIX = "/"
CATEGORY_PREFIX = ":"

QUERY_SET_HELP_TEXT = """Change category to following text.
    Categories can later be used to easily find specific entries from a long time ago.
    Categories are not created until an entry is submitted under them.
    Omit all text (just enter ":") to return to default category."""

SEARCH_HELP_TEXT = f"""Search previous entries according to the given set of parameters.
Search query parameterisation is as follows:
    (#entries)? (date)? (date)? ({CATEGORY_PREFIX}category))?
That is to say,
 - If a limit to the number of queries is desired, begin the query with a number
 - If a specific date is required, specify as follows: 't' for today, 'y' for yesterday, '4' for 4 days ago.
 - If a second date is given, the query will return all entries on the date range inclusive.
 - Searches may be restricted to a category. The default 'no category' category is accessed through searching for '{CATEGORY_PREFIX}'

EXAMPLES:
    t - Returns all entries from today with any category.
    4 y t : - Returns up to 4 entries with no category from yesterday and today.
    :work - Returns all entries with category 'work'.
"""

class Command:
    def __init__(self, invokation, description, display=True):
        self.invokation = invokation
        self.description = description
        self.display = display

COMMANDS = {
        "HELP": Command('h', 'Help'),
        "QUIT": Command('q', 'Quit'),
        "TODAY": Command('t', 'Search for today\'s entries'),
        "YESTERDAY": Command('y', 'Search for yesterday\'s entries'),
        "CATEGORY_SET": Command('c', QUERY_SET_HELP_TEXT),
        "SEARCH": Command('s', SEARCH_HELP_TEXT),
}

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

    def get_day(self, days=None, print_count=0, category=None):
        categories = {categoryid: category for categoryid, category in list(self.__diary.get_categories())}
        #category_padding = max([len(category) for category in categories.values()])
        if category:
            def find_value(target_dict: dict, target_value):
                for key, value in target_dict.items():
                    if value == target_value:
                        return key
                return None
            categoryid = find_value(categories, category)
            if categoryid is None:
                print("Invalid category!")
                return
        else:
            categoryid = None
        entries = self.__diary.get_entries(days, print_count=print_count, categoryid=categoryid)
        for _rowid, timestamp, entry, categoryid in entries:
            if days is not None:
                time = datetime.datetime.fromisoformat(timestamp)
                time_display = time.strftime("%H:%M")
            else:
                time_display = relative_timestamp(timestamp)
            category_display = f"[{categories[categoryid]}]" if (
                categories[categoryid] and categories[categoryid] != diary.DEFAULT_CATEGORY) else ''
            print(f"[{time_display}]{category_display} {entry}")

    def interpret_input(self, input_message):
        if not input_message.strip():
            # Blank enter 
            return
        if input_message[0:1+len(COMMAND_PREFIX)] == COMMAND_PREFIX:
            # Assume user has input a input_message
            input_message = input_message[len(COMMAND_PREFIX):]  # Remove the command prefix
            if input_message == COMMANDS["QUIT"].invokation:
                self.running = False
            elif input_message.startswith(COMMANDS["SEARCH"].invokation):
                # TODO rework search behaviour
                match = ''
                count = int(match.group(2)) if match.group(2) else 0
                if match.group(3):
                    category = match.group(4)
                else:
                    category = None
                if match.group(1):
                    days = 1 if match.group(1) == 'y' else 0


                    print(f"{relative_day_name(days)}'s entries:")
                    self.get_day(days, print_count=count, category=category)
                else:
                    # Number only ('#')
                    self.get_day(None, print_count=count, category=category)
            elif input_message.startswith(COMMANDS["CATEGORY_SET"].invokation):
                self.category = input_message[len(COMMANDS["CATEGORY_SET"].invokation):].strip()
                if not self.category:
                    print("Resetting to default category.")
            else:
                if not input_message.startswith(COMMANDS["HELP"].invokation):
                    # User wasn't asking for help but we did not recognise their command
                    print(f"'{COMMAND_PREFIX}{input_message}' is not a recognised command. Printing help...", end='\n\n')
                # Print help
                print("COMMANDS:")
                for input_message in COMMANDS.values():
                    print(f"{COMMAND_PREFIX}{input_message.invokation} - {input_message.description}")
        else:
            # Assume the user wants to submit the input_message as an entry
            category = self.category or diary.DEFAULT_CATEGORY
            self.__diary.add_entry(input_message, category)
    
    def run(self):
        user_input = ""
        print(f"Welcome to the Diary. All non-command messages sent here are saved to your database file. Enter \"{COMMAND_PREFIX}{COMMANDS['HELP'].invokation}\" to look up commands.")
        try:
            while self.running:
                prompt = f"[{self.category}]>" if self.category else ">"
                user_input = input(prompt)
                self.interpret_input(user_input)
        except (KeyboardInterrupt, EOFError):
            self.running = False
            print("")  # Print newline (end='\n')
    

def run(storage_location):
    ConsoleDiary(storage_location).run()
