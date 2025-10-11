# ABOUTME: Core LLM inference module using LangChain with Google Gemini models
# ABOUTME: Integrates Weave for automatic tracing and observability of LLM operations

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import weave
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env file
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

def basic_google_llm(query, google_model = "gemini-2.5-flash"):
    basic_prompt_file = "prompt_templates/basic_p.txt"
    with open(basic_prompt_file, 'r') as file:
        BASIC_PROMPT = file.read()
    
    prompt_template = PromptTemplate.from_template(BASIC_PROMPT)
    # prompt_template.invoke({"question": query})

    llm = ChatGoogleGenerativeAI(
        model = google_model,
        temperature = 0,
        timeout = None,
        max_retried=1,
    )
    chain = prompt_template | llm
    response = chain.invoke({"question": query})
    # print(response.content)
    return response.content

# def run_inference_with_history(
#     messages: list,
#     model: Optional[str] = None,
#     temperature: float = 0.7,
#     metadata: Optional[Dict[str, Any]] = None,
#     **kwargs
# ) -> str:
#     """
#     Run LLM inference with conversation history for multi-turn dialogues.

#     Args:
#         messages: List of message dicts with 'role' and 'content' keys
#                  Example: [
#                      {"role": "user", "content": "Hello"},
#                      {"role": "assistant", "content": "Hi there!"},
#                      {"role": "user", "content": "How are you?"}
#                  ]
#         model: Optional Gemini model override
#         temperature: Sampling temperature (0.0-1.0)
#         metadata: Optional custom metadata for tracing
#         **kwargs: Additional LLM parameters

#     Returns:
#         The LLM's response as a string
#     """
#     llm = get_llm_client(model=model, temperature=temperature, **kwargs)

#     # Convert message dicts to LangChain message objects
#     langchain_messages = []
#     for msg in messages:
#         if msg["role"] == "user":
#             langchain_messages.append(HumanMessage(content=msg["content"]))
#         elif msg["role"] == "assistant":
#             langchain_messages.append(AIMessage(content=msg["content"]))

#     # Execute with optional metadata
#     if metadata:
#         with weave.attributes(metadata):
#             response = llm.invoke(langchain_messages)
#     else:
#         response = llm.invoke(langchain_messages)

#     if isinstance(response, AIMessage):
#         return response.content
#     return str(response)
