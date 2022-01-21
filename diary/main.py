import datetime
from pathlib import Path
import sys
import time
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

from diary.diary_handler import Diary
from diary.scroll_frame import ScrollableFrame

from tkcalendar import Calendar, DateEntry


DEFAULT_CATEGORY = "Diary"
SCROLLBAR_WIDTH = 30  # Width of scrollbar in pixels, plus a little extra space.
TIMESTAMP_WIDTH = 40
BACKGROUND = "#f0f0f0"
DELETE_BUTTON_WIDTH = 20  # Width in pixels of the todo-list 'delete' button
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def iso_to_weekday(iso_timestamp: str, relative=True) -> str:
    """Extract the weekday from a given ISO timestamp.

    If relative is True, it may instead return either 'Today' or 'Yesterday' if appropriate.
    """

    target_date = datetime.datetime.fromisoformat(iso_timestamp).date()

    if relative:
        today = datetime.datetime.now().date()

        if today == target_date:
            return "Today"
        if today == target_date + datetime.timedelta(days=1):
            return "Yesterday"
    return WEEKDAYS[target_date.weekday()]


class DateTimeSelectorWindow:
    """Open a window to encourage the user to select a date and time.
    """

    def __init__(self, master, var, default_time="00:00"):

        self.root = Toplevel(master)
        self.var = var

        today = datetime.datetime.now()

        calendar = Calendar(self.root, font="Arial 14", selectmode='day', locale='en_US',
                            cursor="hand1", year=today.year, month=today.month, day=today.day, )
        calendar.grid(row=0, column=0, columnspan=2, sticky="NESW")

        # Need a mini-frame to get padding on the Entry
        time_of_day_frame = ttk.Frame(self.root, padding="3 50 3 3")
        time_of_day_frame.grid(row=1, column=0, columnspan=2, sticky="NESW")

        time_of_day_label = ttk.Label(time_of_day_frame, text="Time: ")
        time_of_day_label.grid(row=1, column=0, sticky="NESW")

        time_of_day_var = StringVar()
        time_of_day_var.set(default_time)
        time_of_day = ttk.Entry(time_of_day_frame, textvariable=time_of_day_var)
        time_of_day.grid(row=1, column=1, sticky="NESW")

        def submit(*_args):
            month, day, year = calendar.get_date().split("/")  # (D)M/(D)D/YY, no zero-padding
            year = int(year)+2000  # I know, I know. It is what it is.
            iso_date = f"{year}-{int(month):02}-{int(day):02}"
            self.var.set(f"{iso_date} {time_of_day_var.get().strip()}")
            self.root.destroy()

        def cancel(*_args):
            self.root.destroy()

        submit_button = ttk.Button(self.root, text="Select", command=submit)
        submit_button.grid(row=2, column=0, sticky="W")

        cancel_button = ttk.Button(self.root, text="Cancel", command=cancel)
        cancel_button.grid(row=2, column=1, sticky="E")

    def __bool__(self):
        return self.root.winfo_exists() if self.root else False


class GenericWindow:
    def __init__(self, master):
        self.master = master
        self.root = Toplevel(master)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.update_list = []

    def __bool__(self):
        return bool(self.root.winfo_exists()) if self.root else False

    def update(self):
        for item in self.update_list:
            if item:
                item.update()

    def focus(self):
        if self.root:
            self.root.focus()


class TodayWindow(GenericWindow):
    def __init__(self, master, background=BACKGROUND):
        super().__init__(master)
        self.entry_labels = []
        self.no_entries_label = None

        # Instantiate entries
        self.entries_frame = EntryFrame(self.root, background=background, timestamp_format="%H:%M")
        self.entries_frame.grid(row=0, column=0, columnspan=4, sticky="NESW")
        self.entries_frame.grid_columnconfigure(0, weight=1)
        self.update_list.append(self.entries_frame)

        # Add a text entry box
        self.entry_field = ScrolledText(self.root, height=5, wrap=WORD)
        self.entry_field.grid(row=1, column=0, columnspan=4, sticky="NESW")

        # Add a category selection / input combobox, and a label for it
        self.category_label = ttk.Label(self.root, text="Category: ")
        self.category_label.grid(row=2, column=0, sticky="W")
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
            category_text = category.get().strip()
            if len(message) > 0:
                self.master.get_diary().add_entry(message, category_text)
                _timestamp = self.master.get_diary().get_timestamp()
                self.entries_frame.add_message(message, _timestamp)
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

        if entries := self.master.get_diary().get_day(0):
            for row, (rowid, timestamp, entry_text) in enumerate(entries):
                self.entries_frame.add_message(entry_text, timestamp)
        self.refresh()

    def refresh(self):
        # Update combobox categories
        categories = [row[1] for row in self.master.get_diary().get_categories()]
        self.category_combobox["values"] = categories


