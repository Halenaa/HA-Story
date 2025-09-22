import json
from typing import List, Dict
from src.utils.utils import generate_response, convert_json

class ConflictDetector:
    """
    ConflictDetector agent for detecting narrative contradictions, entity inconsistencies,
    emotional shifts, and event ordering issues.
    """

    def __init__(self, memory: Dict):
        """
        Initialize with shared memory, including prior events, character states, etc.
        """
        self.memory = memory  # Expect keys like 'history', 'character_states', 'event_timeline'

    def detect_conflicts(self, current_sentence: str) -> Dict:
        """
        Detect various types of conflicts in current sentence against memory.
        Returns a structured report.
        """
        return {
            "contradiction": self._detect_contradiction(current_sentence),
            "entity_issue": self._check_entity_consistency(current_sentence),
            "emotion_shift": self._check_emotion_shift(current_sentence),
            "temporal_issue": self._check_temporal_order(current_sentence)
        }

    def _detect_contradiction(self, sentence: str) -> Dict:
        prompt = f"""
You are a contradiction critic. Check whether the following current sentence contradicts the previous story context.

Context:
{self.memory.get('history', '')}

Current sentence:
{sentence}

Return strictly JSON in the format:
{{"conflict": true/false, "reason": "..."}}
        """
        try:
            response = generate_response([{"role": "user", "content": prompt}])
            return convert_json(response)
        except:
            return {"conflict": False, "reason": "Check failed"}

    def _check_entity_consistency(self, sentence: str) -> Dict:
        characters = self.memory.get("characters", [])
        prompt = f"""
You are an entity consistency checker. From the sentence below, determine if any character appears who should not be present based on the memory.

Characters present so far: {characters}

Current sentence:
{sentence}

Return JSON:
{{"issue": true/false, "reason": "..."}}
        """
        try:
            response = generate_response([{"role": "user", "content": prompt}])
            return convert_json(response)
        except:
            return {"issue": False, "reason": "Check failed"}

    def _check_emotion_shift(self, sentence: str) -> Dict:
        previous_emotion = self.memory.get("prev_emotion", "neutral")
        prompt = f"""
Check if the emotional tone in the following sentence shifts abruptly from the previous emotion: {previous_emotion}

Sentence:
{sentence}

Return JSON:
{{"emotion_shift": true/false, "reason": "..."}}
        """
        try:
            response = generate_response([{"role": "user", "content": prompt}])
            return convert_json(response)
        except:
            return {"emotion_shift": False, "reason": "Check failed"}

    def _check_temporal_order(self, sentence: str) -> Dict:
        timeline = self.memory.get("event_timeline", [])
        prompt = f"""
Check if the following sentence presents a temporal contradiction based on the event timeline:
{timeline}

Sentence:
{sentence}

Return JSON:
{{"temporal_conflict": true/false, "reason": "..."}}
        """
        try:
            response = generate_response([{"role": "user", "content": prompt}])
            return convert_json(response)
        except:
            return {"temporal_conflict": False, "reason": "Check failed"}


# Example usage:
if __name__ == "__main__":
    dummy_memory = {
        "history": "Anna left the room in tears. The others remained silent.",
        "characters": ["Anna", "Tom", "Lisa"],
        "prev_emotion": "sad",
        "event_timeline": ["Anna leaves the room", "Tom comforts Lisa"]
    }

    detector = ConflictDetector(dummy_memory)
    result = detector.detect_conflicts("Anna suddenly smiled and walked back in cheerfully.")
    print(json.dumps(result, indent=2, ensure_ascii=False))