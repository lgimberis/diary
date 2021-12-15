from pathlib import Path
import sys
from tkinter import *
from tkinter import ttk

from diary.diary_handler import Diary


class DiaryProgram(Frame):
    """Master class for the program's GUI.
    """
    def __init__(self, master):
        super().__init__(master)

        # Instantiate the Diary
        if len(sys.argv) > 1:
            root_directory = Path(sys.argv[1]).absolute()
        else:
            root_directory = Path().absolute()

        self.diary = Diary(root_directory)

        # Create a small sidebar containing a column of buttons
        sidebar = Frame(self)
        sidebar.grid(column=0)

        # Create buttons for the sidebar
        sidebar_today = Button(sidebar, text="Today's entry", command=self.today)
        sidebar_today.grid(row=0)
        sidebar_search = Button(sidebar, text="Search previous entries", command=self.search)
        sidebar_search.grid(row=1)
        sidebar_calendar = Button(sidebar, text="Calendar", command=self.add_calendar_item)
        sidebar_calendar.grid(row=2)
        sidebar_settings = Button(sidebar, text="Settings", command=self.settings)
        sidebar_settings.grid(row=3)

        # Inline the to-do list
        todo_list_frame = Frame(self)
        todo_list_frame.grid(column=1)

        # Add a label to the top
        todo_list_header = Label(todo_list_frame, text="To-Do List")
        todo_list_header.grid(row=0, sticky=N)
        row_counter = 1
        # Grab the current to-do list
        todo_list_items = self.diary.get_todo_list()
        if todo_list_items:
            for todo_list_item in todo_list_items:
                todo_list_item_frame = Frame(todo_list_frame)
                todo_list_item_frame.grid(row=row_counter)
                row_counter += 1
                Label(todo_list_item_frame, text=todo_list_item)
        else:
            Label(todo_list_frame, text="List is empty!").grid(row=row_counter)

        # Add buttons to the bottom of the to-do list
        todo_list_button_add = Button(text="Add new item", command=self.add_todo_list_item)
        todo_list_button_add.grid(row=row_counter+1, sticky=S)

        # Add calendar appointments for the coming week
        calendar_frame = Frame(self)
        calendar_frame.grid(column=2)

        calendar_frame_header = Label(calendar_frame)
        calendar_frame_header.grid(row=0)

        row_counter = 1
        calendar_items = self.diary.get_calendar_this_week()
        if calendar_items:
            for calendar_item in calendar_items:
                # TODO
                pass
        else:
            Label(calendar_frame, text="No upcoming appointments").grid(row=row_counter)

    def today(self):
        """Open up a dialog box for interacting with today's entry.
        """
        pass

    def search(self):
        """Open up a dialog box for searching through previous entries.
        """
        pass

    def settings(self):
        """Open the settings dialog box.
        """
        pass

    def add_todo_list_item(self):
        """Open a small prompt that adds a new to-do list item.
        """

    def add_calendar_item(self):
        """Open up a dialog box for adding a new calendar item."""
        pass


def main():
    root = Tk.tk()
    program = DiaryProgram(root)
    program.grid(sticky=(N, E, S, W))
    root.mainloop()


if __name__ == "__main__":
    main()
