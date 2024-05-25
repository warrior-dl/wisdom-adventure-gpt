import os
import json
import asyncio
import erniebot

from erniebot_agent.agents import FunctionAgent
from erniebot_agent.chat_models import ERNIEBot
from erniebot_agent.tools import RemoteToolkit
from erniebot_agent.chat_models.erniebot import ERNIEBot
from erniebot_agent.memory import HumanMessage, AIMessage, SystemMessage, FunctionMessage

def load_dataset(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    

async def main():
    os.environ["EB_AGENT_ACCESS_TOKEN"] = "c65601e18d2fa9f4e8c39d9d7947303eade35507"
    event_setting = """
{  
  "eventName": "遭遇事件名称",  
  "eventContent": "这里是关于遭遇事件的详细描述。",  
  "eventType": "characterInteraction|choice|resourceDecision", // characterInteraction:人物交流 choice:选择 resourceDecision:资源判定
  "eventCharacters": {  
    "background": "事件NPC人物的背景信息。",  
    "purpose": "事件NPC人物的目的或动机。"  
  },  // 如果不必要则不需要添加
  "eventOptions": [  
    {  
      "optionId": 1, // 可以是序号、标识符或其他唯一值  
      "optionContent": "选项的具体描述或提示。",  
      "result": "选择此选项后的结果描述。", 
      "award": {
        "key": "stellarCurrency|shipEnergy|explorationCapability|reputationValue",
        "value": 5 // 惩罚则为负数
      },
      "precondition": {  
        "operator": "<|>",  
        "threshold": 20,  
        "key": "stellarCurrency|shipEnergy|explorationCapability|reputationValue"  
      }    //需要满足的条件才能选择此选项
    },  
    {  
      "optionId": 2,  
      "optionContent": "另一个选项的具体描述或提示。",  
      "result": "选择此选项后的结果描述。"  
      // ...  
    }
  ]  // eventType不是choice时只有一个选项
}"""
    system_message = SystemMessage(content="你是一个星际大冒险知识科普游戏的事件设计师，你需要根据以下的科普问答知识来制作一个游戏事件。"
                                   "事件需要以科普知识为主要目的，作为激发儿童好奇心的引子。"
                                   "有三种事件类型：人物交流characterInteraction, 选择choice和资源判定事件resourceDecision。"
                                   "人物交流characterInteraction：需要和玩家以外的NPC对话交流，完成NPC的目的，在eventOptions给出交涉成功和失败的选项；"
                                   "选择choice：需要给出eventOptions选项供玩家选择；"
                                   "资源判定事件resourceDecision：需要对NPC的资源进行判定，在eventOptions给出判定成功和失败的选项。"
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
        # print(ai_message.content)
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