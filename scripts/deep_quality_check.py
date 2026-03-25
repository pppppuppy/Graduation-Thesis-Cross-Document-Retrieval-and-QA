import json
import re
import os
from collections import Counter

def load_qa_data():
    with open('data/qa_dataset/multihop_qa_v3.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_passages():
    with open('data/passages.json', 'r', encoding='utf-8') as f:
        passages = json.load(f)
    return {p['doc_id']: p for p in passages}

def analyze_question_quality(qa_list):
    print("\n" + "="*60)
    print("一、问题质量分析")
    print("="*60)
    
    issues = {
        'too_short': [],
        'no_question_word': [],
        'too_generic': [],
        'grammar_issues': []
    }
    
    generic_patterns = [
        r'^what is the .* (in|of|for) .*$',
        r'^why is .* important\?$',
        r'^how does .* work\?$',
    ]
    
    for i, qa in enumerate(qa_list):
        q = qa['question']
        
        if len(q.split()) < 8:
            issues['too_short'].append((i, q))
        
        if not re.search(r'^(what|how|why|when|where|which|who)', q.lower()):
            issues['no_question_word'].append((i, q))
        
        for pattern in generic_patterns:
            if re.match(pattern, q.lower()):
                issues['too_generic'].append((i, q))
                break
    
    print(f"\n1. 问题长度分析:")
    lengths = [len(qa['question'].split()) for qa in qa_list]
    print(f"   平均词数: {sum(lengths)/len(lengths):.1f}")
    print(f"   最短: {min(lengths)}, 最长: {max(lengths)}")
    print(f"   短问题(<8词): {len(issues['too_short'])} 条 ({len(issues['too_short'])/len(qa_list)*100:.1f}%)")
    
    print(f"\n2. 疑问词分析:")
    question_words = Counter()
    for qa in qa_list:
        q = qa['question'].lower()
        for word in ['what', 'how', 'why', 'when', 'where', 'which', 'who']:
            if q.startswith(word):
                question_words[word] += 1
    for w, c in question_words.most_common():
        print(f"   {w}: {c} ({c/len(qa_list)*100:.1f}%)")
    
    print(f"\n3. 过于笼统的问题: {len(issues['too_generic'])} 条")
    if issues['too_generic']:
        for i, q in issues['too_generic'][:5]:
            print(f"   - {q[:60]}...")

def analyze_answer_quality(qa_list):
    print("\n" + "="*60)
    print("二、答案质量分析")
    print("="*60)
    
    issues = {
        'too_short': [],
        'too_long': [],
        'no_content_words': []
    }
    
    for i, qa in enumerate(qa_list):
        a = qa['answer']
        words = a.split()
        
        if len(words) < 10:
            issues['too_short'].append((i, a[:50]))
        elif len(words) > 100:
            issues['too_long'].append((i, a[:50]))
        
        content_words = [w for w in words if len(w) > 4]
        if len(content_words) < 5:
            issues['no_content_words'].append((i, a[:50]))
    
    print(f"\n1. 答案长度分析:")
    lengths = [len(qa['answer'].split()) for qa in qa_list]
    print(f"   平均词数: {sum(lengths)/len(lengths):.1f}")
    print(f"   最短: {min(lengths)}, 最长: {max(lengths)}")
    print(f"   短答案(<10词): {len(issues['too_short'])} 条")
    print(f"   长答案(>100词): {len(issues['too_long'])} 条")
    
    print(f"\n2. 内容丰富度分析:")
    content_richness = [len([w for w in qa['answer'].split() if len(w) > 4]) for qa in qa_list]
    print(f"   平均内容词数: {sum(content_richness)/len(content_richness):.1f}")

def analyze_evidence_quality(qa_list, passages_dict):
    print("\n" + "="*60)
    print("三、证据质量分析")
    print("="*60)
    
    issues = {
        'same_doc': [],
        'same_page': [],
        'cross_doc': [],
        'invalid_doc': []
    }
    
    for i, qa in enumerate(qa_list):
        evidence = qa['evidence']
        
        if len(evidence) < 2:
            continue
        
        doc_ids = [e['doc_id'] for e in evidence]
        pages = [e['page'] for e in evidence]
        
        if len(set(doc_ids)) == 1:
            issues['same_doc'].append((i, doc_ids[0], evidence))
        
        if len(set(pages)) == 1:
            issues['same_page'].append((i, pages[0]))
        
        if len(set(doc_ids)) > 1:
            issues['cross_doc'].append(i)
        
        for e in evidence:
            if e['doc_id'] not in passages_dict:
                issues['invalid_doc'].append((i, e['doc_id']))
    
    print(f"\n1. 证据数量分布:")
    evidence_counts = Counter(len(qa['evidence']) for qa in qa_list)
    for count, num in sorted(evidence_counts.items()):
        print(f"   {count}个证据: {num} 条 ({num/len(qa_list)*100:.1f}%)")
    
    print(f"\n2. 跨文档证据: {len(issues['cross_doc'])} 条 ({len(issues['cross_doc'])/len(qa_list)*100:.1f}%)")
    print(f"   同文档证据: {len(issues['same_doc'])} 条")
    
    print(f"\n3. 同页码问题: {len(issues['same_page'])} 条")
    if issues['same_page'][:3]:
        for i, p in issues['same_page'][:3]:
            print(f"   - 页码 {p}")

def analyze_reasoning_type(qa_list):
    print("\n" + "="*60)
    print("四、推理类型分析")
    print("="*60)
    
    type_counts = Counter(qa.get('type', 'unknown') for qa in qa_list)
    print(f"\n推理类型分布:")
    for t, c in type_counts.most_common():
        print(f"   {t}: {c} ({c/len(qa_list)*100:.1f}%)")
    
    sequential = [qa for qa in qa_list if qa.get('type') == 'sequential']
    parallel = [qa for qa in qa_list if qa.get('type') == 'parallel']
    
    print(f"\n串行推理示例 (sequential):")
    for qa in sequential[:2]:
        print(f"   Q: {qa['question'][:50]}...")
        print(f"   Evidence: {[e['doc_id'][:15] for e in qa['evidence']]}")
    
    print(f"\n并行推理示例 (parallel):")
    for qa in parallel[:2]:
        print(f"   Q: {qa['question'][:50]}...")
        print(f"   Evidence: {[e['doc_id'][:15] for e in qa['evidence']]}")

def check_multi_hop_logic(qa_list):
    print("\n" + "="*60)
    print("五、多跳逻辑合理性检测")
    print("="*60)
    
    issues = []
    
    multi_hop_keywords = [
        'therefore', 'thus', 'so', 'hence', 'consequently',
        'as a result', 'because', 'since', 'due to',
        'and then', 'after that', 'first', 'second',
        'combine', 'integrate', 'merge', 'use both'
    ]
    
    for i, qa in enumerate(qa_list):
        q = qa['question'].lower()
        a = qa['answer'].lower()
        
        has_connective = any(kw in q or kw in a for kw in multi_hop_keywords)
        
        if not has_connective and qa.get('type') == 'sequential':
            issues.append((i, qa['question'][:50], "串行推理但缺少连接词"))
    
    print(f"\n潜在问题数: {len(issues)}")
    if issues[:5]:
        for i, q, reason in issues[:5]:
            print(f"   [{i}] {reason}")
            print(f"       {q}...")

def generate_summary(qa_list):
    print("\n" + "="*60)
    print("六、质量总结报告")
    print("="*60)
    
    lengths = [len(qa['question'].split()) for qa in qa_list]
    answer_lengths = [len(qa['answer'].split()) for qa in qa_list]
    evidence_counts = [len(qa['evidence']) for qa in qa_list]
    
    print(f"""
数据集基本信息:
- 总QA数: {len(qa_list)}

问题质量:
- 平均长度: {sum(lengths)/len(lengths):.1f} 词
- 长度范围: {min(lengths)} - {max(lengths)} 词
- 合格(>=8词): {sum(1 for l in lengths if l >= 8)} ({sum(1 for l in lengths if l >= 8)/len(qa_list)*100:.1f}%)

答案质量:
- 平均长度: {sum(answer_lengths)/len(answer_lengths):.1f} 词
- 长度范围: {min(answer_lengths)} - {max(answer_lengths)} 词
- 合格(>=10词): {sum(1 for l in answer_lengths if l >= 10)} ({sum(1 for l in answer_lengths if l >= 10)/len(qa_list)*100:.1f}%)

证据质量:
- 平均证据数: {sum(evidence_counts)/len(evidence_counts):.1f}
- 多证据(>=2): {sum(1 for c in evidence_counts if c >= 2)} ({sum(1 for c in evidence_counts if c >= 2)/len(qa_list)*100:.1f}%)

推理类型:
- 串行(sequential): {sum(1 for qa in qa_list if qa.get('type') == 'sequential')}
- 并行(parallel): {sum(1 for qa in qa_list if qa.get('type') == 'parallel')}
""")
    
    overall_score = (
        (sum(1 for l in lengths if l >= 8) / len(qa_list) * 0.3) +
        (sum(1 for l in answer_lengths if l >= 10) / len(qa_list) * 0.3) +
        (sum(1 for c in evidence_counts if c >= 2) / len(qa_list) * 0.4)
    ) * 100
    
    print(f"总体质量评分: {overall_score:.1f}%")

def main():
    print("="*60)
    print("多跳QA数据集 - 深度质量分析")
    print("="*60)
    
    qa_list = load_qa_data()
    passages_dict = load_passages()
    
    print(f"\n加载数据: {len(qa_list)} 条QA")
    
    analyze_question_quality(qa_list)
    analyze_answer_quality(qa_list)
    analyze_evidence_quality(qa_list, passages_dict)
    analyze_reasoning_type(qa_list)
    check_multi_hop_logic(qa_list)
    generate_summary(qa_list)

if __name__ == "__main__":
    main()
