from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field
from typing import List, Literal
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ai_workspace.utils import save_graph_visualization
from typing import Optional

# Constants
FASTLLM = "gpt-4o-mini"
LONGCONTEXTLLM = "o3-mini-2025-01-31"

# Define the vector store
# Load the vector Store and set up retriever
vector_store_path = r"ai_workspace\vectorstores\ME_course_catalog_index"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = FAISS.load_local(
    vector_store_path, embeddings, allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})


## Query Generator
class Query(BaseModel):
    """A list of queries which will be used for the retrieval"""

    queries: List[str] = Field(..., description="A list of queries for searching")


llm_query = ChatOpenAI(model=FASTLLM)
structured_query = llm_query.with_structured_output(Query)
query_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert at generating effective search queries for academic databases.

Your task is to analyze the user's question and generate up to **three concise and unique search queries**. These queries will be used to search a database of course descriptions from the University of California, Riverside (UCR).

Guidelines:
- Focus on the **semantic intent** behind the question.
- Each query should:
  - Be direct and non-redundant
  - Reflect a different possible interpretation or aspect of the question
  - Help identify relevant UCR courses that might cover the topic

Context:
- The database contains course descriptions, topics covered, and learning outcomes.
- A single question may relate to multiple disciplines or course levels. 
  - For example, a question on **projectile motion** could be associated with an **introductory dynamics** course.
  - A question on the **first law of thermodynamics** could relate to both **intro-level** and **graduate-level** thermodynamics courses.

Be thoughtful in identifying the core concept of the question and consider interdisciplinary relevance where appropriate.
""",
        ),
        ("human", "{question}"),
    ]
)

query_generator = query_prompt | structured_query


## Retrieval grader
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: Literal["yes", "no"] = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


llm = ChatOpenAI(model=FASTLLM)
structured_llm_grader = llm.with_structured_output(GradeDocuments)

system = """
You are a grader assessing the relevance of a retrieved course description to a user’s academic question.

### Task:
Determine whether the provided course description is relevant to the user's question.

### Guidelines:
- A course is considered **relevant** if its description contains:
  - Keywords or phrases related to the question
  - Concepts that are semantically aligned with the question’s intent or subject matter
- This is **not a strict or detailed grading task**. Your goal is to filter out clearly unrelated or erroneous retrievals.
- Some overlap or indirect relevance is acceptable if the course logically relates to the topic of the question.

### Instructions:
- Respond with a **binary score**: either `"yes"` (relevant) or `"no"` (not relevant).
- Focus on **academic alignment**: would a student reasonably expect to encounter this question in the given course?

### Example Scenarios:
- A question about **fluid flow in pipes** would be relevant to a course on **fluid mechanics** → `"yes"`
- A question about **circuit analysis** would not be relevant to a course on **thermodynamics** → `"no"`

Be thoughtful but not overly strict. Use common academic reasoning.
"""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n  question: {question}"),
    ]
)
retrieval_grader = grade_prompt | structured_llm_grader

# Generate
system = """
You are an assistant for academic question-answering and classification tasks.

Your goal is to analyze the given question and classify it under one or more relevant course codes offered by the University of California, Riverside (UCR).

### Task:
- Review the student's question.
- Identify the core academic concepts and topics involved.
- Match the question to one or more relevant **UCR course codes**, based on the provided context.

### Context:
- You will be provided with a list of course descriptions that include:
  - Course titles and codes
  - Topics covered
  - Prerequisites and course level (introductory, intermediate, advanced)
  - Learning outcomes

- A single question may map to **multiple courses**, especially if it spans multiple disciplines or academic levels.
  - For example:
    - A question about **projectile motion** may belong to both **introductory physics** and **dynamics** courses.
    - A question about the **first law of thermodynamics** could apply to **Thermo 100A**, **Thermo 100B**, or even a **graduate-level course** in energy systems.

### Requirements:
- Only return course codes that appear in the provided context.
- If you are unsure or the context does not contain sufficient information, respond with:
  **"I don't know based on the provided information. Return None"**

