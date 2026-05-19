#!/usr/bin/env python3
"""
反馈进化模块
职责：根据历史表现自动调整策略权重

流程：
1. 记录每次问题处理的结果
2. 用户/Agent 打分（1-5星）
3. 自动分析哪些方法论+工具组合效果好
4. 调整 config.yaml 中的权重配置

进化维度：
- 方法论选择权重（按领域）
- 工具评分权重
- 复杂度预估准确度

用法：
    from evolution import FeedbackEvolution, Rating

    evolution = FeedbackEvolution()
    evolution.record(problem_os_result)
    evolution.rate(quality=5, notes="方法论选得很准")
    evolution.adapt()  # 分析并更新权重
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
from collections import defaultdict


@dataclass
class Rating:
    """评分记录"""
    stars: int              # 1-5星
    notes: str = ""        # 可选备注
    timestamp: str = ""


@dataclass
class ProcessingRecord:
    """单次处理记录"""
    question: str
    domain: str
    complexity: str
    methodology: str
    tools_selected: list[str]
    tool_audit_passed: bool
    rating: Optional[Rating] = None
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "domain": self.domain,
            "complexity": self.complexity,
            "methodology": self.methodology,
            "tools_selected": self.tools_selected,
            "tool_audit_passed": self.tool_audit_passed,
            "rating": asdict(self.rating) if self.rating else None,
            "timestamp": self.timestamp
        }


@dataclass
class DomainStats:
    """领域统计"""
    total: int = 0
    good_ratings: int = 0  # >= 4星
    method_usage: dict = field(default_factory=dict)  # 方法论→次数
    method_good: dict = field(default_factory=dict)   # 方法论→好次数

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdaptedWeights:
    """调整后的权重"""
    methodology: dict = field(default_factory=dict)   # 领域→{方法论→权重}
    tool_weights: dict = field(default_factory=dict)  # 工具→权重
    complexity_threshold: dict = field(default_factory=dict)  # 领域→阈值

    def to_dict(self) -> dict:
        return asdict(self)


class FeedbackEvolution:
    """
    反馈进化引擎

    工作流程：
    1. record() - 记录每次处理
    2. rate() - 收集评分
    3. adapt() - 分析并更新权重
    """

    # 评分阈值：>=4星算好
    GOOD_THRESHOLD = 4
    # 最小样本量才触发进化
    MIN_SAMPLES = 3

    def __init__(self, data_path: str = "~/.hermes/agent-problem-os/evolution_data.json"):
        self.data_path = Path(data_path).expanduser()
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[ProcessingRecord] = []
        self.weights = AdaptedWeights()
        self._load()

    def _load(self):
        """加载历史数据"""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = [self._dict_to_record(r) for r in data.get("records", [])]
                    self.weights = AdaptedWeights(**data.get("weights", {}))
            except (json.JSONDecodeError, KeyError):
                self.records = []

    def _save(self):
        """保存数据"""
        data = {
            "records": [r.to_dict() for r in self.records],
            "weights": self.weights.to_dict(),
            "last_updated": datetime.now().isoformat()
        }
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _dict_to_record(self, d: dict) -> ProcessingRecord:
        """字典转记录"""
        rating = None
        if d.get("rating"):
            rating = Rating(**d["rating"])
        return ProcessingRecord(
            question=d["question"],
            domain=d["domain"],
            complexity=d["complexity"],
            methodology=d["methodology"],
            tools_selected=d["tools_selected"],
            tool_audit_passed=d["tool_audit_passed"],
            rating=rating,
            timestamp=d.get("timestamp", "")
        )

    def record(self, question: str, domain: str, complexity: str,
               methodology: str, tools_selected: list[str],
               tool_audit_passed: bool):
        """
        记录一次处理

        Args:
            question: 用户问题
            domain: 领域分类
            complexity: 复杂度等级
            methodology: 选用的方法论
            tools_selected: 选中的工具列表
            tool_audit_passed: 工具审核是否通过
        """
        record = ProcessingRecord(
            question=question,
            domain=domain,
            complexity=complexity,
            methodology=methodology,
            tools_selected=tools_selected,
            tool_audit_passed=tool_audit_passed,
            timestamp=datetime.now().isoformat()
        )
        self.records.append(record)
        self._save()
        return len(self.records)  # 返回记录ID

    def rate(self, record_id: int, stars: int, notes: str = ""):
        """
        对一次处理评分

        Args:
            record_id: 记录ID（从1开始）
            stars: 1-5星
            notes: 可选备注
        """
        if record_id < 1 or record_id > len(self.records):
            raise ValueError(f"Invalid record_id: {record_id}")

        stars = max(1, min(5, stars))  # 限制在1-5
        self.records[record_id - 1].rating = Rating(
            stars=stars,
            notes=notes,
            timestamp=datetime.now().isoformat()
        )
        self._save()

    def _analyze_domain(self, domain: str) -> DomainStats:
        """分析某个领域的历史表现"""
        domain_records = [r for r in self.records if r.domain == domain]
        rated = [r for r in domain_records if r.rating is not None]

        stats = DomainStats(total=len(rated))

        if not rated:
            return stats

        stats.good_ratings = len([r for r in rated if r.rating.stars >= self.GOOD_THRESHOLD])

        # 统计各方法论表现
        for r in rated:
            method = r.methodology
            stats.method_usage[method] = stats.method_usage.get(method, 0) + 1
            if r.rating.stars >= self.GOOD_THRESHOLD:
                stats.method_good[method] = stats.method_good.get(method, 0) + 1

        return stats

    def _calculate_methodology_weights(self, domain: str) -> dict[str, float]:
        """计算方法论权重"""
        stats = self._analyze_domain(domain)
        if stats.total < self.MIN_SAMPLES:
            return {}

        weights = {}
        for method, usage in stats.method_usage.items():
            good_count = stats.method_good.get(method, 0)
            success_rate = good_count / usage if usage > 0 else 0
            # 权重 = 成功率 * 使用次数因子（用过多次且成功率高的权重更高）
            weights[method] = round(success_rate * (1 + 0.1 * (usage - 1)), 3)

        return weights

    def _calculate_tool_weights(self) -> dict[str, float]:
        """计算机器评分权重"""
        tool_stats = defaultdict(lambda: {"total": 0, "good": 0})

        for r in self.records:
            if not r.rating:
                continue
            for tool in r.tools_selected:
                tool_stats[tool]["total"] += 1
                if r.rating.stars >= self.GOOD_THRESHOLD:
                    tool_stats[tool]["good"] += 1

        weights = {}
        for tool, stats in tool_stats.items():
            if stats["total"] >= 2:  # 至少用过2次
                success_rate = stats["good"] / stats["total"]
                weights[tool] = round(success_rate, 3)

        return weights

    def adapt(self) -> dict:
        """
        分析历史数据，生成调整建议

        Returns:
            dict: 包含调整建议的字典
        """
        suggestions = {
            "methodology_weights": {},
            "tool_weights": {},
            "summary": ""
        }

        # 分析每个有数据的领域
        domains = set(r.domain for r in self.records if r.rating)
        if not domains:
            suggestions["summary"] = "暂无评分数据，无法进化"
            return suggestions

        # 方法论权重
        for domain in domains:
            method_weights = self._calculate_methodology_weights(domain)
            if method_weights:
                suggestions["methodology_weights"][domain] = method_weights

        # 工具权重
        tool_weights = self._calculate_tool_weights()
        if tool_weights:
            suggestions["tool_weights"] = tool_weights

        # 生成总结
        rated_count = len([r for r in self.records if r.rating])
        suggestions["summary"] = (
            f"分析了 {rated_count} 条评分记录，"
            f"涵盖 {len(domains)} 个领域"
        )

        return suggestions

    def apply_weights(self, suggestions: dict):
        """
        将建议应用到权重对象并保存
        """
        if suggestions.get("methodology_weights"):
            self.weights.methodology = suggestions["methodology_weights"]
        if suggestions.get("tool_weights"):
            self.weights.tool_weights = suggestions["tool_weights"]
        self._save()

    def get_best_methodology(self, domain: str) -> Optional[str]:
        """
        获取某个领域目前表现最好的方法论

        Returns:
            方法论名称，或 None（数据不足）
        """
        suggestions = self.adapt()
        domain_weights = suggestions.get("methodology_weights", {}).get(domain, {})
        if not domain_weights:
            return None
        return max(domain_weights, key=domain_weights.get)

    def get_report(self) -> str:
        """生成进化报告"""
        rated = [r for r in self.records if r.rating]
        if not rated:
            return "暂无评分数据。处理完问题后用 evolution.rate() 打分"

        total = len(rated)
        good = len([r for r in rated if r.rating.stars >= 4])
        avg_stars = sum(r.rating.stars for r in rated) / total

        lines = [
            "=" * 50,
            "📊 反馈进化报告",
            "=" * 50,
            f"总评分记录: {total}",
            f"好评分(>=4星): {good} ({good/total*100:.0f}%)",
            f"平均评分: {avg_stars:.1f}星",
            ""
        ]

        # 各领域表现
        domains = set(r.domain for r in rated)
        if domains:
            lines.append("各领域方法论表现：")
            for domain in sorted(domains):
                best = self.get_best_methodology(domain)
                if best:
                    lines.append(f"  {domain}: {best}")
            lines.append("")

        # 工具表现
        suggestions = self.adapt()
        tool_weights = suggestions.get("tool_weights", {})
        if tool_weights:
            lines.append("工具权重更新：")
            for tool, weight in sorted(tool_weights.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"  {tool}: {weight}")
            lines.append("")

        lines.append(f"数据文件: {self.data_path}")
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 50)
    print("反馈进化模块 - 测试")
    print("=" * 50)

    # 创建实例
    evo = FeedbackEvolution("~/tmp/evolution_test.json")

    # 模拟记录几次处理
    print("\n📝 模拟记录3次处理...")
    evo.record(
        question="如何优化Python并发性能？",
        domain="技术类",
        complexity="复杂",
        methodology="性能剖析法",
        tools_selected=["py-spy", "perf"],
        tool_audit_passed=True
    )
    evo.record(
        question="如何设计微服务架构？",
        domain="技术类",
        complexity="超复杂",
        methodology="架构探索法",
        tools_selected=["Docker", "GitHub CLI"],
        tool_audit_passed=True
    )
    evo.record(
        question="Python异步编程怎么做？",
        domain="技术类",
        complexity="中等",
        methodology="结构化调试法",
        tools_selected=["代码编辑器"],
        tool_audit_passed=True
    )

    # 模拟评分
    print("⭐ 模拟评分...")
    evo.rate(1, stars=5, notes="方法论很准")
    evo.rate(2, stars=4, notes="工具有效")
    evo.rate(3, stars=3, notes="方法论不太匹配")

    # 分析进化
    print("\n🧬 运行自适应分析...")
    suggestions = evo.adapt()
    print(f"\n分析结果: {suggestions['summary']}")
    print(f"\n方法论权重: {suggestions.get('methodology_weights', {})}")
    print(f"工具权重: {suggestions.get('tool_weights', {})}")

    # 应用权重
    evo.apply_weights(suggestions)

    # 生成报告
    print("\n" + evo.get_report())
