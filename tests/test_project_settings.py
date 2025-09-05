"""Unit tests for project settings functionality."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clot_contraction_monitor.project_settings import ProjectSettings
from clot_contraction_monitor.settings_persistence import (
    SettingsPersistence,
    SettingsPersistenceError,
)
from clot_contraction_monitor.settings_validator import (
    ExperimentNameError,
    GroupNamesError,
    SamplingRateError,
    SettingsValidationError,
    SettingsValidator,
    WellsCountError,
)


class TestProjectSettings(unittest.TestCase):
    """Test cases for ProjectSettings dataclass."""

    def test_valid_project_settings(self):
        """Test creating valid project settings."""
        settings = ProjectSettings(
            experiment_name="Test Experiment",
            group_names=["Control", "Treatment"],
            wells_count=40,
            sampling_rate_seconds=1.0,
            description="Test description",
        )

        self.assertEqual(settings.experiment_name, "Test Experiment")
        self.assertEqual(settings.group_names, ["Control", "Treatment"])
        self.assertEqual(settings.wells_count, 40)
        self.assertEqual(settings.sampling_rate_seconds, 1.0)
        self.assertEqual(settings.description, "Test description")

    def test_validation_empty_experiment_name(self):
        """Test validation fails for empty experiment name."""
        with self.assertRaises(ValueError):
            ProjectSettings(experiment_name="", group_names=["Control"], wells_count=40)

    def test_validation_empty_group_names(self):
        """Test validation fails for empty group names list."""
        with self.assertRaises(ValueError):
            ProjectSettings(experiment_name="Test", group_names=[], wells_count=40)

    def test_validation_duplicate_group_names(self):
        """Test validation fails for duplicate group names."""
        with self.assertRaises(ValueError):
            ProjectSettings(
                experiment_name="Test",
                group_names=["Control", "Control"],
                wells_count=40,
            )

    def test_validation_invalid_wells_count(self):
        """Test validation fails for invalid wells count."""
        with self.assertRaises(ValueError):
            ProjectSettings(
                experiment_name="Test", group_names=["Control"], wells_count=-1
            )

    def test_validation_invalid_sampling_rate(self):
        """Test validation fails for invalid sampling rate."""
        with self.assertRaises(ValueError):
            ProjectSettings(
                experiment_name="Test",
                group_names=["Control"],
                wells_count=40,
                sampling_rate_seconds=-1.0,
            )


class TestSettingsValidator(unittest.TestCase):
    """Test cases for SettingsValidator."""

    def test_validate_experiment_name_valid(self):
        """Test validating a valid experiment name."""
        SettingsValidator.validate_experiment_name("Valid Experiment Name 123")
        # Should not raise exception

    def test_validate_experiment_name_empty(self):
        """Test validating an empty experiment name."""
        with self.assertRaises(ExperimentNameError):
            SettingsValidator.validate_experiment_name("")

    def test_validate_experiment_name_too_long(self):
        """Test validating an experiment name that's too long."""
        long_name = "A" * 101
        with self.assertRaises(ExperimentNameError):
            SettingsValidator.validate_experiment_name(long_name)

    def test_validate_experiment_name_invalid_chars(self):
        """Test validating experiment name with invalid characters."""
        with self.assertRaises(ExperimentNameError):
            SettingsValidator.validate_experiment_name("Test<File")

    def test_validate_wells_count_valid(self):
        """Test validating a valid wells count."""
        SettingsValidator.validate_wells_count(40)
        SettingsValidator.validate_wells_count(1)
        SettingsValidator.validate_wells_count(200)

    def test_validate_wells_count_invalid(self):
        """Test validating invalid wells counts."""
        with self.assertRaises(WellsCountError):
            SettingsValidator.validate_wells_count(-1)

        with self.assertRaises(WellsCountError):
            SettingsValidator.validate_wells_count(201)

        with self.assertRaises(WellsCountError):
            SettingsValidator.validate_wells_count(3.5)  # Non-integer

    def test_validate_sampling_rate_valid(self):
        """Test validating valid sampling rates."""
        SettingsValidator.validate_sampling_rate(0.5)
        SettingsValidator.validate_sampling_rate(1.0)
        SettingsValidator.validate_sampling_rate(3600.0)

    def test_validate_sampling_rate_invalid(self):
        """Test validating invalid sampling rates."""
        with self.assertRaises(SamplingRateError):
            SettingsValidator.validate_sampling_rate(-1.0)

        with self.assertRaises(SamplingRateError):
            SettingsValidator.validate_sampling_rate(3601.0)

        with self.assertRaises(SamplingRateError):
            SettingsValidator.validate_sampling_rate("invalid")  # Non-numeric

    def test_validate_group_names_valid(self):
        """Test validating valid group names."""
        SettingsValidator.validate_group_names(["Control", "Treatment", "Group 3"])
        SettingsValidator.validate_group_names(["A"])

    def test_validate_group_names_invalid(self):
        """Test validating invalid group names."""
        with self.assertRaises(GroupNamesError):
            SettingsValidator.validate_group_names([])  # Empty list

        with self.assertRaises(GroupNamesError):
            SettingsValidator.validate_group_names(["", "Valid"])  # Empty name

        with self.assertRaises(GroupNamesError):
            SettingsValidator.validate_group_names(["Same", "Same"])  # Duplicates

        with self.assertRaises(GroupNamesError):
            SettingsValidator.validate_group_names(["A"] * 51)  # Too many groups


