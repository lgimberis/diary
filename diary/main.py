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

        self.red_cross = PhotoImage(file='./red_cross.png')

        # Instantiate the Diary
        if len(sys.argv) > 1:
            root_directory = Path(sys.argv[1]).absolute()
        else:
            root_directory = Path().absolute()

        self.diary = Diary(root_directory)
        self.diary.__enter__()

        # Create a small sidebar containing a column of buttons
        sidebar = Frame(self)
        sidebar.grid(row=0, column=0)

        # Create buttons for the sidebar
        sidebar_today = Button(sidebar, text="Today's entry", command=self.today)
        sidebar_today.grid(row=0, sticky=(W, E))
        sidebar_search = Button(sidebar, text="Search previous entries", command=self.search)
        sidebar_search.grid(row=1, sticky=(W, E))
        sidebar_calendar = Button(sidebar, text="Calendar", command=self.add_calendar_item)
        sidebar_calendar.grid(row=2, sticky=(W, E))
        sidebar_settings = Button(sidebar, text="Settings", command=self.settings)
        sidebar_settings.grid(row=3, sticky=(W, E))

        # Inline the to-do list
        self.todo_list_frame = None
        self.refresh()

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

    def refresh(self):
        if self.todo_list_frame:
            self.todo_list_frame.destroy()
        todo_list_frame = Frame(self, background="red")
        todo_list_frame.grid(row=0, column=1, sticky="NS")
        self.todo_list_frame = todo_list_frame

        # Add a label to the top
        todo_list_header = Label(todo_list_frame, text="To-Do List")
        todo_list_header.grid(row=0, sticky=N)
        # Grab the current to-do list
        todo_list_items = list(self.diary.get_todo_list())
        if todo_list_items:
            todo_list_item_frame = Frame(todo_list_frame)
            todo_list_item_frame.grid(row=1, column=0, columnspan=2, sticky=N)
            for row, (rowid, timestamp, text) in enumerate(todo_list_items):
                ttk.Button(todo_list_item_frame, image=self.red_cross,
                           command=self.todo_list_item_remover_factory(rowid)) \
                    .grid(row=row, column=0, sticky=W)
                ttk.Label(todo_list_item_frame, text=text).grid(row=row, column=1, sticky=E)
        else:
            Label(todo_list_frame, text="List is empty!").grid(row=1)

        # Add buttons to the bottom of the to-do list
        todo_list_button_add = Button(todo_list_frame, text="Add new item", command=self.add_todo_list_item)
        todo_list_button_add.grid(row=2, sticky=S)

    def today(self):
        """Open up a dialog box for interacting with today's entry.
        """
        pass

    def todo_list_item_remover_factory(self, rowid):
        def f(*args):
            self.diary.remove_todo_list_item(rowid)
            self.refresh()
        return f

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
        entry = Toplevel(self)
        text = StringVar()
        ttk.Label(entry, text="Enter a new item to add to the to-do list:").grid(row=0, column=0, columnspan=2)
        entry_field = ttk.Entry(entry, textvariable=text)
        entry_field.grid(row=1, column=0, columnspan=2)

        def add(*args):
            self.diary.add_todo_list_item(text.get())
            self.refresh()
            entry.destroy()

        def cancel(*args):
            entry.destroy()

        entry_field.focus()

        Button(entry, text="Add", command=add).grid(row=2, column=0)
        Button(entry, text="Cancel", command=cancel).grid(row=2, column=1)

        entry.bind('<Return>', add)
        entry.bind('<Escape>', cancel)



    def add_calendar_item(self):
        """Open up a dialog box for adding a new calendar item."""
        pass


def main():
    root = Tk()
    program = DiaryProgram(root)
    program.grid(sticky=(N, E, S, W))
    root.mainloop()


if __name__ == "__main__":
    main()