class EntryFrame(ScrollableFrame):
    """Utility subclass which displays a list of messages alongside their timestamps."""

    WEEKDAY_CODE_RELATIVE = "RELATIVE_WEEKDAY"
    WEEKDAY_CODE = "WEEKDAY"

    def __init__(self, master, background=BACKGROUND, timestamp_format=f"{WEEKDAY_CODE_RELATIVE} %H:%M"):
        super().__init__(master, background)
        self.timestamp_format = timestamp_format

        self.timestamps = []
        self.entries = []
        self.count_entries = 0
        self.view.grid_columnconfigure(1, weight=1)

    def clear(self):
        for timestamp, entry in zip(self.timestamps, self.entries):
            timestamp.destroy()
            entry.destroy()
        self.timestamps = []
        self.entries = []
        self.count_entries = 0

    def add_message(self, entry, iso_timestamp):
        self.count_entries += 1
        self.view.rowconfigure(self.count_entries, weight=1)

        time = datetime.datetime.fromisoformat(iso_timestamp)
        if self.WEEKDAY_CODE_RELATIVE in self.timestamp_format:
            timestamp_format = self.timestamp_format.replace(self.WEEKDAY_CODE_RELATIVE, iso_to_weekday(iso_timestamp, relative=True))
        elif self.WEEKDAY_CODE in self.timestamp_format:
            timestamp_format = self.timestamp_format.replace(self.WEEKDAY_CODE, iso_to_weekday(iso_timestamp, relative=False))
        else:
            timestamp_format = self.timestamp_format
        timestamp = time.strftime(timestamp_format)

        timestamp_label = ttk.Label(self.view, text=timestamp)
        timestamp_label.grid(row=self.count_entries, column=0, sticky="NEW")
        self.timestamps.append(timestamp_label)

        entry_label = ttk.Label(self.view, text=entry)
        entry_label.grid(row=self.count_entries, column=1, sticky="NESW")
        self.entries.append(entry_label)

    def update(self):
        if self.master.winfo_exists() and self.entries:
            width = max(self.entries[0].winfo_width() - self._scrollbar.winfo_width(), 0)
            for label_c in self.entries:
                label_c.configure(wraplength=width)


class PreviousWindow(GenericWindow):
    """Open a window for searching, reviewing and/or editing previous entries.

    The main window lists all messages with the most recent first."""

    def __init__(self, master):
        super().__init__(master)
        self.root.title("Previous Entries")
        self.diary = self.master.get_diary()

        self.sidebar = Frame(self.root)
        self.sidebar.grid(row=0, column=0, sticky="NW")

        self.entry_frame = EntryFrame(self.root)
        self.entry_frame.grid(row=0, column=1, sticky="NESW")
        self.update_list.append(self.entry_frame)

        def today_or_yesterday(days_ago):
            def f(*args):
                self.entry_frame.clear()
                for rowid, timestamp, entry in self.diary.get_day(days_ago):
                    self.entry_frame.add_message(entry, timestamp)
            return f

        def seven_days(*args):
            self.entry_frame.clear()
            for rowid, timestamp, entry in self.diary.get_day(7, since=True):
                weekday = iso_to_weekday(timestamp)
                timestamp_formatted = (datetime.datetime.fromisoformat(timestamp)).strftime("%H:%M")
                self.entry_frame.add_message(entry, timestamp)

        self.sidebar_today = ttk.Button(self.sidebar, text="Today", command=today_or_yesterday(0))
        self.sidebar_today.grid(row=0, column=0)

        self.sidebar_yesterday = ttk.Button(self.sidebar, text="Yesterday", command=today_or_yesterday(1))
        self.sidebar_yesterday.grid(row=1, column=0)

        self.sidebar_seven_days = ttk.Button(self.sidebar, text="Past 7 days", command=seven_days)
        self.sidebar_seven_days.grid(row=2, column=0)

        def search(*args):
            root = Toplevel(self.master)
            root.title("Search Previous Entries")

            # Add a box to filter by time
            time_label = ttk.Label(root, text="Filter by time:")
            time_label.grid(row=0, column=0, columnspan=2, sticky="W")

            start_time_var = StringVar()
            time_start_entry = ttk.Entry(root, textvariable=start_time_var)
            time_start_entry.grid(row=1, column=1, sticky="NESW")

            end_time_var = StringVar()
            time_end_entry = ttk.Entry(root, textvariable=end_time_var)
            time_end_entry.grid(row=2, column=1, sticky="NESW")

            def get_start_time(*_args):
                self.search_start_time = DateTimeSelectorWindow(root, start_time_var)

            def get_end_time(*_args):
                self.search_end_time = DateTimeSelectorWindow(root, end_time_var, default_time="23:59")

            time_start_calendar_button = ttk.Button(root, text="Select earliest date", command=get_start_time)
            time_start_calendar_button.grid(row=1, column=0)

            time_end_calendar_button = ttk.Button(root, text="Select latest date", command=get_end_time)
            time_end_calendar_button.grid(row=2, column=0)

            # Add a box to filter by category
            category_label = ttk.Label(root, text="Category: ")
            category_label.grid(row=3, column=0)

            categories = [""]
            for row in self.master.get_diary().get_categories():
                categories.append(row[1])
            if DEFAULT_CATEGORY not in categories:
                categories.append(DEFAULT_CATEGORY)
            category_var = StringVar()
            category_var.set("")
            category_combobox = ttk.Combobox(root, textvariable=category_var, values=categories)
            category_combobox.grid(row=3, column=1, sticky="NESW")

            # Add a box to filter by text
            text_filter_label = ttk.Label(root, text="Contains text: ")
            text_filter_label.grid(row=4, column=0)

            text_filter_var = StringVar()
            text_filter_entry = ttk.Entry(root, textvariable=text_filter_var)
            text_filter_entry.grid(row=4, column=1, sticky="NESW")

            def run(*_args):
                # Update the entry frame with results
                start_time = start_time_var.get().strip()
                end_time = end_time_var.get().strip()
                category = category_var.get().strip()
                text_filter = text_filter_var.get().strip()
                if category and not self.diary.get_category_id(category):
                    messagebox.showerror("Invalid Category", f"Category '{category}' is not associated with any entries.")
                    root.focus()
                elif not (start_time or end_time or category or text_filter):
                    messagebox.showerror("Filter Required", "Please filter on at least one field.")
                    root.focus()
                else:
                    entries = list(self.diary.entry_search(start_time, end_time, category, text_filter))
                    if entries:
                        self.entry_frame.clear()
                        for rowid, timestamp, entry in entries:
                            self.entry_frame.add_message(entry, timestamp)
                        # Destroy search window
                        root.destroy()
                    else:
                        messagebox.showinfo("Search failed", "No results found")
                        root.focus()

            # Add buttons
            search_button = ttk.Button(root, text="Search", command=run)
            search_button.grid(row=100, column=0)

            def cancel(*_args):
                root.destroy()
            cancel_button = ttk.Button(root, text="Cancel", command=cancel)
            cancel_button.grid(row=100, column=1)

            root.bind('<Return>', run)
            root.bind('<Escape>', cancel)

        self.sidebar_search = ttk.Button(self.sidebar, text="Search", command=search)
        self.sidebar_search.grid(row=3, column=0)

        # Load up previous 7 days by default
        seven_days()

    def refresh(self):
        pass


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
        todo_list_items = list(self.diary.todo_list_get())
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
            width = max(bbox[2] - SCROLLBAR_WIDTH - DELETE_BUTTON_WIDTH, 0)
            for label in self.todo_list_labels:
                label.configure(wraplength=width)

    def add_todo_list_item(self):
        entry = Toplevel(self.master)
        ttk.Label(entry, text="Enter a new item to add to the to-do list:").grid(row=0, column=0, columnspan=2)
        entry_field = ScrolledText(entry, wrap=WORD)
        entry_field.grid(row=1, column=0, columnspan=2)

        def add(*args):
            text = entry_field.get("1.0", "end-1c").strip()
            if len(text) > 0:
                self.diary.todo_list_add(text)
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
            self.diary.todo_list_remove(rowid)
            self.refresh()
        return f


