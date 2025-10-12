from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from src.agents.tools import calculator_tool
from dotenv import load_dotenv

load_dotenv()

def google_agent(query: str):
    """Math problem solver using calculator tool."""
    tools = [calculator_tool]
    
    with open("prompt_templates/google_agent_p.txt", 'r') as f:
        system_prompt = f.read()
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        timeout=None,
        max_retries=1,
    )
    
    # Create agent with LLM bound to tools
    agent = create_react_agent(llm, tools)
    
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