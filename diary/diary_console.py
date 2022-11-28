from collections import defaultdict
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
    (#entries)? (date)?(-date)? ({CATEGORY_PREFIX}category))?
That is to say,
 - If a limit to the number of queries is desired, begin the query with a number
 - If a specific date is required, specify as follows: 't' for today, 'y' for yesterday, '4' for 4 days ago.
 - If a second date is given, the query will return all entries on the date range inclusive.
 - Searches may be restricted to a category. The default 'no category' category is accessed through searching for '{CATEGORY_PREFIX}'

EXAMPLES:
    "t" Returns all entries from today with any category.
    "4 y-t" Returns at most 4 of the most recent entries with no category from today and yesterday.
    "4 1-0" The same as above.
    "4 1-" Again the same as the above - returns 4 recent entries since yesterday, which includes today.
    "4 1" Returns 4 most recent entries from yesterday only.
    ":" Returns all entries with no category.
    ":work" Returns all entries with category 'work'.
    "10 5-1" Returns at most 10 recent entries from yesterday (1 day ago) to 5 days ago.
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

def relative_day(target: datetime.date) -> str:
    today = datetime.date.today()
    days_difference = abs((today - target).days)
    return relative_day_name(days_difference)

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
        # People who mess with their system clocks punish themselves enough;
        # I could raise an error here but then I'd be obliged to implement recovery procedures.
        return f"{days_ago} days in the future (!)"

def relative_timestamp_from_timestamp(timestamp: str, leniency=3) -> str:
    target = datetime.datetime.fromisoformat(timestamp)
    return relative_timestamp(target, leniency)


def relative_timestamp(target: datetime.datetime, leniency=3) -> str:
    today = datetime.date.today()
    days_difference = (today - target.date()).days
    if abs(days_difference) > leniency:
        return target.strftime("%Y/%m/%d %H:%M")
    else:
        return f"{relative_day_name(days_difference)} {target.strftime('%H:%M')}"

class ConsoleDiary:
    def __init__(self, root):
        self.__diary = diary.diary_handler.Diary(root)
        self.running = True
        self.category = ''

    def perform_search(self, start_date, end_date, count=0, category=None, since=False, text=None):

        # Start by obtaining categoryid
        categories = {categoryid: category for categoryid, category in list(self.__diary.get_categories())}
        if category:
            def find_value(target_dict: dict, target_value):
                for key, value in target_dict.items():
                    if value == target_value:
                        return key
                return None
            categoryid = find_value(categories, category)
            if categoryid is None:
                # Distinguish null category from valid falsy category `""`
                print("Invalid category!")
                return
        else:
            categoryid = None

        # Get a full list of entries matching our filters
        entries = self.__diary.get_entries(start_date=start_date, end_date=end_date, count=count, categoryid=categoryid, since=since, text=text)

        for _rowid, timestamp, entry, categoryid in entries:
            time_display = relative_timestamp_from_timestamp(timestamp)
            category_display = f"[{categories[categoryid]}]" if (
                categories[categoryid] and categories[categoryid] != diary.DEFAULT_CATEGORY) else ''
            print(f"[{time_display}]{category_display} {entry}")

    def interpret_date(self, timestamp: str) -> datetime.date:
        """Convert the user-given timestamp or date indicator to a proper datetime object.

        Raises a ValueError if the timestamp does not match accepted values.
        """

        timestamp_pattern = r'''
            ((\d{4})\W)?       # Optionally allow 4 numbers indicating year
            (\d{2})\W(\d{2})   # Require a further two numbers indicating month and day
        '''
        timestamp_pattern_compiled = re.compile(timestamp_pattern, re.VERBOSE)
        today = datetime.date.today()
        if match_timestamp := timestamp_pattern_compiled.match(timestamp):
            (year, month, day) = (int(match_timestamp.group(x)) for x in range(1, 4))
            if not year:
                if month <= today.month and day <= today.day:
                    year = today.year
                else:
                    year = today.year - 1
            return datetime.date.fromisocalendar(year, month, day)
        if timestamp == 't':
            return datetime.date.today()
        elif timestamp == 'y':
            return datetime.date.today() - datetime.timedelta(days=1)
        else:
            days = int(timestamp)  # May raise a ValueError
            return datetime.date.today() - datetime.timedelta(days=days)

    def interpret_search(self, input_message):
        """Interpret the user-passed { input_message } and display results from the resulting search query.

        Accepted search query parameters:
        "I want all entries from 10 days ago": -10
        "I want 5 entries since 3 days ago": 5 3-
        "I want all entries from between 14 and 7 days ago of category 'help'": 14-7 :help
        """

        query_filters = input_message[len(COMMANDS["SEARCH"].invokation):].strip()
        query_components = re.split(r'\s+', query_filters)
 
        def combine_dict(a, b):
            return {**a, **b}
        
        component_patterns = (
                (r"^:(\w+)$", lambda k, m: combine_dict(k, {"category": m.group(1)})),
                (r"^\"(\w+)\"$", lambda k, m: combine_dict(k, {"text": m.group(1)})),                
                (r"^\d+$", lambda kwargs, match: combine_dict(kwargs, {"count": match.group(1)})),
                (r"^(\w+)?(-(\w+))?$", lambda k, m: combine_dict(combine_dict(k, {"start": m.group(1)}), {"end": m.group(3)})),
        )

        filters = defaultdict(lambda: None, {})
        for component in query_components:
            for pattern, func in component_patterns:
                if match := re.match(pattern, component):
                    filters = func(filters, match)
                    break
            else:
                # NOTE: 'else' of 'for' triggers when 'for' does not break
                raise ValueError(f"Search query component {component} does not match any search filter rules, please consult the help")

        count = filters['count'] or 0

        if filters['start_date']:
            start_date = self.interpret_date(filters['start_date'])
        else:
            start_date = None

        since = False
        end_date = None
        if filters['end_date'] is not None:
            if filters['end_date']:
                end_date = self.interpret_date(filters['end_date'])
                if not start_date:
                    start_date = end_date
            else:
                if not start_date:
                    start_date = end_date = datetime.date.today()
                since = True

            
        # Give the user a summary of their query
        if start_date and since:
            time_description = f" since {relative_day(start_date)}"
        elif start_date and end_date and start_date != end_date:
            time_description = f" between {relative_day(start_date)} and {relative_day(end_date)}"
        elif start_date:
            time_description = f" from {relative_day(start_date)}"
        elif end_date:
            time_description = f" until {relative_day(end_date)}"
        else:
            time_description = ""

        category = filters['category'] 
        text = filters['text']
        if category == "":
            category_description = f" of the default category"
        elif category:
            category_description = f" of category {category}"
        else:
            category_description = ""
        print(f"Showing {f'up to {count} of the most recent ' if count else ''}entries{time_description}{category_description}"
              f"{f' containing search string `{text}`' if text else ''}".strip())
        self.perform_search(start_date, end_date, count, category, since, text)

    def interpret_input(self, input_message):
        input_message = input_message.strip()
        if not input_message:
            # Blank enter 
            return
        if input_message[0:len(COMMAND_PREFIX)] == COMMAND_PREFIX:
            # Assume user has input a input_message
            input_message = input_message[len(COMMAND_PREFIX):]  # Remove the command prefix
            if input_message == COMMANDS["QUIT"].invokation:
                self.running = False
            elif input_message.startswith(COMMANDS["SEARCH"].invokation):
                self.interpret_search(input_message)
            elif input_message.startswith(COMMANDS["TODAY"].invokation):
                self.interpret_search("s t")
            elif input_message.startswith(COMMANDS["YESTERDAY"].invokation):
                self.interpret_search("s y")
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

