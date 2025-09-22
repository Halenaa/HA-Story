# File: src/agent/agent_coordinator.py
# -*- coding: utf-8 -*-
"""
AgentCoordinator (Director Agent)
---------------------------------
- 统一调度各个专用 Agent/模块（大纲→重排→角色→情节→对话→冲突→修复→导出）。
- 依赖 A2: SharedMemory（黑板）进行读写、快照、回滚与审计。
- 提供 Hook 机制（before/after 每阶段）、失败回退策略、与性能分析器对接。
- 以“结构硬 / 内容软”为原则：这里控制流程与数据契约，内容由下游 LLM 生成。

用法见文件末尾的示例。
"""
from __future__ import annotations
from typing import Any, Dict, Callable, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


StageFn = Callable[..., Any]


@dataclass
class CoordinatorConfig:
    topic: str
    style: str
    generation_mode: str = "traditional"  # "traditional" | "description_based"
    reorder_mode: str = "linear"          # "linear" | "nonlinear"
    behavior_model: str = "gpt-4.1"
    temperature: float = 0.7
    seed: int = 42
    use_cache: bool = True
    enable_conflict_detection: bool = True
    enable_conflict_resolution: bool = True


class AgentCoordinator:
    """Director/Coordinator：负责调度、黑板读写、快照回滚、日志与容错。"""

    def __init__(self,
                 memory,
                 modules: Dict[str, StageFn],
                 config: CoordinatorConfig,
                 performance_analyzer: Optional[Any] = None,
                 hooks: Optional[Dict[str, Callable[[str, Dict[str, Any]], None]]] = None):
        """
        参数：
          - memory: SharedMemory 实例（A2）
          - modules: 依赖注入的阶段函数/类，键名约定见下（缺失则跳过）
          - config: 协调器配置
          - performance_analyzer: 可选性能分析器（你项目已有）
          - hooks: 可选钩子 dict，包含 on_stage_start/on_stage_end/on_error 三个回调
        """
        self.m = memory
        self.mod = modules
        self.cfg = config
        self.pa = performance_analyzer
        self.hooks = hooks or {}

    # --------------------------- 工具 ---------------------------
    def _hook(self, name: str, stage: str, payload: Dict[str, Any]):
        fn = self.hooks.get(name)
        if fn:
            try:
                fn(stage, payload)
            except Exception:
                pass

    def _start_stage(self, stage: str, meta: Dict[str, Any]):
        self._hook("on_stage_start", stage, meta)
        if self.pa:
            self.pa.start_stage(stage, meta)

    def _end_stage(self, stage: str, output: Any):
        if self.pa:
            self.pa.end_stage(stage, output)
        self._hook("on_stage_end", stage, {"output_keys": list(output.keys())} if isinstance(output, dict) else {"done": True})

    def _safe_call(self, stage: str, fn: StageFn, *args, snapshot_tag: Optional[str] = None, **kwargs) -> Tuple[bool, Any]:
        """带快照与异常捕获的调用。"""
        snap_id = self.m.snapshot(snapshot_tag or f"before_{stage}")
        try:
            self._start_stage(stage, {"args": list(map(type, args)), "kwargs": list(kwargs.keys())})
            out = fn(*args, **kwargs)
            self._end_stage(stage, {"ok": True})
            return True, out
        except Exception as e:
            # 回滚，并抛给上层或记录错误
            try:
                self.m.rollback(snap_id)
            except Exception:
                pass
            self._hook("on_error", stage, {"error": str(e)})
            return False, e

    # --------------------------- 主流程 ---------------------------
    def run(self, user_description: Optional[str] = None, file_content: Optional[str] = None) -> Dict[str, Any]:
        """执行完整流程。所有中间结果写入 SharedMemory。"""
        # ========== Stage 1: Outline ==========
        if "outline_generator" in self.mod:
            def _outline():
                if self.cfg.generation_mode == "traditional":
                    return self.mod["outline_generator"](
                        topic=self.cfg.topic,
                        style=self.cfg.style,
                        custom_instruction="",
                        generation_mode="traditional",
                        performance_analyzer=self.pa,
                    )
                else:
                    return self.mod["outline_generator"](
                        topic=self.cfg.topic,
                        style=self.cfg.style,
                        custom_instruction="",
                        generation_mode="description_based",
                        user_description=user_description,
                        file_content=file_content,
                        performance_analyzer=self.pa,
                    )
            ok, outline = self._safe_call("outline_generation", _outline, snapshot_tag="s1_outline")
            if not ok:
                raise RuntimeError(f"outline_generation failed: {outline}")
            self.m.set("outline", outline, meta={"stage": "outline_generation"})
        else:
            raise RuntimeError("missing module: outline_generator")

        # ========== Stage 2: Reorder (optional) ==========
        if self.cfg.reorder_mode == "nonlinear" and "reorder_chapters" in self.mod:
            ok, reordered = self._safe_call(
                "chapter_reorder",
                self.mod["reorder_chapters"],
                self.m.get("outline"),
                snapshot_tag="s2_reorder",
                mode="nonlinear",
                performance_analyzer=self.pa,
            )
            if not ok:
                # 失败则切回 linear
                reordered = self.m.get("outline")
            self.m.set("reordered_outline", reordered, meta={"stage": "chapter_reorder", "mode": self.cfg.reorder_mode})
        else:
            self.m.set("reordered_outline", self.m.get("outline"), meta={"stage": "chapter_reorder", "mode": "linear"})

        # ========== Stage 3: Characters ==========
        if "generate_characters" in self.mod:
            ok, chars = self._safe_call(
                "character_generation",
                self.mod["generate_characters"],
                self.m.get("reordered_outline"),
                snapshot_tag="s3_characters",
                performance_analyzer=self.pa,
            )
            if not ok:
                raise RuntimeError(f"character_generation failed: {chars}")
            self.m.set("characters", chars, meta={"stage": "character_generation"})
        else:
            raise RuntimeError("missing module: generate_characters")

        # ========== Stage 4: Story Expansion ==========
        if "expand_story" in self.mod:
            ok, story = self._safe_call(
                "story_expansion",
                self.mod["expand_story"],
                self.m.get("reordered_outline"),
                self.m.get("characters"),
                snapshot_tag="s4_story",
                custom_instruction="",
                performance_analyzer=self.pa,
            )
            if not ok:
                raise RuntimeError(f"story_expansion failed: {story}")
            # 统一补充 chapter_id/title（与现有代码风格一致）
            outline_map = {ch.get("chapter_id"): ch for ch in self.m.get("reordered_outline")}
            for ch in story:
                cid = ch.get("chapter_id")
                if cid in outline_map:
                    ch.setdefault("chapter_id", cid)
                    ch.setdefault("title", outline_map[cid].get("title"))
            self.m.set("story", story, meta={"stage": "story_expansion"})
        else:
            raise RuntimeError("missing module: expand_story")

        # ========== Stage 5: Dialogue (sentence-level) ==========
        if "dialogue_insertion" in self.mod:
            ok, dialog_out = self._safe_call(
                "dialogue_generation",
                self.mod["dialogue_insertion"],
                self.m.get("story"),
                self.m.get("characters"),
                snapshot_tag="s5_dialogue",
                performance_analyzer=self.pa,
            )
            if not ok:
                raise RuntimeError(f"dialogue_generation failed: {dialog_out}")
            chapter_results, sentence_results, behavior_timeline = dialog_out
            self.m.set("dialogue_marks", chapter_results, meta={"stage": "dialogue_generation"})
            self.m.set("sentence_dialogues", sentence_results, meta={"stage": "dialogue_generation"})
            self.m.set("behavior_timeline", behavior_timeline, meta={"stage": "dialogue_generation"})
        else:
            # 允许跳过对话阶段
            self.m.set("dialogue_marks", [], meta={"stage": "dialogue_generation", "skipped": True})
            self.m.set("sentence_dialogues", [], meta={"stage": "dialogue_generation", "skipped": True})
            self.m.set("behavior_timeline", [], meta={"stage": "dialogue_generation", "skipped": True})

        # ========== Stage 6: Role State ==========
        if "role_state_from_behavior" in self.mod:
            ok, role_state = self._safe_call(
                "role_state_build",
                self.mod["role_state_from_behavior"],
                self.m.get("behavior_timeline"),
                snapshot_tag="s6_role_state",
            )
            if not ok:
                raise RuntimeError(f"role_state_build failed: {role_state}")
            self.m.set("role_state", role_state, meta={"stage": "role_state_build"})

        # ========== Stage 7: Conflict Detection & Resolution ==========
        if self.cfg.enable_conflict_detection and "conflict_detector_factory" in self.mod:
            # 通过工厂注入，以便读取黑板聚合的上下文
            detector = self.mod["conflict_detector_factory"](self.m)
            reports = []
            # 这里示例：对 sentence_dialogues 的每一句做检测（你也可以改为 story 逐句）
            for item in self.m.get("sentence_dialogues") or []:
                sent = item.get("sentence", "")
                if not sent:
                    continue
                rep = detector.detect_conflicts(sent)
                reports.append({"chapter_id": item.get("chapter_id"), "sentence_index": item.get("sentence_index"), **rep})
            self.m.set("conflict_reports", reports, meta={"stage": "conflict_detection"})

            if self.cfg.enable_conflict_resolution and "conflict_resolver" in self.mod and reports:
                ok, resolved_story = self._safe_call(
                    "conflict_resolution",
                    self.mod["conflict_resolver"],
                    self.m.get("story"),
                    reports,
                    snapshot_tag="s7_resolution",
                )
                if ok and resolved_story:
                    self.m.set("story", resolved_story, meta={"stage": "conflict_resolution"})
        # ========== 完成 ==========
        # 打包常用输出返回
        return self.m.export_story_bundle()


