import re
from status import PlayerStatus, StatusManager, BattleResult, GameStatus
from event import EventManager
from voice import Voice
from loguru import logger
from llm import LLM
class Controller:

    def __init__(self):
        self.status_manager = StatusManager()
        self.event_manager = EventManager("data/event_list.json", "data/data.json", "data/battle.json", "data/OEBPS/Images", "data/OEBPS/Battle_Images")
        self.llm = LLM()
        self.voice = Voice()
    def get_event(self, session):
        if session is None:
            logger.warning("session is None")
            return None
        status = self.status_manager.get_status_with_session(session) 
        return status.get_cur_event()
    def update_event(self, session) :
        status = self.status_manager.get_status_with_session(session)
        game_time = status.get_game_time()
        if game_time % 5 == 0 and game_time != 0:
            index, event = self.event_manager.get_battle_by_index(0)
            status.set_cur_event(event)
            status.add_game_time()
            enemy_info = event.get_enemy_info()
            enemy_hp = enemy_info["hp"]
            enemy_attack = enemy_info["attack"]
            status.set_battle_status(player_hp=100, enemy_hp=enemy_hp, enemy_attack=enemy_attack)
            return True
        while True:
            index, event = self.event_manager.get_event_random()
            if not status.is_in_history(index):
                status.set_cur_event(event)
                status.add_game_time()
                status.add_history(index)
                return True
            elif len(status.get_history()) == len(self.event_manager.event_list):
                logger.info("No more event")
                # TODO: 结算
                self.current_event = None
                return False
    def get_game_status(self, session=None):
        status = self.status_manager.get_status_with_session(session)
        return status.get_game_status()
    def set_game_status(self, session, status: GameStatus):
        pys = self.status_manager.get_status_with_session(session)
        pys.set_game_status(status)
    def get_resource(self, session=None):
        status = self.status_manager.get_status_with_session(session)
        return status.get_resource()

    def update_resource(self, session:str, optionId:int):
        status = self.status_manager.get_status_with_session(session)
        cur_event = status.get_cur_event()
        if cur_event is None:
            logger.warning("current event is None")
            return
        awards = cur_event.get_option_award(optionId)
        if awards is None:
            logger.warning("award is None")
            return
        status.update_resource(awards)

    def get_event_option(self, session, optionId:int):
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
    def get_battle_status(self, session):
        status = self.status_manager.get_status_with_session(session)
        return status.get_battle_status()

    def format_awards(self, awards):
        msg = ""
        for award in awards:
            if award["key"] == "stellarCurrency":
                msg = msg + "获得{}星币!\n".format(award["value"])
            if award["key"] == "shipEnergy":
                msg = msg + "获得{}能量!\n".format(award["value"])
            if award["key"] == "reputationValue":
                msg = msg + "获得{}声望!\n".format(award["value"])
        return msg
    def update_battle_status(self, session, optionId):
        status = self.status_manager.get_status_with_session(session)
        cur_event = status.get_cur_event()
        if cur_event is None:
            logger.warning("current event is None")
            return
        awards = cur_event.get_option_award(optionId)
        if awards is None:
            logger.warning("award is None")
            return
        battle_result, msg = status.update_battle_status(awards)
        match battle_result:
            case BattleResult.PLAYER_WIN:
                awards = cur_event.get_event_award()
                status.update_resource(awards)
                # 格式化奖励
                msg = msg + "\n" + self.format_awards(awards)
                return battle_result, msg
            case BattleResult.RESOURCE_NOT_ENOUGH:
                logger.warning("battle_result: {}, msg: {}", battle_result, msg)
                return battle_result, msg
            case BattleResult.ENEMY_WIN:
                logger.warning("battle_result: {}, msg: {}", battle_result, msg)
                return battle_result, msg
            case BattleResult.NOT_FINISHED:
                logger.warning("battle_result: {}, msg: {}", battle_result, msg)
                return battle_result, self.get_event_option(session, optionId)["result"] + "\n" + msg

    
    def get_gallery(self, session):
        status = self.status_manager.get_status_with_session(session)
        return status.current_event.get_images()
    