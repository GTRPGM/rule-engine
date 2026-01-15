from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from configs.setting import ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY


class LLMManager:
    _instances = {}

    @classmethod
    def get_instance(cls, provider="gemini"):
        provider = provider.lower()

        if provider in cls._instances:
            return cls._instances[provider]

        if provider == "gemini":
            instance = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.0,
                api_key=GEMINI_API_KEY
            )
        elif provider == "openai":
            instance = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=OPENAI_API_KEY
            )
        elif provider == "claude":
            instance = ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                temperature=0.0,
                api_key=ANTHROPIC_API_KEY
            )
        else:
            raise ValueError(f"지원하지 않는 모델 제공자입니다: {provider}")

        cls._instances[provider] = instance
        return instance


gemini = LLMManager.get_instance("gemini")
gpt = LLMManager.get_instance("openai")
claude = LLMManager.get_instance("claude")