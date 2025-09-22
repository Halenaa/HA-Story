# File: src/decision/dialogue_affordance_decider.py
# -*- coding: utf-8 -*-
"""
Dialogue Affordance (No-Numeric) Decision
----------------------------------------
• 目标：在不使用任何“数值权重/阈值/关键词表”的情况下，决定一句话之后是否插入对话。
• 方法：两阶段 ——
  (1) LLM 分类器输出**离散标签**（Presence ∈ {AFFIRMED/UNCERTAIN/DENIED}；
      Intensity ∈ {HIGH/MED/LOW}；Info ∈ {HIGH/MED/LOW}；Pacing ∈ {ENCOURAGE/HOLD}），并给出依据。
  (2) 符号化规则本（Decision Table）执行**无数字**的层级裁决；仅用优先级与布尔逻辑；
      如：Presence=DENIED → 否决；Intensity=HIGH → 插入；否则根据 (Info,Pacing) 做合议；
      边界情况交给 LLM 进行二元裁决（仅 yes/no，非内容生成）。
• Presence 的定义（避免“句内找人名”的伪逻辑）：
  - 以**共享记忆**中的 scene participants（最近场景参与者集合）与“位置/视角连续性”推断在场；
  - 若句子为场景叙述（无显式姓名），可由 LLM 依据**上一句的说话人/场景切换提示**判定 AFFIRMED/UNCERTAIN；
  - 支持“屏外沟通”（电话/无线电）等情形；
  - 不依赖关键词表，完全基于语义判别（中英皆可）。
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Callable

from src.utils.utils import generate_response, convert_json

# ---------------- Enums as strings ----------------
PRESENCE = ["AFFIRMED", "UNCERTAIN", "DENIED"]
INTENSITY = ["HIGH", "MED", "LOW"]
INFO = ["HIGH", "MED", "LOW"]
PACING = ["ENCOURAGE", "HOLD"]


@dataclass
class AffordanceLabels:
    presence: str
    intensity: str
    info: str
    pacing: str
    justifications: Dict[str, str]


class DialogueAffordanceClassifier:
    """调用 LLM 产出离散标签（无数字）。"""
    def __init__(self):
        pass

    def classify(self,
                 sentence: str,
                 *,
                 local_context: str = "",
                 global_context: str = "",
                 scene_participants: Optional[List[str]] = None,
                 last_speaker: Optional[str] = None,
                 channel: Optional[str] = None  # e.g., face_to_face / phone / radio
                 ) -> AffordanceLabels:
        scene_participants = scene_participants or []
        prompt = [{
            "role": "system",
            "content": f"""
You are a narratology-aware classifier. For the given context, assign discrete labels without numbers.
Return STRICT JSON with:
- presence ∈ {{AFFIRMED, UNCERTAIN, DENIED}}  // dialogue affordance given participants & continuity
- intensity ∈ {{HIGH, MED, LOW}}               // dramatic tension / conflict around this point
- info ∈ {{HIGH, MED, LOW}}                    // information gain by using dialogue here
- pacing ∈ {{ENCOURAGE, HOLD}}                 // whether dialogue helps pacing or should hold
- justifications: a map of short textual reasons for each label

Guidelines (semantic, no keyword lists):
• Presence considers scene participants, spatial/temporal continuity, narrator viewpoint, off-screen channels (phone/radio), and whether immediate exchange is plausible even if no names appear in the sentence.
• Intensity considers stakes, confrontation, secrets, dilemmas, or decision points implied by the context.
• Info considers whether dialogue would clarify motives/facts/relationships better than narration now.
• Pacing considers rhythm after long exposition or to avoid redundancy; set HOLD if dialogue would stall.

Input:
- Sentence: {sentence}
- Local context: {local_context}
- Global context: {global_context}
- Scene participants: {scene_participants}
- Last speaker: {last_speaker}
- Channel hint: {channel}

