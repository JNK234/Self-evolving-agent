# ABOUTME: LangChain wrapper for WBInference preserving Weave tracing
# ABOUTME: Simple adapter between W&B Inference and LangChain agent interface

from typing import Any, List, Optional, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
import weave
from .wb_inference import WBInference


class WBInferenceLangChain(BaseChatModel):
    """LangChain adapter for WBInference with Weave tracing."""

    wb_client: WBInference
    model: str
    temperature: float

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        wb_client = WBInference(model=model, temperature=temperature)
        super().__init__(
            wb_client=wb_client,
            model=wb_client.model,
            temperature=wb_client.temperature,
            **kwargs
        )

    @property
    def _llm_type(self) -> str:
        return "wb_inference"

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenAI format."""
        role_map = {
            SystemMessage: "system",
            HumanMessage: "user",
            AIMessage: "assistant",
        }
        return [
            {"role": role_map.get(type(msg), "user"), "content": msg.content}
            for msg in messages
        ]

    @weave.op()
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response with Weave tracing."""
        wb_messages = self._convert_messages(messages)
        response_text = self.wb_client.run_inference_with_history(
            messages=wb_messages,
            **kwargs
        )
        message = AIMessage(content=response_text)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def bind_tools(self, tools: List[Any], **kwargs) -> "WBInferenceLangChain":
        return self
