# ABOUTME: Test tool calling capability of WB Inference model
# ABOUTME: Verifies if the model can properly invoke tools through LangChain

import os
import weave
from dotenv import load_dotenv
from src.llm.wb_langchain import WBInferenceLangChain
from src.agents.tools.langchain_calculator import calculator_tool

load_dotenv()


def test_direct_tool_binding():
    """Test if model supports tool binding."""
    print("Testing tool binding capability...")
    print("="*60)

    # Initialize
    weave.init(os.getenv("WB_INFERENCE_PROJECT", "self-evolving-agent"))
    llm = WBInferenceLangChain(temperature=0)

    # Bind tools
    llm_with_tools = llm.bind_tools([calculator_tool])

    # Test message that should trigger tool use
    messages = [{
        "role": "user",
        "content": "Use the calculator_tool to compute 25 * 34. You must call the tool."
    }]

    print(f"\nPrompt: {messages[0]['content']}")
    print("\nCalling model with bound tools...")

    try:
        response = llm_with_tools.invoke(messages)
        print(f"\nResponse type: {type(response)}")
        print(f"Response content: {response.content[:200]}")

        # Check for tool calls
        if hasattr(response, 'tool_calls'):
            print(f"\nTool calls: {response.tool_calls}")
        else:
            print("\n⚠️  No tool_calls attribute found on response")

        # Check additional_kwargs
        if hasattr(response, 'additional_kwargs'):
            print(f"Additional kwargs: {response.additional_kwargs}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_direct_tool_binding()
