# import pytest
# from uuid import uuid4

# from api.models.file_model import File
# from api.models.question_model import Question
# from api.data import file_db as file_service
# from backend.src.app_test.unit.database.conftest import db_session


# @pytest.fixture
# def sample_question(db_session):
#     """Create and return a sample Question for linking files."""
#     q = Question(
#         title="Sample Question",
#         ai_generated=True,
#         isAdaptive=False,
#         createdBy="tester",
#         user_id=1,
#     )
#     db_session.add(q)
#     db_session.commit()
#     db_session.refresh(q)
#     return q


# def test_add_and_get_file(db_session, sample_question):
#     file_obj = File(
#         filename="test_file.txt",
#         content="hello world",
#         question_id=sample_question.id,
#     )
#     added = file_service.add_file(file_obj, db_session)

#     assert added.id is not None
#     assert added.filename == "test_file.txt"
#     assert added.content == "hello world"
#     assert added.question_id == sample_question.id

#     # Retrieve by id
#     fetched = file_service.get_file_by_id(added.id, db_session)
#     assert fetched.id == added.id
#     assert fetched.filename == "test_file.txt"
#     assert fetched.question_id == sample_question.id


# def test_get_file_by_id_not_found(db_session):
#     fake_id = uuid4()
#     with pytest.raises(ValueError, match="File not found"):
#         file_service.get_file_by_id(fake_id, db_session)


# def test_list_files(db_session, sample_question):
#     file_obj = File(
#         filename="list_me.txt",
#         content="data",
#         question_id=sample_question.id,
#     )
#     file_service.add_file(file_obj, db_session)

#     files = file_service.list_files(db_session)
#     assert isinstance(files, list)
#     assert any(f.filename == "list_me.txt" for f in files)


# def test_edit_file_content(db_session, sample_question):
#     file_obj = File(
#         filename="edit_test.txt",
#         content="old content",
#         question_id=sample_question.id,
#     )
#     added = file_service.add_file(file_obj, db_session)

#     # Edit content (string)
#     updated = file_service.update_file_content_by_file_id(
#         added.id, "new content", db_session
#     )
#     assert updated.content == "new content"

#     # Edit with dict content (stored as JSON string)
#     updated = file_service.update_file_content_by_file_id(
#         added.id, {"key": "value"}, db_session
#     )
#     assert '"key": "value"' in updated.content # type: ignore


# def test_delete_file(db_session, sample_question):
#     file_obj = File(
#         filename="delete_me.txt",
#         content="temp",
#         question_id=sample_question.id,
#     )
#     added = file_service.add_file(file_obj, db_session)

#     # Delete
#     file_service.delete_file(db_session, added.id)

#     # Verify deletion
#     with pytest.raises(ValueError, match="File not found"):
#         file_service.get_file_by_id(added.id, db_session)
