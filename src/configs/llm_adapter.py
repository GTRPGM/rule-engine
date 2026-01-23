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
from langchain_core.runnables import RunnableLambda
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

from configs.llm import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from configs.llm import (
    ChatMessage as SchemaChatMessage,
)
from configs.setting import LANGCHAIN_GATEWAY_PORT, REMOTE_HOST


class NarrativeChatModel(BaseChatModel):
    """
    Custom LangChain ChatModel adapter for the LLM Gateway Narrative endpoint.
    """

    base_url: str = Field(
        default_factory=lambda: f"http://{REMOTE_HOST}:{LANGCHAIN_GATEWAY_PORT}"
    )
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
        import json

        schema_messages = [self._convert_message_to_schema(m) for m in messages]

        request_body = ChatCompletionRequest(
            model="gemini-2.0-flash",
            messages=schema_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
            response_format=kwargs.get("response_format"),
            tools=kwargs.get("tools"),
            tool_choice=kwargs.get("tool_choice"),
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

        # tool_calls 처리
        msg_kwargs = {}
        if choice.message.tool_calls:
            msg_kwargs["tool_calls"] = [
                tc.model_dump() for tc in choice.message.tool_calls
            ]

        raw_content = choice.message.content or ""

        # structured output 처리
        parsed_content = None
        response_format = kwargs.get("response_format")

        if response_format and isinstance(raw_content, str):
            fmt_type = response_format.get("type")
            if fmt_type in ("json_object", "json_schema"):
                try:
                    parsed_content = json.loads(raw_content)
                except json.JSONDecodeError:
                    parsed_content = None

        if parsed_content is not None:
            if isinstance(parsed_content, list):
                final_content = parsed_content
            else:
                final_content = [parsed_content]

            msg_kwargs["parsed"] = parsed_content
        else:
            final_content = raw_content

        generation = ChatGeneration(
            message=AIMessage(
                content=final_content,
                additional_kwargs=msg_kwargs,  # 항상 dict
            ),
            generation_info={"finish_reason": choice.finish_reason},
        )

        return ChatResult(generations=[generation])

    def with_structured_output(self, schema, *, method: str = "json_schema", **kwargs):
        async def _call(messages):
            result = await self.ainvoke(
                messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"schema": schema.model_json_schema()},
                },
            )

            content = result.content

            # LangChain content 규격(list[str|dict]) 처리
            if isinstance(content, list):
                if not content:
                    raise ValueError("Empty structured output")
                data = content[0]
            else:
                data = content

            # Pydantic 객체로 직접 변환
            return schema.model_validate(data)

        return RunnableLambda(_call)
