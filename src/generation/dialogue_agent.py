import os
import yaml
from langchain_openai import ChatOpenAI
from src.utils.utils import convert_json

# Load config/prompt.yaml
def load_prompt():
    path = os.path.join("config", "prompt.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

PROMPT_TEMPLATE = load_prompt()

class DialogueAgent:
    def __init__(self, name, speaker_info, plot, scene, model=None):
        self.name = name
        self.plot = plot
        self.scene = scene
        self.prefix = f"{self.name}: "
        self.system_message = PROMPT_TEMPLATE["character"].format(
            speaker_info=speaker_info,
            plot=plot,
            scene=scene
        )
        self.model = model or ChatOpenAI(
            temperature=0.7,
            model="gpt-4.1",
            api_key=os.getenv("CLAUDE_KEY"),
            base_url="CLAUDE_API_BASE"
        )
        self.reset()

    def reset(self):
        self.message_history = ["Here is the conversation so far."]

    def send(self, sentence, mode="dialogue") -> dict:
        prompt = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": f"""
Dialogue history:
{self.message_history}

Please generate contextually appropriate {mode} for this plot sentence:
\"{sentence}\"

Output format:
{{
  "output": "...",
  "action": "..."
}}
"""}
        ]
        response = self.model.invoke(prompt)
        return convert_json(response.content)

    def receive(self, character_output: dict, mode: str, curr_speaker: str):
        if mode == "dialogue":
            self.message_history.append(f"{curr_speaker}-dialogue: {character_output['output']}")
        elif curr_speaker == self.name:
            self.message_history.append(f"{curr_speaker}-monologue: {character_output['output']}")
        if character_output.get("action"):
            self.message_history.append(f"{curr_speaker}-action: {character_output['action']}")
