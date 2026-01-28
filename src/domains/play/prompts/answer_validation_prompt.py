def generate_answer_validation_prompt(correct_answer: str, user_guess: str) -> str:
    """정답 검증을 위한 LLM 프롬프트를 생성합니다."""
    return (
        f"수수께끼 정답이 '{correct_answer}'일 때, "
        f"사용자가 '{user_guess}'라고 답했습니다. "
        f"의미상 정답인가요? 오직 Y 또는 N으로만 대답하세요."
    )