Return STRICT JSON:
{{
  "presence": "AFFIRMED|UNCERTAIN|DENIED",
  "intensity": "HIGH|MED|LOW",
  "info": "HIGH|MED|LOW",
  "pacing": "ENCOURAGE|HOLD",
  "justifications": {{"presence": "...", "intensity": "...", "info": "...", "pacing": "..."}}
}}
"""
        }]
        res = generate_response(prompt)
        obj = convert_json(res)
        # 合法性与回退
        def norm(v: str, space: List[str], default: str) -> str:
            v = str(v).upper()
            return v if v in space else default
        labels = AffordanceLabels(
            presence=norm(obj.get("presence"), PRESENCE, "UNCERTAIN"),
            intensity=norm(obj.get("intensity"), INTENSITY, "LOW"),
            info=norm(obj.get("info"), INFO, "LOW"),
            pacing=norm(obj.get("pacing"), PACING, "HOLD"),
            justifications=obj.get("justifications", {}) or {}
        )
        return labels


# ---------------- Symbolic Decision (no numbers) ----------------
@dataclass
class Decision:
    need: int
    label_snapshot: Dict[str, str]
    reasons: List[str]

class SymbolicDialogueDecider:
    """不使用数值，基于决策表与优先级进行裁决。"""
    def __init__(self,
                 llm_tiebreaker: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
                 cooldown: bool = True):
        self.cooldown = cooldown
        self.llm_tiebreaker = llm_tiebreaker or self.default_llm_tiebreaker

    def decide(self,
               labels: AffordanceLabels,
               *,
               last_inserted: bool = False,
               sentence_text: str = "",
               local_context: str = "",
               global_context: str = "") -> Decision:
        R: List[str] = []
        L = labels

        # 1) Veto
        if L.presence == "DENIED":
            R.append("VETO: presence=DENIED → 不插入")
            return Decision(need=0, label_snapshot=asdict(L), reasons=R)

        # Presence affirmed/uncertain 的解释
        if L.presence == "AFFIRMED":
            R.append("presence=AFFIRMED（在场或可对话的情境被确认）")
        else:
            R.append("presence=UNCERTAIN（语义上可能，但需谨慎）")

        # 2) Hard trigger
        if L.intensity == "HIGH":
            R.append("HARD TRIGGER: intensity=HIGH → 插入")
            return Decision(need=1, label_snapshot=asdict(L), reasons=R)

        # 3) Cooldown（避免连发）
        if self.cooldown and last_inserted and L.intensity != "HIGH":
            if L.pacing != "ENCOURAGE":
                R.append("COOLDOWN: 上句刚插入且非高强度，且 pacing!=ENCOURAGE → 不插入")
                return Decision(need=0, label_snapshot=asdict(L), reasons=R)
            else:
                R.append("COOLDOWN passed: pacing=ENCOURAGE 允许紧跟插入")

        # 4) Quorum（两票同意）
        votes = 0
        if L.intensity == "MED":
            votes += 1; R.append("vote: intensity=MED")
        if L.info == "HIGH":
            votes += 1; R.append("vote: info=HIGH")
        if L.pacing == "ENCOURAGE":
            votes += 1; R.append("vote: pacing=ENCOURAGE")

        if votes >= 2 and L.presence != "UNCERTAIN":
            R.append("QUORUM PASS: 两票同意 + presence 确认 → 插入")
            return Decision(need=1, label_snapshot=asdict(L), reasons=R)

        # 5) Tie-break（信息高但强度低时，由节奏打破）
        if L.info == "HIGH" and L.intensity == "LOW":
            if L.pacing == "ENCOURAGE" and L.presence != "UNCERTAIN":
                R.append("TIE-BREAK: info=HIGH & intensity=LOW & pacing=ENCOURAGE → 插入")
                return Decision(need=1, label_snapshot=asdict(L), reasons=R)
            else:
                R.append("TIE-BREAK: info=HIGH 但强度低且节奏不支持 → 不插入")
                return Decision(need=0, label_snapshot=asdict(L), reasons=R)

        # 6) 仍不确定 → LLM 二元裁决
        R.append("UNDECIDED → 交给 LLM 二元裁决（仅 yes/no）")
        yes = self.llm_tiebreaker(sentence_text, {
            "presence": L.presence,
            "intensity": L.intensity,
            "info": L.info,
            "pacing": L.pacing,
            "local_context": local_context,
            "global_context": global_context
        })
        R.append("LLM 裁决 → {}".format("插入" if yes else "不插入"))
        return Decision(need=1 if yes else 0, label_snapshot=asdict(L), reasons=R)

    # ---- 最小化 LLM 裁决器：返回 {"insert": true/false} ----
    def default_llm_tiebreaker(self, sentence_text: str, features: Dict[str, Any]) -> bool:
        prompt = [{
            "role": "system",
            "content": f"""
You are a dialogue insertion judge. Decide YES/NO only.
Return STRICT JSON: {{"insert": true/false, "reason": "..."}}
Sentence: {sentence_text}
Hints: {features}
"""
        }]
        try:
            res = generate_response(prompt)
            obj = convert_json(res)
            return bool(obj.get("insert", False))
        except Exception:
            return False


# ---------------- Integration Sketch ----------------
# 示例：在 analyze_dialogue_insertions_v2 的句子循环前
if __name__ == "__main__":
    sentence = "她盯着封口的信，迟疑着把它递给他。"
    local = "窗外下着雨。他刚到，明显回避她的视线。"
    glob = "本章关于她与他对多年隐瞒的真相的摊牌。"
    participants = ["她", "他"]  # 来自 SharedMemory 的 scene participants

    clf = DialogueAffordanceClassifier()
    labels = clf.classify(sentence, local_context=local, global_context=glob, scene_participants=participants)

    decider = SymbolicDialogueDecider(cooldown=True)
    decision = decider.decide(labels, last_inserted=False, sentence_text=sentence, local_context=local, global_context=glob)

    print(decision.need, decision.reasons)
