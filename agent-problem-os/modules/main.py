#!/usr/bin/env python3
"""
主入口 - 整合所有7个模块的完整流程

用法：
    python main.py "用户问题"

示例：
    python main.py "如何用Python实现并发编程？以及如何优化性能？"
"""

import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.preprocess import Preprocessor
from modules.cognition import ProblemCognition
from modules.analysis import ProblemAnalysis
from modules.tool_audit import ToolAuditor
from modules.tool_install import ToolInstaller
from modules.todo import TodoPlanner, TaskStatus
from modules.evolution import FeedbackEvolution


def run_problem_os(question: str) -> dict:
    """
    运行完整的问题处理OS流程
    
    Returns:
        dict: 包含所有模块的结果
    """
    results = {
        "question": question,
        "preprocess": None,
        "cognition": None,
        "analysis": None,
        "tool_audit": None,
        "tool_install": None,
        "todo_summary": None
    }
    
    print("=" * 60)
    print("🤖 Agent Problem OS - 完整流程")
    print("=" * 60)
    print(f"\n📝 问题: {question}\n")
    
    # ========== Step 1: 问题预处理 ==========
    print("━" * 40)
    print("Step 1: 问题预处理")
    print("-" * 40)
    preprocessor = Preprocessor()
    pre_result = preprocessor.process(question)
    results["preprocess"] = pre_result.to_dict()
    
    print(f"  领域: {pre_result.primary_domain}")
    print(f"  复杂度: {pre_result.complexity}")
    print(f"  子问题数: {len(pre_result.sub_problems)}")
    for sp in pre_result.sub_problems:
        print(f"    [{sp.id}] {sp.text[:50]}...")
    
    # ========== Step 2: 问题认知（三层探测） ==========
    print("\n" + "━" * 40)
    print("Step 2: 问题认知（三层知识探测）")
    print("-" * 40)
    cognition = ProblemCognition()
    cog_result = cognition.process(pre_result.to_dict())
    results["cognition"] = cog_result.to_dict()
    
    print(f"  决策: {cog_result.decision}")
    print(f"  置信度: {cog_result.confidence.overall}%")
    if cog_result.knowledge_gap:
        print(f"  发现知识盲区: {len(cog_result.knowledge_gap)} 个")
    
    # ========== Step 3: 问题分析 ==========
    print("\n" + "━" * 40)
    print("Step 3: 问题分析")
    print("-" * 40)
    analyzer = ProblemAnalysis()
    analysis_result = analyzer.process(pre_result.to_dict(), cog_result.to_dict())
    results["analysis"] = analysis_result.to_dict()
    
    print(f"  选用方法论: {analysis_result.methodology}")
    print(f"  方法论理由: {analysis_result.methodology_reasoning}")
    print(f"  推荐工具: {', '.join(analysis_result.recommended_tools[:3])}")
    print(f"  总结: {analysis_result.overall_summary}")
    
    # ========== Step 4: 工具审核 ==========
    print("\n" + "━" * 40)
    print("Step 4: 工具审核（SlowMist审计）")
    print("-" * 40)
    auditor = ToolAuditor()
    audit_result = auditor.audit_tools(analysis_result.recommended_tools)
    results["tool_audit"] = audit_result.to_dict()
    
    print(f"  候选工具数: {len(audit_result.candidates)}")
    for c in audit_result.candidates:
        print(f"    - {c.name} (评分: {c.score})")
    print(f"  审计通过: {audit_result.selected_tool or '无'}")
    print(f"  备选工具: {audit_result.fallback_tool or '无'}")
    
    # ========== Step 5: 工具安装 ==========
    print("\n" + "━" * 40)
    print("Step 5: 工具安装")
    print("-" * 40)
    installer = ToolInstaller()
    
    if audit_result.selected_tool:
        install_result = installer.install(
            audit_result.selected_tool,
            fallback=audit_result.fallback_tool
        )
        results["tool_install"] = install_result.to_dict()
        print(f"  安装结果: {install_result.tool_name}")
        print(f"  状态: {install_result.status.value}")
        if install_result.version:
            print(f"  版本: {install_result.version}")
        if install_result.error_message:
            print(f"  错误: {install_result.error_message}")
    else:
        print("  无可安装工具（审核未通过）")
    
    # ========== Step 6: Todo计划 ==========
    print("\n" + "━" * 40)
    print("Step 6: Todo计划")
    print("-" * 40)
    planner = TodoPlanner()
    
    # 生成任务计划
    planner.add_task("问题预处理", depends_on=[])
    t_analysis = planner.add_task("问题分析", depends_on=[])
    t_tool = planner.add_task("工具准备", depends_on=[t_analysis])
    planner.add_task("执行解决方案", depends_on=[t_tool])
    
    summary = planner.get_summary()
    results["todo_summary"] = summary
    
    print(f"  总任务数: {summary['total_tasks']}")
    print(f"  进度: {summary['completed']}/{summary['total_tasks']} ({summary['progress_percent']}%)")
    
    print("\n" + "=" * 60)
    print("✅ 问题处理OS流程完成")
    print("=" * 60)
    
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <问题>")
        print("示例: python main.py '如何用Python实现并发编程？以及如何优化性能？'")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    results = run_problem_os(question)
    
    # 可选：输出JSON格式结果
    if "--json" in sys.argv:
        print("\n" + json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
