import json
import os
import re
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib import font_manager

# 한국어 폰트 설정
font_manager.fontManager.addfont("C:/Windows/Fonts/malgun.ttf")
plt.rc("font", family="Malgun Gothic")
plt.rcParams["axes.unicode_minus"] = False


LOG_DIR = "test/bert_test_logs"
OUTPUT_DIR = "test/bert_test_results_visualize"  # 그래프 출력 디렉토리


def parse_log_files(pattern: str):
    """
    주어진 패턴과 일치하는 JSON 로그 파일을 파싱하여 타임스탬프와 정확도를 추출합니다.
    """
    timestamps = []
    accuracies = []

    if not os.path.exists(LOG_DIR):
        print(f"오류: 로그 디렉토리 '{LOG_DIR}'를 찾을 수 없습니다.")
        return [], []

    log_files = [f for f in os.listdir(LOG_DIR) if re.match(pattern, f)]

    for filename in sorted(log_files):
        filepath = os.path.join(LOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                timestamps.append(
                    datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                )
                accuracies.append(data["accuracy"])
        except json.JSONDecodeError:
            print(f"{filepath}에서 JSON 디코딩 오류가 발생했습니다.")
        except KeyError as e:
            print(f"{filepath}에 '{e}' 키가 없습니다.")
        except Exception as e:
            print(f"{filepath}를 읽는 중 예기치 않은 오류가 발생했습니다: {e}")

    if timestamps:
        sorted_data = sorted(zip(timestamps, accuracies))
        timestamps, accuracies = zip(*sorted_data)

    return list(timestamps), list(accuracies)


def plot_accuracy(timestamps, accuracies, title: str, output_filename: str):
    """
    Seaborn을 사용하여 시간에 따른 정확도 변화를 라인 플롯으로 생성하고 저장합니다.
    """
    if not timestamps:
        print(f"{title}에 대한 플롯 데이터가 없어 생성을 건너뜁니다.")
        return

    df = pd.DataFrame({"Timestamp": timestamps, "Accuracy": accuracies})

    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    ax = sns.lineplot(
        x="Timestamp", y="Accuracy", data=df, marker="o", color="skyblue", linewidth=2.5
    )

    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel("타임스탬프", fontsize=12)
    ax.set_ylabel("정확도", fontsize=12)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout(pad=1.5)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_filepath)
    plt.close()
    print(f"그래프가 {output_filepath}에 저장되었습니다.")


if __name__ == "__main__":
    bert_timestamps, bert_accuracies = parse_log_files(r"^bert_.*\.json$")
    plot_accuracy(
        bert_timestamps,
        bert_accuracies,
        "BERT 모델 정확도 변화 (프롬프트 조정)",
        "bert_accuracy_prompt_adjustment.png",
    )

    kdl_bert_timestamps, kdl_bert_accuracies = parse_log_files(r"^kdl_bert_.*\.json$")
    plot_accuracy(
        kdl_bert_timestamps,
        kdl_bert_accuracies,
        "KDL BERT 모델 정확도 변화 (지식 증류)",
        "kdl_bert_accuracy_knowledge_distillation.png",
    )

    print("시각화 프로세스가 완료되었습니다.")
    print(f"생성된 그래프는 '{OUTPUT_DIR}' 디렉토리에 있습니다.")
