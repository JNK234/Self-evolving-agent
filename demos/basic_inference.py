# ABOUTME: Main entry point demonstrating LLM inference with Gemini and Weave integration
# ABOUTME: Shows both simple and conversational inference patterns with automatic tracing

from src.llm import run_inference
from src.llm.inference import run_inference_with_history


def main():
    """
    Demonstrate LLM inference capabilities with Weave tracing.

    This example shows:
    1. Simple single-turn inference with metadata
    2. Multi-turn conversation with history
    """
    print("=== Self-Evolving Agent - LLM Inference Demo ===\n")

    # Example 1: Simple inference with custom metadata
    print("Example 1: Simple Inference")
    print("-" * 50)

    response1 = run_inference(
        prompt="Explain what a self-evolving agent is in one sentence.",
        temperature=0.7,
        metadata={
            "task_type": "definition",
            "example_number": 1
        }
    )
    print(f"Prompt: Explain what a self-evolving agent is in one sentence.")
    print(f"Response: {response1}\n")

    # Example 2: Multi-turn conversation
    print("Example 2: Multi-turn Conversation")
    print("-" * 50)

    conversation_history = [
        {"role": "user", "content": "What is machine learning?"},
        {"role": "assistant", "content": "Machine learning is a subset of AI where systems learn from data."},
        {"role": "user", "content": "Can you give me a practical example?"}
    ]

    response2 = run_inference_with_history(
        messages=conversation_history,
        temperature=0.8,
        metadata={
            "task_type": "conversation",
            "example_number": 2,
            "turn_count": len(conversation_history)
        }
    )

    print("Conversation History:")
    for msg in conversation_history:
        print(f"  {msg['role'].capitalize()}: {msg['content']}")
    print(f"\nAssistant: {response2}\n")

    print("=" * 50)
    print("\nAll interactions have been traced in Weave!")
    print("Check your Weights & Biases dashboard to view traces.")


if __name__ == "__main__":
    main()
