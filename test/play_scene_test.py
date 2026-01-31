import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app
from utils.logger import RULE_LEVEL_NUM

# 테스트 데이터 파일 경로
TEST_DATA_DIR = Path(__file__).parent
TEST_REQUEST_FILES = [f for f in TEST_DATA_DIR.glob("play_*.json")]

def setup_module(module):
    if "RULE" not in logging._levelToName.values():
        logging.addLevelName(RULE_LEVEL_NUM, "RULE")


@pytest.fixture(scope="module")
def client():
    from logging.config import dictConfig

    from src.configs.logging_config import LOGGING_CONFIG
    dictConfig(LOGGING_CONFIG)
    
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    "request_file", TEST_REQUEST_FILES, ids=[f.name for f in TEST_REQUEST_FILES]
)
def test_play_scenario_api(client: TestClient, request_file: Path):
    with open(request_file, "r", encoding="utf-8") as f:
        request_data = json.load(f)

    print("\n")
    print("=" * 10 + " 단위 테스트 시작 " + "=" * 10)
    print("☞" + f" [테스트 데이터 위치]: {request_file} ")

    response = client.post("/play/scenario", json=request_data)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "룰 판정 결과를 반환합니다."
    assert "data" in response_json
    assert "session_id" in response_json["data"]
    assert "scenario_id" in response_json["data"]
    assert "phase_type" in response_json["data"]
    assert "reason" in response_json["data"]
    assert "success" in response_json["data"]
    assert isinstance(response_json["data"]["success"], bool)
    assert "suggested" in response_json["data"]
    assert isinstance(response_json["data"]["suggested"], dict)
    assert "diffs" in response_json["data"]["suggested"]
    assert "relations" in response_json["data"]["suggested"]
    assert isinstance(response_json["data"]["suggested"]["diffs"], list)
    assert isinstance(response_json["data"]["suggested"]["relations"], list)
    assert "logs" in response_json["data"]
    assert isinstance(response_json["data"]["logs"], list)

    print("=" * 10 + " 단위 테스트 종료 " + "=" * 10 + "\n\n")
