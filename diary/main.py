from pathlib import Path
import re, sys
import time
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from diary.diary_handler import Diary
from diary.scroll_frame import ScrollableFrame


class DiaryProgram(Frame):
    """Master class for the program's GUI.
    """
    DEFAULT_CATEGORY = "Diary"
    WRAPPING_STATIC_GAP = 30  # Width of scrollbar in pixels, plus a little extra space.
    DELETE_BUTTON_WIDTH = 20  # Width in pixels of the todo-list 'delete' button

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
        sidebar.grid(row=0, column=0, sticky="NW")
        self.grid_rowconfigure(0, weight=1)

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
        self.todo_list_labels = []
        self.refresh_todo()

        # Prepare 'today' variables
        self.today_no_entries_label = None
        self.today_entries = []
        self.today_entries_frame = None

        self.grid_columnconfigure(1, weight=3)

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

    def update(self, *args):
        if self.todo_list_labels:
            bbox = self.todo_list_frame.bbox(self.todo_list_labels[0])
            width = max(bbox[2] - self.WRAPPING_STATIC_GAP - self.DELETE_BUTTON_WIDTH, 0)
            for label in self.todo_list_labels:
                label.configure(wraplength=width)

    def refresh_todo(self):
        if self.todo_list_frame:
            self.todo_list_frame.destroy()
        todo_list_frame = Frame(self, background="red")
        self.todo_list_frame = todo_list_frame

        todo_list_frame.grid(row=0, column=1, sticky="NESW")
        todo_list_frame.columnconfigure(0, weight=1)
        todo_list_frame.rowconfigure(1, weight=1)

        # Add a label to the top
        todo_list_header = Label(todo_list_frame, text="To-Do List")
        todo_list_header.grid(row=0, sticky="NEW")
        # Grab the current to-do list
        todo_list_items = list(self.diary.get_todo_list())
        if todo_list_items:
            todo_list_item_frame = ScrollableFrame(todo_list_frame, background="SystemButtonFace")
            todo_list_item_frame.grid(row=1, columnspan=2, sticky="NESW")

            self.todo_list_labels = []

            for row, (rowid, timestamp, text) in enumerate(todo_list_items):
                ttk.Button(todo_list_item_frame.view, image=self.red_cross,
                           command=self.todo_list_item_remover_factory(rowid)) \
                    .grid(row=row, column=0, sticky="NESW")
                label = ttk.Label(todo_list_item_frame.view, text=text, wraplength=20)
                label.grid(row=row, column=1, sticky="NESW")
                self.todo_list_labels.append(label)
                todo_list_item_frame.rowconfigure(row, weight=1)
        else:
            Label(todo_list_frame, text="List is empty!").grid(row=1)

        # Add buttons to the bottom of the to-do list
        todo_list_button_add = Button(todo_list_frame, text="Add new item", command=self.add_todo_list_item)
        todo_list_button_add.grid(row=2, sticky="EWS")

    @staticmethod
    def wrap_labels(master, labels):

        def f(*args):
            offset = DiaryProgram.WRAPPING_STATIC_GAP
            if labels:
                offset += max([t.winfo_width() for t, c in labels])
            for t, label in labels:
                label.configure(wraplength=max(master.winfo_width() - offset, 1))
        return f

    def refresh_today(self, *args):
        if self.today_entries_frame:
            if self.today_entries:
                for timestamp_label, content_label in self.today_entries:
                    timestamp_label.destroy()
                    content_label.destroy()
            if self.today_no_entries_label:
                self.today_no_entries_label.destroy()

            self.today_entries = []
            if entries := self.diary.get_today():
                for row, (rowid, timestamp, entry_text) in enumerate(entries):
                    timestamp_time = re.search(r"\d\d:\d\d", timestamp)

                    timestamp_label = ttk.Label(self.today_entries_frame.view, text=timestamp_time.group(0))
                    timestamp_label.grid(row=row, column=0, sticky="NESW")
                    content_label = ttk.Label(self.today_entries_frame.view, text=entry_text)
                    content_label.grid(row=row, column=1, sticky="NESW")

                    self.today_entries.append((timestamp_label, content_label))
                self.today_entries_frame.view.bind('<Configure>',
                                                   self.wrap_labels(self.today_entries_frame.view, self.today_entries))
            else:
                self.today_no_entries_label = ttk.Label(self.today_entries_frame.view, text="No entries yet.").grid(row=0, column=0, sticky="NESW")

    def today(self):
        """Open up a dialog box for interacting with today's entry.
        """
        entry = Toplevel(self)
        entry.grid_rowconfigure(0, weight=1)
        entry.grid_columnconfigure(0, weight=1)

        # Instantiate entries
        self.today_entries_frame = ScrollableFrame(entry, background="SystemButtonFace")
        self.today_entries_frame.grid(row=0, columnspan=2, sticky="NESW")
        self.refresh_today()

        # Add a text entry box
        text = StringVar()
        entry_field = ttk.Entry(entry, textvariable=text)
        entry_field.grid(row=1, columnspan=2, sticky="NESW")

        # Add a category selection / input combobox
        categories = [row[1] for row in self.diary.get_categories()]
        if self.DEFAULT_CATEGORY not in categories:
            categories.append(self.DEFAULT_CATEGORY)
        category = StringVar()
        category.set(self.DEFAULT_CATEGORY)
        category_field = ttk.Combobox(entry, textvariable=category, values=categories)
        category_field.grid(row=2, column=0)

        # Add 'add' and 'close' buttons
        def add(*args):
            if len(text.get()) > 0:
                self.diary.add_entry(text.get(), category.get())
                text.set("")
                category.set(self.DEFAULT_CATEGORY)
                self.refresh_today()

        def close(*args):
            entry.destroy()

        submit_button = ttk.Button(entry, text="Submit", command=add).grid(row=5, column=0)
        close_button = ttk.Button(entry, text="Close", command=close).grid(row=5, column=1)

        entry.bind('<Return>', add)
        entry.bind('<Escape>', close)

    def todo_list_item_remover_factory(self, rowid):
        def f(*args):
            self.diary.remove_todo_list_item(rowid)
            self.refresh_todo()
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
        ttk.Label(entry, text="Enter a new item to add to the to-do list:").grid(row=0, column=0, columnspan=2)
        entry_field = ScrolledText(entry, wrap=WORD)
        entry_field.grid(row=1, column=0, columnspan=2)

        def add(*args):
            self.diary.add_todo_list_item(entry_field.get("1.0", "end-1c").strip())
            entry.destroy()
            self.refresh_todo()

        def cancel(*args):
            entry.destroy()

        entry_field.focus()

        Button(entry, text="Add", command=add).grid(row=2, column=0)
        Button(entry, text="Cancel", command=cancel).grid(row=2, column=1)

        entry.bind('<Shift-Return>', lambda x:None)  # Allow user to shift-return to enter newlines
        entry.bind('<Return>', add)
        entry.bind('<Escape>', cancel)



    def add_calendar_item(self):
        """Open up a dialog box for adding a new calendar item."""
        pass


def main():
    root = Tk()
    program = DiaryProgram(root)
    program.grid(sticky=(N, E, S, W))
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    try:
        while True:
            time.sleep(0.017)
            root.update_idletasks()
            root.update()
            program.update()
    except TclError as e:
        # Expected normal close of the program
        pass


if __name__ == "__main__":
    main()
