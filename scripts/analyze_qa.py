import json

with open('data/qa_dataset/multihop_qa_v3.json', 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

print('=' * 60)
print('QA 质量分析报告')
print('=' * 60)

print(f'\n总 QA 数: {len(qa_data)}')

# 1. 问题长度
question_lengths = [len(q['question'].split()) for q in qa_data]
print(f'\n[1] 问题词数统计')
print(f'    平均: {sum(question_lengths)/len(question_lengths):.1f}')
print(f'    最短: {min(question_lengths)}')
print(f'    最长: {max(question_lengths)}')

# 2. 答案长度
answer_lengths = [len(q['answer'].split()) for q in qa_data]
print(f'\n[2] 答案词数统计')
print(f'    平均: {sum(answer_lengths)/len(answer_lengths):.1f}')
print(f'    最短: {min(answer_lengths)}')
print(f'    最长: {max(answer_lengths)}')

# 3. 证据数量
evidence_counts = [len(q['evidence']) for q in qa_data]
print(f'\n[3] 证据数量统计')
print(f'    平均: {sum(evidence_counts)/len(evidence_counts):.1f}')
print(f'    1个证据: {evidence_counts.count(1)}')
print(f'    2个证据: {evidence_counts.count(2)}')
print(f'    3+个证据: {sum(1 for c in evidence_counts if c >= 3)}')

# 4. 推理类型
types = [q.get('type', 'unknown') for q in qa_data]
print(f'\n[4] 推理类型')
print(f'    sequential: {types.count("sequential")}')
print(f'    parallel: {types.count("parallel")}')

# 5. 检查 evidence 中的 doc_id 是否有效
print(f'\n[5] Evidence 有效性')
with open('data/passages.json', 'r', encoding='utf-8') as f:
    passages = json.load(f)
valid_doc_ids = set(p['doc_id'] for p in passages)

invalid_count = 0
for qa in qa_data:
    for ev in qa['evidence']:
        if ev['doc_id'] not in valid_doc_ids:
            invalid_count += 1
            print(f'    无效 doc_id: {ev["doc_id"]}')
            break

if invalid_count == 0:
    print(f'    所有 doc_id 有效!')

# 6. 示例展示
print(f'\n[6] 示例展示')
for i in range(3):
    qa = qa_data[i]
    print(f'\n--- 示例 {i+1} ---')
    print(f'Q: {qa["question"][:60]}...')
    print(f'A: {qa["answer"][:60]}...')
    print(f'Evidence: {qa["evidence"]}')
    print(f'Type: {qa.get("type", "N/A")}')
