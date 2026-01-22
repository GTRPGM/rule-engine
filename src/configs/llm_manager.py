from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from configs.setting import APP_ENV, GEMINI_API_KEY, OPENAI_API_KEY
from configs.llm_adapter import NarrativeChatModel


class LLMManager:
    _instances = {}

    @classmethod
    def get_instance(cls, provider="gemini"):
        provider = provider.lower()

        if provider in cls._instances:
            return cls._instances[provider]

        if provider == "gateway":
            instance = NarrativeChatModel()

        elif provider == "gemini":
            selected_model = (
                "gemini-2.5-flash" if APP_ENV == "local" else "gemini-3-pro-preview"
            )
            instance = ChatGoogleGenerativeAI(
                model=selected_model, temperature=0.0, api_key=GEMINI_API_KEY
            )
        elif provider == "openai":
            selected_model = "gpt-4o-mini" if APP_ENV == "local" else "gpt-4o"
            instance = ChatOpenAI(
                model=selected_model, temperature=0.0, api_key=OPENAI_API_KEY
            )
        elif provider == "ollama":
            # 로컬 Ollama 설정
            instance = ChatOllama(
                model="qwen2.5:3b",  # 가장 안정적인 한국어 인식 - 빠름. 가끔 부분 외국어로 응답
                # model="qwen2.5:1.5b",  # 정확도 70% - 가끔 중국어로 응답 - 빠름
                # model="qwen3:1.7b",  # 정확하지만 시간이 너무 오래 걸림
                # model="qwen3:4b",  # 이건 더 시간이 오래 걸림. 재고할 가치도 없음
                # model="qwen3:8b",  # - 처리속도 약간 느림
                temperature=0.0,
            )
        else:
            raise ValueError(f"지원하지 않는 모델 제공자입니다: {provider}")

        cls._instances[provider] = instance
        return instance
