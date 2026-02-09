import json
import os
import re
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# Configure font for Korean characters
font_name = font_manager.FontProperties(fname="C:/Windows/Fonts/malgun.ttf").get_name()
rc("font", family=font_name)
plt.rcParams["axes.unicode_minus"] = False

LOG_DIR = "test_logs"
OUTPUT_DIR = "test/visualizations"  # Output directory for plots


def parse_log_files(pattern: str):
    """
    Parses JSON log files matching a given pattern and extracts timestamp and accuracy.
    """
    timestamps = []
    accuracies = []

    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        print(f"Error: Log directory '{LOG_DIR}' not found.")
        return [], []

    log_files = [f for f in os.listdir(LOG_DIR) if re.match(pattern, f)]

    for filename in sorted(
        log_files
    ):  # Sort to process chronologically if filenames contain chronological info
        filepath = os.path.join(LOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Assuming 'timestamp' is a string like "YYYY-MM-DD HH:MM:SS"
                timestamps.append(
                    datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                )
                accuracies.append(data["accuracy"])
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {filepath}")
        except KeyError as e:
            print(f"Missing key '{e}' in {filepath}")
        except Exception as e:
            print(f"An unexpected error occurred while reading {filepath}: {e}")

    # Sort data by timestamp
    if timestamps:
        sorted_data = sorted(zip(timestamps, accuracies))
        timestamps, accuracies = zip(*sorted_data)

    return list(timestamps), list(accuracies)


def plot_accuracy(timestamps, accuracies, title: str, output_filename: str):
    """
    Generates and saves a line plot of accuracy over time.
    """
    if not timestamps:
        print(f"No data to plot for {title}. Skipping plot generation.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, accuracies, marker="o", linestyle="-", color="skyblue")
    plt.title(title)
    plt.xlabel("Timestamp")
    plt.ylabel("Accuracy")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_filepath)
    plt.close()
    print(f"Plot saved to {output_filepath}")


if __name__ == "__main__":
    # Data for BERT with prompt adjustment
    bert_timestamps, bert_accuracies = parse_log_files(r"^bert_.*\.json$")
    plot_accuracy(
        bert_timestamps,
        bert_accuracies,
        "BERT 모델 정확도 변화 (프롬프트 조정)",
        "bert_accuracy_prompt_adjustment.png",
    )

    # Data for KDL BERT with knowledge distillation
    kdl_bert_timestamps, kdl_bert_accuracies = parse_log_files(r"^kdl_bert_.*\.json$")
    plot_accuracy(
        kdl_bert_timestamps,
        kdl_bert_accuracies,
        "KDL BERT 모델 정확도 변화 (지식 증류)",
        "kdl_bert_accuracy_knowledge_distillation.png",
    )

    print("Visualization process complete.")
    print(f"Generated plots are in the '{OUTPUT_DIR}' directory.")
