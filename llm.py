
import time
import os
import asyncio
import myKeys
from langchain_core.prompts import ChatPromptTemplate
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




class LLM:
    def __init__(self):
        os.environ["EB_AGENT_LOGGING_LEVEL"] = "INFO"
        os.environ["EB_AGENT_ACCESS_TOKEN"] =  myKeys.EB_AGENT_ACCESS_TOKEN
        memory = SlidingWindowMemory(max_round=5)
        llm_final = ERNIEBot(model="ernie-3.5", api_type="aistudio", enable_multi_step_tool_call=True)
        guider_prompt = "你是智途问答大冒险中的游戏助手，叫做小桨，你负责陪伴玩家在太空进行探险，用比较通俗易懂的方式解答玩家遇到的问题。\n"
        self.guider_agent_all = FunctionAgent(llm=llm_final, tools=[], memory=memory, system=guider_prompt)

        ## 问答prompt
        self.npc_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是智途问答大冒险中的NPC，你需要根据以下的背景，目的，科普知识，与玩家进行对话，达成目的。\n" \
                            "背景：{background}\n" \
                            "目的：{purpose}\n" \
                            "科普知识：{knowledge}\n"),
                ("human", "{input}"),
                ("ai", ""),
            ]
        )

    async def chat_with_guider(self, input):
        retries = 3
        for _ in range(retries):
            try:
                response = await self.guider_agent_all.run(input)
                logger.info("guider: {}".format(response.text))
                return response.text
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(1)  # Retry after 1 second
        raise Exception("Failed after {} retries".format(retries))


    
