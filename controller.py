import os
import json
import time
from status import PlayerStatus, StatusManager, BattleResult, GameStatus
from event import EventManager
from voice import Voice
from loguru import logger
from llm import LLM
import wave
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
        if game_time >= 16:
            # 结算
            return False
        if game_time % 5 == 0 and game_time != 0:
            index, event = self.event_manager.get_battle_by_index(int(game_time/5)-1)
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
    def get_record(self, session=None):
        status = self.status_manager.get_status_with_session(session)
        return status.get_record()

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
    def chat_with_question(self, input, event_content):
        output = self.llm.chat_with_question(input, event_content)
        logger.info("question: {}", output)
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
    
    def chat_and_speech(self, input, session = None):
        text = self.chat(input, session)
        # 获取本地时间戳
        timestamp = time.time()
        # 生成tts
        for t in text:
            self.push_tts_queue(session, t, timestamp)
            yield t

    def generate_tts(self, session, text):
        # 获取时间戳
        timestamp = time.time()
        self.push_tts_queue(session, text, timestamp)

    def push_event_option_tts(self, session, id, option_id):
        timestamp = time.time()
        # 拼接文件名
        file_name = f"{id}-option-{option_id}.wav"
        # 拼接路径
        file_path = os.path.join("data/TTS", file_name)
        self.push_tts_queue_with_file(session, file_path, timestamp)
    
    def push_event_content_tts(self, session, id):
        timestamp = time.time()
        # 拼接文件名
        file_name = f"{id}-content.wav"
        # 拼接路径
        file_path = os.path.join("data/TTS", file_name)
        self.push_tts_queue_with_file(session, file_path, timestamp)

    def push_tts_queue(self, session, text, timestamp):
        status = self.status_manager.get_status_with_session(session)
        # 请求的时间戳小于队列的时间戳，说明过期，不再请求
        if timestamp < status.get_tts_queue_timer():
            logger.info("timestamp timeout")
            return
        tts, duration  = self.get_tts(text)
        status.push_tts(tts, duration)
        status.update_tts_queue_timer(timestamp)

    def push_tts_queue_with_file(self, session, wav_path, timestamp):
        status = self.status_manager.get_status_with_session(session)
        # 请求的时间戳小于队列的时间戳，说明过期，不再请求
        if timestamp < status.get_tts_queue_timer():
            logger.info("timestamp timeout")
            return
        if not os.path.exists(wav_path):
            logger.warning("wav_path not exists: {}", wav_path)
            return
        with wave.open(wav_path, 'rb') as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        status.push_tts(wav_path, duration)
        status.update_tts_queue_timer(timestamp)

    def pop_tts_queue(self, session):
        status = self.status_manager.get_status_with_session(session)
        return status.pop_tts_queue()
    def clear_tts_queue(self, session):
        status = self.status_manager.get_status_with_session(session)
        status.clear_tts_queue()

    def referee_judge(self, session, input):
        status = self.status_manager.get_status_with_session(session)
        event = status.get_cur_event()
        if event is None:
            logger.warning("current event is None")
            raise Exception("current event is None")
        event_content = event.get_content()
        str_out =  self.chat_with_referee(input, event_content)
        try:
            content = str_out.replace("```json", "").replace("```", "")
            res = json.loads(content)
            logger.info(" res: {}", res)
            return int(res["event_option"]), res["result"]
        except:
            logger.warning("referee failed, str_out: {}", str_out)
            raise Exception("referee failed, str_out: {}".format(str_out))
        
    def create_question(self, session, input):
        status = self.status_manager.get_status_with_session(session)
        event = status.get_cur_event()
        if event is None:
            logger.warning("current event is None")
            raise Exception("current event is None")
        event_content = event.get_content()
        str_out =  self.chat_with_question(input, event_content)
        try:
            content = str_out.replace("```json", "").replace("```", "")
            ## json序列化
            return json.loads(content)
        except:
            logger.warning("json failed, str_out: {}", content)
            raise Exception("json failed, str_out: {}".format(content))

    def get_tts(self, text)-> tuple[str, int]:
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
    
    def get_game_time(self, session):
        status = self.status_manager.get_status_with_session(session)
        return status.get_game_time()
    # 结算游戏积分
    def calculate_score(self, session):
        status = self.status_manager.get_status_with_session(session)
        return status.calculate_score()