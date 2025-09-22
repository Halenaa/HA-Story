# File: src/memory/shared_memory.py
# -*- coding: utf-8 -*-
"""
SharedMemory (Blackboard) for multi-agent storytelling system
-------------------------------------------------------------
- 统一的共享内存 / 黑板（Blackboard）容器，集中管理各 Agent 的读写。
- 关键能力：命名空间、类型/结构校验、审计日志、快照/回滚、差异比较、持久化。
- 设计目标：可解释、可追踪、便于论文描述与复现实验。

依赖：仅标准库（json、copy、datetime、pathlib、typing）。
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import copy


@dataclass
class MemoryEvent:
    time: str
    op: str              # set / append / update / snapshot / rollback / load / save
    key: Optional[str]   # 作用 key（无则为全局）
    meta: Dict[str, Any]


class SchemaError(Exception):
    pass


class SharedMemory:
    """轻量级黑板。支持：
    - 命名空间：例如 memory.set("story", data), memory.get("story")
    - 类型/结构校验：可选 schema；不严格时可跳过
    - 审计日志：每次写入记录 MemoryEvent，便于复现实验
    - 快照/回滚：checkpoint/rollback 支持阶段性试错
    - 差异比较：diff 快速定位改动
    - 持久化：save/load 为 JSON（含元信息）
    """

    DEFAULT_SCHEMA: Dict[str, str] = {
        # 关键字段的期望类型（仅作轻校验；允许更复杂校验器见 self.validators）
        "outline": "list",               # list[Chapter]
        "reordered_outline": "list",     # list[Chapter]
        "characters": "list",            # list[Character]
        "story": "list",                 # list[ChapterStory]
        "dialogue_marks": "list",        # chapter-level dialogue decisions
        "sentence_dialogues": "list",    # sentence-level detailed results
        "behavior_timeline": "list",     # extracted behaviors over time
        "role_state": "dict",            # chapter->character->behaviors
        "conflict_reports": "list",      # list[ConflictReport]
        "performance": "dict"            # performance metrics or references
    }

    def __init__(self,
                 task_name: str,
                 schema: Optional[Dict[str, str]] = None,
                 validators: Optional[Dict[str, Callable[[Any], bool]]] = None):
        self.task_name = task_name
        self._data: Dict[str, Any] = {}
        self._events: List[MemoryEvent] = []
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self.schema = schema or copy.deepcopy(self.DEFAULT_SCHEMA)
        self.validators = validators or {}
        # 元信息
        self.meta: Dict[str, Any] = {
            "task": task_name,
            "created_at": datetime.utcnow().isoformat(),
            "version": 1
        }

    # --------------------------- 基础读写 ---------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def exists(self, key: str) -> bool:
        return key in self._data

    def set(self, key: str, value: Any, *, meta: Optional[Dict[str, Any]] = None) -> None:
        self._validate(key, value)
        self._data[key] = value
        self._log("set", key, meta or {})

    def update(self, key: str, updater: Callable[[Any], Any], *, meta: Optional[Dict[str, Any]] = None) -> None:
        old = copy.deepcopy(self._data.get(key))
        new_val = updater(old)
        self.set(key, new_val, meta=meta)
        self._log("update", key, {"from": type(old).__name__, "to": type(new_val).__name__, **(meta or {})})

    def append(self, key: str, item: Any, *, meta: Optional[Dict[str, Any]] = None) -> None:
        cur = self._data.get(key)
        if cur is None:
            cur = []
        if not isinstance(cur, list):
            raise SchemaError(f"append 目标必须是 list，但 {key} 是 {type(cur).__name__}")
        cur.append(item)
        self.set(key, cur, meta=meta)
        self._log("append", key, meta or {})

    # --------------------------- 校验 ---------------------------
    def _validate(self, key: str, value: Any) -> None:
        expected = self.schema.get(key)
        if expected is None:
            return  # 未列入 schema 的键允许写入
        type_map = {
            "list": list,
            "dict": dict,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "any": object,
        }
        pytype = type_map.get(expected)
        if pytype and expected != "any" and not isinstance(value, pytype):
            raise SchemaError(f"{key} 期望 {expected}, 实得 {type(value).__name__}")
        # 自定义校验器
        validator = self.validators.get(key)
        if validator and not validator(value):
            raise SchemaError(f"{key} 自定义校验未通过")

    # --------------------------- 审计/快照/回滚/差异 ---------------------------
    def _log(self, op: str, key: Optional[str], meta: Dict[str, Any]) -> None:
        evt = MemoryEvent(time=datetime.utcnow().isoformat(), op=op, key=key, meta=meta)
        self._events.append(evt)

    def events(self) -> List[MemoryEvent]:
        return copy.deepcopy(self._events)

    def snapshot(self, tag: Optional[str] = None) -> str:
        sid = tag or f"snap_{len(self._snapshots)+1}"
        self._snapshots[sid] = copy.deepcopy(self._data)
        self._log("snapshot", None, {"sid": sid})
        return sid

    def rollback(self, snapshot_id: str) -> None:
        if snapshot_id not in self._snapshots:
            raise KeyError(f"找不到快照 {snapshot_id}")
        self._data = copy.deepcopy(self._snapshots[snapshot_id])
        self._log("rollback", None, {"sid": snapshot_id})

    def diff(self, a: str, b: str) -> Dict[str, Dict[str, Any]]:
        """比较两个快照，返回 {key: {"a": old, "b": new}}"""
        if a not in self._snapshots or b not in self._snapshots:
            raise KeyError("diff 需要存在的快照 id")
        da, db = self._snapshots[a], self._snapshots[b]
        keys = set(da.keys()) | set(db.keys())
        out: Dict[str, Dict[str, Any]] = {}
        for k in keys:
            va, vb = da.get(k), db.get(k)
            if json.dumps(va, ensure_ascii=False, sort_keys=True) != json.dumps(vb, ensure_ascii=False, sort_keys=True):
                out[k] = {"a": va, "b": vb}
        return out

    # --------------------------- 持久化 ---------------------------
    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "meta": self.meta,
            "data": self._data,
            "events": [evt.__dict__ for evt in self._events],
        }
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._log("save", None, {"path": str(p)})
        return p

    @classmethod
    def load(cls, path: str | Path) -> "SharedMemory":
        p = Path(path)
        payload = json.loads(p.read_text(encoding="utf-8"))
        mem = cls(task_name=payload.get("meta", {}).get("task", "unknown"))
        mem.meta = payload.get("meta", {})
        mem._data = payload.get("data", {})
        mem._events = [MemoryEvent(**e) for e in payload.get("events", [])]
        mem._log("load", None, {"path": str(p)})
        return mem

    # --------------------------- 便捷工具 ---------------------------
    def export_story_bundle(self) -> Dict[str, Any]:
        """将常用输出打包给下游（渲染/评估）。"""
        return {
            "outline": self.get("outline"),
            "reordered_outline": self.get("reordered_outline"),
            "characters": self.get("characters"),
            "story": self.get("story"),
            "sentence_dialogues": self.get("sentence_dialogues"),
            "behavior_timeline": self.get("behavior_timeline"),
            "role_state": self.get("role_state"),
            "conflict_reports": self.get("conflict_reports"),
        }


# --------------------------- 使用示例 ---------------------------
if __name__ == "__main__":
    mem = SharedMemory(task_name="demo_task")
    mem.set("outline", [{"chapter_id": "ch1", "title": "A"}])
    sid1 = mem.snapshot("after_outline")

    mem.append("characters", {"name": "Alice"})
    mem.set("story", [{"chapter_id": "ch1", "plot": "Alice left."}])
    sid2 = mem.snapshot("after_story")

    print("diff:", json.dumps(mem.diff(sid1, sid2), ensure_ascii=False, indent=2))
    path = mem.save("data/output/memory_demo.json")
    mem2 = SharedMemory.load(path)
    print("loaded keys:", mem2.keys())
