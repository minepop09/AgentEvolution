#!/usr/bin/env python3
"""
工具审核模块
职责：找最优工具，并通过 SlowMist Agent Security 进行安全审计

流程：
1. 枚举候选工具
2. 获取网络综合评分
3. 取评分前2
4. SlowMist 安全审计
5. 审计结果处理：Low不装，Pass则安装

用法：
    from tool_audit import ToolAuditor, AuditResult
    
    auditor = ToolAuditor()
    result = auditor.audit_tools(["工具A", "工具B"])
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class AuditVerdict(Enum):
    """审计裁决"""
    PASS = "Pass"      # 通过
    LOW = "Low"        # 低风险，可安装
    MEDIUM = "Medium"  # 中风险，谨慎安装
    HIGH = "High"      # 高风险，不安装
    CRITICAL = "Critical"  # 严重风险，不安装


@dataclass
class ToolCandidate:
    """候选工具"""
    name: str
    score: float = 0.0          # 网络综合评分 0-10
    description: str = ""
    category: str = ""          # 分类
    install_command: str = ""    # 安装命令
    website: str = ""


@dataclass
class AuditResult:
    """审计结果"""
    tool_name: str
    verdict: AuditVerdict
    issues: list[str] = field(default_factory=list)
    score: float = 0.0
    recommendation: str = ""
    raw_report: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "verdict": self.verdict.value,
            "issues": self.issues,
            "score": self.score,
            "recommendation": self.recommendation,
            "raw_report": self.raw_report
        }


@dataclass
class ToolAuditSummary:
    """工具审核总结"""
    candidates: list[ToolCandidate]
    audit_results: list[AuditResult]
    selected_tool: Optional[str] = None
    fallback_tool: Optional[str] = None
    all_passed: bool = False

    def to_dict(self) -> dict:
        return {
            "candidates": [
                {"name": c.name, "score": c.score} for c in self.candidates
            ],
            "audit_results": [r.to_dict() for r in self.audit_results],
            "selected_tool": self.selected_tool,
            "fallback_tool": self.fallback_tool,
            "all_passed": self.all_passed
        }


class SlowMistSimulator:
    """
    SlowMist Agent Security 审计模拟器
    
    实际使用时，替换为真实调用 slowmist-agent-security skill
    这里模拟审计结果
    """

    # 模拟的风险评分规则
    RISK_PATTERNS = {
        "github": {"risk": "LOW", "issues": []},
        "npm": {"risk": "LOW", "issues": []},
        "pip": {"risk": "LOW", "issues": []},
        "docker": {"risk": "LOW", "issues": []},
        "curl": {"risk": "LOW", "issues": []},
        "wget": {"risk": "LOW", "issues": []},
        "unknown": {"risk": "MEDIUM", "issues": ["无法验证来源"]},
    }

    def audit(self, tool_name: str, install_command: str = "") -> dict:
        """
        执行审计
        
        Returns: 模拟的审计报告
        """
        tool_lower = tool_name.lower()
        install_lower = install_command.lower()

        # 匹配风险模式
        detected_risk = "MEDIUM"
        detected_issues = []

        for pattern, result in self.RISK_PATTERNS.items():
            if pattern in tool_lower or pattern in install_lower:
                detected_risk = result["risk"]
                detected_issues = result["issues"]
                break

        # 模拟：名称中包含某些关键词会触发更高风险
        high_risk_keywords = ["root", "sudo", "eval", "exec", "__import__"]
        if any(kw in tool_lower for kw in high_risk_keywords):
            detected_risk = "HIGH"
            detected_issues.append("包含潜在危险操作")

        # 模拟：安装命令为空
        if not install_command:
            detected_risk = "MEDIUM"
            detected_issues.append("无安装命令，无法验证安全性")

        return {
            "tool_name": tool_name,
            "risk_level": detected_risk,
            "issues": detected_issues,
            "recommendation": "安装" if detected_risk in ["LOW", "MEDIUM"] else "不安装"
        }


class ToolAuditor:
    """工具审核模块"""

    MAX_CANDIDATES = 2  # 最多审核前N个候选

    def __init__(self):
        self.slowmist = SlowMistSimulator()

    def _get_tool_candidates(self, tool_names: list[str]) -> list[ToolCandidate]:
        """
        模拟获取工具候选列表及其评分
        
        实际使用时，接入真实的工具搜索API
        """
        # 模拟工具数据库
        TOOL_DB = {
            "代码编辑器": [
                {"name": "VSCode", "score": 9.5, "install": "winget install VSCode"},
                {"name": "Cursor", "score": 9.2, "install": "brew install cursor"},
                {"name": "JetBrains", "score": 9.0, "install": "brew install intellij-idea"},
            ],
            "搜索引擎": [
                {"name": "Google", "score": 9.8, "install": ""},
                {"name": "DuckDuckGo", "score": 9.0, "install": ""},
            ],
            "性能分析": [
                {"name": "py-spy", "score": 8.5, "install": "pip install py-spy"},
                {"name": "perf", "score": 8.0, "install": "apt install linux-perf"},
                {"name": "Valgrind", "score": 7.5, "install": "apt install valgrind"},
            ],
            "API文档": [
                {"name": "Postman", "score": 9.3, "install": "brew install postman"},
                {"name": "Insomnia", "score": 8.8, "install": "brew install insomnia"},
            ],
            "git": [
                {"name": "GitHub CLI", "score": 9.0, "install": "brew install gh"},
                {"name": "Git", "score": 9.5, "install": "apt install git"},
            ],
            "docker": [
                {"name": "Docker Desktop", "score": 9.2, "install": "brew install --cask docker"},
                {"name": "Rancher Desktop", "score": 8.5, "install": "brew install rancher-desktop"},
            ],
        }

        candidates = []
        
        for tool_name in tool_names:
            # 查找匹配的工具
            for category, tools in TOOL_DB.items():
                for t in tools:
                    if tool_name.lower() in t["name"].lower():
                        candidates.append(ToolCandidate(
                            name=t["name"],
                            score=t["score"],
                            install_command=t["install"],
                            category=category
                        ))
                        break
        
        # 如果没找到匹配，按名称创建占位符
        found_names = {c.name for c in candidates}
        for tool_name in tool_names:
            if tool_name not in found_names:
                candidates.append(ToolCandidate(
                    name=tool_name,
                    score=7.0,  # 默认中等评分
                    install_command=f"pip install {tool_name}" if "python" in tool_name.lower() else "",
                    category="其他"
                ))

        # 按评分排序，取前2
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:self.MAX_CANDIDATES]

    def _slowmist_audit(self, candidate: ToolCandidate) -> AuditResult:
        """
        调用 SlowMist 进行安全审计
        
        实际使用时调用 slowmist-agent-security skill
        """
        report = self.slowmist.audit(candidate.name, candidate.install_command)

        # 转换裁决
        risk_to_verdict = {
            "LOW": AuditVerdict.PASS,
            "MEDIUM": AuditVerdict.MEDIUM,
            "HIGH": AuditVerdict.HIGH,
            "CRITICAL": AuditVerdict.CRITICAL
        }
        verdict = risk_to_verdict.get(report["risk_level"], AuditVerdict.MEDIUM)

        return AuditResult(
            tool_name=candidate.name,
            verdict=verdict,
            issues=report.get("issues", []),
            score=candidate.score,
            recommendation=report.get("recommendation", ""),
            raw_report=report
        )

    def audit_tools(self, tool_names: list[str]) -> ToolAuditSummary:
        """
        审核工具列表
        
        Args:
            tool_names: 需要审核的工具名称列表
            
        Returns:
            ToolAuditSummary: 审核总结
        """
        # 1. 枚举候选工具并获取评分
        candidates = self._get_tool_candidates(tool_names)

        # 2. 对每个候选进行 SlowMist 审计
        audit_results = []
        selected = None
        fallback = None

        for candidate in candidates:
            result = self._slowmist_audit(candidate)
            audit_results.append(result)

            # 选择通过审核的工具
            if result.verdict in [AuditVerdict.PASS, AuditVerdict.MEDIUM]:
                if not selected:
                    selected = candidate.name
                elif not fallback:
                    fallback = candidate.name

        summary = ToolAuditSummary(
            candidates=candidates,
            audit_results=audit_results,
            selected_tool=selected,
            fallback_tool=fallback,
            all_passed=selected is not None
        )

        return summary

    def run(self, tools_json: str) -> str:
        """
        运行工具审核（JSON格式）
        """
        tools = json.loads(tools_json)
        result = self.audit_tools(tools)
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("=" * 50)
    print("工具审核模块 - SlowMist 安全审计")
    print("=" * 50)
    
    auditor = ToolAuditor()
    
    # 审核工具列表
    tools = ["代码编辑器", "性能分析", "git", "docker"]
    result = auditor.audit_tools(tools)
    
    print(f"\n🔍 审核了 {len(result.candidates)} 个候选工具")
    print(f"\n候选工具（按评分）：")
    for c in result.candidates:
        print(f"   {c.name}: {c.score}")
    
    print(f"\n审计结果：")
    for r in result.audit_results:
        verdict_icon = "✅" if r.verdict.value == "Pass" else "⚠️" if r.verdict.value == "Medium" else "❌"
        print(f"   {verdict_icon} {r.tool_name}: {r.verdict.value}")
        if r.issues:
            for issue in r.issues:
                print(f"      - {issue}")
    
    print(f"\n选择：")
    print(f"   主工具: {result.selected_tool or '无'}")
    print(f"   备选: {result.fallback_tool or '无'}")
