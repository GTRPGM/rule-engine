import logging

RULE_LEVEL_NUM = 25
if "RULE" not in logging._levelToName.values():
    logging.addLevelName(RULE_LEVEL_NUM, "RULE")

# 실제 사용할 로거 객체 가져오기
logger = logging.getLogger("uvicorn")

# RULE 로거 사용 함수
def rule(message, *args, **kwargs):
    logger.log(RULE_LEVEL_NUM, message, *args, **kwargs)

info = logger.info
error = logger.error
warning = logger.warning