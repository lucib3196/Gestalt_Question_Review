import pytest


@pytest.fixture
def simple_question_text():
    """Basic free-response style physics question."""
    question = (
        "A ball is traveling along a straight road at a constant speed of 20 miles per hour. "
        "What is the total distance traveled after 5 hours?"
    )
    additional_metadata = {"user_id": 0, "created_by": "Luciano@gmail.com"}
    return {"question": question, "additional_meta": additional_metadata}


@pytest.fixture
def multiple_choice_math_question():
    """Multiple-choice algebra question."""
    question = (
        "What is the solution to the equation 2x + 3 = 7?\n"
        "A) x = 1\nB) x = 2\nC) x = 3\nD) x = 4"
    )
    additional_metadata = {"user_id": 1, "created_by": "MathTeacher"}
    return {"question": question, "additional_meta": additional_metadata}


@pytest.fixture
def conceptual_physics_question():
    """Conceptual physics (no numbers, reasoning based)."""
    question = "Why does an object in motion stay in motion unless acted upon by an external force?"
    additional_metadata = {"user_id": 2, "created_by": "PhysicsDept"}
    return {"question": question, "additional_meta": additional_metadata}


@pytest.fixture
def engineering_design_question():
    """Open-ended engineering design style question."""
    question = (
        "Design a simple beam to support a uniformly distributed load of 500 N/m over a span "
        "of 3 meters. What cross-section and material would you choose?"
    )
    additional_metadata = {"user_id": 3, "created_by": "EngInstructor"}
    return {"question": question, "additional_meta": additional_metadata}


@pytest.fixture
def computer_science_question():
    """Programming / CS multiple choice."""
    question = (
        "Which of the following has a time complexity of O(log n)?\n"
        "A) Linear Search\nB) Binary Search\nC) Bubble Sort\nD) Selection Sort"
    )
    additional_metadata = {"user_id": 4, "created_by": "CSProfessor"}
    return {"question": question, "additional_meta": additional_metadata}


@pytest.fixture
def question_payloads(
    simple_question_text,
    multiple_choice_math_question,
    conceptual_physics_question,
    engineering_design_question,
    computer_science_question,
):
    """
    Aggregate all individual question fixtures into a single list
    so tests can iterate over them.
    """
    return [
        simple_question_text,
        multiple_choice_math_question,
        conceptual_physics_question,
        engineering_design_question,
        computer_science_question,
    ]
