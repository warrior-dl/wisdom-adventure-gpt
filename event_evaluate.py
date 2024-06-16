import os
import json
import asyncio
import erniebot
import myKeys
import re

from erniebot_agent.agents import FunctionAgent
from erniebot_agent.chat_models import ERNIEBot
from erniebot_agent.tools import RemoteToolkit
from erniebot_agent.chat_models.erniebot import ERNIEBot
from erniebot_agent.memory import HumanMessage, AIMessage, SystemMessage, FunctionMessage

def load_event_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    

async def main():
    os.environ["EB_AGENT_ACCESS_TOKEN"] = myKeys.EB_AGENT_ACCESS_TOKEN

    example = '''{"reasonableness": 5, "interest": 5, "popularize": 5, "options": 5}'''
    system_message = SystemMessage(content="你是一个星际大冒险知识科普游戏的事件设计师，你需要对以下的游戏事件进行评分。"
                                            "评分分为四个维度：事件合理性、事件趣味性、事件科普有利性、选项区分度。每个维度1-10分"
                                            "你需要直接输出以下json格式的评分：" + example
                                   )
    model = ERNIEBot(model="ernie-3.5", system=system_message.content)

    event_list = load_event_list("data/event_list.json")
    event_evaluate = []

    for i in range(len(event_list)):
        question = event_list[i]
        messages = [HumanMessage(content=json.dumps(question, ensure_ascii=False))]
        ai_message = await model.chat(messages=messages)
        print("----------------------------------------------------")
        # print(ai_message.content)
        try :
            content = ai_message.content
            pattern = r'\{.*?\}'
            # 通过re.compile编译正则表达式并设置re.DOTALL标志
            regex = re.compile(pattern, re.DOTALL)
            # 使用findall方法找到所有匹配项
            matches = regex.findall(content)
            print("matches:", matches[0])
            evaluate = json.loads(matches[0])
            item = {"id": i, "evaluate": evaluate}
            event_evaluate.append(item)
        except:
            print("json load error: ", content)

    # 保存event_list
    with open("data/event_evaluate.json", 'w', encoding='utf-8') as f:
        json.dump(event_evaluate, f, ensure_ascii=False)
    

asyncio.run(main())