from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from configs.bert_classifier import BertClassifier, TrainedBertClassifier
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
            # from pathlib import Path
            #
            # import torch
            # from transformers import (
            #     AutoModelForSequenceClassification,
            #     AutoTokenizer,
            #     pipeline,
            # )
            #
            # # 1. 학습된 모델 경로 설정
            # # 현재 파일(src/configs/llm_manager.py) 기준으로 src/models/trained_bert 경로 계산
            # current_file = Path(__file__).resolve()
            # model_path = current_file.parents[1] / "models" / "trained_bert"
            #
            # # 2. 모델 및 토크나이저 로드
            # # 이미 훈련된 모델이므로 Auto 클래스가 라벨 정보를 자동으로 읽어옵니다.
            # tokenizer = AutoTokenizer.from_pretrained(model_path)
            # model = AutoModelForSequenceClassification.from_pretrained(model_path)
            #
            # # 3. 분류 파이프라인 생성
            # # GPU가 있으면 device=0, 없으면 -1(CPU)
            # device = 0 if torch.cuda.is_available() else -1
            # classifier = pipeline(
            #     "text-classification", model=model, tokenizer=tokenizer, device=device
            # )
            instance = TrainedBertClassifier(BertClassifier.classifier)

        cls._instances[instance_key] = instance
        return instance
