import re
from status import PlayerStatus, StatusManager
from event import EventManager
from voice import Voice
from loguru import logger
from llm import LLM
class Controller:

    def __init__(self):
        self.status_manager = StatusManager()
        self.event_manager = EventManager("data/event_list.json", "data/data.json")
        self.llm = LLM()
        self.voice = Voice()
    def get_event(self, session=None):
        if session is None:
            logger.error("session is None")
            return None
        status = self.status_manager.get_status_with_session(session) 
        return status.get_cur_event()
    def update_event(self, session) :
        status = self.status_manager.get_status_with_session(session)
        while True:
            index, event = self.event_manager.get_event_random()
            if not status.is_in_history(index):
                status.set_cur_event(event)
                status.add_history(index)
                return True
            elif len(status.get_history()) == len(self.event_manager.event_list):
                logger.info("No more event")
                # TODO: 结算
                self.current_event = None
                return False
            
    def get_resource(self, session=None):
        status = self.status_manager.get_status_with_session(session)
        return status.get_resource()

    def update_resource(self, session, optionId):
        status = self.status_manager.get_status_with_session(session)
        cur_event = status.get_cur_event()
        if cur_event is None:
            logger.warning("current event is None")
            return
        key, value = cur_event.get_award(optionId)
        if key is not None:
            logger.info(f"award: key: {key}, value: {value}")
            status.update_resource(key, status.resource.get_value(key) + value)

    def get_event_option(self, session, optionId):
        status = self.status_manager.get_status_with_session(session)
        event = status.get_cur_event()
        if event is None:
            return
        for option in event.get_content()["eventOptions"]:
            if option["optionId"] == optionId:
                return option
    def chat_with_guider(self, input, event_content):
        output = self.llm.chat_with_guider(input, event_content)
        logger.info("controller guider: {}", output)
        return output
    
    def chat_with_npc(self, input, event_content, background, purpose, knowledge):
        output = self.llm.chat_with_npc(input, event_content, background, purpose, knowledge)
        logger.info("event npc: {}", output)
        return output
    
    def chat_with_referee(self, input, event_content):
        logger.info("referee: input: {}, event_content: {}", input, event_content)
        output = self.llm.chat_with_referee(input, event_content)
        logger.info("referee: {}", output)
        return output
    def chat(self, input, session = None):
        event_content = ""
        if session is not None:
            status = self.status_manager.get_status_with_session(session)
            event = status.get_cur_event()
            if event is not None:
                # TODO: 需要去除event_content中的奖励结果
                event_content = event.get_content()
                if event.get_type() == "characterInteraction":
                    id = event.get_id()
                    background = event.get_background()
                    purpose = event.get_purpose()
                    knowledge = self.event_manager.get_original_event_by_index(id)
                    return self.chat_with_npc(input, event_content, background, purpose, knowledge)
        return self.chat_with_guider(input, event_content)
    
    def referee_judge(self, session, input):
        status = self.status_manager.get_status_with_session(session)
        event = status.get_cur_event()
        if event is None:
            logger.warning("current event is None")
            raise Exception("current event is None")
        event_content = event.get_content()
        str_out =  self.chat_with_referee(input, event_content)
        try:
            ## str的格式：event_option: 1 xxxxxx，使用正则取出数字1，去除空格换行
            search = re.search(r'event_option:\s*(\d+)', str_out)
            logger.info("search.group(1): {}", search.group(1))
            return int(search.group(1))
        except:
            logger.warning("referee failed, str_out: {}", str_out)
            raise Exception("referee failed, str_out: {}".format(str_out))

    def get_tts(self, text):
        return self.voice.get_tts(text)
    
    def get_asr(self, audio):
        return self.voice.get_asr(audio)

    
