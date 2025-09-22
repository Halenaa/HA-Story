# -*- coding: utf-8 -*-
"""
Conflict Severity Assessor (B2)
- 离散维度的规则引擎 + LLM微裁判，不使用数值加权
- 依赖：你的 SharedMemory / 章节plan / 角色记忆快照
- 输出：severity ∈ {NONE, LOW, MEDIUM, HIGH, CRITICAL} + reasons
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from src.utils.utils import generate_response, convert_json

SEVERITY = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

@dataclass
class ConflictSignals:
    temporal_violation: bool = False          # 时间顺序/呈现顺序冲突（含剧透）
    temporal_fixable_by_rewrite: bool = True  # 是否可通过 rewrite 局部修复
    spoiler_leak: bool = False                # 提前泄露未来信息（plan未授权）
    memory_inconsistency: bool = False        # 角色记忆/状态不一致
    memory_scope_cross_chapter: bool = False  # 是否跨章（更严重）
    world_fact_contradiction: bool = False    # 事实/设定冲突
    local_coherence_issue: bool = False       # 局部连贯/冗余
    redundancy_minor: bool = False            # 轻微重复/水
    details: Dict[str, Any] = None            # 附加说明（可写证据定位）

@dataclass
class ConflictDecision:
    severity: str
    reasons: List[str]
    signals: Dict[str, Any]

class ConflictSeverityAssessor:
    """
    用你的 plan、memory、当前章节文本/对话，先规则筛查，再 LLM 做二元微裁决（仅在不确定时）
    """
    def __init__(self):
        pass

    # ---- 1) 规则检测（可替换/扩展）----
    def compute_signals(self,
                        chapter_id: str,
                        sentence_text: str,
                        dialogue_block: List[Dict[str, str]],
                        *,
                        plan_scene_outline: Dict[str, Any],
                        memory_snapshot: Dict[str, Any],
                        global_story_facts: Dict[str, Any]) -> ConflictSignals:
        """
        用现有结构做快速启发式筛查：
        - 利用 plan_scene_outline (当前场景允许暴露的信息/事件)
        - 利用 memory_snapshot（角色应知/不应知、关系、心境）
        - 利用 global_story_facts（全局已定事实）
        - 对话中若出现未来事件关键词/未授权信息点 → spoiler_leak
        - 若“当前场景前置条件”在记忆/事实里不存在 → temporal_violation or world_fact_contradiction
        - 若情感/动机与 memory_snapshot 明显冲突 → memory_inconsistency
        """
        s = ConflictSignals(details={})

        # ---- 示例逻辑（你可以接你现有的轨迹与plan字段）----
        allowed_disclosures = set(plan_scene_outline.get("allowed_disclosures", []))
        future_events = set(global_story_facts.get("future_events", []))  # 计划中未来才会发生/披露的事件标识
        known_facts = set(global_story_facts.get("established_facts", []))
        # 将对话文本合并用于简单包含式检查（你也可以替换为更精细的抽取）
        dlg_concat = " ".join([turn.get("dialogue", "") for turn in dialogue_block])

        # 1) 剧透检测：对话里出现 future_event，但未在 allowed_disclosures 内
        for evt in future_events:
            if evt in dlg_concat and evt not in allowed_disclosures:
                s.spoiler_leak = True
                s.temporal_violation = True
                s.temporal_fixable_by_rewrite = False  # 通常不允许在此暴露
                s.details.setdefault("spoilers", []).append(evt)

        # 2) 事实/世界设定冲突
        for fact in known_facts:
            # 反例：对话是否否定了已确立事实？（这里可替换更稳健的抽取/对比）
            neg_pattern = f"不是{fact}"  # 简化示例；建议用信息抽取模块
            if neg_pattern in dlg_concat:
                s.world_fact_contradiction = True
                s.details.setdefault("contradicted_facts", []).append(fact)

        # 3) 角色记忆/状态冲突
        # 例如：memory_snapshot["Alice"]["knows"] 集合里没有 X，但台词表明她“知道X”
        for role, mem in (memory_snapshot or {}).items():
            known = set(mem.get("knows", []))
            prohibited = set(mem.get("should_not_know", []))
            # 这里同样建议换成谓词抽取，这里仅示例
            for k in prohibited:
                if k in dlg_concat:
                    s.memory_inconsistency = True
                    s.details.setdefault("memory_breach", []).append((role, k))
            # 情绪/动机可比对 mem["affect"], mem["motivation"] 与台词显性情绪（需情感分类器/LLM）

        # 4) 局部连贯/冗余（示例：上一句已叙述的信息被对白一模一样复述）
        # 你已有 sentence-level 结构，完全可比对。此处留一个简单启发：
        if len(dlg_concat) > 0 and len(dialogue_block) >= 2:
            # 若两个连续说话重复 n-gram 很高，可标记为冗余（此处略，给个开关）
            pass

        return s

    # ---- 2) 严重度映射（决策表，离散，不打分）----
    def map_to_severity(self, s: ConflictSignals) -> ConflictDecision:
        R: List[str] = []
        # 直接命中高优先级
        if s.spoiler_leak:
            R.append("CRITICAL: 提前泄露未来关键信息（plan未授权）")
            return ConflictDecision(severity="CRITICAL", reasons=R, signals=s.__dict__)

        if s.temporal_violation and not s.temporal_fixable_by_rewrite:
            R.append("HIGH/CRITICAL: 时间/因果冲突且不可由rewrite修复")
            return ConflictDecision(severity="HIGH", reasons=R, signals=s.__dict__)

        if s.memory_inconsistency and s.memory_scope_cross_chapter:
            R.append("HIGH: 跨章节角色记忆/状态不一致")
            return ConflictDecision(severity="HIGH", reasons=R, signals=s.__dict__)

        if s.world_fact_contradiction:
            R.append("MEDIUM/HIGH: 既有世界设定被否定")
            # 不立即给 CRITICAL，交由下步裁决
        if s.memory_inconsistency and not s.memory_scope_cross_chapter:
            R.append("MEDIUM: 同章角色记忆/状态冲突（可在本章修复）")

        if s.local_coherence_issue or s.redundancy_minor:
            R.append("LOW: 局部连贯/轻微冗余")

        # 归并：按最严重理由取值
        if any("CRITICAL" in r for r in R):
            sev = "CRITICAL"
        elif any("HIGH" in r for r in R):
            sev = "HIGH"
        elif any("MEDIUM" in r for r in R):
            sev = "MEDIUM"
        elif any("LOW" in r for r in R):
            sev = "LOW"
        else:
            sev = "NONE"; R.append("NONE: 未发现冲突")

        return ConflictDecision(severity=sev, reasons=R, signals=s.__dict__)

    # ---- 3) 不确定场景 → LLM 微裁判（仅 yes/no 升级/降级）----
    def llm_refine_if_needed(self, decision: ConflictDecision,
                             sentence_text: str,
                             dialogue_block: List[Dict[str, str]],
                             plan_scene_outline: Dict[str, Any]) -> ConflictDecision:
        """
        对 MEDIUM/HIGH 级别，用 LLM 询问一句：是否可以通过 rewrite 在当前场景内无损修复？
        YES → 降一级（HIGH→MEDIUM，MEDIUM→LOW）；NO → 维持。
        """
        if decision.severity in ("MEDIUM", "HIGH"):
            prompt = [{
                "role": "system",
                "content": f"""You are a story consistency judge.
