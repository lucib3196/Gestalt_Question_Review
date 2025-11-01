
import re
from src.utils.file_management_utils import *


def test_safe_name_removes_special_characters():
    name = "weird@file#name!.txt"
    safe = safe_dir_name(name)
    assert re.match(r"^[A-Za-z0-9._-]+$", safe)  # only allowed chars
    assert safe.endswith(".txt")


def test_safe_name_replaces_spaces_with_underscores():
    name = "my file name.pdf"
    safe = safe_dir_name(name)
    assert " " not in safe
