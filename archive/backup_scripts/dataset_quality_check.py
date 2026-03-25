import json
import random
import statistics

DATASET_PATH = "./data/qa_dataset/logical_multihop_qa.json"
REPORT_PATH = "./data/qa_dataset/dataset_report.txt"
SAMPLE_PATH = "./data/qa_dataset/manual_check_samples.json"


def basic_quality_check(qa):
    """基础质量检查"""

    q = qa.get("question", "")
    a = qa.get("answer", "")
    evidence = qa.get("evidence", [])

    if len(q.split()) < 5:
        return False

    if len(a.split()) < 2:
        return False

    if len(evidence) < 1:
        return False

    return True


def multihop_check(qa):
    """是否为 multi-hop"""

    return len(qa["evidence"]) >= 2


def compute_statistics(dataset):

    question_lengths = []
    answer_lengths = []
    evidence_counts = []

    for qa in dataset:

        question_lengths.append(len(qa["question"].split()))
        answer_lengths.append(len(qa["answer"].split()))
        evidence_counts.append(len(qa["evidence"]))

    stats = {
        "avg_question_len": statistics.mean(question_lengths),
        "avg_answer_len": statistics.mean(answer_lengths),
        "avg_evidence_num": statistics.mean(evidence_counts)
    }

    return stats


def main():

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total = len(dataset)

    basic_pass = 0
    multihop = 0

    for qa in dataset:

        if basic_quality_check(qa):
            basic_pass += 1

        if multihop_check(qa):
            multihop += 1

    stats = compute_statistics(dataset)

    basic_ratio = basic_pass / total
    multihop_ratio = multihop / total

    report = f"""
Dataset Quality Report
======================

Total QA pairs: {total}

Basic quality pass ratio: {basic_ratio:.2f}

Multi-hop ratio: {multihop_ratio:.2f}

Average question length: {stats["avg_question_len"]:.2f} words
Average answer length: {stats["avg_answer_len"]:.2f} words
Average evidence passages: {stats["avg_evidence_num"]:.2f}

"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)

    # 抽样人工检查
    sample_size = min(50, total)
    samples = random.sample(dataset, sample_size)

    with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    print(f"Manual check samples saved to: {SAMPLE_PATH}")


if __name__ == "__main__":
    main()