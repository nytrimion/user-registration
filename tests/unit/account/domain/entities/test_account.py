import pytest

from src.account.domain.entities.account import Account
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password


def test_account_create_generates_unique_id() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account = Account.create(email, password)

    assert isinstance(account.account_id, AccountId)


def test_account_create_sets_email_and_password() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account = Account.create(email, password)

    assert account.email == email
    assert account.password == password


def test_account_create_starts_as_not_activated() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account = Account.create(email, password)

    assert account.is_activated is False


def test_account_create_generates_different_ids_for_different_accounts() -> None:
    email1 = Email("user1@example.com")
    email2 = Email("user2@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account1 = Account.create(email1, password)
    account2 = Account.create(email2, password)

    assert account1.account_id != account2.account_id


def test_account_create_generates_different_ids_for_same_credentials() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account1 = Account.create(email, password)
    account2 = Account.create(email, password)

    assert account1.account_id != account2.account_id
    assert account1 != account2


def test_account_activate_changes_status_to_true() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    account.activate()

    assert account.is_activated is True


def test_account_activate_raises_if_already_activated() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)
    account.activate()

    with pytest.raises(ValueError, match="Account is already activated"):
        account.activate()


def test_account_equality_by_id() -> None:
    account_id = AccountId.generate()
    email1 = Email("user1@example.com")
    email2 = Email("user2@example.com")
    password1 = Password.from_plain_text("Password123")
    password2 = Password.from_plain_text("DifferentPass456")

    account1 = Account(account_id, email1, password1, False)
    account2 = Account(account_id, email2, password2, True)

    assert account1 == account2


def test_account_inequality_by_different_ids() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account1 = Account.create(email, password)
    account2 = Account.create(email, password)

    assert account1 != account2


def test_account_equality_with_non_account_type() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    assert account != "not an account"
    assert account != 123
    assert account != None  # noqa: E711
    assert (account == "not an account") is False


def test_account_hash_is_based_on_id() -> None:
    account_id = AccountId.generate()
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account1 = Account(account_id, email, password, False)
    account2 = Account(account_id, email, password, True)

    assert hash(account1) == hash(account2)


def test_account_can_be_used_in_set() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account1 = Account.create(email, password)
    account2 = Account.create(email, password)

    account_set = {account1, account2}

    assert len(account_set) == 2


def test_account_set_deduplication_by_id() -> None:
    account_id = AccountId.generate()
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    account = Account(account_id, email, password, False)

    account_set = {account, account}

    assert len(account_set) == 1


def test_account_repr_contains_key_attributes() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    repr_string = repr(account)

    assert "Account" in repr_string
    assert "account_id=" in repr_string
    assert "email=" in repr_string
    assert "is_activated=" in repr_string


def test_account_id_is_immutable() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    with pytest.raises(AttributeError, match="no setter"):
        account.account_id = AccountId.generate()  # type: ignore[misc]


def test_email_cannot_be_set_directly() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    with pytest.raises(AttributeError, match="no setter"):
        account.email = Email("newemail@example.com")  # type: ignore[misc]


def test_password_cannot_be_set_directly() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)
    new_password = Password.from_plain_text("NewPassword456")

    with pytest.raises(AttributeError, match="no setter"):
        account.password = new_password  # type: ignore[misc]


def test_is_activated_cannot_be_set_directly() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    with pytest.raises(AttributeError, match="no setter"):
        account.is_activated = True  # type: ignore[misc]


def test_activate_is_the_only_way_to_activate_account() -> None:
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    account = Account.create(email, password)

    assert account.is_activated is False

    account.activate()

    assert account.is_activated is True
