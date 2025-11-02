from uuid import UUID

import pytest

from src.account.domain.value_objects.account_id import AccountId


def test_account_id_generate_creates_uuid_v7() -> None:
    account_id = AccountId.generate()

    assert isinstance(account_id.value, UUID)
    assert account_id.value.version == 7


def test_account_id_generate_creates_unique_ids() -> None:
    account_id1 = AccountId.generate()
    account_id2 = AccountId.generate()

    assert account_id1.value != account_id2.value


def test_account_id_from_string_parses_valid_uuid_v7() -> None:
    generated = AccountId.generate()
    uuid_string = str(generated.value)

    account_id = AccountId.from_string(uuid_string)

    assert str(account_id.value) == uuid_string
    assert account_id.value.version == 7


def test_account_id_from_string_accepts_uuid_without_hyphens() -> None:
    generated = AccountId.generate()
    uuid_no_hyphens = str(generated.value).replace("-", "")

    account_id = AccountId.from_string(uuid_no_hyphens)

    assert isinstance(account_id.value, UUID)
    assert account_id.value.version == 7


def test_account_id_from_string_rejects_empty() -> None:
    with pytest.raises(ValueError, match="AccountId cannot be empty"):
        AccountId.from_string("")


def test_account_id_from_string_rejects_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid UUID format"):
        AccountId.from_string("not-a-uuid")


def test_account_id_from_string_rejects_non_v7_uuid() -> None:
    uuid_v4_string = "550e8400-e29b-41d4-a716-446655440000"

    with pytest.raises(ValueError, match="UUID must be version 7"):
        AccountId.from_string(uuid_v4_string)


def test_account_id_equality_by_value() -> None:
    generated = AccountId.generate()
    uuid_string = str(generated.value)

    account_id1 = AccountId.from_string(uuid_string)
    account_id2 = AccountId.from_string(uuid_string)

    assert account_id1 == account_id2


def test_account_id_inequality_for_different_uuids() -> None:
    account_id1 = AccountId.generate()
    account_id2 = AccountId.generate()

    assert account_id1 != account_id2


def test_account_id_str_representation() -> None:
    account_id = AccountId.generate()
    uuid_string = str(account_id)

    # UUID v7 format: 8-4-4-4-12 characters
    assert len(uuid_string) == 36
    assert uuid_string.count("-") == 4


def test_account_id_repr_representation() -> None:
    account_id = AccountId.generate()
    repr_string = repr(account_id)

    assert "AccountId" in repr_string
    assert "value=" in repr_string


def test_account_id_is_immutable() -> None:
    account_id = AccountId.generate()

    with pytest.raises(AttributeError):
        account_id.value = UUID("019a463c-ba8b-7325-b61e-8e12dc8f0c7e")  # type: ignore[misc]


def test_account_id_round_trip_string_conversion() -> None:
    original_id = AccountId.generate()
    uuid_string = str(original_id)

    restored_id = AccountId.from_string(uuid_string)

    assert restored_id == original_id
    assert restored_id.value == original_id.value
