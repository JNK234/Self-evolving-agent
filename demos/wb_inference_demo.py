# ABOUTME: Demo script for W&B Inference with Weave tracing
# ABOUTME: Shows basic usage of WBInference class and automatic observability

import os
import sys
from dotenv import load_dotenv
import weave

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.wb_inference import WBInference, run_wb_inference

# Load environment variables
load_dotenv()

# Initialize Weave for tracing (uses WEAVE_PROJECT_NAME from .env)
WEAVE_PROJECT = os.getenv("WEAVE_PROJECT_NAME", "self-evolving-agent")
weave.init(WEAVE_PROJECT)


def demo_basic_inference():
    """Demonstrate basic W&B inference with Weave tracing."""
    print("=" * 60)
    print("Demo 1: Basic W&B Inference")
    print("=" * 60)

    # Create WBInference instance
    wb_llm = WBInference(temperature=0.3)

    # Run a simple inference
    prompt = "Explain what Weights & Biases is in one sentence."
    print(f"\nPrompt: {prompt}")

    response = wb_llm.run_inference(
        prompt=prompt,
        metadata={
            "demo": "basic_inference",
            "task_type": "explanation"
        }
    )

    print(f"\nResponse: {response}")
    print("\n" + "=" * 60)


def demo_with_system_prompt():
    """Demonstrate inference with system prompt and metadata."""
    print("\n" + "=" * 60)
    print("Demo 2: Inference with System Prompt")
    print("=" * 60)

    wb_llm = WBInference(temperature=0.7)

    system_prompt = "You are a helpful AI assistant that explains concepts clearly and concisely."
    user_prompt = "What is machine learning?"

    print(f"\nSystem Prompt: {system_prompt}")
    print(f"User Prompt: {user_prompt}")

    response = wb_llm.run_inference(
        prompt=user_prompt,
        system_prompt=system_prompt,
        metadata={
            "demo": "system_prompt",
            "task_type": "education",
            "user_id": "demo_user"
        }
    )

    print(f"\nResponse: {response}")
    print("\n" + "=" * 60)


def demo_conversation_history():
    """Demonstrate multi-turn conversation with history."""
    print("\n" + "=" * 60)
    print("Demo 3: Multi-turn Conversation")
    print("=" * 60)

    wb_llm = WBInference(temperature=0.5)

    # Build conversation history
    conversation = [
        {"role": "system", "content": "You are a knowledgeable AI assistant."},
        {"role": "user", "content": "What is deep learning?"},
        {"role": "assistant", "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to learn from data."},
        {"role": "user", "content": "Can you give me a practical example?"}
    ]

    print("\nConversation History:")
    for msg in conversation:
        print(f"  {msg['role']}: {msg['content'][:80]}...")

    response = wb_llm.run_inference_with_history(
        messages=conversation,
        metadata={
            "demo": "conversation",
            "turn_number": 2
        }
    )

    print(f"\nAssistant Response: {response}")
    print("\n" + "=" * 60)


def demo_convenience_function():
    """Demonstrate using the convenience function."""
    print("\n" + "=" * 60)
    print("Demo 4: Convenience Function")
    print("=" * 60)

    prompt = "What is the capital of France?"
    print(f"\nPrompt: {prompt}")

    # Use convenience function for quick inference
    response = run_wb_inference(
        prompt=prompt,
        temperature=0.1,
        metadata={"demo": "convenience_function"}
    )

    print(f"\nResponse: {response}")
    print("\n" + "=" * 60)


def main():
    """Run all demo examples."""
    print("\n🚀 W&B Inference Demo with Weave Tracing")
    print("All inference calls are automatically traced in Weave!\n")

    try:
        # # Run all demos
        # demo_basic_inference()
        # demo_with_system_prompt()
        # demo_conversation_history()
        demo_convenience_function()

        print("\n✅ All demos completed successfully!")
        print(f"\n📊 View traces in Weave: https://wandb.ai/{WEAVE_PROJECT}/weave")
        print("\nNote: Make sure you have:")
        print("  1. Set WANDB_API_KEY in your .env file")
        print("  2. Configured WB_INFERENCE_PROJECT (format: username/project-name)")
        print("  3. Run 'uv sync' to install the openai package")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Check that WANDB_API_KEY is set in .env")
        print("  - Verify your W&B API key has inference access")
        print("  - Ensure the model name is correct in .env")
        sys.exit(1)


if __name__ == "__main__":
    main()
