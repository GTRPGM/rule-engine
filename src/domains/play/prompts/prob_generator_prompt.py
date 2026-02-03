import json


def generate_quiz_prompt(theme: str, info: list) -> str:
    """
    동굴 탐험대 세계관과 관련된 퀴즈를 생성합니다.
    """
    info_json = json.dumps(info, ensure_ascii=False, indent=2)
    return f"""
당신은 동굴 탐험대 세계관 기반의 GTRPGM 게임 퀴즈 마스터입니다.
'{theme}'에 대한 다음 정보를 바탕으로 퀴즈 문제를 생성해야 합니다.
퀴즈는 게임과 관련되어야 합니다.
정보는 JSON 형식으로 제공됩니다.

정보:
{info_json}

이 정보를 바탕으로 퀴즈를 만드세요.
응답은 `RiddleData` Pydantic 모델로 파싱할 수 있는 JSON 형식이어야 합니다.
'riddle' 필드에는 퀴즈 질문이 포함되어야 합니다.

예시 응답 형식:
{{
  "riddle": "시작 마을의 대장장이 이름은 무엇인가요?",
  "answer": "존",
  "hint": "그는 마을의 유일한 대장장이입니다.",
  "explanation": "존은 뛰어난 기술로 알려진 시작 마을의 대장장이입니다."
}}
"""
