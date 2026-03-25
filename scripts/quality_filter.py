import json
import os

def quality_filter(qa_dataset):
    filtered = []
    issues = []
    
    for i, qa in enumerate(qa_dataset):
        issue = []
        
        # 1. 检查证据数量（至少2个）
        evidence = qa.get('evidence', [])
        if len(evidence) < 2:
            issue.append("证据数量不足")
        
        # 2. 检查证据是否重复
        evidence_keys = []
        for ev in evidence:
            key = f"{ev.get('doc_id', '')}:{ev.get('page', '')}"
            if key in evidence_keys:
                issue.append("存在重复证据")
                break
            evidence_keys.append(key)
        
        # 3. 检查问题长度
        question = qa.get('question', '')
        if len(question) < 15:
            issue.append("问题太短")
        
        # 4. 检查答案长度
        answer = qa.get('answer', '')
        if len(answer) < 10:
            issue.append("答案太短")
        
        # 5. 检查问题是否多跳
        if "how" in question.lower() or "why" in question.lower() or "what" in question.lower():
            # 简单检查：问题是否包含多个逻辑部分
            if "and" in question.lower() or "?" in question:
                pass  # 可能是多跳
            else:
                # 检查是否需要多个证据
                if len(evidence) == 1:
                    issue.append("可能是单跳问题")
        
        if issue:
            issues.append(f"QA #{i+1}: {', '.join(issue)}")
        else:
            filtered.append(qa)
    
    return filtered, issues

def main():
    input_file = os.path.join(os.path.dirname(__file__), "..", "data", "qa_dataset", "multihop_qa_v4.json")
    output_file = os.path.join(os.path.dirname(__file__), "..", "data", "qa_dataset", "multihop_qa_v4_filtered.json")
    
    # 加载数据
    if not os.path.exists(input_file):
        print(f"错误: 文件不存在 - {input_file}")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"原始QA对数量: {len(data)}")
    
    # 过滤
    filtered, issues = quality_filter(data)
    
    # 保存过滤后的数据
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)
    
    print(f"过滤后QA对数量: {len(filtered)}")
    print(f"发现问题: {len(issues)}")
    
    # 打印前10个问题
    if issues:
        print("\n前10个问题:")
        for i, issue in enumerate(issues[:10]):
            print(f"{i+1}. {issue}")
    
    print(f"\n过滤后的数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
