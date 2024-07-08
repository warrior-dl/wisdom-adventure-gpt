
import time
import os
import asyncio
import myKeys
from functools import wraps
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from loguru import logger
from erniebot_agent.extensions.langchain.llms import ErnieBot
from langchain_community.llms  import QianfanLLMEndpoint
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings, 
)
from langchain_chroma import Chroma
from langchain_community.embeddings import QianfanEmbeddingsEndpoint

def retry(retries: int = 3, delay: float = 1):
    """
    函数执行失败时，重试

    :param retries: 最大重试的次数
    :param delay: 每次重试的间隔时间，单位 秒
    :return:
    """

    # 校验重试的参数，参数值不正确时使用默认参数
    if retries < 1 or delay <= 0:
        retries = 3
        delay = 1

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 第一次正常执行不算重试次数，所以retries+1
            for i in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 检查重试次数
                    if i == retries:
                        logger.warning(f"Error: {repr(e)}")
                        logger.warning(f'"{func.__name__}()" 执行失败，已重试{retries}次')
                        break
                    else:
                        logger.warning(
                            f"Error: {repr(e)}，{delay}秒后第[{i+1}/{retries}]次重试..."
                        )
                        time.sleep(delay)

        return wrapper

    return decorator

class LLM:
    def __init__(self, origin=""):
        os.environ["EB_AGENT_LOGGING_LEVEL"] = "INFO"
        os.environ["EB_AGENT_ACCESS_TOKEN"] =  myKeys.EB_AGENT_ACCESS_TOKEN
        os.environ["QIANFAN_AK"] = myKeys.QIANFAN_AK
        os.environ["QIANFAN_SK"] = myKeys.QIANFAN_SK
        os.environ["LANGCHAIN_TRACING_V2"]="true"
        os.environ["LANGCHAIN_API_KEY"]="ls__c0012d47edfc4b3a8c19c40242a3521e"

        ## 初始化rag
        self.db_path = "./chroma_db"
        if not os.path.exists(self.db_path):
            self.chroma = self.init_rag_from_md("data/data_merge.md")
        else:
            self.chroma = self.init_rag_from_db()

        if origin == "qianfan":
            logger.info("use qianfan llm")
            self.llm = QianfanLLMEndpoint(model="ERNIE-4.0-8K-Preview-0518")
        else:
            self.llm = ErnieBot(aistudio_access_token=myKeys.EB_AGENT_ACCESS_TOKEN, model="ernie-3.5")
        
        guider_prompt = "你是智途问答大冒险中的游戏助手，叫做小桨，你负责陪伴玩家在太空进行探险，用比较通俗易懂的方式解答玩家遇到的问题。当前游戏事件如下：{event_content}\n 参考资料：{rag_content}\n"

        self.guider_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", guider_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        ## 问答prompt
        self.npc_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你需要根据以下的游戏事件，人物背景，目的，科普知识扮演游戏人物，与玩家进行对话，达成目的，引导玩家进行选择。不要暴露你是在扮演。不要输出AI前缀。\n" \
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
                ("system", "你是智途问答大冒险中的裁判，你需要根据以下的游戏事件和玩家对话，判定玩家是否达成游戏事件中的人物目的，选择事件选项对玩家进行奖励和惩罚，并根据对话重新生成选中选项的result，result需要简洁。必须选择一项。只需按照下列示例进行输出json格式结果。\n" \
                            "输出格式示例：" + referee_example + "\n" \
                            "游戏事件：{event_content}\n" \
                            "玩家对话：```{messages}```\n"),
            ]
        )
        question_example = '''["问题1", "问题2", "问题3"]'''
        
        ## 问题推荐
        self.question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你需要根据以下的游戏事件、选项以及玩家对话，推荐三个问题供玩家进行选择。使用json格式输出结果。\n" \
                            "输出格式示例：" + question_example + "\n" \
                            "游戏事件：{event_content}\n" \
                            "玩家对话：```{messages}```\n"),
            ]
        )

        ## rag prompt
        self.rag_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你需要以下参考资料，回答问题。\n" \
                            "参考资料：{content}\n" \
                            "问题：{question}\n"),
            ]
        )

        ## 重新组织问题
        self.reorganize_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你需要根据以下历史对话和游戏事件，重新组织用户输入的问题，补充或替换问题中不清晰的指代主体，以便根据你输出的问题进行搜索。\n" \
                            "对话：```{messages}```\n"
                            "游戏事件：{event_content}\n" \
                            "问题：{question}\n"),
            ]
        )
    @retry(retries=2, delay=1)
    def chat_with_guider(self, input, event_content, rag_content = ""):
        chain  = self.guider_prompt | self.llm | StrOutputParser()
        response = chain.stream({"messages": input, "event_content": event_content, "rag_content": rag_content})
        return response

    @retry(retries=2, delay=1)
    def chat_with_npc(self, input, event_content, background, purpose, knowledge):
        chain  = self.npc_prompt | self.llm | StrOutputParser()
        response = chain.stream({"messages": input, "event_content": event_content, "background": background, "purpose": purpose, "knowledge": knowledge})
        return response

    @retry(retries=2, delay=1)
    def chat_with_referee(self, input, event_content):
        chain  = self.referee_prompt | self.llm | StrOutputParser()
        response = chain.invoke({"messages": input, "event_content": event_content})
        return response

    @retry(retries=2, delay=1)
    def chat_with_question(self, input, event_content):
        chain  = self.question_prompt | self.llm | StrOutputParser()
        response = chain.invoke({"messages": input, "event_content": event_content})
        return response
    
    @retry(retries=2, delay=1)
    def chat_with_reorganize(self, input, event_content):
        chain  = self.reorganize_prompt | self.llm | StrOutputParser()
        response = chain.invoke({"question": input[-1], "messages": input[:-1], "event_content": event_content})
        return response 
    
    def init_rag_from_md(self, path):
        # 读取文件
        with open(path, "r", encoding="utf-8") as f:
            markdown_document = f.read()

        headers_to_split_on = [
            ("#", "Header 1"),
        ]

        # MD splits
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=True
        )
        md_header_splits = markdown_splitter.split_text(markdown_document)
        for split in md_header_splits:
            logger.info("split: {}", split.page_content)

        chunk_size = 250
        chunk_overlap = 30
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        # Split
        splits = text_splitter.split_documents(md_header_splits)

        for idx in range(len(splits)):
            split = splits[idx]
            header = split.metadata["Header 1"]
            content = split.page_content
            splits[idx].page_content = f"[{header}]{content}"
            logger.info("split after text splitter: {}", splits[idx])
        logger.info(f"Split {len(splits)} chunks")

        # save to disk
        return Chroma.from_documents(splits, embedding=QianfanEmbeddingsEndpoint(), persist_directory=self.db_path)

    def init_rag_from_db(self):
        return Chroma(persist_directory=self.db_path, embedding_function=QianfanEmbeddingsEndpoint())
    
    def get_retriever_docs(self, input):
        retriever = self.chroma.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        docs = retriever.invoke(input=input)
        return "\n\n".join(doc.page_content for doc in docs)

    def rag(self, input):
        try:
            content = self.get_retriever_docs(input)
            return content 
        except Exception as e:
            logger.error(e)
            return ""
