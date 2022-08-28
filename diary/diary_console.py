import datetime
import re

import diary


class ConsoleDiary:
    def __init__(self, root):
        self.__diary = diary.diary_handler.Diary(root)
        self.running = True

    def get_day(self, days, print_count=0):
        entries = self.__diary.get_day(days)
        if print_count:
            entries = entries[-print_count:]
        for (rowid, timestamp, entry) in entries:
            time = datetime.datetime.fromisoformat(timestamp)
            time_display = time.strftime("%H:%M")
            print(f"[{time_display}] {entry}")

    def interpret_input(self, command):
        if command == 'h':
            COMMANDS = [
                ('h', 'Help'),
                ('t', 'Today\'s entries'),
                ('y', 'Yesterday\'s entries'),
                ('q', 'Quit'),
                ('# (any number)', 'Send the last # entries only.')
            ]
            for command_key, command_explanation in COMMANDS:
                print(f"{command_key} - {command_explanation}")
        if match := re.match(r't(\d*)', command):
            count = int(match.group(1)) if match.group(1) else 0
            print("Today's entries:")
            self.get_day(0, count)
        if command[0] == 'y':
            print("Yesterday's entries:")
            self.get_day(1)
        if command == 'q':
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
