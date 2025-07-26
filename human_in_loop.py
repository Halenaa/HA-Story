
import json
import yaml
from langchain_openai import ChatOpenAI
from src.constant import output_dir
from src.utils.utils import convert_json
version = "test"

with open(r"D:\WorkSpace\PycharmFile\rewrite_story_refactor\data\prompt\prompt.yaml", "r", encoding="utf-8") as file:
    prompt = yaml.load(file, Loader=yaml.FullLoader)

class DialogueAgent:
    def __init__(
            self,
            name: str,
            system_message,
            model: ChatOpenAI,
    ) -> None:
        self.name = name
        self.system_message = system_message
        self.model = model
        self.prefix = f"{self.name}: "
        self.reset()

    def reset(self):
        self.message_history = ["Here is the conversation so far."]

    def send(self, sentence, mode) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        message = self.model.invoke(
            [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": f"""
                                          历史对话（如有）：
                                          {self.message_history}

                                          当前需要你为这句叙述生成一段符合语境的{mode}**：
                                          "{sentence}"
                                            # 输出格式：
                                          {{
                                            "output": "你的{mode}",
                                            "action": "结合当前场景你可能出现的动作或神态，如果你认为不需要动作可以直接返回：\"" "
                                          }}
                                          """}
            ]
        )
        return message.content

    def update_story(self, sentence: str):
        self.message_history.append(sentence)

    def receive(self, character_output: dict, mode: str, curr_speaker: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        if mode == "dialogue":
            self.message_history.append(f"{curr_speaker}-dialogue: {character_output['output']}")
        else:
            if curr_speaker == self.name:  # 如果是自己就加，不是自己的独白就不加
                self.message_history.append(f"{curr_speaker}-monologue: {character_output['output']}")

        if character_output['action']:
            self.message_history.append(f"{curr_speaker}-action: {character_output['action']}")

with open(f"{output_dir}/{version}/characters.json", "r", encoding="utf-8") as f:
    characters = json.load(f)
with open(f"{output_dir}/{version}/story.json", "r", encoding="utf-8") as f:
    story = json.load(f)
test_story = story[0]

characters_agents = []
for character_name in test_story['characters']:
    characters_agents.append(
        DialogueAgent(
            name=character_name,
            system_message=prompt["character"].format(speaker_info=[i for i in characters if i['name'] ==character_name] [0],
                                                      plot=test_story['plot'],
                                                      scene=test_story['scene'],
                                                      ),
            model=ChatOpenAI(temperature=0.7, model="gpt-4.1",api_key="sk-CacjJcrne1O3wM8CXosEy14IpvwJYXlJsZd3703M9ybfn5x5", base_url="https://api.chatanywhere.com.cn/v1",),
        )
    )


def handler_each_plot_manual(story):
    plot = story['plot']
    characters_list = story['characters']
    scene = story['scene']

    sentences = [item for item in plot.split("。") if item]
    scriptwriter_history = []
    run_history = []

    for inx, sentence in enumerate(sentences, start=1):
        print(f"\n🎬 第{inx}句：{sentence}")
        scriptwriter_history.append(sentence)

        while True:
            print("\n 当前对话上下文：")
            print("\n".join(scriptwriter_history))

            # 👇 人工输入替代 select_next_character
            need_to_talk = int(input("是否需要说话?（1=需要, 0=跳过）: "))
            if need_to_talk == 0:
                scriptwriter_output = {"need_to_talk": 0}
                run_history.append({"scene": sentence})
                run_history.append({"scriptwriter_output": scriptwriter_output})
                break

            actor = input("选择发言角色名: ")
            mode = input("选择发言模式（dialogue 或 monologue）: ")
            scriptwriter_output = {
                "need_to_talk": 1,
                "actor": actor,
                "mode": mode
            }

            run_history.append({"scene": sentence})
            run_history.append({"scriptwriter_output": scriptwriter_output})
            print(f"👉 角色 {actor} 将以 {mode} 方式发言")

            speaker = next(each for each in characters_agents if each.name == actor)
            message = speaker.send(sentence=sentence, mode=mode)
            character_output = convert_json(message)
            print(character_output)

            for receiver in characters_agents:
                receiver.receive(
                    character_output=character_output,
                    mode=mode,
                    curr_speaker=actor
                )

            run_history.append({
                "character_output": f"{actor}-{mode}: {character_output['output']}"
            })
            run_history.append({
                "character_action": f"{actor}: {character_output['action']}"
            })

            scriptwriter_history.append(f"{actor}-{mode}: {character_output['output']}")
            scriptwriter_history.append(f"{actor}: {character_output['action']}")

    return scriptwriter_history, run_history

if __name__ == "__main__":
    handler_each_plot_manual(test_story)