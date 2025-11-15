# ==========================
# Imports
# ==========================

# Standard library
import operator
from typing import Literal

# Third-party
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated

# Local
from src.ai_base.settings import get_settings


# ==========================
# Setup
# ==========================

settings = get_settings()
model = init_chat_model("gpt-4o", temperature=0)


# ==========================
# Tools
# ==========================


@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Add `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# ==========================
# Tool Binding
# ==========================

tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


# ==========================
# Message State
# ==========================


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# ==========================
# LLM Node
# ==========================


def llm_call(state: dict):
    """LLM decides whether to call a tool or not."""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content=(
                            "You are a helpful assistant tasked with performing "
                            "arithmetic on a set of inputs."
                        )
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ==========================
# Tool Node
# ==========================


def tool_node(state: dict):
    """Performs the tool call."""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# ==========================
# Conditional Logic
# ==========================


def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide whether to continue or stop based on LLM output."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, perform it
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, stop (reply to the user)
    return END


# ==========================
# Graph Definition
# ==========================

agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
graph = agent_builder.compile()
