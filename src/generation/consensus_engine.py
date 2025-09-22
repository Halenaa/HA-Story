# -*- coding: utf-8 -*-
"""
ConsensusEngine
- 二类共识：
  (A) YES/NO 决策（如：是否插入对话）
  (B) 序等级严重度共识（如：NONE..CRITICAL）
- 支持：多数票/置信度加权、法定人数（quorum）、LLM平局裁决、审计理由链
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.utils.utils import generate_response, convert_json

SEVERITY_ORDER = ["NONE","LOW","MEDIUM","HIGH","CRITICAL"]
IDX = {s:i for i,s in enumerate(SEVERITY_ORDER)}

@dataclass
class YesNoVote:
    name: str
    label: bool               # True=YES, False=NO
    confidence: float = 1.0
    reason: str = ""

@dataclass
class SeverityVote:
    name: str
    label: str                # in SEVERITY_ORDER
    confidence: float = 1.0
    reason: str = ""

class ConsensusEngine:
    def __init__(self):
        pass

    # ---------- YES/NO 共识 ----------
    def consensus_yesno(self,
                        votes: List[YesNoVote],
                        *,
                        min_quorum: int = 2,
                        tie_breaker_hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        返回: {
          "final_label": bool,
          "method": "weighted"|"count"|"tie-break",
          "tally": {"yes_weight":..,"no_weight":..,"yes_count":..,"no_count":..,"met_quorum":..},
          "votes": [vote dict...]
        }
        """
        yes_w = sum(v.confidence for v in votes if v.label)
        no_w  = sum(v.confidence for v in votes if not v.label)
        y_c   = sum(1 for v in votes if v.label)
        n_c   = len(votes) - y_c
        met_quorum = max(y_c, n_c) >= min_quorum

        if yes_w != no_w:
            final = yes_w > no_w
            method = "weighted"
        elif y_c != n_c:
            final = y_c > n_c
            method = "count"
        else:
            # 平局 → LLM 极简裁判
            final = self._tie_break_yesno(tie_breaker_hint or {})
            method = "tie-break"

        return {
            "final_label": bool(final),
            "method": method,
            "tally": {
                "yes_weight": round(yes_w,4),
                "no_weight": round(no_w,4),
                "yes_count": y_c,
                "no_count": n_c,
                "met_quorum": met_quorum
            },
            "votes": [v.__dict__ for v in votes]
        }

    def _tie_break_yesno(self, hints: Dict[str, Any]) -> bool:
        prompt = [{
            "role": "system",
            "content": f"""You are a strict YES/NO arbiter.
Return STRICT JSON: {{"choose":"YES"|"NO"}}.
Hints: {hints}"""
        }]
        try:
            obj = convert_json(generate_response(prompt))
            return obj.get("choose","NO").upper() == "YES"
        except Exception:
            return False

    # ---------- 严重度序等级共识 ----------
    def consensus_severity(self,
                           votes: List[SeverityVote],
                           *,
                           fixable_hint: Optional[bool] = None,
                           tie_breaker_hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        规则：置信度加权平均到序号 → 四舍五入到最近等级；
        若落在两级中间或相等 → 若 fixable_hint=True 则选更低级，否则更高级；
        仍不定 → LLM 裁判。
        """
        if not votes:
            return {"final_severity": "NONE", "method": "empty", "tally": {}, "votes": []}

        # 过滤非法标签
        clean = [v for v in votes if v.label in SEVERITY_ORDER]
        if not clean:
            return {"final_severity": "NONE", "method": "invalid", "tally": {}, "votes": []}

        # 加权均值
        num = sum(IDX[v.label] * (v.confidence or 1.0) for v in clean)
        den = sum((v.confidence or 1.0) for v in clean)
        avg = num / den if den > 0 else 0.0

        # 近邻两级
        lower_idx = int(avg)
        upper_idx = min(lower_idx + 1, len(SEVERITY_ORDER)-1)
        # 四舍五入
        nearest = round(avg)
        candidates = set([nearest, lower_idx, upper_idx])

        # 单候选
        if len(candidates) == 1:
            final_idx = list(candidates)[0]
            return {
                "final_severity": SEVERITY_ORDER[final_idx],
                "method": "weighted-average",
                "tally": {"avg": avg, "votes": len(clean)},
                "votes": [v.__dict__ for v in clean]
            }

        # 两候选/三候选 → 用 fixable_hint 决策
        if fixable_hint is not None:
            if fixable_hint:
                final_idx = min(candidates)
                method = "fixable-lower"
            else:
                final_idx = max(candidates)
                method = "fixable-higher"
            return {
                "final_severity": SEVERITY_ORDER[final_idx],
                "method": method,
                "tally": {"avg": avg, "votes": len(clean)},
                "votes": [v.__dict__ for v in clean]
            }

        # 仍不定 → LLM 裁判（倾向高一档以保守）
        final = self._tie_break_severity(tie_breaker_hint or {})
        return {
            "final_severity": final,
            "method": "tie-break",
            "tally": {"avg": avg, "votes": len(clean)},
            "votes": [v.__dict__ for v in clean]
        }

    def _tie_break_severity(self, hints: Dict[str, Any]) -> str:
        prompt = [{
            "role": "system",
            "content": f"""You are a severity arbiter on an ordinal scale {SEVERITY_ORDER}.
Return STRICT JSON: {{"choose":"NONE|LOW|MEDIUM|HIGH|CRITICAL"}}.
Hints: {hints}"""
        }]
        try:
            obj = convert_json(generate_response(prompt))
            ch = str(obj.get("choose","HIGH")).upper()
            return ch if ch in SEVERITY_ORDER else "HIGH"
        except Exception:
            return "HIGH"
