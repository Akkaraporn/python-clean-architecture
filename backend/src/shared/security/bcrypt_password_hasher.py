import bcrypt

from src.usecases.ports import PasswordHasher

# bcrypt only looks at the first 72 bytes; bcrypt>=5 raises instead of silently truncating.
MAX_PASSWORD_BYTES = 72


class BcryptPasswordHasher(PasswordHasher):
    def __init__(self, rounds: int = 12) -> None:
        # Each extra round doubles the cost; tests lower it to stay fast.
        self._rounds = rounds

    def hash(self, password: str) -> str:
        encoded = password.encode("utf-8")
        if len(encoded) > MAX_PASSWORD_BYTES:
            raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
        return bcrypt.hashpw(encoded, bcrypt.gensalt(self._rounds)).decode("ascii")

    def verify(self, password: str, hashed_password: str) -> bool:
        encoded = password.encode("utf-8")
        if len(encoded) > MAX_PASSWORD_BYTES:
            return False
        try:
            return bcrypt.checkpw(encoded, hashed_password.encode("ascii"))
        except ValueError:
            # Malformed or non-bcrypt hash stored for this user.
            return False
