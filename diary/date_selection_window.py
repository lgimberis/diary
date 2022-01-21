import datetime
from tkinter import *
import tkinter.ttk as ttk

from tkcalendar import Calendar


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
