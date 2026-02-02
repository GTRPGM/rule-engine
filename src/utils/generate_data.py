import asyncio
import json
import re
from pathlib import Path

from configs.llm_manager import LLMManager


async def generate_distillation_data():
    llm = LLMManager.get_instance("gateway")

    # 1. 더욱 엄격해진 카테고리 정의
    category_info = {
        "전투": "물리적 충돌, 습격, 살기, 무기 사용.",
        "대화": "상호작용, 직접 화법, 언어적 소통.",
        "흥정": "가격 협상, 보상 밀당, 거래 제안.",
        "탐험": "관찰, 거리 유지, 기척 탐지, 사물 조사.",
        "회복": "아이템 즉시 사용, 수치 회복.",
        "휴식": "안전한 수면, 정적인 휴식.",
        "알 수 없음": "배경 묘사, 독백, 날씨.",
    }

    categories = list(category_info.keys())
    dataset = []

    # 2. 지식 증류를 위한 전용 프롬프트
    # Student 모델이 '왜' 그렇게 분류해야 하는지 배우도록 Rationale을 추가합니다.
    distillation_prompt_template = """
    당신은 TRPG 데이터 분류 AI를 가르치는 수석 마스터입니다.
    작은 AI 모델(Student)이 당신의 판단 능력을 복제할 수 있도록 상세한 학습 데이터를 생성하십시오.

    [대상 카테고리]: {category}
    [판정 정의]: {definition}

    [생성 및 증류 규칙]
    1. **Text**: 해당 카테고리를 대표하는 문장을 생성하십시오.
    2. **Rationale**: 이 문장이 왜 {category}인지, Student 모델이 주목해야 할 핵심 단어나 문맥을 설명하십시오.
    3. **Soft_Labels**: 이 문장이 다른 카테고리와 얼마나 유사한지 확률값(0.0~1.0)을 부여하십시오. 7개 카테고리의 합은 반드시 1.0이어야 합니다.
       (예: 전투적인 대화라면 대화: 0.7, 전투: 0.3 처럼 모호성을 인정하십시오.)
    4. "중요: '돈'이나 '상인'이 등장한다고 해서 무조건 '흥정'은 아닙니다. 단순히 상황을 설명하거나 대화를 나누는 중이라면 '대화'로 분류하도록 soft_labels를 정교하게 짜십시오. 예: '상인이 웃으며 인사합니다' -> 대화: 0.9, 흥정: 0.1"

    [형식 가이드]
    - 반드시 아래 JSON 배열 형식으로만 응답하십시오:
    [
      {{
        "text": "문장 내용",
        "label": {label_idx},
        "rationale": "판단 근거 설명",
        "soft_labels": [전투값, 대화값, 흥정값, 탐험값, 회복값, 휴식값, 알수없음값]
      }}
    ]
    - 서로 다른 문장으로 20개씩 생성하십시오.
    """

    for idx, cat in enumerate(categories):
        print(f"🚀 {cat} 지식 증류 데이터 생성 중...")

        for attempt in range(1, 3):  # 효율을 위해 2회 반복 (총 40개 내외)
            try:
                formatted_prompt = distillation_prompt_template.format(
                    category=cat, definition=category_info[cat], label_idx=idx
                )

                response = await llm.ainvoke(formatted_prompt)
                content = response.content.strip()

                # JSON 추출 및 파싱
                match = re.search(r"\[.*\]", content, re.DOTALL)
                if match:
                    items = json.loads(match.group())
                    dataset.extend(items)
                    print(f"   - {len(items)}개 증류 완료")

                await asyncio.sleep(1)  # Rate Limit 방지

            except Exception as e:
                print(f"   - ❌ 에러: {repr(e)}")

    if dataset:
        await save_distillation_dataset(dataset)


async def save_distillation_dataset(dataset):
    # 중복 제거
    unique_data = {d["text"]: d for d in dataset}.values()

    file_path = (
        Path(__file__).resolve().parents[2] / "train_data" / "distillation_data.json"
    )
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=2)

    print(f"\n✨ 총 {len(unique_data)}개의 지식 증류 데이터 저장 완료: {file_path}")


if __name__ == "__main__":
    asyncio.run(generate_distillation_data())
