import os
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from .tools import add, subtract, multiply, divide, power, sqrt
from dotenv import load_dotenv

load_dotenv()

def phi_agent(query: str):
    """
    Simple agent that solves math problems and reports tool usage.
    """
    tools = [add, subtract, multiply, divide, power, sqrt]
    
    with open("prompt_templates/google_agent_p.txt", 'r') as f:
        system_prompt = f.read()
    
    llm = ChatOpenAI(
            base_url=os.getenv("WB_INFERENCE_BASE_URL"),
            api_key=os.getenv("WANDB_API_KEY"),
            model=os.getenv("WB_INFERENCE_MODEL"),
        )
    
    # Create agent with LLM bound to tools
    # agent = create_react_agent(llm, tools)
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    agent = create_react_agent(llm_with_tools, tools)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    
    response = agent.invoke({"messages": messages})
    final_message = response["messages"][-1]
    
    # Check if tools were used
    messages_list = response.get("messages", [])
    tools_used = []
    
    for msg in messages_list:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tools_used.append(tool_call['name'])
    
    # Print tool usage summary
    if tools_used:
        print(f"Tools used: {', '.join(set(tools_used))}")
    else:
        print("No tools were used")

    return final_message.content