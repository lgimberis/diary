import datetime

DEFAULT_CATEGORY = "Diary"
SCROLLBAR_WIDTH = 30  # Width of scrollbar in pixels, plus a little extra space.
TIMESTAMP_WIDTH = 40
BACKGROUND = "#f0f0f0"
DELETE_BUTTON_WIDTH = 20  # Width in pixels of the to-do list 'delete' button
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


import diary.scroll_frame as scroll_frame
import diary.entry_frame as entry_frame
import diary.date_selection_window as date_selection_window
import diary.diary_handler as diary_handler
__all__ = ["scroll_frame", "entry_frame", "date_selection_window", "diary_handler"]