### Additional Notes:
- Be precise, and avoid making assumptions beyond what the context allows.
- Consider interdisciplinary relevance when a question logically connects to more than one subject area.
- Think from a student’s perspective: Where would they most likely encounter this question in the curriculum?

Context:
{context}
"""
rag_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)
llm = ChatOpenAI(model=FASTLLM)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


class CourseClassification(BaseModel):
    course_id: Optional[List[str]] = Field(
        ..., description="A list of the relevan course IDs "
    )


rag_chain = rag_prompt | llm.with_structured_output(CourseClassification)


## Hallucination Grader
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: Literal["yes", "no"] = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


llm = ChatOpenAI(model=FASTLLM)
structured_llm_grader = llm.with_structured_output(GradeHallucinations)
system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
     Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)
hallucination_grader = hallucination_prompt | structured_llm_grader


### Answer Grader
class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: Literal["yes", "no"] = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


llm = ChatOpenAI(model=FASTLLM)
structured_llm_grader = llm.with_structured_output(GradeAnswer)

# Prompt
system = """You are a grader assessing whether an answer addresses / resolves a question \n 
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)
answer_grader = answer_prompt | structured_llm_grader


# Define the graph
class State(BaseModel):
    question: str
    queries: Optional[List[str]] = None
    generation: Optional[str] = None
    documents: Optional[List[Document]] = None


def generate_queries(state: State):
    question = state.question
    results = query_generator.invoke({"question": question})
    return {"question": question, "queries": results.queries}  # type: ignore


def retrieve(state: State):
    queries = state.queries
    all_documents = []
    for q in queries:  # type: ignore
        document = retriever.invoke(q)
        all_documents.extend(document)
    return {"documents": all_documents}


def generate(state: State):
    question = state.question
    documents = state.documents
    if documents:
        generation = rag_chain.invoke({"context": documents, "question": question})
        return {"documents": documents, "question": question, "generation": generation}
    else:
        return


def grade_documents(state: State):
    question = state.question
    documents = state.documents

    # Score each doc
    filtered_docs = []
    for d in documents:  # type: ignore
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score  # type: ignore
        if grade == "yes":
            filtered_docs.append(d)
        else:
            continue
    return {"documents": filtered_docs, "question": question}


from langgraph.graph import END, StateGraph, START

workflow = StateGraph(State)

workflow.add_node(
    "generate_search_queries", generate_queries
)  # Generate relevant search queries
workflow.add_node(
    "retrieve_course_descriptions", retrieve
)  # Retrieve course descriptions based on queries
workflow.add_node(
    "filter_relevant_courses", grade_documents
)  # Grade/filter retrieved descriptions for relevance
workflow.add_node(
    "answer_question_with_context", generate
)  # Generate a final answer using filtered course info

workflow.add_edge(START, "generate_search_queries")
workflow.add_edge("generate_search_queries", "retrieve_course_descriptions")
workflow.add_edge("retrieve_course_descriptions", "filter_relevant_courses")
workflow.add_edge("filter_relevant_courses", "answer_question_with_context")
workflow.add_edge("answer_question_with_context", END)


app = workflow.compile()


if __name__ == "__main__":
    save_graph_visualization(
        app,  # type: ignore
        "course_classification_agent.png",
        base_path=r"ai_workspace/agents/course_classification_agent",
    )  # type: ignore

    test_inputs = [
        {
            "question": "How does entropy change during an isothermal expansion of an ideal gas?"
        },
        {
            "question": "What forces act on a beam fixed at one end when a load is applied at the other?"
        },
        {
            "question": "Explain the differences between laminar and turbulent flow in internal pipe systems."
        },
        {"question": "What is the capital of France"},
        {
            "question": " A car is traveling along a straight rode at a velocity of 100mph after 5 hours what will the total distance covered be?"
        },
    ]

    for t in test_inputs:
        results = app.invoke(t)  # type: ignore
        # print(f"Retrieved Queries {results.get('queries')}\n")
        print("Question: ", t.get("question"))
        print(f"\n Generated answer: {results.get("generation")} \n")
        # print(f"Retrieved Documents {results.get('documents')}\n")
