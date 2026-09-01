"""
记忆系统 - Agent 跨会话经验存储
两层: 短期(会话内消息) + 长期(SQLite持久化经验条目)
"""
import uuid
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MemoryEntry:
    """单条记忆"""
    def __init__(self, content: str, kind: str = "experience",
                 tags: List[str] = None, entry_id: str = None):
        self.id = entry_id or str(uuid.uuid4())
        self.content = content
        self.kind = kind          # experience / tool_result / lesson / flag
        self.tags = tags or []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "kind": self.kind,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


class Memory:
    """
    长期记忆管理器

    两层架构:
    - 短期记忆: 会话内消息列表 (AgentState.memory)，由 Agent.think() 管理
    - 长期记忆: SQLite 持久化条目，跨会话保留

    使用方式:
        memory = Memory()          # 自动创建 data/memory.json
        memory.remember("nmap -sV 扫描发现 22/80 端口", tags=["recon", "nmap"])
        entries = memory.recall("端口扫描")  # 关键词召回
        memory.forget(entry_id)
    """

    def __init__(self, db=None, storage_path: str = "data/memory.json",
                 max_entries: int = 500):
        self.db = db
        self.storage_path = Path(storage_path)
        self.max_entries = max_entries
        self._entries: List[MemoryEntry] = []
        self._load()

    # ---------- 持久化 (JSON 文件, 轻量无依赖) ----------

    def _load(self):
        """从文件加载记忆"""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for item in data:
                    entry = MemoryEntry(
                        content=item["content"],
                        kind=item.get("kind", "experience"),
                        tags=item.get("tags", []),
                        entry_id=item.get("id"),
                    )
                    if "created_at" in item:
                        entry.created_at = datetime.fromisoformat(item["created_at"])
                    self._entries.append(entry)
                logger.info(f"加载了 {len(self._entries)} 条记忆")
            except Exception as e:
                logger.error(f"加载记忆失败: {e}")

    def _save(self):
        """持久化到文件"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self._entries]
        self.storage_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ---------- 核心 API ----------

    def remember(self, content: str, kind: str = "experience",
                 tags: List[str] = None) -> str:
        """存入一条记忆，返回 entry_id"""
        entry = MemoryEntry(content=content, kind=kind, tags=tags)
        self._entries.append(entry)

        # 超出上限时淘汰最旧的
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

        self._save()
        logger.debug(f"记住: [{kind}] {content[:60]}...")
        return entry.id

    def recall(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """
        按关键词相关性召回记忆。

        评分规则:
        - query 中每个词在 content/tags 中出现 → +1 分
        - kind 匹配加分
        - 越新的记忆加权 +0.1/条
        """
        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.split() if len(w.strip()) >= 2]

        scored: List[tuple] = []
        for entry in self._entries:
            score = 0.0
            text = (entry.content + " " + " ".join(entry.tags)).lower()
            # 关键词命中
            for kw in keywords:
                if kw in text:
                    score += 1.0
            # kind 匹配
            if "tool" in query_lower and entry.kind == "tool_result":
                score += 0.5
            if "flag" in query_lower and entry.kind == "flag":
                score += 1.0
            # 新鲜度加权 (最近的条目 index 越大)
            idx = self._entries.index(entry)
            score += idx * 0.001

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def recall_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """直接召回最近 N 条记忆（不需要关键词）"""
        return self._entries[-limit:]

    def forget(self, entry_id: str) -> bool:
        """删除一条记忆，返回是否成功"""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.id != entry_id]
        if len(self._entries) < before:
            self._save()
            return True
        return False

    def clear(self):
        """清空所有记忆"""
        self._entries.clear()
        self._save()
        logger.info("记忆已清空")

    def count(self) -> int:
        return len(self._entries)

    def list_by_kind(self, kind: str) -> List[MemoryEntry]:
        return [e for e in self._entries if e.kind == kind]
