#!/usr/bin/env python3
"""测试Todo计划模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from todo import TodoPlanner, TaskStatus


def test_basic_workflow():
    """正确流程: start() -> complete()"""
    planner = TodoPlanner()
    id1 = planner.add_task("任务1", depends_on=[])
    id2 = planner.add_task("任务2", depends_on=[id1])
    
    # 正确流程: 先 start() 再 complete()
    planner.start(id1)
    planner.complete(id1)
    assert planner.get_task(id1).status == TaskStatus.COMPLETED
    
    # next() 自动处理 start()
    next_task = planner.next()
    assert next_task.id == id2
    assert planner.get_task(id2).status == TaskStatus.IN_PROGRESS
    print("test_basic_workflow passed")


def test_blocked_tasks():
    """测试依赖阻塞机制"""
    planner = TodoPlanner()
    id1 = planner.add_task("任务1", depends_on=[])
    id2 = planner.add_task("任务2", depends_on=[id1])
    
    # 尝试启动被阻塞的任务2
    planner.start(id2)
    assert planner.get_task(id2).status == TaskStatus.BLOCKED
    print("blocked correctly")
    
    # 完成1后，2自动变为pending
    planner.start(id1)
    planner.complete(id1)
    
    next_task = planner.next()
    assert next_task.id == id2
    print("test_blocked_tasks passed")


def test_summary():
    """测试摘要功能"""
    planner = TodoPlanner()
    planner.add_task("任务1")
    planner.add_task("任务2", depends_on=[1])
    
    summary = planner.get_summary()
    assert summary["total_tasks"] == 2
    assert summary["completed"] == 0
    assert summary["progress_percent"] == 0.0
    print("test_summary passed")


if __name__ == "__main__":
    test_basic_workflow()
    test_blocked_tasks()
    test_summary()
    print("\n✅ 所有测试通过!")
