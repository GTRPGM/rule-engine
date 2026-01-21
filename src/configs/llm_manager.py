from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
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
                model="gemini-2.5-flash", temperature=0.0, api_key=GEMINI_API_KEY
            )
        elif provider == "openai":
            instance = ChatOpenAI(
                model="gpt-4o-mini", temperature=0.0, api_key=OPENAI_API_KEY
            )
        elif provider == "claude":
            instance = ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                temperature=0.0,
                api_key=ANTHROPIC_API_KEY,
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
                # base_url="http://localhost:11434" # 기본값이므로 생략 가능
            )
        else:
            raise ValueError(f"지원하지 않는 모델 제공자입니다: {provider}")

        cls._instances[provider] = instance
        return instance


gemini = LLMManager.get_instance("gemini")
# gpt = LLMManager.get_instance("openai")
# claude = LLMManager.get_instance("claude")
ollama = LLMManager.get_instance("ollama")
