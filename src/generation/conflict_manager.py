from typing import List, Dict, Any

class ConflictDecision:
    """内部用来保存 Assessor 的判定结果"""
    def __init__(self, severity: str, reasons: List[str]):
        self.severity = severity
        self.reasons = reasons


class ConflictManager:
    """
    冲突检测 + 冲突解决（Assessor + Resolver 一体化）
    对外只暴露 check_and_resolve 接口
    """

    def __init__(self):
        pass

    # ========== 检测部分（Assessor） ==========
    def assess(self,
               chapter_id: str,
               sentence_text: str,
               dialogue_block: List[Dict[str, str]],
               plan_scene_outline: Dict[str, Any],
               memory_snapshot: Dict[str, Any],
               global_story_facts: Dict[str, Any]) -> ConflictDecision:
        """
        简化版冲突检测：输出 severity 等级 + reasons
        """
        reasons = []
        severity = "NONE"

        # 1. 角色记忆冲突检测
        for d in dialogue_block:
            spk = d.get("speaker")
            line = d.get("dialogue", "")
            if spk in memory_snapshot:
                if any(mem not in line for mem in memory_snapshot[spk]):
                    reasons.append(f"角色 {spk} 的记忆点缺失或不一致")

        # 2. 时间顺序冲突
        if "yesterday" in sentence_text and "tomorrow" in sentence_text:
            reasons.append("句子中出现时间矛盾")

        # 3. 世界事实冲突
        for fact_key, fact_val in global_story_facts.items():
            if fact_key in sentence_text and fact_val not in sentence_text:
                reasons.append(f"与世界事实 {fact_key} 不符")

        # 根据理由数量/严重性，分配等级
        if not reasons:
            severity = "NONE"
        elif len(reasons) == 1:
            severity = "LOW"
        elif len(reasons) == 2:
            severity = "MEDIUM"
        elif len(reasons) == 3:
            severity = "HIGH"
        else:
            severity = "CRITICAL"

        return ConflictDecision(severity, reasons)

    # ========== 解决部分（Resolver） ==========
    def resolve(self,
                decision: ConflictDecision,
                chapter_id: str,
                sentence_text: str,
                dialogue_block: List[Dict[str, str]],
                memory_snapshot: Dict[str, Any],
                plan_scene_outline: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据 severity 输出 resolution plan
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

        elif sev == "LOW":
            result["action"] = "rewrite_local"
            result["notes"] = "轻微冗余/连贯问题 → 在句子级别微调或润色"

        elif sev == "MEDIUM":
            result["action"] = "rewrite_scene"
            result["notes"] = "场景内记忆不一致 → 整个场景级重写"

        elif sev == "HIGH":
            result["action"] = "rollback"
            result["notes"] = "跨章因果冲突 → 回滚到上一个无冲突快照，触发重写"

        elif sev == "CRITICAL":
            result["action"] = "halt"
            result["notes"] = "关键因果/世界观冲突 → 暂停生成，人工复核"

        else:
            result["action"] = "accept"
            result["notes"] = "未知等级，默认接受"

        return result

    # ========== 对外统一接口 ==========
    def check_and_resolve(self,
                          chapter_id: str,
                          sentence_text: str,
                          dialogue_block: List[Dict[str, str]],
                          plan_scene_outline: Dict[str, Any],
                          memory_snapshot: Dict[str, Any],
                          global_story_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        一次调用 = 冲突检测 + 解决
        """
        decision = self.assess(
            chapter_id=chapter_id,
            sentence_text=sentence_text,
            dialogue_block=dialogue_block,
            plan_scene_outline=plan_scene_outline,
            memory_snapshot=memory_snapshot,
            global_story_facts=global_story_facts
        )
        resolution = self.resolve(
            decision,
            chapter_id=chapter_id,
            sentence_text=sentence_text,
            dialogue_block=dialogue_block,
            memory_snapshot=memory_snapshot,
            plan_scene_outline=plan_scene_outline
        )
        return resolution
