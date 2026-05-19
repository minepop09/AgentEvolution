#!/usr/bin/env python3
"""
Todo 计划模块
职责：贯穿全程的任务计划管理

功能：
1. 初始化任务列表
2. 更新任务状态（pending → in_progress → completed / failed）
3. 展示当前进度
4. 序列化/反序列化持久化

用法：
    from 07-todo import TodoPlanner, Task, TaskStatus
    
    planner = TodoPlanner()
    planner.add_task("分析问题", depends_on=[])
    planner.add_task("安装工具", depends_on=[1])
    planner.next()  # 获取下一个可执行任务
    planner.complete(1)  # 标记任务1完成
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from pathlib import Path


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # 等待依赖任务


@dataclass
class Task:
    """任务"""
    id: int
    task: str
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[int] = field(default_factory=list)
    error: Optional[str] = None
    result: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "status": self.status.value,
            "depends_on": self.depends_on,
            "error": self.error,
            "result": self.result
        }


@dataclass
class TodoPlan:
    """Todo计划"""
    session_id: str
    tasks: list[Task] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "tasks": [t.to_dict() for t in self.tasks]
        }


class TodoPlanner:
    """Todo 计划模块"""
    
    def __init__(self, session_id: Optional[str] = None, persist_path: Optional[str] = None):
        """
        初始化 TodoPlanner
        
        Args:
            session_id: 会话ID，默认自动生成
            persist_path: 持久化路径，默认不持久化
        """
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.persist_path = Path(persist_path) if persist_path else None
        self._next_id = 1
        
        # 尝试加载已存在的计划
        if self.persist_path and self.persist_path.exists():
            self._load()
        else:
            self._plan = TodoPlan(session_id=self.session_id)
    
    def _load(self):
        """从文件加载计划"""
        try:
            with open(self.persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._plan = TodoPlan(
                session_id=data['session_id'],
                tasks=[
                    Task(
                        id=t['id'],
                        task=t['task'],
                        status=TaskStatus(t['status']),
                        depends_on=t.get('depends_on', []),
                        error=t.get('error'),
                        result=t.get('result')
                    )
                    for t in data.get('tasks', [])
                ]
            )
            self._next_id = max([t.id for t in self._plan.tasks], default=0) + 1
        except (json.JSONDecodeError, KeyError, ValueError):
            # 加载失败，创建新计划
            self._plan = TodoPlan(session_id=self.session_id)
    
    def save(self):
        """保存计划到文件"""
        if self.persist_path:
            path: Path = self.persist_path
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._plan.to_dict(), f, ensure_ascii=False, indent=2)
    
    @property
    def tasks(self) -> list[Task]:
        return self._plan.tasks
    
    def add_task(self, task: str, depends_on: Optional[list[int]] = None) -> int:
        """
        添加任务
        
        Args:
            task: 任务描述
            depends_on: 依赖的任务ID列表
            
        Returns:
            新任务的ID
        """
        task_id = self._next_id
        self._next_id += 1
        
        new_task = Task(
            id=task_id,
            task=task,
            status=TaskStatus.PENDING,
            depends_on=depends_on or []
        )
        self._plan.tasks.append(new_task)
        
        # 检查并更新被阻塞的任务状态
        self._update_blocked_tasks()
        self.save()
        
        return task_id
    
    def _update_blocked_tasks(self):
        """更新被阻塞的任务状态"""
        for task in self._plan.tasks:
            if task.status == TaskStatus.BLOCKED:
                # 检查依赖是否都完成
                deps = self.get_tasks_by_ids(task.depends_on)
                if all(t.status == TaskStatus.COMPLETED for t in deps):
                    task.status = TaskStatus.PENDING
    
    def get_tasks_by_ids(self, task_ids: list[int]) -> list[Task]:
        """根据ID列表获取任务"""
        return [t for t in self._plan.tasks if t.id in task_ids]
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """根据ID获取任务"""
        for t in self._plan.tasks:
            if t.id == task_id:
                return t
        return None
    
    def _check_can_start(self, task: Task) -> bool:
        """检查任务是否可以开始（依赖都已完成）"""
        if not task.depends_on:
            return True
        deps = self.get_tasks_by_ids(task.depends_on)
        return all(t.status == TaskStatus.COMPLETED for t in deps)
    
    def start(self, task_id: int) -> bool:
        """
        开始任务
        
        Returns:
            是否成功开始（False表示依赖未完成或任务不存在）
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        if task.status not in (TaskStatus.PENDING, TaskStatus.BLOCKED):
            return False
        
        if not self._check_can_start(task):
            task.status = TaskStatus.BLOCKED
            self.save()
            return False
        
        task.status = TaskStatus.IN_PROGRESS
        self.save()
        return True
    
    def complete(self, task_id: int, result: Optional[str] = None, error: Optional[str] = None) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 执行结果
            error: 错误信息
            
        Returns:
            是否成功完成
        """
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.IN_PROGRESS:
            return False
        
        if error:
            task.status = TaskStatus.FAILED
            task.error = error
        else:
            task.status = TaskStatus.COMPLETED
            task.result = result
        
        # 检查并启动被阻塞的任务
        self._update_blocked_tasks()
        self.save()
        return True
    
    def fail(self, task_id: int, error: str) -> bool:
        """标记任务失败"""
        return self.complete(task_id, error=error)
    
    def next(self) -> Optional[Task]:
        """
        获取下一个可执行的任务
        
        Returns:
            下一个任务，如果没有可执行的任务返回None
        """
        for task in self._plan.tasks:
            if task.status == TaskStatus.PENDING and self._check_can_start(task):
                task.status = TaskStatus.IN_PROGRESS
                self.save()
                return task
        return None
    
    def get_summary(self) -> dict:
        """获取计划摘要"""
        total = len(self._plan.tasks)
        completed = sum(1 for t in self._plan.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self._plan.tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in self._plan.tasks if t.status == TaskStatus.PENDING)
        failed = sum(1 for t in self._plan.tasks if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self._plan.tasks if t.status == TaskStatus.BLOCKED)
        
        # 当前正在执行的任务
        current_task = next((t for t in self._plan.tasks if t.status == TaskStatus.IN_PROGRESS), None)
        
        return {
            "session_id": self.session_id,
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "failed": failed,
            "blocked": blocked,
            "progress_percent": round(completed / total * 100, 1) if total > 0 else 0,
            "current_task": current_task.to_dict() if current_task else None,
            "all_completed": completed == total and total > 0,
            "has_failed": failed > 0
        }
    
    def get_status_text(self) -> str:
        """获取状态文本（便于展示）"""
        summary = self.get_summary()
        
        lines = [
            f"📋 Todo计划 [{summary['session_id']}]",
            f"进度: {summary['completed']}/{summary['total_tasks']} ({summary['progress_percent']}%)",
            "",
        ]
        
        if summary['current_task']:
            ct = summary['current_task']
            lines.append(f"🔄 当前: {ct['task']}")
        
        # 显示各类任务
        for task in self._plan.tasks:
            icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌',
                'blocked': '🚫',
            }.get(task.status.value, '❓')
            
            dep_note = f" (等待 {task.depends_on})" if task.depends_on and task.status == TaskStatus.PENDING else ""
            error_note = f" - {task.error}" if task.error else ""
            
            lines.append(f"{icon} [{task.id}] {task.task}{dep_note}{error_note}")
        
        return "\n".join(lines)
    
    def get_json(self) -> str:
        """获取JSON格式的计划"""
        return json.dumps(self._plan.to_dict(), ensure_ascii=False, indent=2)
    
    def get_summary_json(self) -> str:
        """获取JSON格式的摘要"""
        return json.dumps(self.get_summary(), ensure_ascii=False, indent=2)
    
    def reset(self):
        """重置计划"""
        self._plan = TodoPlan(session_id=self.session_id)
        self._next_id = 1
        self.save()


# CLI 入口
if __name__ == "__main__":
    import sys
    
    # 演示用法
    planner = TodoPlanner()
    
    # 添加任务
    planner.add_task("分析问题类型", depends_on=[])
    planner.add_task("学习领域知识", depends_on=[1])
    planner.add_task("深度分析", depends_on=[1])
    planner.add_task("枚举候选工具", depends_on=[3])
    planner.add_task("安装工具", depends_on=[4])
    planner.add_task("执行解决方案", depends_on=[2, 5])
    
    print("=== 初始状态 ===")
    print(planner.get_status_text())
    print()
    
    # 完成第一个任务
    planner.complete(1, result="问题类型：技术类，复杂度：复杂")
    
    print("=== 完成任务1后 ===")
    print(planner.get_status_text())
    print()
    
    # 获取下一个可执行任务
    next_task = planner.next()
    if next_task:
        print(f"下一个任务: {next_task.task} (ID: {next_task.id})")
    
    print()
    print("=== JSON摘要 ===")
    print(planner.get_summary_json())
