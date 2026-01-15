import os


def load_sql(domain: str, filename: str):
    """
    특정 도메인의 queries 폴더 내의 SQL 파일을 읽어옵니다.
    경로: src/domains/{domain}/queries/{filename}
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_root = os.path.abspath(os.path.join(current_dir, ".."))
    file_path = os.path.join(src_root, "domains", domain, "queries", filename)

    print(current_dir)
    print(src_root)
    print(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"SQL 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()