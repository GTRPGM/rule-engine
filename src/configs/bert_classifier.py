from pathlib import Path
from typing import List

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)


class BertClassifier:
    # 1. 학습된 모델 경로 설정
    # 현재 파일(src/configs/llm_manager.py) 기준으로 src/models/trained_bert 경로 계산
    current_file = Path(__file__).resolve()
    model_path = current_file.parents[1] / "models" / "trained_bert"

    # 2. 모델 및 토크나이저 로드
    # 이미 훈련된 모델이므로 Auto 클래스가 라벨 정보를 자동으로 읽어옵니다.
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    # 3. 분류 파이프라인 생성
    # GPU가 있으면 device=0, 없으면 -1(CPU)
    device = 0 if torch.cuda.is_available() else -1
    classifier = pipeline(
        "text-classification", model=model, tokenizer=tokenizer, device=device
    )


class TrainedBertClassifier:
    def __init__(self, pipe):
        self.pipe = pipe

    async def classify(self, text: str, labels: List[str] = None):
        # 모델 추론
        result = self.pipe(text)[0]

        # 'LABEL_0' 형태에서 인덱스 숫자만 추출
        label_idx = int(result["label"].split("_")[-1])

        # 넘겨받은 labels 리스트에서 해당 인덱스의 텍스트를 추출
        # 만약 인덱스가 범위를 벗어나면 '알 수 없음' 반환
        if labels and label_idx < len(labels):
            korean_label = labels[label_idx]
        else:
            # 리스트에 없거나 labels가 안 넘어온 경우 모델의 기본 라벨 사용
            korean_label = result["label"]

        return {"top_label": korean_label, "confidence": result["score"]}
