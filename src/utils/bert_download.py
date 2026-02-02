import os

from transformers import AutoModelForSequenceClassification, AutoTokenizer


def download_base_model():
    # 1. 모델 식별자 (한국어 NLU 최고 성능 모델 중 하나)
    model_name = "klue/roberta-base"

    # 2. 로컬 저장 경로
    save_path = "../models/base_model"

    # 디렉토리가 없으면 생성
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    print(f"🚀 모델 및 토크나이저 다운로드 시작: {model_name}...")

    try:
        # 분류를 위한 모델 구조(7개 라벨)와 토크나이저 다운로드
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=7
        )

        # 3. 로컬에 저장
        tokenizer.save_pretrained(save_path)
        model.save_pretrained(save_path)

        print(f"✅ 다운로드 완료! 경로: {os.path.abspath(save_path)}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    # Shift + F10을 누르면 이 블록이 실행됩니다.
    download_base_model()
