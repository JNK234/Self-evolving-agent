# ABOUTME: Main entry point demonstrating LLM inference with Gemini and Weave integration
# ABOUTME: Shows both simple and conversational inference patterns with automatic tracing

from datasets import load_dataset
from src.llm.inference import run_inference, basic_google_llm
# from src.llm.inference import run_inference_with_history

def eval_gsm8k(llm : str):
    responses = []
    ds = load_dataset("openai/gsm8k", "main")
    test_hud = ds['test'][:100]
    
    for query in test_hud['question']:
        if llm == "basic google llm":
            responses.append(basic_google_llm(query))
        break
    return responses


def main():

    llm = "basic google llm"
    responses = eval_gsm8k(llm)
    print(responses)

    # response1 = run_inference(
    #     prompt="Explain what a self-evolving agent is in one sentence.",
    #     temperature=0.7,
    #     metadata={
    #         "task_type": "definition",
    #         "example_number": 1
    #     }
    # )
    # print("Prompt: Explain what a self-evolving agent is in one sentence.")
    # print(f"Response: {response1}\n")

    # # Example 2: Multi-turn conversation
    # print("Example 2: Multi-turn Conversation")
    # print("-" * 50)

    # conversation_history = [
    #     {"role": "user", "content": "What is machine learning?"},
    #     {"role": "assistant", "content": "Machine learning is a subset of AI where systems learn from data."},
    #     {"role": "user", "content": "Can you give me a practical example?"}
    # ]

    # response2 = run_inference_with_history(
    #     messages=conversation_history,
    #     temperature=0.8,
    #     metadata={
    #         "task_type": "conversation",
    #         "example_number": 2,
    #         "turn_count": len(conversation_history)
    #     }
    # )

    # print("Conversation History:")
    # for msg in conversation_history:
    #     print(f"  {msg['role'].capitalize()}: {msg['content']}")
    # print(f"\nAssistant: {response2}\n")

    # print("=" * 50)
    # print("\nAll interactions have been traced in Weave!")
    # print("Check your Weights & Biases dashboard to view traces.")


if __name__ == "__main__":
    main()
