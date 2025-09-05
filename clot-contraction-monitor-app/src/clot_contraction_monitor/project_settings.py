from dataclasses import dataclass, field
from typing import List


@dataclass
class ProjectSettings:
    """Configuration settings for a clot contraction monitoring project.

    This class encapsulates all the necessary parameters for a monitoring experiment,
    including experiment metadata, well configuration, and sampling parameters.
    """

    experiment_name: str
    group_names: List[str]
    wells_count: int = 40
    sampling_rate_seconds: float = 1.0  # Sampling interval in seconds
    description: str = ""
    created_date: str = field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )

    def __post_init__(self):
        """Validate the settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Perform internal validation of settings."""
        if not self.experiment_name.strip():
            raise ValueError("Experiment name cannot be empty")

        if self.wells_count <= 0:
            raise ValueError("Wells count must be positive")

        if self.sampling_rate_seconds <= 0:
            raise ValueError("Sampling rate must be positive")

        if len(self.group_names) == 0:
            raise ValueError("At least one group name must be specified")

        # Check for duplicate group names
        if len(self.group_names) != len(set(self.group_names)):
            raise ValueError("Group names must be unique")

        # Ensure group names are not empty
        for name in self.group_names:
            if not name.strip():
                raise ValueError("Group names cannot be empty")
