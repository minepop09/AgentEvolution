#!/usr/bin/env python3
"""
问题预处理模块
职责：拆解问题，判断类型和复杂度

输入：用户原始问题（文本）
输出：结构化的问题分析结果

用法：
    from 01-preprocess import Preprocessor
    preprocessor = Preprocessor()
    result = preprocessor.process("用户问题")
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SubProblem:
    """子问题"""
    id: int
    text: str
    domain: str  # 技术类/产品类/分析类/创意类
    keywords: list[str] = field(default_factory=list)


@dataclass
class PreprocessResult:
    """预处理结果"""
    original_question: str
    sub_problems: list[SubProblem]
    primary_domain: str
    complexity: str  # 简单/中等/复杂/超复杂
    requires_learning: Optional[bool] = None  # 初判，待三层探测后确认
    
    def to_dict(self) -> dict:
        return {
            "original_question": self.original_question,
            "sub_problems": [
                {
                    "id": sp.id,
                    "text": sp.text,
                    "domain": sp.domain,
                    "keywords": sp.keywords
                }
                for sp in self.sub_problems
            ],
            "primary_domain": self.primary_domain,
            "complexity": self.complexity,
            "requires_learning": self.requires_learning
        }


class Preprocessor:
    """问题预处理模块"""
    
    # 领域关键词映射
    DOMAIN_KEYWORDS = {
        "技术类": {
            "编程": ["代码", "程序", "函数", "算法", "debug", "bug", "api", "接口", "数据库", "服务器", "部署", "安装", "配置", "编译", "运行", "脚本", "python", "javascript", "java", "go", "rust", "git", "docker", "kubernetes", "linux", "shell"],
            "开发": ["开发", "开发", "实现", "构建", "创建", "编写", "重构", "优化", "性能", "架构", "设计模式", "测试", "单元测试", "集成测试"],
        },
        "产品类": {
            "设计": ["设计", "原型", "ui", "ux", "界面", "交互", "用户体验", "按钮", "布局", "配色", "视觉", "交互"],
            "需求": ["需求", "功能", "feature", "user story", "mvp", "PRD", "规格", "规格说明"],
        },
        "分析类": {
            "数据": ["数据", "分析", "统计", "图表", "可视化", "报表", "指标", "kpi", "趋势", "预测", "挖掘"],
            "市场": ["市场", "竞品", "调研", "用户研究", "市场调研", "行业", "趋势", "份额"],
            "投资": ["股票", "投资", "收益", "回报", "风险", "估值", "财务", "报表", "年报", "估值"],
        },
        "创意类": {
            "内容": ["文章", "文案", "写作", "内容创作", "博客", "社媒", "帖子", "推文", "视频脚本"],
            "设计": ["创意", "头脑风暴", "logo", "品牌", "营销", "活动策划", "方案"],
        }
    }
    
    # 复杂度评估规则
    COMPLEXITY_INDICATORS = {
        "超复杂": ["多", "多个", "整套", "完整", "大型", "复杂系统", "分布式", "微服务", "架构设计"],
        "复杂": ["如何", "怎么", "为什么", "原因", "解决", "优化", "改进", "比较", "对比", "选型"],
        "中等": ["是什么", "什么是", "介绍一下", "说明", "解释", "帮我"],
        "简单": ["帮我", "给我", "查一下", "看看", "有没有", "是不是"],
    }
    
    def __init__(self):
        self._domain_flat = self._flatten_domain_keywords()
    
    def _flatten_domain_keywords(self) -> dict:
        """将领域关键词展平为 {关键词: 领域} 的字典"""
        flat = {}
        for domain_category, subcats in self.DOMAIN_KEYWORDS.items():
            for subcat, keywords in subcats.items():
                for keyword in keywords:
                    flat[keyword] = domain_category
        return flat
    
    def _classify_subproblem(self, text: str) -> tuple[str, list[str]]:
        """对单个子问题进行领域分类，返回 (领域, 匹配关键词列表)"""
        matched_domain = "分析类"  # 默认
        matched_keywords = []
        
        text_lower = text.lower()
        
        # 遍历所有领域关键词，找最长匹配
        best_match_len = 0
        for keyword, domain in self._domain_flat.items():
            if keyword.lower() in text_lower:
                if len(keyword) > best_match_len:
                    best_match_len = len(keyword)
                    matched_domain = domain
                    matched_keywords = [keyword]
                elif len(keyword) == best_match_len and keyword not in matched_keywords:
                    matched_keywords.append(keyword)
        
        return matched_domain, matched_keywords
    
    def _split_into_subproblems(self, question: str) -> list[str]:
        """将问题拆分为原子子问题"""
        # 清理问题
        question = question.strip()
        
        # 检测是否包含多个问题（通过问号、顿号、分号）
        # 常见模式：
        # 1. "问题1？问题2？问题3？"
        # 2. "问题1、问题2、问题3"
        # 3. "我想了解A和B，以及C"
        # 4. "1. xxx 2. xxx 3. xxx"
        
        sub_problems = []
        
        # 模式1：按问号分割
        if "？" in question or "? " in question:
            parts = re.split(r'[？?]', question)
            sub_problems.extend([p.strip() for p in parts if p.strip()])
        
        # 模式2：按"和"、"以及"、"还有"分割
        if len(sub_problems) <= 1:
            connectors = ['和', '以及', '还有', '同时', '并且', '兼']
            for conn in connectors:
                if conn in question:
                    parts = re.split(f'{conn}', question)
                    sub_problems.extend([p.strip() for p in parts if p.strip()])
                    break
        
        # 模式3：按顿号、分号分割
        if len(sub_problems) <= 1:
            for sep in ['、', ';', '；']:
                if sep in question:
                    parts = question.split(sep)
                    sub_problems.extend([p.strip() for p in parts if p.strip()])
                    break
        
        # 模式4：按序号分割 "1. xxx 2. xxx"
        if len(sub_problems) <= 1:
            numbered = re.split(r'\d+[.、]\s*', question)
            if len(numbered) > 1:
                sub_problems.extend([p.strip() for p in numbered if p.strip()])
        
        # 如果仍然只有一个，说明是单一问题
        if len(sub_problems) <= 1:
            sub_problems = [question]
        
        # 去重，保持顺序
        seen = set()
        unique_sub_problems = []
        for p in sub_problems:
            p_clean = p.strip()
            if p_clean and p_clean not in seen:
                seen.add(p_clean)
                unique_sub_problems.append(p_clean)
        
        return unique_sub_problems
    
    def _assess_complexity(self, question: str, sub_problems: list[str]) -> str:
        """评估问题复杂度"""
        question_lower = question.lower()
        
        # 先检查是否有超复杂指标
        for indicator in self.COMPLEXITY_INDICATORS["超复杂"]:
            if indicator.lower() in question_lower:
                return "超复杂"
        
        # 检查复杂指标
        complex_count = 0
        for indicator in self.COMPLEXITY_INDICATORS["复杂"]:
            if indicator.lower() in question_lower:
                complex_count += 1
        
        # 子问题数量也影响复杂度
        if len(sub_problems) >= 4:
            complex_count += 2
        elif len(sub_problems) >= 2:
            complex_count += 1
        
        if complex_count >= 3:
            return "复杂"
        elif complex_count >= 1:
            return "中等"
        else:
            return "简单"
    
    def process(self, question: str) -> PreprocessResult:
        """
        处理用户问题
        
        Args:
            question: 用户原始问题
            
        Returns:
            PreprocessResult: 结构化的问题分析结果
        """
        if not question or not question.strip():
            raise ValueError("问题不能为空")
        
        # 1. 拆解子问题
        sub_problem_texts = self._split_into_subproblems(question)
        
        # 2. 对每个子问题进行领域分类
        sub_problems = []
        domain_counts = {}
        
        for idx, text in enumerate(sub_problem_texts):
            domain, keywords = self._classify_subproblem(text)
            sub_problems.append(SubProblem(
                id=idx + 1,
                text=text,
                domain=domain,
                keywords=keywords
            ))
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # 3. 确定主要领域（出现最多的）
        primary_domain = max(domain_counts, key=lambda d: domain_counts[d]) if domain_counts else "分析类"
        
        # 4. 评估复杂度
        complexity = self._assess_complexity(question, sub_problem_texts)
        
        # 5. 初步判断是否需要学习（待三层探测确认）
        # 粗略判断：如果问题涉及多个领域，可能需要学习
        requires_learning = len(domain_counts) > 1 if domain_counts else False
        
        return PreprocessResult(
            original_question=question,
            sub_problems=sub_problems,
            primary_domain=primary_domain,
            complexity=complexity,
            requires_learning=requires_learning
        )
    
    def run(self, question: str) -> str:
        """
        运行预处理，以JSON格式返回结果
        """
        result = self.process(question)
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


# CLI 入口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 01-preprocess.py <问题>")
        print("示例: python 01-preprocess.py '如何用Python实现并发编程？以及如何优化性能？'")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    preprocessor = Preprocessor()
    print(preprocessor.run(question))
