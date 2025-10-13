# ABOUTME: LangChain agent demo using Google Gemini with calculator tool
# ABOUTME: Demonstrates ReAct agent solving math problems with Weave tracing

import os
import weave
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.tools.langchain_calculator import calculator_tool

load_dotenv()


def main():
    """Run calculator agent demo with math problems."""

    # Initialize Weave for tracing
    project = os.getenv("WB_INFERENCE_PROJECT", "self-evolving-agent")
    weave.init(project)

    # Initialize Gemini LLM and tools
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    tools = [calculator_tool]

    # Create ReAct agent with system message
    system_message = (
        "You are a helpful assistant that MUST use the calculator_tool for ALL mathematical calculations. "
        "Never calculate numbers in your head. Always use the calculator_tool even for simple arithmetic. "
        "Break down complex problems into steps and use the calculator for each calculation."
    )
    agent = create_react_agent(llm, tools, state_modifier=system_message)

    # Test problems
    problems = [
        "What is 25 multiplied by 34?",
        "Calculate (100 - 25) divided by 3",
        "What is 2 to the power of 8?",
        "If I have 127 apples and give away 43, then split the remainder equally among 7 people, how many apples does each person get?",
    ]

    print("\n" + "="*60)
    print("LangChain Calculator Agent Demo")
    print("="*60 + "\n")

    for i, problem in enumerate(problems, 1):
        print(f"\n--- Problem {i} ---")
        print(f"Question: {problem}")

        # Run agent with streaming to see tool calls
        print("\nAgent reasoning:")
        for step in agent.stream({"messages": [{"role": "user", "content": problem}]}, stream_mode="values"):
            last_message = step["messages"][-1]

            # Check if it's a tool call
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    print(f"  🔧 Tool: {tool_call['name']}")
                    print(f"     Args: {tool_call['args']}")

            # Check if it's a tool response
            if hasattr(last_message, 'name') and last_message.name:
                print(f"  📊 Result: {last_message.content}")

        # Get final answer
        final_message = step["messages"][-1]
        print(f"\nFinal Answer: {final_message.content}\n")

    print("="*60)
    print("✓ Demo complete! Check Weave for traces.")
    print("="*60)


if __name__ == "__main__":
    main()
