import inspect

import pytest

from src.domain import errors
from src.domain.errors import DomainError
from src.interface.handlers.fastapi.errors import ERROR_MAPPINGS, FALLBACK, mapping_for

DOMAIN_ERRORS = [
    cls
    for _, cls in inspect.getmembers(errors, inspect.isclass)
    if issubclass(cls, DomainError) and cls is not DomainError
]


@pytest.mark.parametrize("error_class", DOMAIN_ERRORS, ids=lambda cls: cls.__name__)
def test_every_domain_error_has_an_explicit_http_mapping(error_class: type[DomainError]) -> None:
    # A new error that silently falls back to 400 is almost always a forgotten mapping.
    assert error_class in ERROR_MAPPINGS


def test_unknown_domain_error_falls_back_to_400() -> None:
    class SomethingNewError(DomainError):
        pass

    assert mapping_for(SomethingNewError()) is FALLBACK
    assert FALLBACK.status_code == 400
