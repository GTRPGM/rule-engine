import os


def load_prompt(domain: str, filename: str) -> str:
    """
    특정 도메인의 prompts 폴더 내의 파일을 읽어옵니다.
    경로: src/domains/{domain}/prompts/{filename}
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_root = os.path.abspath(os.path.join(current_dir, ".."))
    file_path = os.path.join(src_root, "domains", domain, "prompts", filename)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
