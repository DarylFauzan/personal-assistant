# import package to create agent
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage

# import tools from mcp
import asyncio, json, time
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# create memory for short-term memory
memory = {}

# use client to fetch tools
async def get_tools_prompt():
    print("🛠️fetching tools and prompt...")
    client = MultiServerMCPClient(
        {
            "Personal Assistant": {
                "command": "python",
                "args": ["src/servers/personal_assistant.py"],
                "transport": "stdio",
            }
    },
    )
    tools = await client.get_tools()
    prompt = await client.get_prompt("Personal Assistant", "system message")
    print("fetching tools and prompt success")
    return tools, prompt

model_name = "qwen3:14b"

# create langgraph agent
async def create_agent(model_name = "qwen3:14b"):
    tools, prompt = await get_tools_prompt()
    llm = ChatOllama(model = model_name, temperature = 0.1).bind_tools(tools)

    # create the llm node
    def call_model(state:MessagesState):
        system_prompt = SystemMessage(prompt[0].content)

        response = llm.invoke([system_prompt] + state["messages"])

        return {"messages": response}

    # Create react agent
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
    )
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    return graph

graph = asyncio.run(create_agent())

# build the orchestrator
async def orchestrator(user_id, question, model_name="qwen3:14b"):
    start_time = time.time()
    global memory

    full_response = ""

    # initialize memory for user
    if user_id not in memory:
        memory[user_id] = [HumanMessage(question)]
    else:
        memory[user_id].append(HumanMessage(question))
    print(memory[user_id])

    # stream events from graph
    async for event in graph.astream_events(
        {"messages": memory[user_id][-20:]},
        version="v1"
    ):
        if event["event"] == "on_chat_model_stream":
            delta = event["data"]["chunk"].content
            if delta:
                full_response += delta
                print(delta, end = "")
                yield f"{delta}"

    # save final assistant message
    memory[user_id].append(AIMessage(full_response))
    print(memory[user_id])

    # optionally yield a final "done" event (OPENAI FORMAT)
    # yield "data: [DONE]\n\n"