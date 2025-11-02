from abc import ABC
from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid7


@dataclass(frozen=True)
class UuidV7(ABC):
    """
    Abstract base class for UUID v7-based identifiers.

    Provides factory methods and validation for time-ordered UUIDs.
    All ID value objects should inherit from this class.

    Attributes:
        value: The UUID v7 identifier

    Raises:
        ValueError: If UUID is invalid or not version 7
    """

    value: UUID

    def __post_init__(self) -> None:
        if self.value.version != 7:
            raise ValueError(f"UUID must be version 7, got version {self.value.version}")

    @classmethod
    def generate(cls) -> Self:
        return cls(value=uuid7())

    @classmethod
    def from_string(cls, uuid_string: str) -> Self:
        if not uuid_string:
            raise ValueError(f"{cls.__name__} cannot be empty")

        try:
            uuid_value = UUID(uuid_string)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid UUID format: {uuid_string}") from e

        return cls(value=uuid_value)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r})"
