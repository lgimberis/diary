import datetime
import tkinter.ttk as ttk

import diary


class EntryFrame(diary.scroll_frame.ScrollableFrame):
    """Utility subclass which displays a list of messages alongside their timestamps."""

    WEEKDAY_CODE_RELATIVE = "RELATIVE_WEEKDAY"
    WEEKDAY_CODE = "WEEKDAY"

    def __init__(self, master, background=diary.BACKGROUND, timestamp_format=f"{WEEKDAY_CODE_RELATIVE} %H:%M"):
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
            timestamp_format = self.timestamp_format.replace(self.WEEKDAY_CODE_RELATIVE,
                                                             diary.iso_to_weekday(iso_timestamp, relative=True))
        elif self.WEEKDAY_CODE in self.timestamp_format:
            timestamp_format = self.timestamp_format.replace(self.WEEKDAY_CODE,
                                                             diary.iso_to_weekday(iso_timestamp, relative=False))
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
