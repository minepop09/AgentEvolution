#!/usr/bin/env python3
"""
问题分析模块
职责：在有专业认知的情况下进行深度分析，选择合适的方法论

功能：
1. 根据问题类型选择方法论
2. 对每个子问题进行深度分析
3. 生成 Todo 计划

方法论映射：
- 技术类：结构化调试法 / 重构分析法
- 产品类：用户故事映射 / 需求优先级
- 分析类：假设验证法 / 对比分析法
- 创意类：发散收敛法

用法：
    from 04_analysis import ProblemAnalysis, AnalysisResult
    
    analyzer = ProblemAnalysis()
    result = analyzer.process(preprocess_result, cognition_result)
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Optional


METHODOLOGIES = {
    "技术类": {
        "default": "结构化调试法",
        "options": [
            "结构化调试法",  # 现象→假设→验证→定位→修复
            "重构分析法",    # 识别代码异味→小步重构→测试验证
            "性能剖析法",    # .Profile→瓶颈→优化→验证
            "架构探索法"     # 理解现有架构→识别问题→设计改进
        ]
    },
    "产品类": {
        "default": "用户故事映射",
        "options": [
            "用户故事映射",   # 用户→角色→目标→任务
            "需求优先级",    # MoSCoW / RICE
            "设计思维",      # 同理心→定义→ ideation →原型→测试
            "A/B测试法"      # 假设→分流→数据验证
        ]
    },
    "分析类": {
        "default": "假设验证法",
        "options": [
            "假设验证法",    # 提出假设→收集证据→验证→结论
            "对比分析法",    # 横向对比→找出差异→分析原因
            "漏斗分析法",    # 识别转化漏斗→分析流失→优化
            "回归分析法"     # 确定变量→建模→验证相关性
        ]
    },
    "创意类": {
        "default": "发散收敛法",
        "options": [
            "发散收敛法",    # 大量 ideation → 聚类 → 精选
            "SCAMPER",      # 替代/组合/改编/修改/其他用途/消除/反向
            "六顶思考帽",    # 白帽(事实)→红帽(情感)→黑帽(批判)→黄帽(乐观)→绿帽(创意)→蓝帽(流程)
            "逆向思维法"     # 反向思考→发现新角度
        ]
    }
}


@dataclass
class SubProblemAnalysis:
    """子问题分析"""
    id: int
    text: str
    root_cause: str       # 根本原因
    solution_approach: str # 解决路径
    methodology_used: str  # 使用的方法论
    tools_needed: list[str] = field(default_factory=list)
    difficulty: str = "中等"  # 简单/中等/困难/极难
    notes: str = ""


@dataclass
class AnalysisResult:
    """分析结果"""
    original_question: str
    primary_domain: str
    methodology: str
    methodology_reasoning: str
    sub_problem_analyses: list[SubProblemAnalysis]
    overall_summary: str
    recommended_tools: list[str] = field(default_factory=list)
    estimated_difficulty: str = "中等"

    def to_dict(self) -> dict:
        return {
            "original_question": self.original_question,
            "primary_domain": self.primary_domain,
            "methodology": self.methodology,
            "methodology_reasoning": self.methodology_reasoning,
            "sub_problem_analyses": [asdict(a) for a in self.sub_problem_analyses],
            "overall_summary": self.overall_summary,
            "recommended_tools": self.recommended_tools,
            "estimated_difficulty": self.estimated_difficulty
        }


class ProblemAnalysis:
    """问题分析模块"""

    def __init__(self):
        pass

    def _select_methodology(self, domain: str, sub_problems: list[dict]) -> tuple[str, str]:
        """
        选择方法论
        
        Returns: (methodology_name, reasoning)
        """
        domain_methods = METHODOLOGIES.get(domain, METHODOLOGIES["分析类"])
        
        # 简单场景用默认方法论
        if len(sub_problems) <= 1:
            return domain_methods["default"], f"单问题场景，使用{domain}的默认方法论：{domain_methods['default']}"
        
        # 复杂场景用更系统的方法
        complexity_indicators = ["多个", "整套", "大型", "分布式", "架构", "设计"]
        has_complex = any(ind in str(sub_problems) for ind in complexity_indicators)
        
        if has_complex:
            # 复杂问题用更高级的方法
            if domain == "技术类":
                return "架构探索法", "涉及架构设计，使用架构探索法"
            elif domain == "产品类":
                return "设计思维", "涉及复杂产品设计，使用设计思维流程"
            elif domain == "分析类":
                return "假设验证法", "涉及深度分析，使用假设验证法"
            else:
                return "发散收敛法", "涉及创意探索，使用发散收敛法"
        
        return domain_methods["default"], f"使用{domain}的默认方法论：{domain_methods['default']}"

    def _analyze_sub_problem(self, sp: dict, domain: str, methodology: str) -> SubProblemAnalysis:
        """
        分析单个子问题
        
        这里实现简化的分析逻辑。实际使用时由 LLM 提供真实分析。
        """
        text = sp.get("text", "")
        sp_id = sp.get("id", 0)
        
        # 简化：基于关键词的启发式分析
        root_cause = ""
        solution_approach = ""
        tools_needed = []
        difficulty = "中等"
        
        if "如何" in text or "怎么" in text:
            root_cause = "缺乏系统性方法论"
            solution_approach = f"应用{methodology}进行系统化分析和设计"
            
            if any(k in text.lower() for k in ["python", "java", "代码", "编程"]):
                tools_needed = ["代码编辑器", "搜索引擎", "文档"]
            elif any(k in text for k in ["设计", "架构"]):
                tools_needed = ["架构图工具", "参考资料", "搜索引擎"]
                difficulty = "困难"
        elif "优化" in text:
            root_cause = "现有方案存在效率或性能问题"
            solution_approach = "先定位瓶颈，再针对性优化"
            tools_needed = ["性能分析工具", "监控工具", "搜索引擎"]
            difficulty = "困难"
        elif "选型" in text or "比较" in text:
            root_cause = "需要决策最优方案"
            solution_approach = "建立评估矩阵，对比各方案优劣"
            tools_needed = ["对比表格", "参考资料", "行业报告"]
            difficulty = "中等"
        else:
            root_cause = "需要深入了解问题和上下文"
            solution_approach = "收集信息，分析需求和约束"
            tools_needed = ["搜索引擎", "文档"]
        
        return SubProblemAnalysis(
            id=sp_id,
            text=text,
            root_cause=root_cause,
            solution_approach=solution_approach,
            methodology_used=methodology,
            tools_needed=tools_needed,
            difficulty=difficulty
        )

    def _generate_summary(self, result: AnalysisResult) -> str:
        """生成整体总结"""
        summary_parts = []
        
        summary_parts.append(f"问题领域：{result.primary_domain}")
        summary_parts.append(f"选用方法论：{result.methodology}")
        summary_parts.append(f"涉及 {len(result.sub_problem_analyses)} 个子问题")
        
        difficulties = [a.difficulty for a in result.sub_problem_analyses]
        if "极难" in difficulties:
            result.estimated_difficulty = "极难"
        elif "困难" in difficulties:
            result.estimated_difficulty = "困难"
        
        summary_parts.append(f"预估难度：{result.estimated_difficulty}")
        
        if result.recommended_tools:
            summary_parts.append(f"推荐工具：{', '.join(set(result.recommended_tools))}")
        
        return " | ".join(summary_parts)

    def process(
        self, 
        preprocess_result: dict, 
        cognition_result: Optional[dict] = None
    ) -> AnalysisResult:
        """
        处理问题分析
        
        Args:
            preprocess_result: 预处理结果
            cognition_result: 认知结果（可选）
            
        Returns:
            AnalysisResult: 分析结果
        """
        sub_problems = preprocess_result.get("sub_problems", [])
        primary_domain = preprocess_result.get("primary_domain", "分析类")
        original_question = preprocess_result.get("original_question", "")

        # 选择方法论
        methodology, reasoning = self._select_methodology(primary_domain, sub_problems)

        # 分析每个子问题
        analyses = []
        all_tools = []
        
        for sp in sub_problems:
            analysis = self._analyze_sub_problem(sp, primary_domain, methodology)
            analyses.append(analysis)
            all_tools.extend(analysis.tools_needed)

        # 去重工具列表
        unique_tools = list(dict.fromkeys(all_tools))

        # 创建结果
        result = AnalysisResult(
            original_question=original_question,
            primary_domain=primary_domain,
            methodology=methodology,
            methodology_reasoning=reasoning,
            sub_problem_analyses=analyses,
            overall_summary="",  # 稍后填充
            recommended_tools=unique_tools[:5]  # 最多5个工具
        )
        
        result.overall_summary = self._generate_summary(result)
        
        return result

    def run(self, preprocess_json: str, cognition_json: str = "{}") -> str:
        """
        运行问题分析（JSON格式）
        """
        pre_result = json.loads(preprocess_json)
        cog_result = json.loads(cognition_json) if cognition_json else None
        result = self.process(pre_result, cog_result)
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    from preprocess import Preprocessor
    from cognition import ProblemCognition
    
    print("=" * 50)
    print("问题分析模块")
    print("=" * 50)
    
    # 预处理
    question = "如何设计一个大型分布式系统？如何选择技术栈？"
    p = Preprocessor()
    pre_result = p.process(question)
    
    # 认知
    c = ProblemCognition()
    cog_result = c.process(pre_result.to_dict())
    
    # 分析
    a = ProblemAnalysis()
    analysis = a.process(pre_result.to_dict(), cog_result.to_dict())
    
    print(f"\n📊 分析结果：")
    print(f"   选用方法论: {analysis.methodology}")
    print(f"   方法论理由: {analysis.methodology_reasoning}")
    print(f"   子问题数: {len(analysis.sub_problem_analyses)}")
    print(f"   推荐工具: {', '.join(analysis.recommended_tools)}")
    print(f"\n📝 总结: {analysis.overall_summary}")
