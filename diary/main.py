import datetime
from pathlib import Path
import sys
import time
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

import diary


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
    """Opens a window for entering today's entries.

    Contains an EntryFrame (displays entries), ScrolledText (contains new entry text), and Combobox (selects category).
    """

    def __init__(self, master, __diary, background=diary.BACKGROUND):
        super().__init__(master)
        self.__diary = __diary

        # Instantiate entries
        self.entry_frame = diary.entry_frame.EntryFrame(self.root, background=background, timestamp_format="%H:%M")
        self.entry_frame.grid(row=0, column=0, columnspan=4, sticky="NESW")
        self.entry_frame.grid_columnconfigure(0, weight=1)
        self.update_list.append(self.entry_frame)

        # Add a text entry box
        self.entry_field = ScrolledText(self.root, height=5, wrap=WORD)
        self.entry_field.grid(row=1, column=0, columnspan=4, sticky="NESW")

        # Add a category label and selection / input combobox
        self.category_label = ttk.Label(self.root, text="Category: ")
        self.category_label.grid(row=2, column=0, sticky="W")

        category_var = StringVar()
        category_var.set(diary.DEFAULT_CATEGORY)
        self.category_combobox = ttk.Combobox(self.root, textvariable=category_var)
        self.category_combobox.grid(row=2, column=1, sticky="NESW")

        # Populate entry frame with entries
        if entries := self.__diary.get_day(0):
            for row, (rowid, timestamp, entry_text) in enumerate(entries):
                self.entry_frame.add_message(entry_text, timestamp)
        self.entry_frame.scroll_to_end()

        # Refresh to fill in the category combobox
        self.refresh()

        # 'add' and 'close' buttons
        def add(*args):
            message = self.entry_field.get("1.0", "end-1c").strip()
            category_text = category_var.get().strip()
            if len(message) > 0:
                self.master.get_diary().add_entry(message, category_text)
                _timestamp = self.master.get_diary().get_timestamp()
                self.entry_frame.add_message(message, _timestamp)
                self.entry_field.delete("1.0", "end-1c")
                self.refresh()
                self.entry_frame.scroll_to_end()

        def close(*args):
            self.root.destroy()

        self.submit_button = ttk.Button(self.root, text="Submit", command=add).grid(row=2, column=2, sticky="E")
        close_button = ttk.Button(self.root, text="Close", command=close).grid(row=2, column=3, sticky="E")

        self.entry_field.focus()

        self.root.bind('<Shift-Return>', lambda x: None)
        self.root.bind('<Return>', add)
        self.root.bind('<Escape>', close)

    def refresh(self):
        # Update combobox categories
        categories = [category for categoryid, category in self.__diary.get_categories()]
        if diary.DEFAULT_CATEGORY not in categories:
            categories.append(diary.DEFAULT_CATEGORY)
        self.category_combobox["values"] = categories


class EntrySearchWindow(GenericWindow):
    def __init__(self, master, __diary, entry_frame):
        super().__init__(master)
        self.root.title("Search Previous Entries")
        self.__diary = __diary
        self.entry_frame = entry_frame

        # Add a box to filter by time
        time_label = ttk.Label(self.root, text="Filter by time:")
        time_label.grid(row=0, column=0, columnspan=2, sticky="W")

        self.start_time_var = StringVar()
        time_start_entry = ttk.Entry(self.root, textvariable=self.start_time_var)
        time_start_entry.grid(row=1, column=1, sticky="NESW")

        self.end_time_var = StringVar()
        time_end_entry = ttk.Entry(self.root, textvariable=self.end_time_var)
        time_end_entry.grid(row=2, column=1, sticky="NESW")

        self.start_time_selector = None
        self.end_time_selector = None

        def get_start_time(*args):
            if self.start_time_selector:
                self.start_time_selector.focus()
            else:
                self.start_time_selector = diary.date_selection_window.DateTimeSelectorWindow(self.root, self.start_time_var)

        def get_end_time(*args):
            if self.end_time_selector:
                self.end_time_selector.focus()
            else:
                self.end_time_selector = self.search_end_time = diary.date_selection_window.DateTimeSelectorWindow(self.root, self.end_time_var,
                                                                                      default_time="23:59")

        time_start_calendar_button = ttk.Button(self.root, text="Select earliest date", command=get_start_time)
        time_start_calendar_button.grid(row=1, column=0)

        time_end_calendar_button = ttk.Button(self.root, text="Select latest date", command=get_end_time)
        time_end_calendar_button.grid(row=2, column=0)

        # Add a box to filter by category
        category_label = ttk.Label(self.root, text="Category: ")
        category_label.grid(row=3, column=0)

        categories = [""]
        for row in self.__diary.get_categories():
            categories.append(row[1])
        if diary.DEFAULT_CATEGORY not in categories:
            categories.append(diary.DEFAULT_CATEGORY)
        self.category_var = StringVar()
        self.category_var.set("")
        category_combobox = ttk.Combobox(self.root, textvariable=self.category_var, values=categories)
        category_combobox.grid(row=3, column=1, sticky="NESW")

        # Add a box to filter by text
        text_filter_label = ttk.Label(self.root, text="Contains text: ")
        text_filter_label.grid(row=4, column=0)

        self.text_filter_var = StringVar()
        text_filter_entry = ttk.Entry(self.root, textvariable=self.text_filter_var)
        text_filter_entry.grid(row=4, column=1, sticky="NESW")

        def search(*args):
            if self.run():
                self.root.destroy()
            else:
                self.focus()

        # Add buttons
        search_button = ttk.Button(self.root, text="Search", command=search)
        search_button.grid(row=100, column=0)

        def cancel(*_args):
            self.root.destroy()

        cancel_button = ttk.Button(self.root, text="Cancel", command=cancel)
        cancel_button.grid(row=100, column=1)

        self.root.bind('<Return>', search)
        self.root.bind('<Escape>', cancel)

    def run(self):
        # Update the entry frame with results
        start_time = self.start_time_var.get().strip()
        end_time = self.end_time_var.get().strip()
        category = self.category_var.get().strip()
        text_filter = self.text_filter_var.get().strip()

        if category and not self.__diary.get_category_id(category):
            messagebox.showerror("Invalid Category", f"Category '{category}' is not associated with any entries.")
        elif not (start_time or end_time or category or text_filter):
            messagebox.showerror("Filter Required", "Please filter on at least one field.")
        else:
            entries = list(self.__diary.entry_search(start_time, end_time, category, text_filter))
            if entries:
                self.entry_frame.clear()
                for rowid, timestamp, entry in entries:
                    self.entry_frame.add_message(entry, timestamp)
                return True
            else:
                messagebox.showinfo("Search failed", "No results found")
        return False


