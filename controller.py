from status import PlayerStatus
from event import EventManager
from loguru import logger
from llm import LLM
class Controller:

    def __init__(self):
        self.player_status = PlayerStatus(100, 50, 10, 0)
        self.event_manager = EventManager("data/event_list.json", "data/data.json")
        self.current_event = None
        self.update_status_finish = False
        self.history = []
        self.llm = LLM()
    def get_event(self):
        return self.current_event
    def update_event(self):
        # while True:
            index, event = self.event_manager.get_event_random()
            # if index not in self.history:
            self.current_event = event
            self.update_status_finish = False
            self.history.append(index)
            #     break
            # elif len(self.history) == len(self.event_manager.event_list):
            #     logger.info("No more event")
            #     # TODO: 结算
            #     self.current_event = None
            #     break
        
    def get_status(self):
        return self.player_status
    def update_status(self, optionId):
        if self.update_status_finish:
            logger.info("had update status, not need update again")
            return
        event = self.current_event
        if event is None:
            logger.info("current event is None")
            return
        key, value = self.event_manager.get_award(event, optionId)
        if key is not None:
            self.player_status.update(key, self.player_status.get_value(key) + value)
        self.update_status_finish = True

    def get_event_option(self, optionId):
        event = self.current_event
        if event is None:
            return
        for option in event["eventOptions"]:
            if option["optionId"] == optionId:
                return option
    def chat_with_guider(self, input):
        output = self.llm.chat_with_guider(input)
        logger.info("controllerguider: {}".format(output))
        return output
    


    
