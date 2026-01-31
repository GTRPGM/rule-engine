import copy
import logging

from uvicorn.logging import DefaultFormatter

from configs.colors import MAGENTA, RESET, YELLOW


class ColorFormatter(DefaultFormatter):
    def format(self, record: logging.LogRecord) -> str:
        # 1. 원본 복사
        record_copy = copy.copy(record)

        # 2. 레벨 이름 자체를 보라색으로 강제 교체 (RULE 레벨일 때)
        if record_copy.levelname == "RULE":
            # uvicorn의 levelprefix를 무시하고 직접 색상을 박습니다.
            record_copy.levelname = f"{MAGENTA}RULE{RESET}"
            # prefix 포맷을 직접 정의 (파이참 터미널 인식률을 높임)
            record_copy.levelprefix = f"{MAGENTA}RULE:{RESET}  "

        # 3. 메시지 본문 내 HINT/RULE 강조
        if isinstance(record_copy.msg, str):
            if "HINT:" in record_copy.msg:
                record_copy.msg = record_copy.msg.replace(
                    "HINT:", f"{YELLOW}HINT:{RESET}"
                )
            if "RULE:" in record_copy.msg:
                record_copy.msg = record_copy.msg.replace(
                    "RULE:", f"{MAGENTA}RULE:{RESET}"
                )

        # 4. 부모 클래스의 format을 호출하여 최종 문자열 생성
        result = super().format(record_copy)

        # 5. 만약 위 과정에서도 색상이 삭제된다면, 최종 결과물에 다시 한번 강제 주입
        if record_copy.levelname == f"{MAGENTA}RULE{RESET}":
            # super().format() 과정에서 색상이 날아가는 것을 방지
            return result.replace("RULE:", f"{MAGENTA}RULE:{RESET}")

        return result
