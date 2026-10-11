import pytest

from src.shared.security import BcryptPasswordHasher
from src.usecases.ports import PasswordHasher


@pytest.fixture
def hasher() -> PasswordHasher:
    # Minimum cost keeps the suite fast; production uses the default.
    return BcryptPasswordHasher(rounds=4)


def test_hash_is_not_the_plain_password(hasher: PasswordHasher) -> None:
    hashed = hasher.hash("correct horse")

    assert hashed != "correct horse"
    assert hashed.startswith("$2b$04$")


def test_verify_accepts_the_right_password(hasher: PasswordHasher) -> None:
    assert hasher.verify("correct horse", hasher.hash("correct horse"))


@pytest.mark.parametrize("attempt", ["wrong horse", "Correct horse", "correct horse ", ""])
def test_verify_rejects_a_wrong_password(hasher: PasswordHasher, attempt: str) -> None:
    assert not hasher.verify(attempt, hasher.hash("correct horse"))


def test_same_password_gets_a_different_salt(hasher: PasswordHasher) -> None:
    first, second = hasher.hash("correct horse"), hasher.hash("correct horse")

    assert first != second
    assert hasher.verify("correct horse", first)
    assert hasher.verify("correct horse", second)


def test_non_ascii_password_round_trips(hasher: PasswordHasher) -> None:
    assert hasher.verify("รหัสผ่าน-ภาษาไทย", hasher.hash("รหัสผ่าน-ภาษาไทย"))


@pytest.mark.parametrize("stored", ["", "not-a-bcrypt-hash", "$2b$04$tooshort"])
def test_verify_returns_false_for_malformed_hash(hasher: PasswordHasher, stored: str) -> None:
    assert not hasher.verify("correct horse", stored)


def test_hash_rejects_password_longer_than_bcrypt_limit(hasher: PasswordHasher) -> None:
    with pytest.raises(ValueError, match="72 bytes"):
        hasher.hash("a" * 73)


def test_password_at_bcrypt_limit_is_accepted(hasher: PasswordHasher) -> None:
    assert hasher.verify("a" * 72, hasher.hash("a" * 72))


def test_verify_returns_false_for_overlong_password(hasher: PasswordHasher) -> None:
    assert not hasher.verify("a" * 73, hasher.hash("a" * 72))
