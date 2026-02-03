import asyncio
import json
import re
from pathlib import Path

from tqdm import tqdm  # tqdm 추가

from configs.llm_manager import LLMManager


async def generate_distillation_data():
    # 데이터 생성용이므로 높은 온도로 설정
    llm = LLMManager.get_instance("gateway", temperature=0.8)

    category_info = {
        "전투": "물리적 충돌, 습격, 살기, 무기 사용.",
        "대화": "상호작용, 직접 화법, 언어적 소통.",
        "흥정": "가격 협상, 보상 밀당, 거래 제안.",
        "탐험": "관찰, 거리 유지, 기척 탐지, 사물 조사. 안전하지 않은 장소에서 미지의 NPC와 예상치 못한 첫 만남",
        "회복": "아이템 즉시 사용, 수치 회복.",
        "휴식": "안전한 수면, 정적인 휴식.",
        "알 수 없음": "배경 묘사, 독백, 날씨.",
    }

    categories = list(category_info.keys())
    dataset = []

    distillation_prompt_template = """
    (기존 프롬프트 내용과 동일...)
    """

    total_categories = len(categories)
    total_attempts = 30
    total_steps = total_categories * total_attempts  # 전체 작업 횟수

    # 1. 단일 진행 바로 통합 (position 설정 제거)
    pbar = tqdm(total=total_steps, desc="📊 데이터 생성 시작")

    for cat_idx, cat in enumerate(categories):
        for attempt in range(1, total_attempts + 1):
            try:
                # 2. 진행 바의 설명을 현재 카테고리와 횟수로 실시간 업데이트
                pbar.set_description(f"🚀 {cat} 생성 중 ({attempt}/{total_attempts})")

                formatted_prompt = distillation_prompt_template.format(
                    category=cat, definition=category_info[cat], label_idx=cat_idx
                )

                response = await llm.ainvoke(formatted_prompt)
                content = response.content.strip()

                match = re.search(r"\[.*\]", content, re.DOTALL)
                if match:
                    items = json.loads(match.group())
                    dataset.extend(items)

                    # 3. 우측 포스트픽스에 누적 개수 표시
                    pbar.set_postfix(total_collected=f"{len(dataset)}개")

                await asyncio.sleep(1)

            except Exception as e:
                # 에러 발생 시 진행 바를 깨뜨리지 않고 위에 로그 출력
                tqdm.write(f"   - ❌ 에러 [{cat} - {attempt}회차]: {str(e)[:50]}")

            finally:
                # 성공하든 실패하든 바를 한 칸 전진
                pbar.update(1)

    pbar.close()  # 작업 완료 후 닫기

    if dataset:
        await save_distillation_dataset(dataset)


async def save_distillation_dataset(dataset):
    # 중복 제거 (Text 기준)
    unique_data = {d["text"]: d for d in dataset}.values()

    file_path = (
        Path(__file__).resolve().parents[2] / "train_data" / "distillation_data.json"
    )
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=2)

    tqdm.write(
        f"\n✨ 총 {len(unique_data)}개의 지식 증류 데이터 저장 완료: {file_path}"
    )


if __name__ == "__main__":
    asyncio.run(generate_distillation_data())
