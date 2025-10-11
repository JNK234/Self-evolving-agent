# ABOUTME: W&B Inference client with automatic Weave tracing for observability
# ABOUTME: Provides OpenAI-compatible interface for W&B hosted models with built-in tracking

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import weave
from openai import OpenAI

# Load environment variables
load_dotenv()


class WBInference:
    """
    Weights & Biases Inference client with automatic Weave tracing.

    This class provides a simple interface to W&B's inference API using the OpenAI-compatible
    format. All inference calls are automatically traced through Weave for observability.

    Attributes:
        client: OpenAI client configured for W&B Inference endpoint
        model: Model identifier (e.g., 'coreweave/cw_OpenPipe_Qwen3-14B-Instruct')
        temperature: Sampling temperature for inference

    Example:
        >>> from src.llm.wb_inference import WBInference
        >>>
        >>> wb_llm = WBInference()
        >>> response = wb_llm.run_inference(
        ...     "Explain quantum computing",
        ...     metadata={"task": "explanation"}
        ... )
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        project: Optional[str] = None,
    ):
        """
        Initialize W&B Inference client.

        Args:
            model: W&B model identifier (default from WB_INFERENCE_MODEL env var)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            api_key: W&B API key (default from WANDB_API_KEY env var)
            base_url: W&B Inference API base URL (default from WB_INFERENCE_BASE_URL env var)
            project: W&B project for usage tracking (default from WB_INFERENCE_PROJECT env var)

        Raises:
            ValueError: If WANDB_API_KEY is not set
        """
        # Get configuration from environment or parameters
        self.api_key = api_key or os.getenv("WANDB_API_KEY")
        if not self.api_key:
            raise ValueError(
                "WANDB_API_KEY not found in environment variables. "
                "Please set it in your .env file or pass it as a parameter."
            )

        self.base_url = base_url or os.getenv(
            "WB_INFERENCE_BASE_URL",
            "https://api.inference.wandb.ai/v1"
        )
        self.model = model or os.getenv(
            "WB_INFERENCE_MODEL",
            "coreweave/cw_OpenPipe_Qwen3-14B-Instruct"
        )
        self.temperature = temperature
        self.project = project or os.getenv("WB_INFERENCE_PROJECT")

        # Initialize OpenAI client with W&B Inference endpoint
        client_kwargs = {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "project": self.project,
        }

        self.client = OpenAI(**client_kwargs)

    @weave.op()
    def run_inference(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Run inference with automatic Weave tracing.

        This method is automatically traced by Weave, capturing:
        - Input prompt and system prompt
        - Model configuration
        - Response output
        - Latency and token usage
        - Custom metadata

        Args:
            prompt: User prompt/query for the model
            system_prompt: Optional system prompt to set model behavior
            metadata: Optional dict of custom metadata for tracing
            **kwargs: Additional parameters for chat completion (e.g., max_tokens, top_p)

        Returns:
            str: Model's response text

        Example:
            >>> wb_llm = WBInference()
            >>> response = wb_llm.run_inference(
            ...     "What is machine learning?",
            ...     system_prompt="You are a helpful AI assistant.",
            ...     metadata={"user_id": "123", "task_type": "education"}
            ... )
        """
        # Build messages array
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Prepare chat completion parameters
        completion_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **kwargs
        }

        # Add metadata to Weave trace if provided
        if metadata:
            with weave.attributes(metadata):
                response = self.client.chat.completions.create(**completion_params)
        else:
            response = self.client.chat.completions.create(**completion_params)

        # Extract and return the response text
        return response.choices[0].message.content

    @weave.op()
    def run_inference_with_history(
        self,
        messages: list[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Run inference with conversation history for multi-turn dialogues.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Example: [
                         {"role": "system", "content": "You are helpful."},
                         {"role": "user", "content": "Hello"},
                         {"role": "assistant", "content": "Hi there!"},
                         {"role": "user", "content": "How are you?"}
                     ]
            metadata: Optional custom metadata for tracing
            **kwargs: Additional chat completion parameters

        Returns:
            str: Model's response text

        Example:
            >>> history = [
            ...     {"role": "user", "content": "What is AI?"},
            ...     {"role": "assistant", "content": "AI is artificial intelligence..."},
            ...     {"role": "user", "content": "Tell me more about ML"}
            ... ]
            >>> response = wb_llm.run_inference_with_history(history)
        """
        completion_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **kwargs
        }

        if metadata:
            with weave.attributes(metadata):
                response = self.client.chat.completions.create(**completion_params)
        else:
            response = self.client.chat.completions.create(**completion_params)

        return response.choices[0].message.content


# Convenience function for quick usage
@weave.op()
def run_wb_inference(
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Convenience function for quick W&B inference without managing class instance.

    Args:
        prompt: User prompt/query
        model: Optional model override
        system_prompt: Optional system prompt
        temperature: Sampling temperature (0.0-1.0)
        metadata: Optional tracing metadata
        **kwargs: Additional parameters

    Returns:
        str: Model response

    Example:
        >>> from src.llm.wb_inference import run_wb_inference
        >>> response = run_wb_inference("Explain AI", temperature=0.3)
    """
    wb_llm = WBInference(model=model, temperature=temperature)
    return wb_llm.run_inference(
        prompt=prompt,
        system_prompt=system_prompt,
        metadata=metadata,
        **kwargs
    )
