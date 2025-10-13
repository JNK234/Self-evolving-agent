# ABOUTME: LLM factory for creating model clients based on config.yaml
# ABOUTME: Supports multiple providers (Google Gemini, W&B Inference) with unified interface

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from src.llm.wb_inference import WBInference
from dotenv import load_dotenv

load_dotenv()


class LLMFactory:
    """Factory for creating LLM clients based on configuration."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize LLM factory with configuration file.

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}. "
                "Please create config.yaml in the project root."
            )

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        if 'llm_config' not in config:
            raise ValueError("Config file must contain 'llm_config' section")

        return config

    def get_llm(
        self,
        component_name: str,
        override_model: Optional[str] = None,
        override_temperature: Optional[float] = None,
        **kwargs
    ) -> Union[ChatGoogleGenerativeAI, WBInference]:
        """
        Get LLM client for a specific component.

        Args:
            component_name: Component name (solver, critic, updater, tool_generator, etc.)
            override_model: Optional model name override
            override_temperature: Optional temperature override
            **kwargs: Additional parameters for the LLM client

        Returns:
            Configured LLM client instance

        Raises:
            ValueError: If component not found in config or provider unsupported

        Example:
            >>> factory = LLMFactory()
            >>> critic_llm = factory.get_llm("critic")
            >>> solver_llm = factory.get_llm("solver", override_temperature=0.5)
        """
        llm_config = self.config['llm_config']

        if component_name not in llm_config:
            raise ValueError(
                f"Component '{component_name}' not found in config. "
                f"Available components: {list(llm_config.keys())}"
            )

        component_config = llm_config[component_name]
        provider = component_config['provider']
        model_name = override_model or component_config['model_name']
        temperature = override_temperature if override_temperature is not None else component_config.get('temperature', 0.7)

        if provider == 'google':
            return self._create_google_llm(model_name, temperature, **kwargs)
        elif provider == 'wandb':
            return self._create_wandb_llm(model_name, temperature, **kwargs)
        else:
            raise ValueError(
                f"Unsupported provider '{provider}' for component '{component_name}'. "
                f"Supported providers: google, wandb"
            )

    def _create_google_llm(
        self,
        model: str,
        temperature: float,
        **kwargs
    ) -> ChatGoogleGenerativeAI:
        """Create Google Gemini LLM client."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            **kwargs
        )

    def _create_wandb_llm(
        self,
        model: str,
        temperature: float,
        **kwargs
    ) -> WBInference:
        """Create W&B Inference LLM client."""
        return WBInference(
            model=model,
            temperature=temperature,
            **kwargs
        )

    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration section.

        Args:
            section: Optional section name (e.g., 'self_improvement')
                    If None, returns entire config

        Returns:
            Configuration dictionary
        """
        if section:
            return self.config.get(section, {})
        return self.config


# Global factory instance for convenience
_factory: Optional[LLMFactory] = None


def get_llm(
    component_name: str,
    override_model: Optional[str] = None,
    override_temperature: Optional[float] = None,
    config_path: str = "config.yaml",
    **kwargs
) -> Union[ChatGoogleGenerativeAI, WBInference]:
    """
    Convenience function to get LLM without managing factory instance.

    Args:
        component_name: Component name (solver, critic, updater, etc.)
        override_model: Optional model name override
        override_temperature: Optional temperature override
        config_path: Path to config file (default: config.yaml)
        **kwargs: Additional LLM client parameters

    Returns:
        Configured LLM client instance

    Example:
        >>> from src.llm.llm_factory import get_llm
        >>> critic_llm = get_llm("critic")
        >>> solver_llm = get_llm("solver", override_temperature=0)
    """
    global _factory

    if _factory is None or _factory.config_path != Path(config_path):
        _factory = LLMFactory(config_path)

    return _factory.get_llm(
        component_name,
        override_model=override_model,
        override_temperature=override_temperature,
        **kwargs
    )


def get_config(section: Optional[str] = None, config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Get configuration from config.yaml.

    Args:
        section: Optional section name to retrieve
        config_path: Path to config file

    Returns:
        Configuration dictionary

    Example:
        >>> from src.llm.llm_factory import get_config
        >>> self_improvement_config = get_config("self_improvement")
        >>> trigger_n = self_improvement_config['trigger_every_n_runs']
    """
    global _factory

    if _factory is None or _factory.config_path != Path(config_path):
        _factory = LLMFactory(config_path)

    return _factory.get_config(section)
