import copy
import logging

from uvicorn.logging import DefaultFormatter


class ColorHintFormatter(DefaultFormatter):
    """메시지 본문에 'HINT:'가 있으면 노란색으로 강조하는 포매터"""

    # ANSI 색상 코드
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # 원본 레코드 보존을 위해 복사
        record_copy = copy.copy(record)

        # 메시지 내의 'HINT:'를 찾아 색상 코드 삽입
        if isinstance(record_copy.msg, str) and "HINT:" in record_copy.msg:
            record_copy.msg = record_copy.msg.replace(
                "HINT:", f"{self.YELLOW}HINT:{self.RESET}"
            )

        return super().format(record_copy)
