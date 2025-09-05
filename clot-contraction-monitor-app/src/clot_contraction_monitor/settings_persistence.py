"""Settings persistence module for JSON serialization/deserialization."""

import json
import os
from pathlib import Path
from typing import Optional

from .project_settings import ProjectSettings
from .settings_validator import (
    ExperimentNameError,
    GroupNamesError,
    SamplingRateError,
    SettingsValidationError,
    SettingsValidator,
    WellsCountError,
)


class SettingsPersistenceError(Exception):
    """Base exception for settings persistence errors."""

    pass


class SettingsPersistence:
    """Handles persistence of project settings to/from JSON files."""

    SETTINGS_FILENAME = "settings.json"

    @staticmethod
    def save_settings_to_json(settings: ProjectSettings, folder_path: str) -> bool:
        """Save project settings to a JSON file in the specified folder.

        Args:
            settings: The ProjectSettings instance to save
            folder_path: Path to the folder where settings will be saved

        Returns:
            True if successful, False otherwise

        Raises:
            SettingsPersistenceError: If saving fails
        """
        try:
            # Validate settings before saving
            SettingsValidator.validate_project_settings(settings)

            # Convert settings to dictionary
            settings_dict = {
                "experiment_name": settings.experiment_name,
                "group_names": settings.group_names,
                "wells_count": settings.wells_count,
                "sampling_rate_seconds": settings.sampling_rate_seconds,
                "description": settings.description,
                "created_date": settings.created_date,
            }

            # Ensure folder exists
            folder_path = Path(folder_path)
            folder_path.mkdir(parents=True, exist_ok=True)

            # Save to JSON file
            json_path = folder_path / SettingsPersistence.SETTINGS_FILENAME
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

            return True

        except SettingsValidationError as e:
            raise SettingsPersistenceError(f"Validation failed: {e}")
        except (IOError, OSError) as e:
            raise SettingsPersistenceError(f"Failed to save settings: {e}")
        except Exception as e:
            raise SettingsPersistenceError(f"Unexpected error while saving: {e}")

    @staticmethod
    def load_settings_from_json(folder_path: str) -> Optional[ProjectSettings]:
        """Load project settings from a JSON file in the specified folder.

        Args:
            folder_path: Path to the folder containing the settings file

        Returns:
            ProjectSettings instance if successful, None if file doesn't exist

        Raises:
            SettingsPersistenceError: If loading fails due to validation or I/O errors
        """
        json_path = Path(folder_path) / SettingsPersistence.SETTINGS_FILENAME

        if not json_path.exists():
            return None

        try:
            # Read and parse JSON
            with open(json_path, "r", encoding="utf-8") as f:
                json_content = f.read()

            # Validate JSON schema
            settings_dict = SettingsValidator.validate_json_schema(json_content)

            # Create ProjectSettings instance
            settings = ProjectSettings(
                experiment_name=settings_dict["experiment_name"],
                group_names=settings_dict["group_names"],
                wells_count=settings_dict["wells_count"],
                sampling_rate_seconds=settings_dict["sampling_rate_seconds"],
                description=settings_dict.get("description", ""),
                created_date=settings_dict.get("created_date", ""),
            )

            return settings

        except SettingsValidationError as e:
            raise SettingsPersistenceError(f"Settings validation failed: {e}")
        except json.JSONDecodeError as e:
            raise SettingsPersistenceError(f"Invalid JSON format: {e}")
        except (IOError, OSError) as e:
            raise SettingsPersistenceError(f"Failed to read settings file: {e}")
        except Exception as e:
            raise SettingsPersistenceError(f"Unexpected error while loading: {e}")

    @staticmethod
    def settings_file_exists(folder_path: str) -> bool:
        """Check if a settings file exists in the specified folder.

        Args:
            folder_path: Path to the folder to check

        Returns:
            True if settings file exists, False otherwise
        """
        json_path = Path(folder_path) / SettingsPersistence.SETTINGS_FILENAME
        return json_path.exists() and json_path.is_file()

    @staticmethod
    def validate_settings_file(folder_path: str) -> bool:
        """Validate that a settings file exists and is valid.

        Args:
            folder_path: Path to the folder containing the settings file

        Returns:
            True if the file exists and is valid, False otherwise
        """
        try:
            settings = SettingsPersistence.load_settings_from_json(folder_path)
            return settings is not None
        except SettingsPersistenceError:
            return False

    @staticmethod
    def migrate_legacy_settings(folder_path: str) -> Optional[ProjectSettings]:
        """Attempt to migrate legacy settings or create default settings.

        This method can be used for backward compatibility when upgrading
        from folders that don't have settings.json files.

        Args:
            folder_path: Path to the folder to migrate

        Returns:
            Default ProjectSettings instance, or None if migration fails
        """
        try:
            # For now, return None - we'll handle this in the dialog
            # This allows the dialog to prompt for settings creation
            return None
        except Exception as e:
            # Log the error but don't raise - we'll handle in dialog
            print(f"Warning: Could not migrate legacy settings: {e}")
            return None
