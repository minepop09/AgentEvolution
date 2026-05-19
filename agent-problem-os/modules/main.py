#!/usr/bin/env python3
"""
模块入口 - 整合预处理和Todo计划

用法：
    python main.py "用户问题"
"""

import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.preprocess import Preprocessor
from modules.todo import TodoPlanner


def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <问题>")
        print("示例: python main.py '如何用Python实现并发编程？以及如何优化性能？'")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    print("=" * 50)
    print("问题处理 OS - 预处理 + Todo 计划")
    print("=" * 50)
    print()
    
    # Step 1: 预处理
    print("📋 Step 1: 问题预处理")
    print("-" * 30)
    preprocessor = Preprocessor()
    preprocess_result = preprocessor.process(question)
    
    print(f"原始问题: {preprocess_result.original_question}")
    print(f"主要领域: {preprocess_result.primary_domain}")
    print(f"复杂度: {preprocess_result.complexity}")
    print(f"子问题数量: {len(preprocess_result.sub_problems)}")
    print()
    
    for sp in preprocess_result.sub_problems:
        print(f"  [{sp.id}] {sp.text}")
        print(f"      领域: {sp.domain} | 关键词: {', '.join(sp.keywords) if sp.keywords else '无'}")
    print()
    
    # Step 2: 初始化Todo计划
    print("📝 Step 2: 初始化Todo计划")
    print("-" * 30)
    planner = TodoPlanner()
    
    # 根据预处理结果生成任务
    task_ids = {}
    
    # 任务1: 问题预处理
    task_ids['preprocess'] = planner.add_task("问题预处理", depends_on=[])
    
    # 任务2: 置信度评估（根据领域数量）
    if preprocess_result.requires_learning:
        task_ids['confidence'] = planner.add_task(
            "三层知识探测（置信度评估）", 
            depends_on=[task_ids['preprocess']]
        )
        task_ids['learn'] = planner.add_task(
            "问题认知模块（学习领域知识）", 
            depends_on=[task_ids['confidence']]
        )
        task_ids['analysis'] = planner.add_task(
            "问题分析模块（深度分析）", 
            depends_on=[task_ids['learn']]
        )
    else:
        task_ids['analysis'] = planner.add_task(
            "问题分析模块（深度分析）", 
            depends_on=[task_ids['preprocess']]
        )
    
    # 任务3: 工具审核
    task_ids['tool_audit'] = planner.add_task(
        "工具审核模块（SlowMist审计）", 
        depends_on=[task_ids['analysis']]
    )
    
    # 任务4: 工具安装
    task_ids['tool_install'] = planner.add_task(
        "工具安装模块（安装通过审核的工具）", 
        depends_on=[task_ids['tool_audit']]
    )
    
    # 任务5: 执行
    task_ids['execute'] = planner.add_task(
        "执行解决方案", 
        depends_on=[task_ids['tool_install']]
    )
    
    print("生成的任务计划：")
    print(planner.get_status_text())
    print()
    
    # 演示：完成预处理
    print("📤 演示：完成预处理任务")
    print("-" * 30)
    planner.complete(task_ids['preprocess'], result=json.dumps(preprocess_result.to_dict(), ensure_ascii=False))
    print(planner.get_status_text())
    
    return preprocess_result, planner


if __name__ == "__main__":
    main()
