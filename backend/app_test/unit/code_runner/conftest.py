from pydantic_settings import BaseSettings
from pathlib import Path
import pytest


class TestConfig(BaseSettings):
    asset_path: Path


test_config = TestConfig(
    asset_path=Path("src/app_test/test_assets/code").resolve()
)


@pytest.fixture
def get_asset_path():
    return test_config.asset_path


@pytest.fixture
def js_script_path(get_asset_path):
    """Fixture: returns the path to the test JavaScript file."""
    filepath = get_asset_path / "generate.js"
    assert filepath.exists()
    return filepath


@pytest.fixture
def py_script_path(get_asset_path):
    """Fixture: returns the path to the test Python file."""
    filepath = get_asset_path / "generate.py"
    assert filepath.exists()
    return filepath
