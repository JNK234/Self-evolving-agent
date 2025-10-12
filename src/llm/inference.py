
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import weave
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

load_dotenv()

# Initialize Weave for automatic tracing
# This captures all LangChain operations including prompts, LLM calls, and responses
WEAVE_PROJECT = os.getenv("WEAVE_PROJECT_NAME", "self-evolving-agent")
weave.init(WEAVE_PROJECT)


def get_llm_client(
    model: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> ChatGoogleGenerativeAI:
    """
    Initialize and return a Google Gemini LLM client configured with LangChain.

    Args:
        model: Gemini model name (default: gemini-2.5-flash from env or hardcoded)
        temperature: Sampling temperature for response randomness (0.0-1.0)
        **kwargs: Additional parameters to pass to ChatGoogleGenerativeAI

    Returns:
        Configured ChatGoogleGenerativeAI client instance

    Raises:
        ValueError: If GOOGLE_API_KEY is not set in environment
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        **kwargs
    )


def run_inference(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Run LLM inference with automatic Weave tracing and optional metadata.

    This function automatically traces the LLM call through Weave, capturing:
    - Input prompt
    - Model configuration
    - Response output
    - Latency and token usage
    - Custom metadata (if provided)

    Args:
        prompt: The input text prompt for the LLM
        model: Optional Gemini model override (default from env)
        temperature: Sampling temperature (0.0-1.0)
        metadata: Optional dict of custom metadata to attach to the trace
        **kwargs: Additional parameters for the LLM client

    Returns:
        The LLM's response as a string

    Example:
        >>> result = run_inference(
        ...     "Explain quantum computing in simple terms",
        ...     metadata={"task_type": "explanation", "user_id": "123"}
        ... )
    """
    llm = get_llm_client(model=model, temperature=temperature, **kwargs)

    # Use weave.attributes() to add custom metadata to the trace
    if metadata:
        with weave.attributes(metadata):
            response = llm.invoke([HumanMessage(content=prompt)])
    else:
        response = llm.invoke([HumanMessage(content=prompt)])

    # Extract text content from AIMessage
    if isinstance(response, AIMessage):
        return response.content
    return str(response)


@weave.op()
def run_react_agent(
    question: str,
    tools: List,
    model: Optional[str] = None,
    temperature: float = 0,
    system_message: Optional[str] = None,
    prompt_template_file: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Run a ReAct agent with tool access and automatic Weave tracing.

    This function creates and invokes a LangGraph ReAct agent that can use tools
    to solve problems. It supports flexible prompt configuration and integrates
    with Weave for full observability.

    Args:
        question: The user's question or problem to solve
        tools: List of LangChain tools the agent can use (e.g., calculator, search)
        model: Optional Gemini model override (default from env)
        temperature: Sampling temperature (0.0-1.0), default 0 for deterministic math
        system_message: Optional system prompt string to guide agent behavior
        prompt_template_file: Optional path to prompt template file (overrides system_message)
        metadata: Optional dict of custom metadata to attach to Weave trace
        **kwargs: Additional parameters for the LLM client

    Returns:
        The agent's final answer as a string

    Example:
        >>> from src.agents.tools.langchain_calculator import calculator_tool
        >>> answer = run_react_agent(
        ...     question="What is 25 * 4 + 10?",
        ...     tools=[calculator_tool],
        ...     prompt_template_file="prompt_templates/math_tools.txt",
        ...     temperature=0
        ... )

    Note:
        - The function automatically traces all agent interactions through Weave
        - Tool usage and intermediate reasoning steps are captured
        - The prompt template serves as system instructions; user question is passed separately
    """
    # Get LLM client
    llm = get_llm_client(model=model, temperature=temperature, **kwargs)

    # Load prompt template from file or use provided system message
    if prompt_template_file:
        with open(prompt_template_file, 'r') as f:
            system_prompt = f.read()
    elif system_message:
        system_prompt = system_message
    else:
        # Default minimal system prompt
        system_prompt = "You are a helpful AI assistant. Use the available tools to solve problems."

    # Create messages list with system message and user question
    # ReAct agents need both: system instructions + user query
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ]

    # Create ReAct agent with increased recursion limit for complex problems
    agent = create_react_agent(llm, tools)

    # Invoke agent with optional metadata tracing and recursion limit
    invoke_config = {"recursion_limit": 50}

    if metadata:
        with weave.attributes(metadata):
            result = agent.invoke({"messages": messages}, config=invoke_config)
    else:
        result = agent.invoke({"messages": messages}, config=invoke_config)

    # Extract final answer from agent result
    # The result contains a list of messages, get the last one
    if "messages" in result and len(result["messages"]) > 0:
        final_answer = result["messages"][-1].content
        # If content is empty, return full result for debugging
        if not final_answer or final_answer.strip() == "":
            print(f"WARNING: Empty response from agent. Full result: {result}")
            # Try to find the last non-empty AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content') and msg.content and msg.content.strip():
                    final_answer = msg.content
                    break
    else:
        final_answer = str(result)

    return final_answer


