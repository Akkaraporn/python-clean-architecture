from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.entities import User
from src.domain.errors import UserAlreadyExistsError
from src.domain.repositories import UserRepository
from src.infrastructure.database.postgres.models import UserModel
from src.interface.repositories.postgres.user_mapper import to_entity, to_model

EMAIL_UNIQUE_INDEX = "ix_users_email"


class PostgresUserRepository(UserRepository):
    """SQLAlchemy adapter for the UserRepository port.

    It never commits: the caller that owns the session (one per HTTP request)
    decides to commit or roll back, so every write in a use case succeeds or
    fails together.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> User:
        model = to_model(user)
        try:
            # The savepoint confines a failed INSERT to itself, so the caller's
            # transaction stays usable after a duplicate-email error.
            with self._session.begin_nested():
                self._session.add(model)
                # flush sends the INSERT now, so the unique index is checked here
                # rather than at some later commit far from this call.
                self._session.flush()
        except IntegrityError as exc:
            if _violated_constraint(exc) == EMAIL_UNIQUE_INDEX:
                raise UserAlreadyExistsError(user.email) from exc
            raise
        return to_entity(model)

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return to_entity(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return to_entity(model) if model else None


def _violated_constraint(exc: IntegrityError) -> str | None:
    # psycopg exposes the server's diagnostic fields, including the constraint name.
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
