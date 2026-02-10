import json
import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def get_korean_font():
    """시스템에 설치된 한글 폰트를 찾아 반환합니다."""
    # 윈도우용 맑은 고딕
    font_path = "C:/Windows/Fonts/malgunbd.ttf"  # 맑은 고딕 볼드
    if os.path.exists(font_path):
        return font_path

    # 다른 시스템이나 폰트가 없는 경우를 대비한 대체 폰트 (예: 나눔고딕)
    # 나눔 폰트 설치 경로 예시 (리눅스): /usr/share/fonts/truetype/nanum/NanumGothic.ttf
    # 나눔 폰트 설치 경로 예시 (macOS): /Library/Fonts/NanumGothic.ttf
    fonts = [f.name for f in fm.fontManager.ttflist]
    if "NanumGothic" in fonts:
        for f in fm.fontManager.ttflist:
            if f.name == "NanumGothic":
                return f.fname
    elif "AppleGothic" in fonts:  # macOS
        return "AppleGothic"
    elif "Noto Sans CJK JP" in fonts:  # Google Noto Fonts for CJK
        for f in fm.fontManager.ttflist:
            if f.name == "Noto Sans CJK JP":
                return f.fname

    # 기본 폰트
    return None


def visualize_llm_results(
    results_dir="test/test_results", output_dir="test/test_results_visualize"
):
    """
    LLM 테스트 결과를 시각화하고 이미지 파일로 저장합니다.
    """
    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)

    # 한글 폰트 설정
    font_path = get_korean_font()
    if font_path:
        fm.fontManager.addfont(font_path)
        plt.rcParams["font.family"] = fm.FontProperties(fname=font_path).get_name()
        plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지
        print(f"한글 폰트 설정: {plt.rcParams['font.family']}")
    else:
        print(
            "경고: 적절한 한글 폰트를 찾을 수 없습니다. 그래프에 한글이 깨질 수 있습니다."
        )

    all_results = []
    for filename in os.listdir(results_dir):
        if filename.endswith(".json") and filename.startswith("llm_classification_"):
            filepath = os.path.join(results_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_results.append(data)

    if not all_results:
        print(f"'{results_dir}'에서 시각화할 LLM 테스트 결과를 찾을 수 없습니다.")
        return

    # 필요한 데이터 추출 및 DataFrame 생성
    processed_results = []
    for res in all_results:
        # 파일명에서 timestamp 추출 (예: llm_classification_20260202_174545.json)
        # model_info가 이미 JSON 내부에 있으므로 파일명에서 추출할 필요 없음
        processed_results.append(
            {
                "model_info": res.get("model_info", "unknown_model"),
                "accuracy": res.get("accuracy"),
                "total_time": res.get("total_time"),
                "timestamp": res.get("timestamp"),
            }
        )
    df = pd.DataFrame(processed_results)

    # model_info를 기준으로 중복 제거 (가장 최신 timestamp 결과 사용)
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df.loc[df.groupby("model_info")["timestamp_dt"].idxmax()]
    df = df.drop(columns=["timestamp_dt", "timestamp"])

    if df.empty:
        print("유효한 모델 정보가 없어 시각화할 수 없습니다.")
        return

    # 모델별 고유 색상 팔레트 생성
    num_models = len(df["model_info"].unique())
    base_palette = sns.color_palette(
        "husl", num_models
    )  # Husl은 색상, 채도, 명도가 고르게 분포
    color_map = {
        model: base_palette[i] for i, model in enumerate(df["model_info"].unique())
    }

    # 시각화: Accuracy와 Total Time을 하나의 그래프에 겹쳐서 표시 (이중 Y축)
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Accuracy 막대 그래프 (왼쪽 Y축)
    accuracy_bars = sns.barplot(
        x="model_info",
        y="accuracy",
        data=df,
        ax=ax1,
        palette=[
            sns.set_hls_values(color_map[m], l=0.5, s=0.9) for m in df["model_info"]
        ],  # 진한 색상
        errorbar=None,  # 에러바 없음
        label="정확도",
    )
    ax1.set_xlabel("LLM 모델", fontsize=12)
    ax1.set_ylabel("정확도 (Accuracy)", fontsize=12, color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.set_ylim(0, 1)  # 정확도 범위 0-1

    # Total Time 막대 그래프 (오른쪽 Y축)
    ax2 = ax1.twinx()  # 이중 Y축 설정
    total_time_bars = sns.barplot(
        x="model_info",
        y="total_time",
        data=df,
        ax=ax2,
        palette=[
            sns.set_hls_values(color_map[m], l=0.8, s=0.7) for m in df["model_info"]
        ],  # 연한 색상
        alpha=0.6,  # 투명도 조절
        errorbar=None,  # 에러바 없음
        label="총 소요 시간",
    )
    ax2.set_ylabel("총 소요 시간 (Total Time, 초)", fontsize=12, color="red")
    ax2.tick_params(axis="y", labelcolor="red")
    # ax2.set_ylim(0, df['total_time'].max() * 1.2) # 총 소요 시간 범위

    # 막대 위에 값 표시 (Accuracy)
    for bar in accuracy_bars.patches:
        ax1.annotate(
            f"{bar.get_height():.2f}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
            fontsize=9,
            color="blue",
        )

    # 막대 위에 값 표시 (Total Time)
    for bar in total_time_bars.patches:
        ax2.annotate(
            f"{bar.get_height():.2f}s",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
            fontsize=9,
            color="red",
        )

    plt.title("LLM 모델별 정확도 및 총 소요 시간", fontsize=16)
    fig.tight_layout()  # 레이아웃 자동 조절

    # 범례 합치기
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="upper left")

    output_filepath = os.path.join(output_dir, "llm_performance_comparison.png")
    plt.savefig(output_filepath)
    plt.close()
    print(f"시각화 결과가 '{output_filepath}'에 저장되었습니다.")


if __name__ == "__main__":
    visualize_llm_results()