class DiaryProgram(Frame):
    """Master class for the program's GUI.
    """

    def __init__(self, master, root_directory=None):
        super().__init__(master)

        self.red_cross = PhotoImage(file='./red_cross.png')

        # Instantiate the Diary
        if not root_directory:
            root_directory = Path().absolute()
        self.diary = Diary(root_directory)

        # Create a small sidebar containing a column of buttons
        sidebar = Frame(self)
        sidebar.grid(row=0, column=0, sticky="NW")
        self.grid_rowconfigure(0, weight=1)

        # Create buttons for the sidebar
        sidebar_today = Button(sidebar, text="Today's entry", command=self.today)
        sidebar_today.grid(row=0, sticky=(W, E))
        sidebar_search = Button(sidebar, text="Previous entries", command=self.previous)
        sidebar_search.grid(row=1, sticky=(W, E))
        sidebar_calendar = Button(sidebar, text="Calendar", command=self.add_calendar_item)
        sidebar_calendar.grid(row=2, sticky=(W, E))
        sidebar_settings = Button(sidebar, text="Settings", command=self.settings)
        sidebar_settings.grid(row=3, sticky=(W, E))

        # Inline the to-do list
        self.todo_list = TodoManager(self, self.diary, self.red_cross)

        self.today_window = None
        self.previous_window = None

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
        if self.previous_window:
            self.previous_window.update()

    def today(self):
        """Open up a dialog box for interacting with today's entry.
        """
        if self.today_window:
            self.today_window.focus()
        else:
            self.today_window = TodayWindow(self)

    def get_diary(self):
        return self.diary

    def previous(self):
        """Open up a dialog box for searching through previous entries.
        """
        if self.previous_window:
            self.previous_window.focus()
        else:
            self.previous_window = PreviousWindow(self)

    def settings(self):
        """Open the settings dialog box.
        """
        pass

    def add_calendar_item(self):
        """Open up a dialog box for adding a new calendar item."""
        pass


def main():
    root = Tk()

    root_directory = Path().absolute()
    if len(sys.argv) > 1:
        root_directory = Path(sys.argv[1]).absolute()
    program = DiaryProgram(root, root_directory)
    program.grid(sticky="NESW")
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
    program.diary.close()


if __name__ == "__main__":
    main()