class TestSettingsPersistence(unittest.TestCase):
    """Test cases for SettingsPersistence."""

    def setUp(self):
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_save_and_load_settings(self):
        """Test saving and loading settings from JSON."""
        settings = ProjectSettings(
            experiment_name="Test Experiment",
            group_names=["Control", "Treatment"],
            wells_count=48,
            sampling_rate_seconds=2.0,
            description="Test description",
        )

        # Save settings
        result = SettingsPersistence.save_settings_to_json(settings, self.temp_dir)
        self.assertTrue(result)

        # Check file exists
        settings_file = Path(self.temp_dir) / "settings.json"
        self.assertTrue(settings_file.exists())

        # Load settings
        loaded_settings = SettingsPersistence.load_settings_from_json(self.temp_dir)
        self.assertIsNotNone(loaded_settings)
        self.assertEqual(loaded_settings.experiment_name, "Test Experiment")
        self.assertEqual(loaded_settings.group_names, ["Control", "Treatment"])
        self.assertEqual(loaded_settings.wells_count, 48)
        self.assertEqual(loaded_settings.sampling_rate_seconds, 2.0)
        self.assertEqual(loaded_settings.description, "Test description")

    def test_load_nonexistent_settings(self):
        """Test loading settings when file doesn't exist."""
        loaded_settings = SettingsPersistence.load_settings_from_json(self.temp_dir)
        self.assertIsNone(loaded_settings)

    def test_save_invalid_settings(self):
        """Test saving invalid settings raises error."""
        # Create invalid settings by bypassing constructor validation (for testing)
        settings_dict = {
            "experiment_name": "",  # Invalid
            "group_names": ["Control"],
            "wells_count": 40,
            "sampling_rate_seconds": 1.0,
            "description": "",
            "created_date": "2025-01-01T00:00:00",
        }

        # Save directly via dict (bypassing ProjectSettings validation)
        with self.assertRaises(SettingsPersistenceError):
            SettingsPersistence.save_settings_to_json(settings_dict, self.temp_dir)

    def test_load_invalid_json(self):
        """Test loading invalid JSON."""
        settings_file = Path(self.temp_dir) / "settings.json"
        settings_file.write_text("invalid json content")

        with self.assertRaises(SettingsPersistenceError):
            SettingsPersistence.load_settings_from_json(self.temp_dir)

    def test_settings_file_exists(self):
        """Test checking if settings file exists."""
        # File doesn't exist
        self.assertFalse(SettingsPersistence.settings_file_exists(self.temp_dir))

        # Create file
        settings_file = Path(self.temp_dir) / "settings.json"
        settings_file.write_text("{}")

        # File exists
        self.assertTrue(SettingsPersistence.settings_file_exists(self.temp_dir))


if __name__ == "__main__":
    unittest.main()
