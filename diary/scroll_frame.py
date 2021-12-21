import tkinter as tk
import platform


class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent) # create a frame (self)

        # Place canvas with a nested frame on self, and a scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.view = tk.Frame(self.canvas, background="#ffffff")
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((4,4), window=self.view, anchor="nw", tags="self.view")

        # Bind resizing events
        self.view.bind("<Configure>", self.__on_frame_configure)
        self.canvas.bind("<Configure>", self.__on_canvas_configure)

        # Bind mouse scroll wheel when focus/cursor is in the 'view'
        self.view.bind('<Enter>', self.__on_enter)
        self.view.bind('<Leave>', self.__on_exit)

        self.__on_frame_configure(None)

    def __on_frame_configure(self, event):
        """Reset the scroll region based on the canvas' current bounds"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def __on_canvas_configure(self, event):
        """Ensure the window has the same width as the canvas"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def __on_mouse_wheel_scroll(self, event):
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1 * (event.delta/120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
    
    def __on_enter(self, event):
        """Bind mouse wheel scroll to scroll the canvas when the cursor enters the canvas"""
        if platform.system() == 'Linux':
            self.canvas.bind_all("<Button-4>", self.__on_mouse_wheel_scroll)
            self.canvas.bind_all("<Button-5>", self.__on_mouse_wheel_scroll)
        else:
            self.canvas.bind_all("<MouseWheel>", self.__on_mouse_wheel_scroll)

    def __on_exit(self, event):
        """Unbind mouse wheel scroll controls from the canvas when cursor leaves the canvas"""
        if platform.system() == 'Linux':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")
