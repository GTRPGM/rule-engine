from typing import Any, List, Optional

import httpx
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

from configs.llm import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from configs.llm import (
    ChatMessage as SchemaChatMessage,
)


class NarrativeChatModel(BaseChatModel):
    """
    Custom LangChain ChatModel adapter for the LLM Gateway Narrative endpoint.
    """

    base_url: str = Field(default_factory=lambda: 'http://localhost:8060')
    client: httpx.AsyncClient = Field(default_factory=lambda: httpx.AsyncClient())

    @property
    def _llm_type(self) -> str:
        return "gm_llm_gateway_narrative"

    def _convert_message_to_schema(self, message: BaseMessage) -> SchemaChatMessage:
        """Converts LangChain message to our Pydantic schema."""
        role = "user"
        if isinstance(message, SystemMessage):
            role = "system"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, ChatMessage):
            role = message.role

        return SchemaChatMessage(role=role, content=str(message.content))

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Sync generation is not supported/recommended for this async-first service,
        but required by abstract base class.
        We can bridge it or just raise NotImplemented
        if we only use async.
        """
        raise NotImplementedError(
            "Sync generation not implemented. Use ainvoke/agenerate."
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        schema_messages = [self._convert_message_to_schema(m) for m in messages]

        request_body = ChatCompletionRequest(
            model="gemini-2.0-flash-light",
            messages=schema_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
        )

        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/completions",
            json=request_body.model_dump(exclude_none=True),
        )
        response.raise_for_status()

        chat_response = ChatCompletionResponse(**response.json())

        if not chat_response.choices:
            return ChatResult(generations=[])

        choice = chat_response.choices[0]
        content = choice.message.content or ""

        # Convert back to LangChain format
        generation = ChatGeneration(
            message=AIMessage(content=content),
            generation_info={"finish_reason": choice.finish_reason},
        )

        return ChatResult(generations=[generation])
