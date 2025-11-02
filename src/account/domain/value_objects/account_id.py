from dataclasses import dataclass

from src.shared.domain.value_objects.uuid_v7 import UuidV7


@dataclass(frozen=True)
class AccountId(UuidV7):
    pass
