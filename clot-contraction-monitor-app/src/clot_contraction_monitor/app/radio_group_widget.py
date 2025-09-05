import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional, Tuple


class RadioGroupWidget(ttk.LabelFrame):
    """A generic widget for creating radio button groups.

    Supports both vertical and horizontal layouts, with customizable options
    and callback handling.
    """

    def __init__(
        self,
        master,
        title: str,
        options: List[Tuple[str, str]],
        default_value: str = None,
        orientation: str = "vertical",
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """Initialize the radio group widget.

        Args:
            master: Parent widget
            title: Title for the LabelFrame
            options: List of (text, value) tuples for radio buttons
            default_value: Default selected value
            orientation: "vertical" or "horizontal"
            callback: Function to call when selection changes
            **kwargs: Additional arguments for LabelFrame
        """
        super().__init__(master, text=title, padding=5, **kwargs)

        # Variable to store selected value
        self.variable = tk.StringVar()

        # Set default value
        if default_value is None and options:
            default_value = options[0][1]
        self.variable.set(default_value)

        # Store callback
        self._callback = callback

        # Create radio buttons
        for text, value in options:
            rb = ttk.Radiobutton(
                self,
                text=text,
                variable=self.variable,
                value=value,
                command=self._on_selection_changed,
            )

            if orientation == "horizontal":
                rb.pack(side=tk.LEFT, padx=(0, 10))
            else:  # vertical
                rb.pack(anchor=tk.W)

    def _on_selection_changed(self):
        """Handle selection changes."""
        if self._callback:
            self._callback(self.variable.get())

    def get_value(self) -> str:
        """Get the current selected value.

        Returns:
            Current selected value
        """
        return self.variable.get()

    def set_value(self, value: str):
        """Set the selected value.

        Args:
            value: Value to select
        """
        self.variable.set(value)
