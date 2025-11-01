import pytest
from src.api.database import question_relationship_db as qr


# ======================================================================
# Language tests
# ======================================================================


@pytest.mark.parametrize(
    "language_name",
    [
        "Python",
        "JavaScript",
        "TypeScript    ",  # trailing whitespace should be stripped
    ],
)
def test_create_language(db_session, language_name):
    lang = qr.create_language(db_session, name=language_name)
    assert lang.id is not None
    assert lang.name == language_name.lower().strip()


@pytest.mark.parametrize("language_name", [None, "", "    "])
def test_create_language_no_name(db_session, language_name):
    with pytest.raises(ValueError, match=r"^Name cannot be empty$"):
        qr.create_language(db_session, language_name)


def test_create_duplicate_language_return_existing(db_session):
    lang1 = qr.create_language(db_session, name="Python")
    lang2 = qr.create_language(db_session, name="python")
    assert lang2.id == lang1.id
    assert lang2.name.lower() == lang1.name.lower()
    qr.delete_all_languages(db_session)  # Cleanup


@pytest.mark.parametrize("names", [["Python", "JavaScript", "Rust", "Go"]])
def test_list_languages_returns_all(db_session, names):
    qr.delete_all_languages(db_session)  # Cleanup
    for n in names:
        qr.create_language(db_session, name=n)
    result = qr.list_languages(db_session)
    returned_names = [l.name for l in result]
    assert set(returned_names) == {n.lower().strip() for n in names}


def test_get_language_by_name_found(db_session):
    created = qr.create_language(db_session, name="C++")
    fetched = qr.get_language_by_name(db_session, name="c++")
    assert fetched is not None
    assert fetched.id == created.id


def test_get_language_by_name_not_found_none_return(db_session):
    assert qr.get_language_by_name(db_session, "UnknownLang") is None


def test_delete_language_success(db_session):
    lang = qr.create_language(db_session, name="Ruby")
    retrieved = qr.get_language_by_name(db_session, lang.name)
    assert retrieved == lang
    qr.delete_language(db_session, language=lang)
    assert qr.get_language_by_name(db_session, lang.name) is None


def test_delete_all_languages(db_session):
    qr.delete_all_languages(db_session)
    assert qr.list_languages(db_session) == []


# ======================================================================
# QType tests
# ======================================================================


@pytest.mark.parametrize(
    "qtype_name",
    [
        "Numerical",
        "Multiple Choice",
        "True/False    ",  # trailing whitespace should be stripped
    ],
)
def test_create_qtype(db_session, qtype_name):
    qt = qr.create_qtype(db_session, name=qtype_name)
    assert qt.id is not None
    assert qt.name == qtype_name.lower().strip()


@pytest.mark.parametrize("qtype_name", [None, "", "    "])
def test_create_qtype_no_name(db_session, qtype_name):
    with pytest.raises(ValueError, match=r"^Name cannot be empty$"):
        qr.create_qtype(db_session, qtype_name)


def test_create_duplicate_qtype_return_existing(db_session):
    qt1 = qr.create_qtype(db_session, name="Numerical")
    qt2 = qr.create_qtype(db_session, name="numerical")
    assert qt2.id == qt1.id
    assert qt2.name.lower() == qt1.name.lower()
    qr.delete_all_qtypes(db_session)  # Cleanup


@pytest.mark.parametrize(
    "names", [["Numerical", "Multiple Choice", "True/False", "Short Answer"]]
)
def test_list_qtypes_returns_all(db_session, names):
    qr.delete_all_qtypes(db_session)  # Cleanup
    for n in names:
        qr.create_qtype(db_session, name=n)
    result = qr.list_qtypes(db_session)
    returned_names = [q.name for q in result]
    assert set(returned_names) == {n.lower().strip() for n in names}


def test_get_qtype_by_name_found(db_session):
    created = qr.create_qtype(db_session, name="Multiple Choice")
    fetched = qr.get_qtype_by_name(db_session, name="multiple choice")
    assert fetched is not None
    assert fetched.id == created.id


def test_get_qtype_by_name_not_found_none_return(db_session):
    assert qr.get_qtype_by_name(db_session, "Fill in the Blank") is None


def test_delete_qtype_success(db_session):
    qt = qr.create_qtype(db_session, name="Short Answer")
    retrieved = qr.get_qtype_by_name(db_session, qt.name)
    assert retrieved == qt
    qr.delete_qtype(db_session, qtype=qt)
    assert qr.get_qtype_by_name(db_session, qt.name) is None


def test_delete_all_qtypes(db_session):
    qr.delete_all_qtypes(db_session)
    assert qr.list_qtypes(db_session) == []


# ======================================================================
# Topic tests
# ======================================================================


@pytest.mark.parametrize(
    "topic_name",
    [
        "Kinematics",
        "Machine Learning",
        "Some topic with white space    ",
    ],
)
def test_create_topic(db_session, topic_name):
    topic = qr.create_topic(db_session, name=topic_name)
    assert topic.id is not None
    assert topic.name == topic_name.lower().strip()


@pytest.mark.parametrize("topic_name", [None, "", "    "])
def test_create_topic_no_name(db_session, topic_name):
    with pytest.raises(ValueError, match=r"^Name cannot be empty$"):
        qr.create_topic(db_session, topic_name)


def test_create_duplicate_topic_return_existing(db_session):
    topic1 = qr.create_topic(db_session, name="Thermodynamics")
    topic2 = qr.create_topic(db_session, name="thermodynamics")
    assert topic2.id == topic1.id
    assert topic2.name.lower() == topic1.name.lower()
    qr.delete_all_topics(db_session)  # Cleanup


@pytest.mark.parametrize(
    "names", [["Kinematics", "Machine Learning", "Heat Transfer", "Thermodynamics"]]
)
def test_list_topics_returns_all(db_session, names):
    qr.delete_all_topics(db_session)  # Cleanup
    for n in names:
        qr.create_topic(db_session, name=n)
    result = qr.list_topics(db_session)
    returned_names = [t.name for t in result]
    assert set(returned_names) == {n.lower().strip() for n in names}


def test_get_topic_by_name_found(db_session):
    created = qr.create_topic(db_session, name="Quantum Mechanics")
    fetched = qr.get_topic_by_name(db_session, name="quantum mechanics")
    assert fetched is not None
    assert fetched.id == created.id


def test_get_topic_by_name_not_found_none_return(db_session):
    assert qr.get_topic_by_name(db_session, "Unknown Topic") is None


def test_delete_topic_success(db_session):
    topic = qr.create_topic(db_session, name="Classical Mechanics")
    retrieved_topic = qr.get_topic_by_name(db_session, topic.name)
    assert retrieved_topic == topic
    qr.delete_topic(db_session, topic=topic)
    assert qr.get_topic_by_name(db_session, topic.name) is None


def test_delete_all_topics(db_session):
    qr.delete_all_topics(db_session)
    assert qr.list_topics(db_session) == []
