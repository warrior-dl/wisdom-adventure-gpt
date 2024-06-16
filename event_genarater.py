import os
import json
import asyncio
import erniebot
import myKeys

from langchain_community.chat_models import QianfanChatEndpoint
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

def load_dataset(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    

async def main():
    os.environ["EB_AGENT_ACCESS_TOKEN"] = myKeys.EB_AGENT_ACCESS_TOKEN
    os.environ["QIANFAN_AK"] = myKeys.QIANFAN_AK
    os.environ["QIANFAN_SK"] = myKeys.QIANFAN_SK
    os.environ["LANGCHAIN_TRACING_V2"]="true"
    os.environ["LANGCHAIN_API_KEY"]="ls__c0012d47edfc4b3a8c19c40242a3521e"
    ## 加载event_setting文件作为string
    with open('event_setting.json', 'r', encoding='utf-8') as f:
        event_setting = f.read()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个星际大冒险知识科普游戏的事件设计师，你需要根据以下的科普问答知识来制作一个游戏事件。"
                                   "事件需要以科普知识为主要目的，作为激发儿童好奇心的引子，但是不要生硬的直接以科普为目的，而是应该在玩家推进事件的过程中激发儿童好奇。"
                                   "有两种事件类型：人物交流characterInteraction, 选择choice。"
                                   "人物交流characterInteraction：需要和玩家以外的事件人物对话交流，完成事件人物的目的，在eventOptions给出交涉成功和失败的选项，选项需表现出玩家与人物交流的态度，尽量不涉及具体事件内容；"
                                   "选择choice：需要给出eventOptions选项供玩家选择；"
                                   "你需要直接输出以下json格式的事件：{event_setting}"),
            ("human", "{knowledge}"),
        ]
    )

    #model = ERNIEBot(model="ernie-3.5", system=system_message.content)
    model = QianfanChatEndpoint(model="ERNIE-Speed-8K")
    questions_list = load_dataset("data/data.json")
    event_list = []
    test_questions = questions_list[:50]
    chain  = prompt | model | StrOutputParser()
    for question in test_questions:
        ai_message = chain.invoke({"event_setting": event_setting, "knowledge": json.dumps(question, ensure_ascii=False)})
        print("----------------------------------------------------")
        print(ai_message)
        try :
            # 删除```json```
            content = ai_message.replace("```json", "").replace("```", "")
            event_list.append(json.loads(content))
        except:
            print("json load error: ", content)

    # 保存event_list
    with open("data/event_list.json", 'w', encoding='utf-8') as f:
        json.dump(event_list, f, ensure_ascii=False)
    

asyncio.run(main())