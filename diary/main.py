from pathlib import Path
import re, sys
import time
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from diary.diary_handler import Diary
from diary.scroll_frame import ScrollableFrame


DEFAULT_CATEGORY = "Diary"
WRAPPING_STATIC_GAP = 30  # Width of scrollbar in pixels, plus a little extra space.
TIMESTAMP_WIDTH = 20
BACKGROUND = "#f0f0f0"
DELETE_BUTTON_WIDTH = 20  # Width in pixels of the todo-list 'delete' button


def wrap_labels(master, labels):
    def f(*args):
        offset = WRAPPING_STATIC_GAP
        if labels:
            offset += max([t.winfo_width() for t, c in labels])
        for t, label in labels:
            label.configure(wraplength=max(master.winfo_width() - offset, 1))
    return f


class TodayWindow(Frame):
    def __bool__(self):
        return bool(self.root.winfo_exists())

    def __init__(self, master, background=BACKGROUND):
        self.master = master
        self.root = Toplevel(master)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.entry_labels = []
        self.no_entries_label = None

        # Instantiate entries
        self.entries_frame = ScrollableFrame(self.root, background=background)
        self.entries_frame.grid(row=0, column=1, columnspan=3, sticky="NESW")
        self.entries_frame.grid_columnconfigure(0, weight=1)

        # Add a text entry box
        self.entry_field = ScrolledText(self.root, height=5, wrap=WORD)
        self.entry_field.grid(row=1, column=1, columnspan=3, sticky="NESW")

        # Add a category selection / input combobox
        categories = [row[1] for row in self.master.get_diary().get_categories()]
        if DEFAULT_CATEGORY not in categories:
            categories.append(DEFAULT_CATEGORY)
        category = StringVar()
        category.set(DEFAULT_CATEGORY)
        self.category_combobox = ttk.Combobox(self.root, textvariable=category, values=categories)
        self.category_combobox.grid(row=2, column=1, sticky="NESW")

        # Add 'add' and 'close' buttons
        def add(*args):
            message = self.entry_field.get("1.0", "end-1c").strip()
            if len(message) > 0:
                self.master.get_diary().add_entry(message, category.get())
                self.entry_field.delete("1.0", "end-1c")
                self.refresh()

        def close(*args):
            self.root.destroy()

        self.submit_button = ttk.Button(self.root, text="Submit", command=add).grid(row=2, column=2, sticky="E")
        close_button = ttk.Button(self.root, text="Close", command=close).grid(row=2, column=3, sticky="E")

        self.entry_field.focus()

        self.root.bind('<Shift-Return>', lambda x: None)
        self.root.bind('<Return>', add)
        self.root.bind('<Escape>', close)

        self.refresh()

    def refresh(self):
        # Update combobox categories
        categories = [row[1] for row in self.master.get_diary().get_categories()]
        self.category_combobox["values"] = categories

        # Redraw all entries. Delete the labels
        if self.entry_labels:
            for timestamp_label, content_label in self.entry_labels:
                timestamp_label.destroy()
                content_label.destroy()
        if self.no_entries_label:
            self.no_entries_label.destroy()
            self.no_entries_label = None

        self.entry_labels = []
        if entries := self.master.get_diary().get_today():
            for row, (rowid, timestamp, entry_text) in enumerate(entries):
                timestamp_time = re.search(r"\d\d:\d\d", timestamp)

                timestamp_label = ttk.Label(self.entries_frame.view, text=timestamp_time.group(0))
                timestamp_label.grid(row=row, column=0, sticky="NESW")
                content_label = ttk.Label(self.entries_frame.view, text=entry_text)
                content_label.grid(row=row, column=1, sticky="NESW")
                self.entries_frame.view.rowconfigure(row, weight=1)

                self.entry_labels.append((timestamp_label, content_label))
        else:
            self.no_entries_label = ttk.Label(self.entries_frame.view, text="No entries yet.").grid(
                row=0, column=0, sticky="NESW")

    def update(self):
        if self.entry_labels:
            bbox = self.root.bbox(self.entry_labels[0][0])
            width = max(bbox[2] - WRAPPING_STATIC_GAP - TIMESTAMP_WIDTH, 0)
            for label_t, label_c in self.entry_labels:
                label_c.configure(wraplength=width)


class TodoManager:
    def __init__(self, master, diary, image):
        self.master = master
        self.diary = diary
        self.root = None
        self.todo_list_labels = []
        self.image = image

        self.refresh()

    def __bool__(self):
        return bool(self.root.winfo_exists()) if self.root else False

    def refresh(self):
        if self.root:
            self.root.destroy()
        todo_list_frame = Frame(self.master, background="red")
        self.root = todo_list_frame

        todo_list_frame.grid(row=0, column=1, sticky="NESW")
        todo_list_frame.columnconfigure(1, weight=1)
        todo_list_frame.rowconfigure(1, weight=1)

        # Add a label to the top
        todo_list_header = Label(todo_list_frame, text="To-Do List")
        todo_list_header.grid(row=0, sticky="NEW")
        # Grab the current to-do list
        todo_list_items = list(self.diary.get_todo_list())
        if todo_list_items:
            todo_list_item_frame = ScrollableFrame(todo_list_frame, background=BACKGROUND)
            todo_list_item_frame.grid(row=1, columnspan=2, sticky="NESW")

            self.todo_list_labels = []

            for row, (rowid, timestamp, text) in enumerate(todo_list_items):
                ttk.Button(todo_list_item_frame.view, image=self.image,
                           command=self.remove_todo_list_item_builder(rowid)) \
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

    def update(self):
        if self.todo_list_labels:
            bbox = self.root.bbox(self.todo_list_labels[0])
            width = max(bbox[2] - WRAPPING_STATIC_GAP - DELETE_BUTTON_WIDTH, 0)
            for label in self.todo_list_labels:
                label.configure(wraplength=width)

    def add_todo_list_item(self):
        entry = Toplevel(self.master)
        ttk.Label(entry, text="Enter a new item to add to the to-do list:").grid(row=0, column=0, columnspan=2)
        entry_field = ScrolledText(entry, wrap=WORD)
        entry_field.grid(row=1, column=0, columnspan=2)

        def add(*args):
            self.diary.add_todo_list_item(entry_field.get("1.0", "end-1c").strip())
            entry.destroy()
            self.refresh()

        def cancel(*args):
            entry.destroy()

        entry_field.focus()

        Button(entry, text="Add", command=add).grid(row=2, column=0)
        Button(entry, text="Cancel", command=cancel).grid(row=2, column=1)

        entry.bind('<Shift-Return>', lambda x: None)  # Allow user to shift-return to enter newlines
        entry.bind('<Return>', add)
        entry.bind('<Escape>', cancel)

    def remove_todo_list_item_builder(self, rowid):
        def f(*args):
            self.diary.remove_todo_list_item(rowid)
            self.refresh()
        return f


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
        self.todo_list = TodoManager(self, self.diary, self.red_cross)

        self.today_window = None

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
        if self.todo_list:
            self.todo_list.update()
        if self.today_window:
            self.today_window.update()

    def today(self):
        """Open up a dialog box for interacting with today's entry.
        """
        self.today_window = TodayWindow(self)

    def get_diary(self):
        return self.diary

    def search(self):
        """Open up a dialog box for searching through previous entries.
        """
        pass

    def settings(self):
        """Open the settings dialog box.
        """
        pass

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