# --------------------------- 用法示例 ---------------------------
if __name__ == "__main__":
    from src.memory.shared_memory import SharedMemory
    from src.generation.outline_generator import generate_outline
    from src.generation.chapter_reorder import reorder_chapters
    from src.generation.generate_characters import generate_characters_v1
    from src.generation.expand_story import expand_story_v1
    from src.generation.dialogue_inserter import analyze_dialogue_insertions_v2

    # 可选：你的行为轨迹→角色状态封装函数
    def role_state_from_behavior(behavior_trace):
        from collections import defaultdict
        role_state_by_chapter = defaultdict(lambda: defaultdict(set))
        for item in behavior_trace or []:
            role_state_by_chapter[item.get("chapter_id")][item.get("character")].add(item.get("behavior"))
        result = {}
        for ch, mp in role_state_by_chapter.items():
            result[ch] = {c: sorted(list(bs)) for c, bs in mp.items()}
        return result

    # 可选：冲突检测/解决（按需替换为你的实现）
    try:
        from src.agents.conflict_detector import ConflictDetector
        def conflict_detector_factory(memory):
            # 构造上下文（你可以改为更详细的历史拼接）
            history = "\n".join([s.get("sentence", "") for s in memory.get("sentence_dialogues") or []])
            characters = [c.get("name") for c in (memory.get("characters") or [])]
            timeline = [ch.get("title") for ch in (memory.get("story") or [])]
            return ConflictDetector({
                "history": history,
                "characters": characters,
                "prev_emotion": "neutral",
                "event_timeline": timeline
            })
    except Exception:
        conflict_detector_factory = None

    mem = SharedMemory(task_name="demo")

    modules = {
        "outline_generator": generate_outline,
        "reorder_chapters": reorder_chapters,
        "generate_characters": generate_characters_v1,
        "expand_story": expand_story_v1,
        "dialogue_insertion": analyze_dialogue_insertions_v2,
        "role_state_from_behavior": role_state_from_behavior,
    }
    if conflict_detector_factory:
        modules["conflict_detector_factory"] = conflict_detector_factory
        # modules["conflict_resolver"] = your_conflict_resolver

    cfg = CoordinatorConfig(topic="Little Red Riding Hood", style="Sci-fi rewrite", reorder_mode="linear")
    coor = AgentCoordinator(memory=mem, modules=modules, config=cfg, performance_analyzer=None)
    bundle = coor.run()
    # 现在 bundle 与 mem.export_story_bundle() 相同，可供后续渲染/评估使用
    print("pipeline keys:", list(bundle.keys()))
