import datetime
import tkinter.ttk as ttk

import diary


class EntryFrame(diary.scroll_frame.ScrollableFrame):
    """Utility subclass which displays a list of messages alongside their timestamps."""

    WRAPPING_PADDING = 20

    def __init__(self, master, background=diary.BACKGROUND, timestamp_format="%H:%M", show_day=False, day_relative=False):
        super().__init__(master, background)

        self.timestamp_format = timestamp_format
        self.show_day = show_day
        self.day_relative = day_relative if show_day else False

        self.days = []
        self.timestamps = []
        self.entries = []
        self.count_entries = 0
        self.content_changed = False  # Flag used for programmatic scrolling - requires two updates

        # Add scaling to the content column only
        self.view.grid_columnconfigure(2, weight=1)

    def clear(self) -> None:
        """Clear the EntryFrame of messages.
        """

        [entry.destroy() for entry in self.entries]
        [timestamp.destroy() for timestamp in self.timestamps]
        [day.destroy() for day in self.days]

        self.days = []
        self.timestamps = []
        self.entries = []
        self.count_entries = 0
        self.content_changed = True

    def add_message(self, content: str, iso_timestamp: str, scroll_to_end=False) -> None:
        """Add a message with the given content and timestamp, and displays it at the end of the frame.

        By default also scrolls to the end so that the newly sent message is visible.
        """

        self.count_entries += 1
        self.view.rowconfigure(self.count_entries, weight=1)

        # Update 'day' field
        if self.show_day:
            day_label = ttk.Label(self.view, text=diary.iso_to_weekday(iso_timestamp, relative=self.day_relative))
            day_label.grid(row=self.count_entries, column=0, sticky="NW")
            self.days.append(day_label)

        # Add timestamp
        time = datetime.datetime.fromisoformat(iso_timestamp)
        timestamp_label = ttk.Label(self.view, text=time.strftime(self.timestamp_format))
        timestamp_label.grid(row=self.count_entries, column=1, sticky="NEW")
        self.timestamps.append(timestamp_label)

        # Add entry
        entry_label = ttk.Label(self.view, text=content)
        entry_label.grid(row=self.count_entries, column=2, sticky="NESW")
        self.entries.append(entry_label)

        self.content_changed = True
        if scroll_to_end:
            self.scroll_to_end()

    def scroll_to_end(self, *args):
        """Scroll to the end of the frame, such that the most recent messages are visible.
        """

        if self.content_changed:
            # Must scroll to the start first, otherwise if we start at a scroll position past the end,
            # behaviour will be incorrect
            super().scroll_to_start(*args)

            # Due to word wrapping we have to call update twice in a row to ensure we scroll to the very end.
            # I know, I know.
            # First update will render the frame's contents.
            self.update()
            # Second update will do any required wrapping of the now-present labels.
            self.update()
            # With content displayed and correctly wrapped, we can finally scroll to the end.
            self.content_changed = False
        super().scroll_to_end(*args)

    def update(self):
        """Update all labels so word wrapping is correct for current window width.
        """

        super().update()
        if self.master.winfo_exists() and self.entries:
            width = max(self.entries[0].winfo_width() - self.WRAPPING_PADDING, 0)
            for label in self.entries:
                label.configure(wraplength=width)
