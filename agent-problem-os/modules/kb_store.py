#!/usr/bin/env python3
"""
知识库存储模块
职责：将领域知识以Markdown格式存入知识库

功能：
1. 创建知识库目录结构
2. 将知识存入对应领域分类
3. 按月归档旧版本

用法：
    from kb_store import KnowledgeBaseStore, KBEntry
    
    store = KnowledgeBaseStore(kb_path="~/.hermes/knowledge-base")
    store.save(entries=[KBEntry(domain="技术类", title="Python并发编程", content="...")])
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# 固定领域分类
DOMAINS = ["技术类", "产品类", "分析类", "创意类"]


@dataclass
class KBEntry:
    """知识库条目"""
    domain: str           # 领域分类
    title: str            # 标题
    content: str          # 知识内容（Markdown）
    tags: list[str] = field(default_factory=list)  # 标签
    source: str = ""      # 来源
    created_at: str = ""   # 创建时间
    updated_at: str = ""   # 更新时间
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class KBSearchResult:
    """搜索结果"""
    entries: list[dict]
    total: int


class KnowledgeBaseStore:
    """知识库存储模块"""
    
    # Markdown 模板
    ENTRY_TEMPLATE = '''---
title: {title}
domain: {domain}
tags: [{tags}]
source: {source}
created: {created}
updated: {updated}
---

{content}
'''
    
    def __init__(self, kb_path: str = "~/.hermes/knowledge-base"):
        self.kb_path = Path(kb_path).expanduser()
        self._ensure_structure()
    
    def _ensure_structure(self):
        """确保知识库目录结构存在"""
        for domain in DOMAINS:
            domain_dir = self.kb_path / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, title: str) -> str:
        """将标题转为安全的文件名"""
        # 移除不安全字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', title)
        # 限制长度
        filename = filename[:80]
        return filename.strip()
    
    def _entry_to_markdown(self, entry: KBEntry) -> str:
        """将KBEntry转为Markdown格式"""
        tags_str = ", ".join(entry.tags) if entry.tags else ""
        return self.ENTRY_TEMPLATE.format(
            title=entry.title,
            domain=entry.domain,
            tags=tags_str,
            source=entry.source,
            created=entry.created_at,
            updated=entry.updated_at,
            content=entry.content
        )
    
    def _markdown_to_entry(self, md_path: Path) -> Optional[dict]:
        """从Markdown文件读取为dict"""
        try:
            content = md_path.read_text(encoding="utf-8")
            
            # 解析 frontmatter（简化版）
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].strip()
                    
                    # 解析 frontmatter
                    meta = {}
                    for line in frontmatter.strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            meta[key.strip()] = value.strip()
                    
                    return {
                        "title": meta.get("title", md_path.stem),
                        "domain": meta.get("domain", ""),
                        "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
                        "source": meta.get("source", ""),
                        "created": meta.get("created", ""),
                        "updated": meta.get("updated", ""),
                        "content": body,
                        "path": str(md_path)
                    }
            
            return None
        except Exception:
            return None
    
    def save(self, entries: list[KBEntry]) -> list[str]:
        """
        保存知识条目
        
        Args:
            entries: KBEntry列表
            
        Returns:
            保存的文件路径列表
        """
        saved_paths = []
        
        for entry in entries:
            if entry.domain not in DOMAINS:
                # 默认归入分析类
                entry.domain = "分析类"
            
            # 创建目录
            domain_dir = self.kb_path / entry.domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            filename = self._sanitize_filename(entry.title)
            md_path = domain_dir / f"{filename}.md"
            
            # 如果文件已存在，更新而非创建
            if md_path.exists():
                # 读取现有更新时间
                existing = self._markdown_to_entry(md_path)
                if existing:
                    entry.created_at = existing.get("created", entry.created_at)
            entry.updated_at = datetime.now().strftime("%Y-%m-%d")
            
            # 写入文件
            md_content = self._entry_to_markdown(entry)
            md_path.write_text(md_content, encoding="utf-8")
            saved_paths.append(str(md_path))
        
        return saved_paths
    
    def search(self, query: str, domain: Optional[str] = None, limit: int = 10) -> KBSearchResult:
        """
        搜索知识库
        
        Args:
            query: 搜索关键词
            domain: 限定领域（可选）
            limit: 返回数量限制
            
        Returns:
            KBSearchResult
        """
        results = []
        query_lower = query.lower()
        
        search_domains = [domain] if domain else DOMAINS
        
        for d in search_domains:
            domain_dir = self.kb_path / d
            if not domain_dir.exists():
                continue
            
            for md_file in domain_dir.rglob("*.md"):
                entry = self._markdown_to_entry(md_file)
                if not entry:
                    continue
                
                # 简单关键词匹配
                full_text = f"{entry.get('title', '')} {entry.get('content', '')}".lower()
                if query_lower in full_text:
                    results.append(entry)
                    
                    # 计算相关性分数
                    entry["_relevance"] = full_text.count(query_lower) / len(full_text)
                
                if len(results) >= limit:
                    break
        
        # 按相关性排序
        results.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        
        return KBSearchResult(entries=results[:limit], total=len(results))
    
    def list_entries(self, domain: Optional[str] = None) -> list[dict]:
        """列出知识库条目"""
        entries = []
        domains = [domain] if domain else DOMAINS
        
        for d in domains:
            domain_dir = self.kb_path / d
            if not domain_dir.exists():
                continue
            
            for md_file in domain_dir.rglob("*.md"):
                entry = self._markdown_to_entry(md_file)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def archive_old_entries(self, months: int = 3) -> int:
        """
        归档旧条目（移动到archive目录）
        
        Args:
            months: 超过多少个月的条目被归档
            
        Returns:
            归档的条目数
        """
        archived_count = 0
        cutoff_date = datetime.now()
        # 简化：用月数做判断
        
        for domain in DOMAINS:
            domain_dir = self.kb_path / domain
            archive_dir = domain_dir / "archive"
            
            if not domain_dir.exists():
                continue
            
            for md_file in domain_dir.rglob("*.md"):
                if "archive" in md_file.parts:
                    continue
                
                entry = self._markdown_to_entry(md_file)
                if not entry:
                    continue
                
                # 检查更新时间
                updated = entry.get("updated", "")
                if updated:
                    try:
                        updated_dt = datetime.strptime(updated, "%Y-%m-%d")
                        age_months = (cutoff_date - updated_dt).days // 30
                        if age_months >= months:
                            # 移动到archive
                            archive_dir.mkdir(exist_ok=True)
                            archive_path = archive_dir / md_file.name
                            md_file.rename(archive_path)
                            archived_count += 1
                    except ValueError:
                        pass
        
        return archived_count
    
    def get_stats(self) -> dict:
        """获取知识库统计"""
        stats = {domain: 0 for domain in DOMAINS}
        total_content_size = 0
        
        for domain in DOMAINS:
            domain_dir = self.kb_path / domain
            if domain_dir.exists():
                md_files = list(domain_dir.rglob("*.md"))
                # 排除archive目录
                md_files = [f for f in md_files if "archive" not in f.parts]
                stats[domain] = len(md_files)
                total_content_size += sum(f.stat().st_size for f in md_files)
        
        return {
            "domains": stats,
            "total_entries": sum(stats.values()),
            "total_size_kb": round(total_content_size / 1024, 1)
        }


if __name__ == "__main__":
    # 演示用法
    print("=" * 50)
    print("知识库存储模块")
    print("=" * 50)
    
    store = KnowledgeBaseStore(kb_path="/tmp/demo-knowledge-base")
    
    # 保存几条知识
    entries = [
        KBEntry(
            domain="技术类",
            title="Python并发编程",
            content="# 异步编程\n\n asyncio 是Python标准库...",
            tags=["python", "async", "并发"]
        ),
        KBEntry(
            domain="产品类",
            title="用户研究方法",
            content="# 用户访谈\n\n 1对1深度访谈是了解用户需求的重要方法...",
            tags=["用户研究", "访谈", "需求"]
        )
    ]
    
    paths = store.save(entries)
    print(f"\n✅ 保存了 {len(paths)} 个知识条目")
    for p in paths:
        print(f"   - {p}")
    
    # 搜索
    results = store.search("python")
    print(f"\n🔍 搜索'python'结果: {results.total} 条")
    for r in results.entries:
        print(f"   - {r['title']} ({r['domain']})")
    
    # 统计
    stats = store.get_stats()
    print(f"\n📊 知识库统计: {stats}")
