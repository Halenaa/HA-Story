import os
import yaml
from langchain_openai import ChatOpenAI
from src.utils.utils import convert_json

# 加载 config/prompt.yaml
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
            temperature=0.9,
            model="gpt-4o",
            api_key=os.getenv("OPENAI_KEY"),
            base_url="https://api.chatanywhere.com.cn/v1"
        )
        self.reset()

    def reset(self):
        self.message_history = ["Here is the conversation so far."]

    def send(self, sentence, mode="dialogue") -> dict:
        prompt = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": f"""
历史对话：
{self.message_history}

请你为这句剧情生成一段符合语境的{mode}：
\"{sentence}\"

输出格式：
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
