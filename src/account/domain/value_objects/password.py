from dataclasses import dataclass

import bcrypt


@dataclass(frozen=True)
class Password:
    """
    Password value object with hashing.

    Immutable representation of a hashed password.
    Plain text password is hashed immediately using bcrypt.

    Attributes:
        hashed_value: The bcrypt-hashed password (never stores plain text)

    Raises:
        ValueError: If password is invalid (too short, empty)
    """

    hashed_value: str

    @classmethod
    def from_plain_text(cls, plain_password: str) -> "Password":
        if not plain_password:
            raise ValueError("Password cannot be empty")

        if len(plain_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())

        return cls(hashed_value=hashed.decode("utf-8"))

    @classmethod
    def from_hash(cls, hashed_value: str) -> "Password":
        if not hashed_value:
            raise ValueError("Hashed password cannot be empty")

        return cls(hashed_value=hashed_value)

    def verify(self, plain_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), self.hashed_value.encode("utf-8"))

    def __str__(self) -> str:
        return "********"

    def __repr__(self) -> str:
        return "Password(hashed_value='***')"
