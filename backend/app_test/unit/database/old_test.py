def test_create_question_with_relationships(
    db_session, question_payload_with_relationships
):
    created = question.create_question(question_payload_with_relationships, db_session)
    assert {t.name for t in created.topics} == set(
        question_payload_with_relationships["topics"]
    )
    assert {t.name for t in created.languages} == set(
        question_payload_with_relationships["languages"]
    )
    assert {t.name for t in created.qtypes} == set(
        question_payload_with_relationships["qtypes"]
    )


@pytest.mark.asyncio
async def test_get_question_data(combined_payload, db_session):
    for q in combined_payload:
        created = qdb.create_question(q, db_session)
        r = await qdb.get_question_data(created.id, db_session)


@pytest.mark.asyncio
async def test_get_all_question_data(combined_payload, db_session):
    for q in combined_payload:
        created = question.create_question(q, db_session)
    retrieved = await question.get_all_question_data(db_session)
    assert len(retrieved) == len(combined_payload)
    assert isinstance(retrieved, list)


# Test updating
def test_updating_question_multiple_fields(db_session):

    payload = {
        "title": "AutoCreate",
        "ai_generated": True,
        "isAdaptive": False,
        "createdBy": "Alice",
        "user_id": 1,
        "topics": ["topic1", "topic2"],
    }
    created = question.create_question(payload, db_session)
    assert created.title == payload["title"]

    original_topics = {t.name for t in created.topics}

    # Act 1: update several fields at once
    updated = question.update_question(
        db_session,
        question_id=created.id,
        title="NewTitle",
        isAdaptive=True,
        ai_generated=False,
        createdBy="Bob",
    )

    # Assert after first update
    assert updated.id == created.id
    assert updated.title == "NewTitle"
    assert updated.isAdaptive is True
    assert updated.ai_generated is False
    assert updated.createdBy == "Bob"
    assert {t.name for t in updated.topics} == original_topics  # topics unchanged

    # Act 2: another update (different fields)
    updated2 = question.update_question(
        db_session,
        question_id=created.id,
        title="FinalTitle",
        createdBy="Carol",
    )

    # Assert after second update
    assert updated2.id == created.id
    assert updated2.title == "FinalTitle"
    assert updated2.createdBy == "Carol"
    # prior boolean changes persist
    assert updated2.isAdaptive is True
    assert updated2.ai_generated is False
    assert {t.name for t in updated2.topics} == original_topics


# Test Filtering
def test_question_filtering(db_session):
    # Arrange: clean slate

    q1 = question.create_question(
        {
            "title": "AutoCreate",
            "ai_generated": True,
            "isAdaptive": False,
            "createdBy": "Alice",
            "user_id": 1,
            "topics": ["topic1", "topic2"],
        },
        db_session,
    )

    q2 = question.create_question(
        {
            "title": "Other Question",
            "ai_generated": False,
            "isAdaptive": True,
            "createdBy": "Bob",
            "user_id": 2,
            "topics": ["topic3"],
        },
        db_session,
    )

    # AND across keys: title + ai_generated + topic name
    res = question.filter_questions(
        db_session, title="autocreate", ai_generated=True, topics="topic1"
    )
    assert isinstance(res, list)
    assert {r.id for r in res} == {q1.id}
    assert all("autocreate" in r.title.lower() for r in res)
    assert all(r.ai_generated is True for r in res)
    assert all(any(t.name == "topic1" for t in r.topics) for r in res)

    # OR within a single key (topics): either topic1 OR topic3
    res_or = question.filter_questions(db_session, topics=["topic1", "topic3"])
    assert {r.id for r in res_or} == {q1.id, q2.id}

    # Negative case: no match when AND condition fails
    res_none = question.filter_questions(
        db_session, title="AutoCreate", ai_generated=False
    )
    assert res_none == []
