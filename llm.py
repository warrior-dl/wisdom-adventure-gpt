
import time
import os
import asyncio
import myKeys
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from erniebot_agent.extensions.langchain.chat_models import ErnieBotChat
from langchain_core.output_parsers import StrOutputParser
from loguru import logger

from erniebot_agent.chat_models import ERNIEBot
from erniebot_agent.memory import HumanMessage, SlidingWindowMemory
from erniebot_agent.tools.base import Tool
from erniebot_agent.tools.schema import ToolParameterView
from erniebot_agent.agents import FunctionAgent
from erniebot_agent.tools import RemoteToolkit
from erniebot_agent.file import GlobalFileManagerHandler

from erniebot_agent.extensions.langchain.llms import ErnieBot


class LLM:
    def __init__(self):
        os.environ["EB_AGENT_LOGGING_LEVEL"] = "INFO"
        os.environ["EB_AGENT_ACCESS_TOKEN"] =  myKeys.EB_AGENT_ACCESS_TOKEN
        self.llm = ErnieBot(aistudio_access_token=myKeys.EB_AGENT_ACCESS_TOKEN)
        

        memory = SlidingWindowMemory(max_round=5)
        llm_final = ERNIEBot(model="ernie-3.5", api_type="aistudio", enable_multi_step_tool_call=True)
        guider_prompt = "你是智途问答大冒险中的游戏助手，叫做小桨，你负责陪伴玩家在太空进行探险，用比较通俗易懂的方式解答玩家遇到的问题。当前游戏事件如下：{event_content}\n"
        self.guider_agent_all = FunctionAgent(llm=llm_final, tools=[], memory=memory, system=guider_prompt)

        self.guider_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", guider_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        ## 问答prompt
        self.npc_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你需要根据以下的游戏事件，人物背景，目的，科普知识扮演游戏人物，与玩家进行对话，达成目的，引导玩家进行选择。不要暴露你是在扮演。\n" \
                            "游戏事件：{event_content}\n" \
                            "人物背景：{background}\n" \
                            "目的：{purpose}\n" \
                            "科普知识：{knowledge}\n"),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        referee_example = '''{{"event_option": 1, "result": "旁白对事件结果进行客观描述"}}'''
        ## 裁判prompt
        self.referee_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是智途问答大冒险中的裁判，你需要根据以下的游戏事件和玩家对话，判定玩家是否达成游戏事件中的人物目的，选择事件选项对玩家进行奖励和惩罚，并根据对话重新生成选中选项的result。必须选择一项。只需按照下列示例进行输出json格式结果。\n" \
                            "输出格式示例：" + referee_example + "\n" \
                            "游戏事件：{event_content}\n" \
                            "玩家对话：```{messages}```\n"),
            ]
        )
        question_example = '''["问题1", "问题2", "问题3"]'''
        
        ## 问题推荐
        self.question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你需要根据以下的游戏事件和玩家对话，推荐三个科普知识问题或者选项供玩家进行选择。使用json格式输出结果。\n" \
                            "输出格式示例：" + question_example + "\n" \
                            "游戏事件：{event_content}\n" \
                            "玩家对话：```{messages}```\n"),
            ]
        )
    def chat_with_guider(self, input, event_content):
        retries = 3
        for _ in range(retries):
            try:
                chain  = self.guider_prompt | self.llm | StrOutputParser()
                response = chain.stream({"messages": input, "event_content": event_content})
                return response
            except Exception as e:
                logger.error(e)
                time.sleep(1)  # Retry after 1 second
        raise Exception("Failed after {} retries".format(retries))

    def chat_with_npc(self, input, event_content, background, purpose, knowledge):
        retries = 3
        for _ in range(retries):
            try:
                chain  = self.npc_prompt | self.llm | StrOutputParser()
                response = chain.stream({"messages": input, "event_content": event_content, "background": background, "purpose": purpose, "knowledge": knowledge})
                return response
            except Exception as e:
                logger.error(e)
                time.sleep(1)  # Retry after 1 second
        raise Exception("Failed after {} retries".format(retries))

    def chat_with_referee(self, input, event_content):
        retries = 3
        for _ in range(retries):
            try:
                chain  = self.referee_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"messages": input, "event_content": event_content})
                return response
            except Exception as e:
                logger.error(e)
                time.sleep(1)  # Retry after 1 second
        raise Exception("Failed after {} retries".format(retries))

    def chat_with_question(self, input, event_content):
        retries = 3
        for _ in range(retries):
            try:
                chain  = self.question_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"messages": input, "event_content": event_content})
                return response
            except Exception as e:
                logger.error(e)
                time.sleep(1)  # Retry after 1 second
        raise Exception("Failed after {} retries".format(retries))