import pytest

from src.account.domain.value_objects.email import Email


def test_email_creation_with_valid_email() -> None:
    email = Email("user@example.com")

    assert email.value == "user@example.com"


def test_email_normalizes_to_lowercase() -> None:
    email = Email("User@EXAMPLE.COM")

    assert email.value == "user@example.com"


def test_email_rejects_empty_string() -> None:
    with pytest.raises(ValueError, match="Email cannot be empty"):
        Email("")


def test_email_rejects_whitespace_only() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("   ")


def test_email_rejects_email_with_spaces() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("user @example.com")


def test_email_rejects_email_with_leading_space() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email(" user@example.com")


def test_email_rejects_email_with_trailing_space() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("user@example.com ")


def test_email_rejects_missing_at_symbol() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("userexample.com")


def test_email_rejects_missing_domain() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("user@")


def test_email_rejects_missing_local_part() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("@example.com")


def test_email_rejects_invalid_characters() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        Email("user name@example.com")


def test_email_equality_by_value() -> None:
    email1 = Email("user@example.com")
    email2 = Email("user@example.com")

    assert email1 == email2


def test_email_equality_case_insensitive() -> None:
    email1 = Email("User@Example.COM")
    email2 = Email("user@example.com")

    assert email1 == email2


def test_email_str_representation() -> None:
    email = Email("user@example.com")

    assert str(email) == "user@example.com"


def test_email_repr_representation() -> None:
    email = Email("user@example.com")

    assert repr(email) == "Email(value='user@example.com')"


def test_email_is_immutable() -> None:
    email = Email("user@example.com")

    with pytest.raises(AttributeError):
        email.value = "hacker@malicious.com"  # type: ignore[misc]
