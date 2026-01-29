from typing import List


def create_potion_selection_prompt(potion_names: List[str], story: str) -> str:
    """
    플레이어가 사용할 포션을 선택하도록 LLM에 지시하는 프롬프트를 생성합니다.

    Args:
        potion_names: 플레이어가 소유한 포션 이름의 목록입니다.
        story: 현재까지 진행된 스토리 내용입니다.

    Returns:
        LLM에게 전달될 프롬프트 문자열입니다.
    """
    return f"""플레이어는 다음 포션들을 가지고 있습니다: {', '.join(potion_names)}.
최근 이야기: "{story}"
이야기 내용에 따라 플레이어가 사용하려는 포션의 이름을 정확히 하나만 응답해주십시오. 만약 알 수 없다면 "없음"이라고 응답하십시오."""
