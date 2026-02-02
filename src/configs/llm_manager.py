from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from configs.llm_adapter import NarrativeChatModel
from configs.setting import APP_ENV, GEMINI_API_KEY, OPENAI_API_KEY


class LLMManager:
    _instances = {}

    @classmethod
    def get_instance(cls, provider="gemini", temperature=0.0):
        provider = provider.lower()
        instance_key = f"{provider}_{temperature}"  # 고유 키

        if instance_key in cls._instances:
            return cls._instances[instance_key]

        if provider == "gateway":
            instance = NarrativeChatModel(temperature=temperature)

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
        # LLMManager 내부 수정
        elif provider == "bert":
            from transformers import pipeline

            # 한국어 지원이 원활한 다국어 Zero-shot 모델
            model_id = "vicgalle/xlm-roberta-large-xnli-anli"
            classifier = pipeline("zero-shot-classification", model=model_id)

            class BertClassifier:
                def __init__(self, pipe):
                    self.pipe = pipe

                async def classify(self, text: str, labels: List[str]):
                    # 실시간으로 넘겨받은 labels를 기준으로 분류
                    result = self.pipe(text, labels)
                    return {
                        "top_label": result["labels"][0],
                        "confidence": result["scores"][0],
                        "all_scores": dict(zip(result["labels"], result["scores"])),
                    }

            instance = BertClassifier(classifier)
        else:
            raise ValueError(f"지원하지 않는 모델 제공자입니다: {provider}")

        cls._instances[instance_key] = instance
        return instance
