"""Settings validation module for project configuration."""

import json
from typing import Any, Dict, List

from .project_settings import ProjectSettings


class SettingsValidationError(Exception):
    """Base exception for settings validation errors."""

    pass


class ExperimentNameError(SettingsValidationError):
    """Exception raised for invalid experiment name."""

    pass


class WellsCountError(SettingsValidationError):
    """Exception raised for invalid wells count."""

    pass


class SamplingRateError(SettingsValidationError):
    """Exception raised for invalid sampling rate."""

    pass


class GroupNamesError(SettingsValidationError):
    """Exception raised for invalid group names."""

    pass


class SettingsValidator:
    """Validator class for project settings with detailed error handling."""

    @staticmethod
    def validate_experiment_name(name: str) -> None:
        """Validate experiment name.

        Args:
            name: The experiment name to validate

        Raises:
            ExperimentNameError: If the experiment name is invalid
        """
        if not isinstance(name, str):
            raise ExperimentNameError("Experiment name must be a string")

        name = name.strip()
        if not name:
            raise ExperimentNameError("Experiment name cannot be empty")

        if len(name) > 100:
            raise ExperimentNameError("Experiment name cannot exceed 100 characters")

        # Check for invalid characters
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in invalid_chars:
            if char in name:
                raise ExperimentNameError(
                    f"Experiment name contains invalid character: {char}"
                )

    @staticmethod
    def validate_wells_count(count: int) -> None:
        """Validate wells count.

        Args:
            count: The number of wells to validate

        Raises:
            WellsCountError: If the wells count is invalid
        """
        if not isinstance(count, int):
            raise WellsCountError("Wells count must be an integer")

        if count <= 0:
            raise WellsCountError("Wells count must be positive")

        if count > 200:  # Reasonable upper limit
            raise WellsCountError("Wells count cannot exceed 200")

    @staticmethod
    def validate_sampling_rate(rate: float) -> None:
        """Validate sampling rate in seconds.

        Args:
            rate: The sampling rate in seconds to validate

        Raises:
            SamplingRateError: If the sampling rate is invalid
        """
        if not isinstance(rate, (int, float)):
            raise SamplingRateError("Sampling rate must be a number")

        if rate <= 0:
            raise SamplingRateError("Sampling rate must be positive")

        if rate > 3600:  # 1 hour maximum interval
            raise SamplingRateError("Sampling rate cannot exceed 3600 seconds (1 hour)")

    @staticmethod
    def validate_group_names(names: List[str]) -> None:
        """Validate group names list.

        Args:
            names: The list of group names to validate

        Raises:
            GroupNamesError: If the group names are invalid
        """
        if not isinstance(names, list):
            raise GroupNamesError("Group names must be a list")

        if len(names) == 0:
            raise GroupNamesError("At least one group name must be specified")

        if len(names) > 50:  # Reasonable upper limit for groups
            raise GroupNamesError("Cannot have more than 50 groups")

        seen_names = set()
        for i, name in enumerate(names):
            if not isinstance(name, str):
                raise GroupNamesError(f"Group name at index {i} must be a string")

            name = name.strip()
            if not name:
                raise GroupNamesError(f"Group name at index {i} cannot be empty")

            if len(name) > 50:
                raise GroupNamesError(
                    f"Group name at index {i} cannot exceed 50 characters"
                )

            if name in seen_names:
                raise GroupNamesError(f"Duplicate group name: {name}")

            seen_names.add(name)

    @staticmethod
    def validate_settings_dict(settings_dict: Dict[str, Any]) -> None:
        """Validate a settings dictionary before creating ProjectSettings.

        Args:
            settings_dict: Dictionary containing project settings

        Raises:
            SettingsValidationError: If any setting is invalid
        """
        required_fields = [
            "experiment_name",
            "group_names",
            "wells_count",
            "sampling_rate_seconds",
        ]

        for field in required_fields:
            if field not in settings_dict:
                raise SettingsValidationError(f"Missing required field: {field}")

        SettingsValidator.validate_experiment_name(settings_dict["experiment_name"])
        SettingsValidator.validate_group_names(settings_dict["group_names"])
        SettingsValidator.validate_wells_count(settings_dict["wells_count"])
        SettingsValidator.validate_sampling_rate(settings_dict["sampling_rate_seconds"])

        # Validate optional fields
        if "description" in settings_dict:
            if not isinstance(settings_dict["description"], str):
                raise SettingsValidationError("Description must be a string")

    @staticmethod
    def validate_json_schema(json_str: str) -> Dict[str, Any]:
        """Validate JSON structure and return parsed dictionary.

        Args:
            json_str: JSON string to validate

        Returns:
            Parsed dictionary from JSON

        Raises:
            SettingsValidationError: If JSON is invalid or schema doesn't match
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise SettingsValidationError(f"Invalid JSON format: {e}")

        if not isinstance(data, dict):
            raise SettingsValidationError("Settings JSON must be an object")

        SettingsValidator.validate_settings_dict(data)
        return data

    @classmethod
    def validate_project_settings(cls, settings: ProjectSettings) -> None:
        """Validate a ProjectSettings instance.

        Args:
            settings: The ProjectSettings instance to validate

        Raises:
            SettingsValidationError: If any setting is invalid
        """
        cls.validate_experiment_name(settings.experiment_name)
        cls.validate_group_names(settings.group_names)
        cls.validate_wells_count(settings.wells_count)
        cls.validate_sampling_rate(settings.sampling_rate_seconds)
