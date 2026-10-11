from uuid import UUID


class DomainError(Exception):
    """Base class for business-rule violations; the web layer maps these to HTTP codes."""


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"A user with email '{email}' already exists")
        self.email = email


class InvalidCredentialsError(DomainError):
    # Deliberately does not say whether the email or the password was wrong,
    # so callers cannot use it to discover which emails are registered.
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InactiveUserError(DomainError):
    def __init__(self) -> None:
        super().__init__("User account is inactive")


class UserNotFoundError(DomainError):
    def __init__(self, user_id: UUID) -> None:
        super().__init__(f"User '{user_id}' was not found")
        self.user_id = user_id
