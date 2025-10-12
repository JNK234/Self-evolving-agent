from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from .tools import add, subtract, multiply, divide, power, sqrt
from dotenv import load_dotenv

load_dotenv()

def updater(query: str, response: str, critic: str, initial_prompt: str):
    with open("prompt_templates/sea_updater_p.txt", "r") as f:
        system_prompt = f.read()


    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        timeout=None,
        max_retries=1,
    )

    agent = create_react_agent(llm)
    messages = [
        SystemMessage(content = system_prompt),
        HumanMessage(content = f"{query}\nResponse: {response}, Critic: {critic}, Initial prompt: {initial_prompt}"),
    ]

    response = agent.invoke({"messages": messages})
    return response
