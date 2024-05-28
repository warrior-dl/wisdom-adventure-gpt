from status import PlayerStatus, StatusManager
from event import EventManager
from loguru import logger
from llm import LLM
class Controller:

    def __init__(self):
        self.status_manager = StatusManager()
        self.event_manager = EventManager("data/event_list.json", "data/data.json")
        self.llm = LLM()
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
        for option in event.content["eventOptions"]:
            if option["optionId"] == optionId:
                return option
    def chat_with_guider(self, input):
        output = self.llm.chat_with_guider(input)
        logger.info("controllerguider: {}".format(output))
        return output
    


    
