"""
Unit tests for ActivationCode value object.

Tests verify:
    - Random code generation produces valid 4-digit codes
    - Validation rejects invalid formats (length, non-numeric)
    - Immutability (frozen dataclass)
    - Code matching logic (matches() method)
"""

import pytest

from src.account.domain.value_objects.activation_code import ActivationCode


class TestActivationCode:
    """Test suite for ActivationCode value object."""

    def test_generate_produces_valid_4_digit_code(self) -> None:
        """Verify generate() produces a valid 4-digit numeric code."""
        # Act
        code = ActivationCode.generate()

        # Assert
        assert len(code.code) == ActivationCode.CODE_LENGTH
        assert code.code.isdigit()

    def test_generate_produces_different_codes(self) -> None:
        """Verify generate() produces different codes (randomness check)."""
        # Act: Generate multiple codes
        codes = [ActivationCode.generate().code for _ in range(100)]

        # Assert: At least 50 unique codes (statistical randomness)
        unique_codes = set(codes)
        assert len(unique_codes) >= 50

    def test_create_with_valid_4_digit_code(self) -> None:
        """Verify ActivationCode accepts valid 4-digit codes."""
        # Act
        code = ActivationCode("1234")

        # Assert
        assert code.code == "1234"

    def test_create_with_leading_zeros(self) -> None:
        """Verify ActivationCode accepts codes with leading zeros."""
        # Act
        code = ActivationCode("0042")

        # Assert
        assert code.code == "0042"

    def test_create_with_all_zeros(self) -> None:
        """Verify ActivationCode accepts code with all zeros."""
        # Act
        code = ActivationCode("0000")

        # Assert
        assert code.code == "0000"

    def test_create_with_less_than_4_digits_raises_error(self) -> None:
        """Verify ActivationCode rejects codes with less than 4 digits."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be exactly 4 digits"):
            ActivationCode("123")

    def test_create_with_more_than_4_digits_raises_error(self) -> None:
        """Verify ActivationCode rejects codes with more than 4 digits."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be exactly 4 digits"):
            ActivationCode("12345")

    def test_create_with_non_numeric_characters_raises_error(self) -> None:
        """Verify ActivationCode rejects codes with non-numeric characters."""
        # Act & Assert
        with pytest.raises(ValueError, match="must contain only numeric digits"):
            ActivationCode("12a4")

    def test_create_with_empty_string_raises_error(self) -> None:
        """Verify ActivationCode rejects empty string."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be exactly 4 digits"):
            ActivationCode("")

    def test_create_with_non_string_raises_error(self) -> None:
        """Verify ActivationCode rejects non-string types."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be a string"):
            ActivationCode(1234)  # type: ignore[arg-type]

    def test_activation_code_is_immutable(self) -> None:
        """Verify ActivationCode cannot be modified after creation."""
        # Arrange
        code = ActivationCode("1234")

        # Act & Assert
        with pytest.raises(AttributeError):
            code.code = "5678"  # type: ignore[misc]

    def test_matches_returns_true_for_correct_code(self) -> None:
        """Verify matches() returns True when input matches stored code."""
        # Arrange
        code = ActivationCode("1234")

        # Act & Assert
        assert code.matches("1234") is True

    def test_matches_returns_false_for_incorrect_code(self) -> None:
        """Verify matches() returns False when input does not match stored code."""
        # Arrange
        code = ActivationCode("1234")

        # Act & Assert
        assert code.matches("5678") is False

    def test_matches_is_exact_string_comparison(self) -> None:
        """Verify matches() performs exact string comparison (no normalization)."""
        # Arrange
        code = ActivationCode("0042")

        # Act & Assert
        assert code.matches("0042") is True
        assert code.matches("42") is False  # Missing leading zeros
        assert code.matches("00042") is False  # Extra digit
