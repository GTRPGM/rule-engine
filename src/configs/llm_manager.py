import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from configs.http_client import http_holder
from configs.llm_adapter import NarrativeChatModel
from configs.setting import APP_ENV, GEMINI_API_KEY, OPENAI_API_KEY


class LLMManager:
    _instances = {}

    @classmethod
    def get_instance(cls, provider="gateway", temperature=0.0):
        provider = provider.lower()
        instance_key = f"{provider}_{temperature}"  # 고유 키

        if instance_key in cls._instances:
            return cls._instances[instance_key]

        if provider == "gateway":
            # lifespan에서 생성된 전역 클라이언트를 주입합니다.
            if not http_holder.client:
                # 만약 테스트 환경 등에서 client가 초기화되지 않았을 경우를 대비한 방어 코드
                http_holder.client = httpx.AsyncClient()

            instance = NarrativeChatModel(
                temperature=temperature,
                client=http_holder.client,  # 전역 클라이언트 사용
            )

        elif provider == "gemini":
            selected_model = (
                "gemini-2.5-flash" if APP_ENV == "local" else "gemini-3-pro-preview"
            )
            instance = ChatGoogleGenerativeAI(
                model=selected_model, temperature=temperature, api_key=GEMINI_API_KEY
            )
        elif provider == "openai":
            selected_model = "gpt-4o-mini" if APP_ENV == "local" else "gpt-4o"
            instance = ChatOpenAI(
                model=selected_model, temperature=temperature, api_key=OPENAI_API_KEY
            )
        elif provider == "ollama":
            # 로컬 Ollama 설정
            instance = ChatOllama(
                model="qwen2.5:3b",  # 가장 안정적인 한국어 인식 - 빠름. 가끔 부분 외국어로 응답
                # model="qwen2.5:1.5b",  # 정확도 70% - 가끔 중국어로 응답 - 빠름
                # model="qwen3:1.7b",  # 정확하지만 시간이 너무 오래 걸림
                # model="qwen3:4b",  # 이건 더 시간이 오래 걸림. 재고할 가치도 없음
                # model="qwen3:8b",  # - 처리속도 약간 느림
                temperature=temperature,
            )
        else:
            raise ValueError(f"지원하지 않는 모델 제공자입니다: {provider}")

        cls._instances[instance_key] = instance
        return instance
