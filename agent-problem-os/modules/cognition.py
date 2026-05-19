#!/usr/bin/env python3
"""
问题认知模块
职责：三层知识探测机制，判断Agent是否具备处理此问题的专业知识

三层探测：
1. 置信度自评 → ≥80% 直接跳过
2. 知识库验证 → 命中且新鲜则跳过
3. 主动探测 → 发现盲区才触发学习

用法：
    from cognition import ProblemCognition, CognitionResult
    cognition = ProblemCognition()
    result = cognition.process(preprocess_result)
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


@dataclass
class ConfidenceScore:
    """置信度评分"""
    overall: int  # 0-100
    per_sub_problem: list[dict]  # [{"id": 1, "text": "...", "confidence": 85}]
    reasoning: str  # 评分理由


@dataclass
class KnowledgeHit:
    """知识库命中结果"""
    hit: bool
    documents: list[dict] = field(default_factory=list)  # [{"title": "", "path": "", "relevance": 0.9, "freshness": "2026-05"}]
    missing_domains: list[str] = field(default_factory=list)


@dataclass
class CognitionResult:
    """认知结果"""
    decision: str  # "进入分析模块" / "触发学习流程"
    knowledge_gap: list[str] = field(default_factory=list)  # 发现的盲区
    learning_results: list[str] = field(default_factory=list)  # 学习项
    context_loaded: bool = False
    confidence: ConfidenceScore = None  # type: ignore
    knowledge_hit: KnowledgeHit = None  # type: ignore
    self_assessment: str = ""

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "knowledge_gap": self.knowledge_gap,
            "learning_results": self.learning_results,
            "context_loaded": self.context_loaded,
            "confidence": asdict(self.confidence),
            "knowledge_hit": asdict(self.knowledge_hit),
            "self_assessment": self.self_assessment
        }


class ProblemCognition:
    """问题认知模块 - 三层知识探测"""

    CONFIDENCE_THRESHOLD = 80  # 置信度阈值

    def __init__(self, kb_path: str = "~/.hermes/knowledge-base"):
        self.kb_path = Path(kb_path).expanduser()

    # ========== 第一层：置信度自评 ==========

    def _assess_confidence(self, preprocess_result: dict) -> ConfidenceScore:
        """
        第一层：Agent 自我评估置信度
        
        这里模拟 Agent 的自评逻辑（实际使用时由LLM提供真实评估）
        """
        sub_problems = preprocess_result.get("sub_problems", [])
        domain = preprocess_result.get("primary_domain", "分析类")
        complexity = preprocess_result.get("complexity", "中等")

        # 模拟自评逻辑（基于问题特征）
        # 实际使用时这里应该调用 LLM 获取真实置信度
        scores = []
        
        for sp in sub_problems:
            text = sp.get("text", "")
            sp_domain = sp.get("domain", "分析类")
            
            # 模拟评分逻辑
            score = 50  # 默认中等置信度
            
            # 技术类问题如果有明确关键词，置信度较高
            if sp_domain == "技术类":
                tech_keywords = ["python", "代码", "编程", "api", "git", "docker", "部署"]
                if any(kw in text.lower() for kw in tech_keywords):
                    score = 75
            
            # 创意类问题置信度较低（创意类任务主观性强）
            if sp_domain == "创意类":
                score = 60
            
            # 复杂度影响
            if complexity == "超复杂":
                score = max(30, score - 20)
            elif complexity == "简单":
                score = min(90, score + 15)
            
            scores.append({
                "id": sp.get("id"),
                "text": text[:50],
                "confidence": score,
                "domain": sp_domain
            })

        overall = sum(s["confidence"] for s in scores) // len(scores) if scores else 50
        
        # 生成推理
        reasoning = f"主要领域：{domain}，复杂度：{complexity}，子问题数：{len(sub_problems)}"
        if overall >= self.CONFIDENCE_THRESHOLD:
            reasoning += " → 置信度达标，可直接进入分析"
        else:
            reasoning += " → 置信度不足，触发第二层验证"

        return ConfidenceScore(
            overall=overall,
            per_sub_problem=scores,
            reasoning=reasoning
        )

    # ========== 第二层：知识库验证 ==========

    def _check_knowledge_base(self, preprocess_result: dict) -> KnowledgeHit:
        """
        第二层：查询本地知识库
        """
        sub_problems = preprocess_result.get("sub_problems", [])
        primary_domain = preprocess_result.get("primary_domain", "分析类")
        
        # 检查知识库目录是否存在
        if not self.kb_path.exists():
            return KnowledgeHit(
                hit=False,
                missing_domains=[primary_domain]
            )

        # 扫描知识库
        kb_dir = self.kb_path / primary_domain
        hit_documents = []
        missing_domains = []

        if kb_dir.exists():
            # 查找相关文档
            md_files = list(kb_dir.rglob("*.md"))
            for md_file in md_files[:10]:  # 最多检查10个文档
                # 简单匹配：检查文档名是否包含领域关键词
                rel_path = md_file.relative_to(self.kb_path)
                hit_documents.append({
                    "title": md_file.stem,
                    "path": str(rel_path),
                    "relevance": 0.7,  # 简化：静态评分
                    "freshness": "2026-05"  # 简化：静态值
                })
        else:
            missing_domains.append(primary_domain)

        return KnowledgeHit(
            hit=len(hit_documents) > 0,
            documents=hit_documents,
            missing_domains=missing_domains
        )

    # ========== 第三层：主动探测 ==========

    def _probe_knowledge_gaps(self, preprocess_result: dict) -> list[str]:
        """
        第三层：主动探测，发现知识盲区
        
        这里模拟探测逻辑（实际使用时由LLM分析）
        """
        sub_problems = preprocess_result.get("sub_problems", [])
        gaps = []

        # 模拟检测逻辑
        for sp in sub_problems:
            text = sp.get("text", "")
            
            # 触发盲区检测的关键词
            uncertain_patterns = [
                "如何设计", "如何架构", "如何优化",
                "多个", "整套", "大型", "分布式",
                "微服务", "跨平台", "安全"
            ]
            
            if any(p in text for p in uncertain_patterns):
                gaps.append(f"子问题{sp.get('id')}: {text[:30]}... - 涉及深层设计")
        
        return gaps

    # ========== 主流程 ==========

    def process(self, preprocess_result: dict) -> CognitionResult:
        """
        处理问题认知

        Args:
            preprocess_result: 预处理模块的输出
            
        Returns:
            CognitionResult: 认知结果
        """
        # 第一层：置信度自评
        confidence = self._assess_confidence(preprocess_result)
        self_assessment = confidence.reasoning

        if confidence.overall >= self.CONFIDENCE_THRESHOLD:
            # 置信度达标，直接进入分析
            return CognitionResult(
                decision="进入分析模块",
                knowledge_gap=[],
                learning_results=[],
                context_loaded=False,
                confidence=confidence,
                knowledge_hit=KnowledgeHit(hit=False),
                self_assessment=self_assessment
            )

        # 第二层：知识库验证
        kb_hit = self._check_knowledge_base(preprocess_result)

        if kb_hit.hit and not kb_hit.missing_domains:
            # 知识库命中，进入分析
            return CognitionResult(
                decision="进入分析模块",
                knowledge_gap=[],
                learning_results=[],
                context_loaded=True,
                confidence=confidence,
                knowledge_hit=kb_hit,
                self_assessment=self_assessment + " | 知识库命中"
            )

        # 第三层：主动探测
        gaps = self._probe_knowledge_gaps(preprocess_result)

        if gaps:
            # 发现盲区，触发学习
            return CognitionResult(
                decision="触发学习流程",
                knowledge_gap=gaps,
                learning_results=[f"需学习: {g}" for g in gaps],
                context_loaded=False,
                confidence=confidence,
                knowledge_hit=kb_hit,
                self_assessment=self_assessment + " | 发现知识盲区"
            )

        # 有置信度不足但无明确盲区
        return CognitionResult(
            decision="进入分析模块（低置信度）",
            knowledge_gap=[],
            learning_results=[],
            context_loaded=False,
            confidence=confidence,
            knowledge_hit=kb_hit,
            self_assessment=self_assessment + " | 建议分析过程中留意知识盲区"
        )

    def run(self, preprocess_json: str) -> str:
        """
        运行认知模块（JSON格式）
        """
        preprocess_result = json.loads(preprocess_json)
        result = self.process(preprocess_result)
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    
    # 演示用法
    from preprocess import Preprocessor
    
    if len(sys.argv) < 2:
        question = "如何设计一个大型分布式系统？"
    else:
        question = " ".join(sys.argv[1:])
    
    print("=" * 50)
    print("问题认知模块 - 三层知识探测")
    print("=" * 50)
    
    # 预处理
    p = Preprocessor()
    pre_result = p.process(question)
    pre_dict = pre_result.to_dict()
    
    print(f"\n📋 预处理结果：")
    print(f"   领域: {pre_result.primary_domain}")
    print(f"   复杂度: {pre_result.complexity}")
    print(f"   子问题数: {len(pre_result.sub_problems)}")
    
    # 认知
    c = ProblemCognition()
    cog_result = c.process(pre_dict)
    
    print(f"\n🧠 认知结果：")
    print(f"   决策: {cog_result.decision}")
    print(f"   置信度: {cog_result.confidence.overall}%")
    print(f"   知识库命中: {cog_result.knowledge_hit.hit}")
    print(f"   知识盲区: {len(cog_result.knowledge_gap)} 个")
    
    if cog_result.knowledge_gap:
        for gap in cog_result.knowledge_gap:
            print(f"     - {gap}")
