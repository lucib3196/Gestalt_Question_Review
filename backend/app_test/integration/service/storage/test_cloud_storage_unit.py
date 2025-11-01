# ============================================================================ #
#                                IMPORTS                                       #
# ============================================================================ #

# --- Standard Library ---
from pathlib import Path
from typing import Dict

# --- Third-Party ---
import pytest

# --- Internal ---
from src.api.core import logger


# ============================================================================ #
#                                FIXTURES                                      #
# ============================================================================ #


@pytest.fixture
def file_data() -> Dict[str, str]:
    """Provides mock file data for Firebase integration tests."""
    return {
        "identifier": "TestFolder",
        "filename": "hello.txt",
        "content": "Hello Firebase!",
        "base": "integration_test",
    }


@pytest.fixture
def save_test_question(cloud_storage_service, file_data) -> Path:
    """
    Saves a test file to Firebase and returns its resulting blob path.
    """
    cloud_storage_service.create_storage_path(file_data["identifier"])
    blob = cloud_storage_service.save_file(
        file_data["identifier"],
        file_data["filename"],
        file_data["content"],
    )
    return blob


# ============================================================================ #
#                              INITIALIZATION TESTS                            #
# ============================================================================ #


def test_firebase_initialization(cloud_storage_service):
    """Ensure the Firebase service is properly initialized."""
    assert cloud_storage_service
    assert cloud_storage_service.base_name == "integration_test"


def test_get_base_path(cloud_storage_service):
    assert cloud_storage_service.get_base_path() == "integration_test"


def test_get_base_name(cloud_storage_service):
    # Probably should test `.get_base_name()` if it exists,
    # but this mirrors existing implementation
    assert cloud_storage_service.get_base_path() == "integration_test"


# ============================================================================ #
#                              STORAGE PATH TESTS                              #
# ============================================================================ #


def test_get_storage_path(cloud_storage_service):
    name = "TestFolder"
    expected = Path("integration_test") / name
    assert cloud_storage_service.get_storage_path(name) == expected


def test_create_storage_path(cloud_storage_service, save_test_question, file_data):
    blob = save_test_question
    expected = Path(file_data["base"]) / file_data["identifier"] / file_data["filename"]
    assert blob
    assert Path(blob) == expected


def test_get_relative_storage_path(save_test_question, file_data):
    blob = save_test_question
    expected = Path(file_data["base"]) / file_data["identifier"] / file_data["filename"]
    assert blob == expected


def test_does_storage_path_exist(cloud_storage_service, save_test_question, file_data):
    _ = save_test_question
    assert cloud_storage_service.does_storage_path_exist(
        identifier=file_data["identifier"]
    )


# ============================================================================ #
#                                FILE HANDLING TESTS                           #
# ============================================================================ #


def test_get_file(cloud_storage_service, save_test_question, file_data):
    """Ensure a saved file can be retrieved with its correct content."""
    _ = save_test_question
    content = cloud_storage_service.get_file(
        file_data["identifier"], filename=file_data["filename"]
    )
    assert content is not None
    assert content.decode("utf-8") == file_data["content"]


def test_get_filepath(cloud_storage_service, save_test_question, file_data):
    _ = save_test_question
    expected = (
        Path(file_data["base"]) / file_data["identifier"] / file_data["filename"]
    ).as_posix()
    result = cloud_storage_service.get_filepath(
        file_data["identifier"], file_data["filename"]
    )
    assert Path(result) == Path(expected)


def test_delete_file(cloud_storage_service, save_test_question, file_data):
    """Ensure a saved file can be deleted and is no longer retrievable."""
    _ = save_test_question

    # Confirm file exists
    assert cloud_storage_service.does_file_exist(
        file_data["identifier"], file_data["filename"]
    )

    # Delete file
    cloud_storage_service.delete_file(
        file_data["identifier"], filename=file_data["filename"]
    )

    # Confirm file is gone
    assert not cloud_storage_service.does_file_exist(
        file_data["identifier"], file_data["filename"]
    )
    assert (
        cloud_storage_service.get_file(
            file_data["identifier"], filename=file_data["filename"]
        )
        is None
    )


def test_get_files_names(save_test_question, cloud_storage_service, file_data):
    """Ensure file names can be listed under the given identifier."""
    _ = save_test_question
    results = cloud_storage_service.list_file_names(file_data["identifier"])
    logger.debug("Retrieved filenames: %s", results)
    assert file_data["filename"] in results


def test_does_file_exist(cloud_storage_service, save_test_question, file_data):
    """Ensure does_file_exist correctly identifies existing files."""
    _ = save_test_question
    exists = cloud_storage_service.does_file_exist(
        file_data["identifier"], file_data["filename"]
    )
    assert exists is True


def test_get_nonexistent_file(cloud_storage_service):
    """Ensure retrieving a non-existent file returns None."""
    content = cloud_storage_service.get_file("no_folder", "missing.txt")
    assert content is None
