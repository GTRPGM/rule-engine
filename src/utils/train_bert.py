import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from datasets import Dataset
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


@dataclass
class DistillationDataCollator(DataCollatorWithPadding):
    # 상속을 통해 tokenizer.pad를 내부적으로 안전하게 사용합니다.

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        # 1. soft_labels를 안전하게 추출 (이미 텐서일 가능성이 높으므로 stack 사용)
        soft_labels = torch.stack([f.pop("soft_labels") for f in features])

        # 2. 부모 클래스의 패딩 처리
        batch = super().__call__(features)

        # 3. float32 형변환 확인 후 삽입
        batch["soft_labels"] = soft_labels.to(torch.float32)

        return batch


# 1. 지식 증류를 위한 커스텀 트레이너 정의
class DistillationTrainer(Trainer):
    def __init__(self, *args, alpha=0.5, temperature=2.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpha = alpha  # Soft Label(Teacher)과 Hard Label(정답)의 반영 비율
        self.temperature = temperature  # 확률 분포를 부드럽게 만드는 가중치

    def compute_loss(
        self, model, inputs, return_outputs=False, num_items_in_batch=None
    ):
        # Teacher가 준 soft_labels 추출
        soft_labels = inputs.pop("soft_labels")
        labels = inputs.get("labels")

        # Student 모델의 예측 (Logits)
        outputs = model(**inputs)
        student_logits = outputs.get("logits")

        # 1) Soft Loss: Teacher의 분포와 Student의 분포 차이 (KL Divergence)
        # Temperature를 적용해 분포를 완만하게 만듭니다.
        soft_loss = nn.KLDivLoss(reduction="batchmean")(
            F.log_softmax(student_logits / self.temperature, dim=-1),
            F.softmax(soft_labels / self.temperature, dim=-1),
        ) * (self.temperature**2)

        # 2) Hard Loss: 실제 정답과의 차이 (Cross Entropy)
        hard_loss = F.cross_entropy(student_logits, labels)

        # 최종 손실: 두 로스를 섞음
        loss = self.alpha * soft_loss + (1.0 - self.alpha) * hard_loss

        return (loss, outputs) if return_outputs else loss


def train_bert():
    current_file = Path(__file__).resolve()
    root_dir = current_file.parents[2]
    src_dir = current_file.parents[1]

    # 데이터 경로를 지식 증류용 파일로 변경
    data_path = root_dir / "train_data" / "distillation_data.json"
    model_path = src_dir / "models" / "base_model"
    output_dir = src_dir / "models" / "trained_bert"

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # 2. 데이터 전처리: soft_labels 리스트를 텐서로 변환할 준비
    train_df, val_df = train_test_split(
        df, test_size=0.1, random_state=42, stratify=df["label"]
    )

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    def tokenize_function(examples):
        result = tokenizer(
            examples["text"], truncation=True, padding="max_length", max_length=128
        )
        # Teacher가 준 확률 분포 저장
        result["soft_labels"] = examples["soft_labels"]
        return result

    train_dataset = Dataset.from_pandas(train_df, preserve_index=False).map(
        tokenize_function, batched=True
    )
    val_dataset = Dataset.from_pandas(val_df, preserve_index=False).map(
        tokenize_function, batched=True
    )

    # 텐서 형식 지정
    train_dataset.set_format(
        type="torch", columns=["input_ids", "attention_mask", "label", "soft_labels"]
    )
    val_dataset.set_format(
        type="torch", columns=["input_ids", "attention_mask", "label", "soft_labels"]
    )

    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=7)

    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=10,  # 증류 학습은 조금 더 오래 하는 것이 좋습니다
        per_device_train_batch_size=16,
        learning_rate=5e-5,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        remove_unused_columns=False,
    )

    # 3. 커스텀 증류 트레이너 사용
    trainer = DistillationTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DistillationDataCollator(tokenizer=tokenizer),
        alpha=0.7,  # Teacher의 말을 70% 반영
        temperature=5.0,  # 지식 전이를 위해 확률 분포를 더 부드럽게 설정
    )

    print("🚀 지식 증류 기반 학습을 시작합니다...")
    trainer.train()

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"✨ 증류된 모델 저장 완료: {output_dir}")


if __name__ == "__main__":
    train_bert()
