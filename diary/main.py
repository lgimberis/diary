from pathlib import Path
import re, sys
from tkinter import *
from tkinter import ttk

from diary.diary_handler import Diary
from diary.scroll_frame import ScrollableFrame


class DiaryProgram(Frame):
    """Master class for the program's GUI.
    """
    DEFAULT_CATEGORY = "Diary"

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

        #self.on_resize()
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, *args):
        if self.todo_list_labels:
            bbox = self.todo_list_frame.bbox(self.todo_list_labels[0])
            width = bbox[2] - 50  # TODO dynamically find scrollbar/delete button width
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
            todo_list_item_frame = ScrollableFrame(todo_list_frame)
            todo_list_item_frame.grid(row=1, columnspan=2, sticky="NESW")

            self.todo_list_labels = []

            for row, (rowid, timestamp, text) in enumerate(todo_list_items):
                ttk.Button(todo_list_item_frame.view, image=self.red_cross,
                           command=self.todo_list_item_remover_factory(rowid)) \
                    .grid(row=row, column=0, sticky="NESW")
                label = ttk.Label(todo_list_item_frame.view, text=text, wraplength=400)
                label.grid(row=row, column=1, sticky="NESW")
                self.todo_list_labels.append(label)
                todo_list_item_frame.rowconfigure(row, weight=1)
        else:
            Label(todo_list_frame, text="List is empty!").grid(row=1)

        # Add buttons to the bottom of the to-do list
        todo_list_button_add = Button(todo_list_frame, text="Add new item", command=self.add_todo_list_item)
        todo_list_button_add.grid(row=2, sticky="EWS")

    def manage_tags(self):
        pass

    def today(self):
        """Open up a dialog box for interacting with today's entry.
        """
        entry = Toplevel(self)

        existing_entries = ScrollableFrame(entry)
        existing_entries.grid(row=0, columnspan=2, sticky="NESW")
        todays_entries = self.diary.get_today()
        if todays_entries:
            for row, (rowid, timestamp, entry_text) in enumerate(todays_entries):
                timestamp_time = re.search(r"\d\d:\d\d", timestamp)
                timestamp_label = ttk.Label(existing_entries.view, text=timestamp_time.group(0))
                timestamp_label.grid(row=row, column=0, sticky="NESW")
                content_label = ttk.Label(existing_entries.view, text=entry_text, wraplength=400)
                content_label.grid(row=row, column=1, sticky="NESW")
        else:
            ttk.Label(existing_entries.view, text="No entries yet.").grid(row=0, column=0, sticky="NESW")


        text = StringVar()
        entry_field = ttk.Entry(entry, textvariable=text)
        entry_field.grid(row=1, columnspan=2, sticky="NESW")

        categories = [row[0] for row in self.diary.get_categories()]
        if self.DEFAULT_CATEGORY not in categories:
            categories.append(self.DEFAULT_CATEGORY)
        category = StringVar()
        category.set(self.DEFAULT_CATEGORY)
        category_field = ttk.Combobox(entry, textvariable=category, values=categories)
        category_field.grid(row=2, column=0)

        tag_frame = Frame(entry)
        tag_frame.grid(row=2, column=1)

        tag_box = Listbox(tag_frame)
        tag_box.grid(row=0, column=0)
        tag_scrollbar = ttk.Scrollbar(tag_frame, orient=VERTICAL, command=tag_box.yview)
        tag_scrollbar.grid(row=0, column=1)
        tag_box.configure(yscrollcommand=tag_scrollbar.set)
        tag_button = ttk.Button(tag_box, text="Manage Tags", command=self.manage_tags)
        tag_button.grid(row=1, column=0, sticky="W")

        category_tags = self.diary.get_tags(category.get())
        for rowid, tag in enumerate(category_tags):
            tag_box.insert(rowid, tag)

        def add(*args):
            tags = [item[1] for item in tag_box.curselection()]
            self.diary.add_entry(text.get(), category.get(), tags=tags)
            text.set("")
            category.set(self.DEFAULT_CATEGORY)
            tag_box.selection_clear(0, END)

        def close(*args):
            entry.destroy()

        submit_button = ttk.Button(entry, text="Submit", command=add).grid(row=5, column=0)
        cancel_button = ttk.Button(entry, text="Close", command=close).grid(row=5, column=1)

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
        text = StringVar()
        ttk.Label(entry, text="Enter a new item to add to the to-do list:").grid(row=0, column=0, columnspan=2)
        entry_field = ttk.Entry(entry, textvariable=text)
        entry_field.grid(row=1, column=0, columnspan=2)

        def add(*args):
            self.diary.add_todo_list_item(text.get())
            self.refresh_todo()
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
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.mainloop()



if __name__ == "__main__":
    main()
