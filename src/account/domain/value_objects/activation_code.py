"""
Activation code value object for account activation workflow.

This module defines the ActivationCode value object that encapsulates
a 4-digit numeric code used for account activation. The code provides
validation logic and random generation capabilities.
"""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationCode:
    """
    Value object representing a 4-digit activation code.

    Activation codes are immutable and validated at construction time.
    They consist of exactly 4 numeric digits (0000-9999).

    Attributes:
        code: 4-digit numeric string (e.g., "1234", "0042")

    Class Attributes:
        CODE_LENGTH: Number of digits in activation code (default: 4)

    Example:
        # Generate random code
        code = ActivationCode.generate()

        # Create specific code
        code = ActivationCode("1234")

        # Validate user input
        if code.matches("1234"):
            print("Code is valid!")

    Raises:
        ValueError: If code is not exactly 4 numeric digits
    """

    code: str

    CODE_LENGTH: int = 4

    def __post_init__(self) -> None:
        """
        Validate activation code format after initialization.

        Raises:
            ValueError: If code is not exactly 4 numeric digits
        """
        if not isinstance(self.code, str):
            raise ValueError("Activation code must be a string")

        if len(self.code) != self.CODE_LENGTH:
            raise ValueError(f"Activation code must be exactly {self.CODE_LENGTH} digits")

        if not self.code.isdigit():
            raise ValueError("Activation code must contain only numeric digits")

    @staticmethod
    def generate() -> "ActivationCode":
        """
        Generate a random 4-digit activation code.

        Returns:
            ActivationCode: New instance with random code (0000-9999)

        Example:
            code = ActivationCode.generate()
            # code.code might be "0042", "1234", "9876", etc.
        """
        random_code = str(random.randint(0, 9999)).zfill(ActivationCode.CODE_LENGTH)
        return ActivationCode(random_code)

    def matches(self, input_code: str) -> bool:
        """
        Check if input code matches this activation code.

        Args:
            input_code: User-provided code to validate

        Returns:
            bool: True if input matches, False otherwise

        Example:
            code = ActivationCode("1234")
            code.matches("1234")  # True
            code.matches("0000")  # False
        """
        return self.code == input_code
