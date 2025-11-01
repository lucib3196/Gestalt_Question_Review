from src.api.service.storage import directory_service as ds
import pytest
from src.api.core import logger
from pathlib import Path
from typing import Tuple
from src.utils import safe_dir_name


@pytest.fixture
def dir_service(tmp_path):
    return ds.DirectoryService(tmp_path)


@pytest.fixture
def test_dir(dir_service) -> Tuple[Path, str]:
    testname = "test_question"
    return dir_service.set_directory(testname, relative=False), testname


@pytest.fixture
def dir_with_files(test_dir):
    qdir = test_dir[0]
    test_name = test_dir[1]
    filename = "test_file.txt"
    filepath = qdir / filename
    filepath.write_text("Hello World")


def test_set_directory_absolute(dir_service):
    testname = "test_question"
    qdir = dir_service.set_directory(testname, relative=False)
    expected_path = dir_service.base_dir / testname
    assert qdir == expected_path


def test_set_directory_relative(dir_service):
    testname = "test_question"
    qdir = dir_service.set_directory(testname, relative=True)
    assert qdir == Path(testname)


@pytest.mark.parametrize(
    "unsafe_name",
    [
        "../etc/passwd",  # directory traversal
        "/absolute/path",  # absolute path
        "name with spaces",  # spaces
        "name?invalid",  # invalid chars on some OS
        "con",  # reserved name on Windows
        "a" * 300,  # too long
    ],
)
def test_unsafe_names(dir_service, unsafe_name):
    q_dir = dir_service.get_question_dir(unsafe_name)
    # you can either expect failure OR sanitize
    assert dir_service.base_dir / safe_dir_name(unsafe_name) == q_dir


def test_set_directory_path_exist(test_dir):
    assert Path(test_dir[0]).exists()


def test_get_question_dir(test_dir, dir_service):
    test_name = test_dir[1]
    expected_dir = dir_service.base_dir / test_name
    assert dir_service.get_question_dir(test_name) == expected_dir


def test_list_files_names(test_dir, dir_service):
    qdir = test_dir[0]
    test_name = test_dir[1]
    filename = "test_file.txt"
    filepath = qdir / filename
    filepath.write_text("Hello World")

    files = dir_service.list_files_names(test_name)
    assert filename in files
    assert len(files) == 1


def test_list_files_path(test_dir, dir_service):
    qdir = test_dir[0]
    test_name = test_dir[1]
    filename = "test_file.txt"
    filepath = qdir / filename
    filepath.write_text("Hello World")

    files = dir_service.list_file_paths(test_name)
    filepath = qdir / filename
    assert filepath in files
    assert len(files) == 1


def test_get_file(test_dir, dir_with_files, dir_service):
    test_name = test_dir[1]
    filename = "test_file.txt"
    retrieved = dir_service.get_file(test_name, filename)
    assert retrieved


def test_remove_question_dir(dir_with_files, test_dir, dir_service):
    # Initialize and create
    test_name = test_dir[1]
    files = dir_service.list_files_names(test_name)
    assert files
    assert len(files) == 1

    dir_service.remove_question_dir(test_name)
    files = dir_service.list_files_names(test_name)
    assert files == []
    assert len(files) == 0
