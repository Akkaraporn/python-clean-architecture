from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def normalize_email(email: str) -> str:
    # Email addresses are treated as case-insensitive so "A@x.com" and "a@x.com"
    # cannot become two separate accounts.
    return email.strip().lower()


@dataclass(eq=False, slots=True)
class User:
    id: UUID
    email: str
    hashed_password: str = field(repr=False)
    full_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.email = normalize_email(self.email)
        self.full_name = self.full_name.strip()

    @classmethod
    def create(cls, *, email: str, hashed_password: str, full_name: str) -> "User":
        # The id is generated here rather than by the database so an entity is
        # complete before it is persisted and needs no round trip to get its identity.
        return cls(id=uuid4(), email=email, hashed_password=hashed_password, full_name=full_name)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    # An entity is identified by its id, not by its current attribute values.
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
