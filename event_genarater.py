import os
import json
import asyncio
import erniebot
import myKeys

from erniebot_agent.agents import FunctionAgent
from erniebot_agent.chat_models import ERNIEBot
from erniebot_agent.tools import RemoteToolkit
from erniebot_agent.chat_models.erniebot import ERNIEBot
from erniebot_agent.memory import HumanMessage, AIMessage, SystemMessage, FunctionMessage

def load_dataset(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    

async def main():
    os.environ["EB_AGENT_ACCESS_TOKEN"] = myKeys.EB_AGENT_ACCESS_TOKEN
    ## 加载event_setting文件作为string
    with open('event_setting.json', 'r', encoding='utf-8') as f:
        event_setting = f.read()
    system_message = SystemMessage(content="你是一个星际大冒险知识科普游戏的事件设计师，你需要根据以下的科普问答知识来制作一个游戏事件。"
                                   "事件需要以科普知识为主要目的，作为激发儿童好奇心的引子。"
                                   "有三种事件类型：人物交流characterInteraction, 选择choice。"
                                   "人物交流characterInteraction：需要和玩家以外的事件人物对话交流，完成事件人物的目的，在eventOptions给出交涉成功和失败的选项，选项需表现出玩家与人物交流的态度，尽量不涉及具体事件内容；"
                                   "选择choice：需要给出eventOptions选项供玩家选择；"
                                   "你需要直接输出以下json格式的事件：" + event_setting
                                   )
    model = ERNIEBot(model="ernie-3.5", system=system_message.content)

    questions_list = load_dataset("data/data.json")
    event_list = []
    test_questions = questions_list[:10]
    for question in test_questions:
        messages = [HumanMessage(content=json.dumps(question, ensure_ascii=False))]
        ai_message = await model.chat(messages=messages)
        print("----------------------------------------------------")
        print(ai_message.content)
        try :
            # 删除```json```
            content = ai_message.content.replace("```json", "").replace("```", "")
            event_list.append(json.loads(content))
        except:
            print("json load error: ", content)

    # 保存event_list
    with open("data/event_list.json", 'w', encoding='utf-8') as f:
        json.dump(event_list, f, ensure_ascii=False)
    

asyncio.run(main())