Given the scene outline and a dialogue snippet, answer STRICT JSON:
{{"fixable_by_rewrite": true/false, "reason":"..."}}
Scene outline: {plan_scene_outline}
Sentence+Dialogue: {sentence_text} || {dialogue_block}"""
            }]
            try:
                res = generate_response(prompt)
                obj = convert_json(res)
                fixable = bool(obj.get("fixable_by_rewrite", False))
                if fixable and decision.severity == "HIGH":
                    return ConflictDecision(severity="MEDIUM",
                                            reasons=decision.reasons + ["LLM: 可rewrite修复 → 从HIGH降为MEDIUM"],
                                            signals=decision.signals)
                if fixable and decision.severity == "MEDIUM":
                    return ConflictDecision(severity="LOW",
                                            reasons=decision.reasons + ["LLM: 可rewrite修复 → 从MEDIUM降为LOW"],
                                            signals=decision.signals)
            except Exception:
                pass
        return decision

    # ---- 总入口 ----
    def assess(self,
               chapter_id: str,
               sentence_text: str,
               dialogue_block: List[Dict[str, str]],
               *,
               plan_scene_outline: Dict[str, Any],
               memory_snapshot: Dict[str, Any],
               global_story_facts: Dict[str, Any]) -> ConflictDecision:
        s = self.compute_signals(
            chapter_id, sentence_text, dialogue_block,
            plan_scene_outline=plan_scene_outline,
            memory_snapshot=memory_snapshot,
            global_story_facts=global_story_facts
        )
        decision = self.map_to_severity(s)
        decision = self.llm_refine_if_needed(decision, sentence_text, dialogue_block, plan_scene_outline)
        return decision

    """
    Conflict resolution策略器
    - 根据 severity 采取不同的修复/回滚/人工干预策略
    - 可以在 AgentCoordinator 调 dialogue_generation 后调用
    """
    def __init__(self):
        pass

    def resolve(self,
                decision: ConflictDecision,
                chapter_id: str,
                sentence_text: str,
                dialogue_block: List[Dict[str, str]],
                *,
                memory_snapshot: Dict[str, Any],
                plan_scene_outline: Dict[str, Any]) -> Dict[str, Any]:
        """
        返回 resolution_result dict:
        {
          "action": one of {"accept","rewrite_local","rewrite_scene","rollback","halt"},
          "severity": decision.severity,
          "reasons": decision.reasons,
          "notes": explanation string,
          "revised_dialogue": Optional[List[Dict[str,str]]]
        }
        """
        sev = decision.severity
        R = decision.reasons
        result = {
            "action": None,
            "severity": sev,
            "reasons": R,
            "notes": "",
            "revised_dialogue": None
        }

        if sev == "NONE":
            result["action"] = "accept"
            result["notes"] = "无冲突，直接接受输出"
            return result

        if sev == "LOW":
            # 局部轻微问题，可小改写
            result["action"] = "rewrite_local"
            result["notes"] = "轻微冗余/连贯问题 → 在本句级别微调或润色"
            # TODO: 调用 LLM 微改写函数，避免重复/冗余
            return result

        if sev == "MEDIUM":
            # 场景内冲突，可scene级 rewrite
            result["action"] = "rewrite_scene"
            result["notes"] = "场景内记忆不一致 → 整个场景级重写可修复"
            # TODO: 调用 rewrite_scene(chapter_id, plan_scene_outline, memory_snapshot)
            return result

        if sev == "HIGH":
            # 跨场景冲突，回滚上一状态
            result["action"] = "rollback"
            result["notes"] = "跨章记忆/时间因果冲突 → 回滚到上一个无冲突快照，触发重写"
            # TODO: 调用 rollback_and_regenerate(...)
            return result

        if sev == "CRITICAL":
            # 严重冲突 → 冻结 & 人工干预
            result["action"] = "halt"
            result["notes"] = "关键因果/剧透冲突 → 暂停生成，人工复核"
            return result

        # 默认fallback
        result["action"] = "accept"
        result["notes"] = "未识别严重度，默认接受"
        return result