class PreviousWindow(GenericWindow):
    """Open a window for searching, reviewing and/or editing previous entries.

    The main window lists all messages with the most recent first."""

    def __init__(self, master, __diary):
        super().__init__(master)
        self.root.title("Previous Entries")
        self.__diary = __diary

        self.sidebar = Frame(self.root)
        self.sidebar.grid(row=0, column=0, sticky="NW")

        self.entry_frame = diary.entry_frame.EntryFrame(self.root)
        self.entry_frame.grid(row=0, column=1, sticky="NESW")
        self.update_list.append(self.entry_frame)

        def entries_from_previous_day(days_ago, since=False):
            def f(*args):
                self.entry_frame.clear()
                for rowid, timestamp, entry in self.__diary.get_day(days_ago, since=since):
                    self.entry_frame.add_message(entry, timestamp)

                self.entry_frame.scroll_to_end()
            return f

        self.sidebar_today = ttk.Button(self.sidebar,
                                        text="Today",
                                        command=entries_from_previous_day(days_ago=0))
        self.sidebar_today.grid(row=0, column=0)

        self.sidebar_yesterday = ttk.Button(self.sidebar,
                                            text="Yesterday",
                                            command=entries_from_previous_day(days_ago=1))
        self.sidebar_yesterday.grid(row=1, column=0)

        self.sidebar_seven_days = ttk.Button(self.sidebar,
                                             text="Past 7 days",
                                             command=entries_from_previous_day(days_ago=7, since=True))
        self.sidebar_seven_days.grid(row=2, column=0)

        self.entry_search_window = None

        def entry_search(*args):
            if self.entry_search_window:
                self.entry_search_window.focus()
            else:
                self.entry_search_window = EntrySearchWindow(self.root, self.__diary, self.entry_frame)

        self.sidebar_search = ttk.Button(self.sidebar, text="Search", command=entry_search)
        self.sidebar_search.grid(row=3, column=0)

        # Load up previous 7 days by default
        entries_from_previous_day(7, since=True)()


class TodoManager:
    def __init__(self, master, __diary, image):
        self.master = master
        self.__diary = __diary
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
        todo_list_items = list(self.__diary.todo_list_get())
        if todo_list_items:
            todo_list_item_frame = diary.scroll_frame.ScrollableFrame(todo_list_frame, background=diary.BACKGROUND)
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
            width = max(bbox[2] - diary.SCROLLBAR_WIDTH - diary.DELETE_BUTTON_WIDTH, 0)
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
                self.__diary.todo_list_add(text)
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
            self.__diary.todo_list_remove(rowid)
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
        self.__diary = diary.diary_handler.Diary(root_directory)

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
        self.todo_list = TodoManager(self, self.__diary, self.red_cross)

        self.today_window = None
        self.previous_window = None

        self.grid_columnconfigure(1, weight=3)

        # Add calendar appointments for the coming week
        calendar_frame = Frame(self)
        calendar_frame.grid(column=2)

        calendar_frame_header = Label(calendar_frame)
        calendar_frame_header.grid(row=0)

        row_counter = 1
        calendar_items = self.__diary.get_calendar_this_week()
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
            self.today_window = TodayWindow(self, self.__diary)

    def get_diary(self):
        return self.__diary

    def previous(self):
        """Open up a dialog box for searching through previous entries.
        """
        if self.previous_window:
            self.previous_window.focus()
        else:
            self.previous_window = PreviousWindow(self, self.__diary)

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


if __name__ == "__main__":
    main()
