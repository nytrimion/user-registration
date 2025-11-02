import pytest

from src.account.domain.value_objects.password import Password

BCRYPT_HASH_PREFIX = "$2b$"


def test_password_from_plain_text_creates_hash() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    assert password.hashed_value.startswith(BCRYPT_HASH_PREFIX)
    assert password.hashed_value != "MySecurePassword123"


def test_password_from_plain_text_rejects_empty() -> None:
    with pytest.raises(ValueError, match="Password cannot be empty"):
        Password.from_plain_text("")


def test_password_from_plain_text_rejects_too_short() -> None:
    with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
        Password.from_plain_text("short")


def test_password_from_plain_text_accepts_minimum_length() -> None:
    password = Password.from_plain_text("Valid123")

    assert password.hashed_value.startswith(BCRYPT_HASH_PREFIX)


def test_password_verify_returns_true_for_correct_password() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    assert password.verify("MySecurePassword123") is True


def test_password_verify_returns_false_for_incorrect_password() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    assert password.verify("WrongPassword") is False


def test_password_verify_is_case_sensitive() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    assert password.verify("mysecurepassword123") is False


def test_password_from_hash_creates_password_from_existing_hash() -> None:
    """Test creating Password with existing hash from persistence layer."""
    original_password = Password.from_plain_text("MySecurePassword123")
    stored_hash = original_password.hashed_value

    restored_password = Password.from_hash(stored_hash)

    assert restored_password.hashed_value == stored_hash
    assert restored_password.verify("MySecurePassword123") is True


def test_password_from_hash_rejects_empty() -> None:
    with pytest.raises(ValueError, match="Hashed password cannot be empty"):
        Password.from_hash("")


def test_password_different_instances_have_different_hashes() -> None:
    """Test that 2 instances from same plain text have different hashes with random salt."""
    password1 = Password.from_plain_text("MySecurePassword123")
    password2 = Password.from_plain_text("MySecurePassword123")

    assert password1.hashed_value != password2.hashed_value
    assert password1.verify("MySecurePassword123") is True
    assert password2.verify("MySecurePassword123") is True


def test_password_str_representation_is_masked() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    assert str(password) == "********"


def test_password_repr_representation_is_masked() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    assert repr(password) == "Password(hashed_value='***')"


def test_password_is_immutable() -> None:
    password = Password.from_plain_text("MySecurePassword123")

    with pytest.raises(AttributeError):
        password.hashed_value = "hacked"  # type: ignore[misc]
