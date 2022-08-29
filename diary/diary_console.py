import datetime
import re

import diary


class ConsoleDiary:
    def __init__(self, root):
        self.__diary = diary.diary_handler.Diary(root)
        self.running = True

    def get_day(self, days=None, print_count=0):
        entries = self.__diary.get_entries(days, print_count=print_count)
        for (rowid, timestamp, entry) in entries:
            time = datetime.datetime.fromisoformat(timestamp)
            if days is not None:
                time_display = time.strftime("%H:%M")
            else:
                time_display = time.strftime("%Y/%m/%d %H:%M")
            print(f"[{time_display}] {entry}")

    def interpret_input(self, command):
        if not command:
            # Blank enter
            return
        if command == 'h':
            COMMANDS = [
                ('h', 'Help'),
                ('t', 'Today\'s entries'),
                ('y', 'Yesterday\'s entries'),
                ('q', 'Quit'),
                ('# (any number)', 'Send the last # entries. Can be combined with "t" and "y".')
            ]
            for command_key, command_explanation in COMMANDS:
                print(f"{command_key} - {command_explanation}")
        if match := re.match(r'([ty]?)(\d*)', command):
            count = int(match.group(2)) if match.group(2) else 0
            if match.group(1):
                days = 1 if match.group(1) == 'y' else 0
                def print_relative_day_name(_days):
                    if _days == 0:
                        return "Today"
                    elif _days == 1:
                        return "Yesterday"
                    elif _days > 0:
                        return f"{_days} days ago"
                    else:
                        return f"{_days} days ahead"

                print(f"{print_relative_day_name(days)}'s entries:")
                self.get_day(days, count)
            else:
                # Number only ('#')
                self.get_day(None, print_count=count)
                
        elif command == 'q':
            self.running = False
    
    def run(self):
        command = ""
        try:
            while self.running:
                command = input(">")
                self.interpret_input(command)
        except KeyboardInterrupt:
            self.running = False
    

def run(storage_location):
    ConsoleDiary(storage_location).run()
