import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from src.agents.shared.tool_loader import load_agent_tools
from dotenv import load_dotenv

load_dotenv()

def solver(query: str, custom_prompt: str = None):
    tools = load_agent_tools("math_solver", include_generated=True)

    if custom_prompt:
        system_prompt = custom_prompt
    else:
        with open("prompt_templates/agents/math_solver/solver.txt", "r") as f:
            system_prompt = f.read()

    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.0-flash",
    #     temperature=0,
    #     timeout=None,
    #     max_retries=1,
    # )

    llm = ChatOpenAI(
            base_url=os.getenv("WB_INFERENCE_BASE_URL"),
            api_key=os.getenv("WANDB_API_KEY"),
            model=os.getenv("WB_INFERENCE_MODEL"),
        )

    agent = create_react_agent(llm, tools)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query),
    ]

    response = agent.invoke({"messages": messages})
    messages_list = response.get("messages", [])
    final_message = messages_list[-1]

    # Build sequential string
    conversation = ""
    for msg in messages_list:
        conversation += msg.content.strip() + "\n"
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tool_call in msg.tool_calls:
                args = tool_call.get("args", {})
                arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
                conversation += f"Tool being called: {tool_call['name']}({arg_str})\n"
        elif isinstance(msg, ToolMessage):
            conversation += msg.content.strip() + "\n"
    return conversation.strip(), system_prompt