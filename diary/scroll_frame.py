import tkinter as tk
import platform


class ScrollableFrame(tk.Frame):
    """A Frame which supports a vertical scrollbar to scroll its contents.

    Any widgets intended to be placed within this frame should have its 'view' as a parent.
    """

    def __init__(self, parent, background="#ffffff"):
        super().__init__(parent)

        # Place __canvas with a nested frame on self, and a _scrollbar
        self.__canvas = tk.Canvas(self, borderwidth=0, background=background)
        self.view = tk.Frame(self.__canvas, background=background)
        self._scrollbar = tk.Scrollbar(self, orient="vertical", command=self.__canvas.yview)
        self.__canvas.configure(yscrollcommand=self._scrollbar.set)

        self.__canvas.grid(row=0, column=0, sticky="NESW")
        self._scrollbar.grid(row=0, column=1, sticky="NS")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.__canvas_window = self.__canvas.create_window((0, 0), window=self.view, anchor="nw",
                                                           tags="self.view")

        # Bind resizing events
        self.view.bind("<Configure>", self.__on_frame_configure)
        self.__canvas.bind("<Configure>", self.__on_canvas_configure)

        # Bind mouse scroll wheel when focus/cursor is in the 'view'
        self.bind('<Enter>', self.__on_enter)
        self.bind('<Leave>', self.__on_exit)

        self.__platform = platform.system()

    def __on_frame_configure(self, event):
        """Reset the scroll region based on the __canvas' current bounds"""
        self.__canvas.configure(scrollregion=self.__canvas.bbox("all"))

    def __on_canvas_configure(self, event):
        """Ensure the window has the same width as the __canvas"""
        canvas_width = event.width
        self.__canvas.itemconfig(self.__canvas_window, width=canvas_width)

    def __on_scroll(self, event):
        """Perform scrolling of the view.
        """
        if self.__platform == 'Windows' or self.__platform == 'Darwin':
            scrolling_up = (event.delta > 0)
            scroll_amount = -int(event.delta/120) if self.__platform == 'Windows' else -event.delta
        else:
            scrolling_up = (event.num == 4)  # 4 = scroll-up, 5 = scroll-down
            scroll_amount = -1 if scrolling_up else 1

        # Extra conditions to avoid scrolling beyond content
        if scrolling_up and self.view.winfo_y() < 0 or \
                not scrolling_up and self.view.winfo_y() - self.view.winfo_height() < -self.__canvas.winfo_height():
            self.__canvas.yview_scroll(scroll_amount, "units")

    def scroll_to_start(self, *args):
        """Force the frame to scroll to the start of its content."""
        self.__canvas.yview_moveto(0.00)

    def scroll_to_end(self, *args):
        """Force the frame to scroll to the end of its content."""
        self.__canvas.yview_moveto(1.00)

    def __on_enter(self, event):
        """Bind mouse wheel scroll to scroll the canvas.
        """
        if self.__platform == 'Linux':
            self.__canvas.bind_all("<Button-4>", self.__on_scroll)
            self.__canvas.bind_all("<Button-5>", self.__on_scroll)
        else:
            self.__canvas.bind_all("<MouseWheel>", self.__on_scroll)

    def __on_exit(self, event):
        """Unbind mouse wheel scroll controls on the canvas when cursor leaves the canvas.
        """
        if self.__platform == 'Linux':
            self.__canvas.unbind_all("<Button-4>")
            self.__canvas.unbind_all("<Button-5>")
        else:
            self.__canvas.unbind_all("<MouseWheel>")
