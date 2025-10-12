from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from typing import Optional
import re
from dotenv import load_dotenv


load_dotenv()

# Define arithmetic tools
@tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        return float('nan')
    return a / b


@tool
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent


@tool
def sqrt(x: float) -> float:
    """Calculate the square root of a number."""
    if x < 0:
        return float('nan')
    return x ** 0.5


def gsm8k_agent(query: str, verbose: bool = True) -> str:
    """
    GSM8K-optimized tool-calling agent.
    Forces step-by-step breakdown and tool usage.
    
    Args:
        query: The math word problem to solve
        verbose: Whether to print reasoning and tool calls
        
    Returns:
        The agent's final response with answer
    """
    tools = [add, subtract, multiply, divide, power, sqrt]
    
    system_prompt = """You are an expert math problem solver specializing in word problems.

CRITICAL INSTRUCTIONS:
1. BREAK DOWN the problem into individual steps
2. For EACH calculation, you MUST use a tool - NEVER do mental math
3. Show your work by explicitly stating what you're calculating before using a tool
4. Format your response clearly with steps and calculations
5. At the end, provide the final answer in this format: #### <number>

STEP-BY-STEP APPROACH:
- Read the problem carefully
- Identify all numbers and operations needed
- Call tools in sequence for each operation
- Report each result before moving to the next step
- Show the final calculation explicitly

EXAMPLE FORMAT:
Step 1: Calculate eggs eaten for breakfast. Use subtract: 16 - 3 = ?
Step 2: Calculate eggs used for baking. Use subtract: result - 4 = ?
Step 3: Calculate revenue. Use multiply: result * 2 = ?
#### <final answer>

TOOL USAGE RULES:
- ALWAYS use tools - never skip calling a tool
- Every arithmetic operation must go through a tool
- If you need to add three numbers, do: add(a, b) first, then add(result, c)
- Report the result after each tool call before proceeding"""
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        timeout=None,
        max_retries=1,
    )
    
    # Create agent
    agent = create_react_agent(llm, tools)
    
    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Solve this problem step by step using tools for every calculation:\n\n{query}")
    ]
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"PROBLEM:")
        print(f"{'='*70}")
        print(f"{query}\n")
    
    try:
        # Invoke agent
        response = agent.invoke({"messages": messages})
        print(response)
        # Extract final message
        final_message = response["messages"][-1]
        answer_text = final_message.content
        
        if verbose:
            print(f"{'='*70}")
            print(f"AGENT SOLUTION:")
            print(f"{'='*70}")
            print(f"{answer_text}\n")
            
            # Show tool usage with results
            messages_list = response.get("messages", [])
            tool_calls = []
            tool_results = []
            
            # Collect tool calls and results
            for i, msg in enumerate(messages_list):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_calls.append({
                            'name': tool_call['name'],
                            'args': tool_call['args'],
                            'id': tool_call.get('id', '')
                        })
                
                # Look for tool results in subsequent messages
                if hasattr(msg, 'content') and isinstance(msg.content, list):
                    for content in msg.content:
                        if hasattr(content, 'type') and content.type == 'tool_result':
                            tool_results.append(content.content)
            
            print(f"{'='*70}")
            print(f"TOOL CALLS AND RESULTS:")
            print(f"{'='*70}")
            
            for idx, (call, result) in enumerate(zip(tool_calls, tool_results), 1):
                a = call['args'].get('a', call['args'].get('base', call['args'].get('x')))
                b = call['args'].get('b', call['args'].get('exponent', ''))
                
                if b != '':
                    print(f"{idx}. {call['name']}({a}, {b}) = {result}")
                else:
                    print(f"{idx}. {call['name']}({a}) = {result}")
            
            if len(tool_calls) == 0:
                print("⚠️  WARNING: No tools were called! Agent solved mentally.")
            else:
                print(f"\n✅ Total tools called: {len(tool_calls)}")
            print(f"{'='*70}\n")
        
        return answer_text
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def extract_final_answer(text: str) -> Optional[float]:
    """Extract the numerical answer preceded by ####"""
    if not text:
        return None
    
    # Look for #### <number> pattern
    match = re.search(r'####\s*([\d.,\-]+)', text)
    if match:
        try:
            # Remove commas and convert to float
            num_str = match.group(1).replace(',', '')
            return float(num_str)
        except ValueError:
            pass
    
    return None


def eval_gsm8k_with_tools(dataset_samples: int = 10, verbose: bool = True):
    """
    Evaluate GSM8K dataset using the tool-calling agent.
    
    Args:
        dataset_samples: Number of samples to evaluate
        verbose: Whether to print details
        
    Returns:
        Dictionary with evaluation results
    """
    from datasets import load_dataset
    
    print(f"\n🚀 Loading GSM8K dataset...")
    ds = load_dataset("openai/gsm8k", "main")
    dataset = ds['test'][:dataset_samples]
    
    correct = 0
    incorrect = 0
    no_tools = 0
    responses = []
    
    for idx, (question, expected_answer) in enumerate(zip(dataset['question'], dataset['answer']), 1):
        print(f"\n{'─'*70}")
        print(f"Problem {idx}/{dataset_samples}")
        print(f"{'─'*70}")
        
        # Run agent
        agent_response = gsm8k_agent(question, verbose=verbose)
        
        # Extract answers
        agent_answer = extract_final_answer(agent_response)
        expected_num = extract_final_answer(expected_answer)
        
        # Check if tools were used
        tool_count = agent_response.count('add(') + agent_response.count('subtract(') + \
                     agent_response.count('multiply(') + agent_response.count('divide(')
        
        if tool_count == 0:
            no_tools += 1
        
        # Compare answers
        is_correct = False
        if agent_answer is not None and expected_num is not None:
            is_correct = abs(agent_answer - expected_num) < 0.01
        
        if is_correct:
            correct += 1
            status = "✅ CORRECT"
        else:
            incorrect += 1
            status = "❌ INCORRECT"
        
        print(f"\n{status}")
        print(f"Expected: {expected_num}")
        print(f"Got: {agent_answer}")
        print(f"Tools used: {tool_count}")
        
        responses.append({
            "question": question,
            "expected_answer": expected_num,
            "agent_answer": agent_answer,
            "correct": is_correct,
            "tools_used": tool_count,
            "full_response": agent_response
        })
    
    # Summary
    accuracy = correct / dataset_samples if dataset_samples > 0 else 0
    
    print(f"\n\n{'='*70}")
    print(f"EVALUATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total problems: {dataset_samples}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {incorrect}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"Problems with no tool usage: {no_tools}")
    print(f"{'='*70}\n")
    
    return {
        "accuracy": accuracy,
        "correct": correct,
        "incorrect": incorrect,
        "total": dataset_samples,
        "no_tools": no_tools,
        "responses": responses
    }


# Example usage
if __name__ == "__main__":
    # Single problem test
    problem = """Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning 
and bakes muffins for her friends every day with four. She sells the remainder at the farmers' 
market daily for $2 per fresh duck egg. How much in dollars does she make every day at the 
farmers' market?"""
    
    print("\n" + "="*70)
    print("TESTING SINGLE PROBLEM")
    print("="*70)
    
    response = gsm8k_agent(problem, verbose=True)
    final_answer = extract_final_answer(response)
    print(f"Final Answer Extracted: {final_answer}\n")
    

    # Uncomment below to evaluate on multiple GSM8K problems
    # print("\n" + "="*70)
    # print("RUNNING FULL EVALUATION")
    # print("="*70)
    # results = eval_gsm8k_with_tools(dataset_samples=5, verbose=False)