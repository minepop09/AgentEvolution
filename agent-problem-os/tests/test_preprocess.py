#!/usr/bin/env python3
"""测试问题预处理模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from preprocess import Preprocessor


def test_single_question():
    """测试单一问题"""
    p = Preprocessor()
    result = p.process("如何用Python实现并发编程？")
    
    assert result.primary_domain == "技术类"
    assert len(result.sub_problems) == 1
    print(f"✅ 单一问题: {result.original_question}")
    print(f"   领域: {result.primary_domain}, 复杂度: {result.complexity}")


def test_multiple_questions():
    """测试多问题"""
    p = Preprocessor()
    result = p.process("如何用Python实现并发编程？以及如何优化性能？")
    
    assert result.primary_domain == "技术类"
    assert len(result.sub_problems) == 2
    print(f"✅ 多问题: {result.original_question}")
    print(f"   子问题数: {len(result.sub_problems)}")


def test_product_question():
    """测试产品类问题"""
    p = Preprocessor()
    result = p.process("帮我设计一个社交APP的用户界面")
    
    assert result.primary_domain == "产品类"
    print(f"✅ 产品类问题: {result.original_question}")
    print(f"   领域: {result.primary_domain}, 复杂度: {result.complexity}")


def test_complex_question():
    """测试复杂问题"""
    p = Preprocessor()
    result = p.process("我需要做一个大型分布式系统，如何设计架构？如何选择技术栈？如何优化性能？")
    
    assert result.complexity in ["复杂", "超复杂"]
    print(f"✅ 复杂问题: {result.original_question}")
    print(f"   复杂度: {result.complexity}, 子问题数: {len(result.sub_problems)}")


if __name__ == "__main__":
    test_single_question()
    test_multiple_questions()
    test_product_question()
    test_complex_question()
    print("\n✅ 所有测试通过！")
