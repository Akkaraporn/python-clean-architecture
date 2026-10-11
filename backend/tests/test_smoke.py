import importlib

import pytest

LAYERS = [
    "src.config",
    "src.domain",
    "src.usecases",
    "src.interface",
    "src.infrastructure",
    "src.shared",
]


@pytest.mark.parametrize("module", LAYERS)
def test_layer_package_is_importable(module: str) -> None:
    assert importlib.import_module(module) is not None
