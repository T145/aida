from typing import Literal

from langchain_core.messages import (
    ToolMessage,
)
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore


class AidaState(MessagesState):
    #ask_human: bool
    summary: str


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls

    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> ToolNode:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

# Define the function that determines whether to continue or not
def should_continue(state: AidaState) -> Literal["end", "continue"]:
    messages = state["messages"]
    last_message = messages[-1]
    return "continue" if last_message.tool_calls else "end"


async def build_graph(checkpointer: BaseCheckpointSaver):
    tools = []
    model = ChatOllama(
        model='aida',
        keep_alive=-1, # https://github.com/ollama/ollama/issues/4427#issuecomment-2143525092
        streaming=True
    ).bind_tools(
        tools,
        #tool_choice='any' # Llama loves tool calls, often above its own reasoning, so we force it to always call a tool and have one that makes it rely on itself.
    )
    in_memory_store = InMemoryStore()

    # Define the function that calls the model
    async def call_model(state: AidaState):
        messages = state["messages"]
        response = await model.ainvoke(messages)
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    workflow = StateGraph(AidaState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("action", create_tool_node_with_fallback(tools))

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.add_edge(START, "agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        # First, we define the start node. We use `agent`.
        # This means these are the edges taken after the `agent` node is called.
        "agent",
        # Next, we pass in the function that will determine which node is called next.
        should_continue,
        # Finally we pass in a mapping.
        # The keys are strings, and the values are other nodes.
        # END is a special node marking that the graph should finish.
        # What will happen is we will call `should_continue`, and then the output of that
        # will be matched against the keys in this mapping.
        # Based on which one it matches, that node will then be called.
        {
            # If `tools`, then we call the tool node.
            "continue": "action",
            # Otherwise we finish.
            "end": END,
        },
    )

    # We now add a normal edge from `tools` to `agent`.
    # This means that after `tools` is called, `agent` node is called next.
    workflow.add_edge("action", "agent")

    app = workflow.compile(
        checkpointer=checkpointer,
        store=in_memory_store
    )

    with open('graph.png', 'wb') as png:
        png.write(app.get_graph().draw_mermaid_png())

    return app
