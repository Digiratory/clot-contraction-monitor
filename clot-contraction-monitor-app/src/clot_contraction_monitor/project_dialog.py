"""Project creation dialog for configuring experiment settings."""

import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, Optional

from .project_settings import ProjectSettings
from .settings_persistence import SettingsPersistence, SettingsPersistenceError
from .settings_validator import (
    ExperimentNameError,
    GroupNamesError,
    SamplingRateError,
    SettingsValidationError,
    SettingsValidator,
    WellsCountError,
)


class ProjectDialog(tk.Toplevel):
    """Modal dialog for creating or importing project settings.

    This dialog appears after folder selection and blocks execution until
    the user configures project settings or selects an existing configuration.
    """

    def __init__(
        self,
        parent: tk.Tk,
        folder_path: str,
        callback: Callable[[ProjectSettings], None],
    ):
        """Initialize the project dialog.

        Args:
            parent: Parent Tkinter window
            folder_path: Path to the selected folder
            callback: Function to call with configured settings
        """
        super().__init__(parent)
        self.parent = parent
        self.folder_path = folder_path
        self.callback = callback
        self.result_settings: Optional[ProjectSettings] = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Configure window
        self.title("Configure Project Settings")
        self.geometry("500x600")
        self.resizable(False, False)

        # Center the dialog
        self.center_window()

        # Initialize variables
        self.experiment_name_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.wells_count_var = tk.StringVar(value="40")
        self.sampling_rate_var = tk.StringVar(value="1.0")
        self.group_names_text = tk.Text(self, height=3, width=40)

        # Build UI
        self._create_widgets()
        self._load_existing_settings()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Wait for user input
        self.wait_window(self)

    def center_window(self) -> None:
        """Center the dialog on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and layout the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Project Configuration", font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.pack(fill="x", pady=(0, 15))

        # Radio buttons for option selection
        self.option_var = tk.StringVar(value="new")
        ttk.Radiobutton(
            options_frame,
            text="Create new project settings",
            variable=self.option_var,
            value="new",
            command=self._on_option_changed,
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            options_frame,
            text="Import existing settings template",
            variable=self.option_var,
            value="import",
            command=self._on_option_changed,
        ).pack(anchor="w", pady=2)

        # Input frame for new project settings
        self.input_frame = ttk.LabelFrame(
            main_frame, text="New Project Settings", padding="10"
        )
        self.input_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Create a scrollable frame for form inputs
        form_canvas = tk.Canvas(self.input_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.input_frame, orient="vertical", command=form_canvas.yview
        )
        scrollable_frame = ttk.Frame(form_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all")),
        )
        form_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        form_canvas.configure(yscrollcommand=scrollbar.set)

        form_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Experiment name
        name_frame = ttk.Frame(scrollable_frame)
        name_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(name_frame, text="Experiment Name:").pack(anchor="w")
        name_entry = ttk.Entry(name_frame, textvariable=self.experiment_name_var)
        name_entry.pack(fill="x", pady=(2, 0))

        # Description
        desc_frame = ttk.Frame(scrollable_frame)
        desc_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(desc_frame, text="Description:").pack(anchor="w")
        desc_entry = ttk.Entry(desc_frame, textvariable=self.description_var)
        desc_entry.pack(fill="x", pady=(2, 0))

        # Wells count
        wells_frame = ttk.Frame(scrollable_frame)
        wells_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(wells_frame, text="Wells Count:").pack(anchor="w")
        wells_entry = ttk.Entry(wells_frame, textvariable=self.wells_count_var)
        wells_entry.pack(fill="x", pady=(2, 0))

        # Sampling rate
        rate_frame = ttk.Frame(scrollable_frame)
        rate_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(rate_frame, text="Sampling Rate (seconds):").pack(anchor="w")
        rate_entry = ttk.Entry(rate_frame, textvariable=self.sampling_rate_var)
        rate_entry.pack(fill="x", pady=(2, 0))

        # Group names
        groups_frame = ttk.Frame(scrollable_frame)
        groups_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(groups_frame, text="Group Names (one per line):").pack(anchor="w")
        self.group_names_text = tk.Text(groups_frame, height=4)
        self.group_names_text.pack(fill="x", pady=(2, 0))

        name_entry.focus()  # Set initial focus

        # Template import frame (initially hidden)
        self.template_frame = ttk.LabelFrame(
            main_frame, text="Import Template", padding="10"
        )
        self.template_frame.pack_forget()  # Initially hidden

        ttk.Label(self.template_frame, text="Select a settings template file:").pack(
            anchor="w"
        )
        template_frame = ttk.Frame(self.template_frame)
        template_frame.pack(fill="x", pady=(5, 0))

        self.template_path_var = tk.StringVar()
        template_entry = ttk.Entry(template_frame, textvariable=self.template_path_var)
        template_entry.pack(side="left", fill="x", expand=True)

        browse_button = ttk.Button(
            template_frame, text="Browse...", command=self._browse_template
        )
        browse_button.pack(side="right", padx=(5, 0))

        # Error message label
        self.error_label = ttk.Label(main_frame, text="", foreground="red")
        self.error_label.pack(pady=(5, 0))

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(buttons_frame, text="Cancel", command=self._on_cancel).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(buttons_frame, text="OK", command=self._on_ok).pack(side="right")

        # Bind validation
        self._bind_validation()

    def _bind_validation(self) -> None:
        """Bind validation to input fields."""
        self.experiment_name_var.trace_add(
            "write", lambda *args: self._validate_input()
        )
        self.wells_count_var.trace_add("write", lambda *args: self._validate_input())
        self.sampling_rate_var.trace_add("write", lambda *args: self._validate_input())
        self.group_names_text.bind("<KeyRelease>", lambda *args: self._validate_input())

    def _validate_input(self) -> bool:
        """Validate current input values and update error message.

        Returns:
            True if all inputs are valid, False otherwise
        """
        try:
            # Get current values
            experiment_name = self.experiment_name_var.get().strip()
            wells_count_str = self.wells_count_var.get().strip()
            sampling_rate_str = self.sampling_rate_var.get().strip()
            group_names_text = self.group_names_text.get("1.0", "end-1c").strip()

            # Parse and validate
            if self.option_var.get() == "new":
                if not experiment_name:
                    raise ExperimentNameError("Experiment name is required")

                if experiment_name:
                    SettingsValidator.validate_experiment_name(experiment_name)

                if wells_count_str:
                    try:
                        wells_count = int(wells_count_str)
                        SettingsValidator.validate_wells_count(wells_count)
                    except ValueError:
                        raise WellsCountError("Wells count must be a number")

                if sampling_rate_str:
                    try:
                        sampling_rate = float(sampling_rate_str)
                        SettingsValidator.validate_sampling_rate(sampling_rate)
                    except ValueError:
                        raise SamplingRateError("Sampling rate must be a number")

                if group_names_text:
                    group_names = [
                        name.strip()
                        for name in group_names_text.split("\n")
                        if name.strip()
                    ]
                    SettingsValidator.validate_group_names(group_names)

            self.error_label.config(text="")
            return True

        except (
            ExperimentNameError,
            WellsCountError,
            SamplingRateError,
            GroupNamesError,
        ) as e:
            self.error_label.config(text=str(e))
            return False

    def _on_option_changed(self) -> None:
        """Handle option selection change between new/import."""
        if self.option_var.get() == "new":
            self.template_frame.pack_forget()
            self.input_frame.pack(fill="both", expand=True, pady=(0, 15))
        else:
            self.input_frame.pack_forget()
            self.template_frame.pack(fill="x", pady=(0, 15))

        self._validate_input()

    def _browse_template(self) -> None:
        """Open file dialog to select a settings template."""
        filename = filedialog.askopenfilename(
            title="Select Settings Template",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filename:
            self.template_path_var.set(filename)
            self._validate_input()

    def _load_existing_settings(self) -> None:
        """Load existing settings if they exist in the folder."""
        try:
            existing_settings = SettingsPersistence.load_settings_from_json(
                self.folder_path
            )
            if existing_settings:
                # Pre-populate fields with existing settings
                self.experiment_name_var.set(existing_settings.experiment_name)
                self.description_var.set(existing_settings.description)
                self.wells_count_var.set(str(existing_settings.wells_count))
                self.sampling_rate_var.set(str(existing_settings.sampling_rate_seconds))

                # Set group names
                self.group_names_text.delete("1.0", "end")
                for name in existing_settings.group_names:
                    self.group_names_text.insert("end", name + "\n")
                self.group_names_text.delete("end-1c")  # Remove trailing newline

                messagebox.showinfo(
                    "Existing Settings Found",
                    "Existing settings were loaded. You can modify them as needed.",
                )

        except SettingsPersistenceError as e:
            messagebox.showwarning("Warning", f"Could not load existing settings: {e}")

    def _on_ok(self) -> None:
        """Handle OK button click."""
        if not self._validate_input():
            return

        try:
            if self.option_var.get() == "new":
                self._create_new_project()
            else:
                self._import_template()

            if self.result_settings:
                self._save_and_callback()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process settings: {e}")

    def _create_new_project(self) -> None:
        """Create project settings from user input."""
        experiment_name = self.experiment_name_var.get().strip()
        description = self.description_var.get().strip()
        wells_count = int(self.wells_count_var.get().strip())
        sampling_rate = float(self.sampling_rate_var.get().strip())

        group_names_text = self.group_names_text.get("1.0", "end-1c").strip()
        group_names = [
            name.strip() for name in group_names_text.split("\n") if name.strip()
        ]

        self.result_settings = ProjectSettings(
            experiment_name=experiment_name,
            group_names=group_names,
            wells_count=wells_count,
            sampling_rate_seconds=sampling_rate,
            description=description,
        )

    def _import_template(self) -> None:
        """Import settings from a template file."""
        template_path = self.template_path_var.get().strip()
        if not template_path:
            raise ValueError("Please select a template file")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)

            # Validate template data
            SettingsValidator.validate_settings_dict(template_data)

            # Create settings from template
            self.result_settings = ProjectSettings(
                experiment_name=template_data["experiment_name"],
                group_names=template_data["group_names"],
                wells_count=template_data["wells_count"],
                sampling_rate_seconds=template_data["sampling_rate_seconds"],
                description=template_data.get("description", ""),
                created_date=template_data.get("created_date", ""),
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in template file: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in template: {e}")

    def _save_and_callback(self) -> None:
        """Save settings and call the callback function."""
        try:
            SettingsPersistence.save_settings_to_json(
                self.result_settings, self.folder_path
            )
            self.callback(self.result_settings)
            self.destroy()
        except SettingsPersistenceError as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _on_cancel(self) -> None:
        """Handle dialog cancellation."""
        self.result_settings = None
        self.destroy()


def show_project_dialog(
    parent: tk.Tk, folder_path: str, callback: Callable[[ProjectSettings], None]
) -> ProjectDialog:
    """Convenience function to show the project dialog.

    Args:
        parent: Parent Tkinter window
        folder_path: Path to the selected folder
        callback: Function to call with configured settings

    Returns:
        The dialog instance
    """
    return ProjectDialog(parent, folder_path, callback)
