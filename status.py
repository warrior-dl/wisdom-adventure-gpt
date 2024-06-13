
from loguru import logger
from event import Event
from enum import Enum
import cachetools
from cachetools import TTLCache

class Resource:
    def __init__(self, stellar_currency: int, ship_energy : int, exploration_capability : int, reputation_value : int):
        self.stellarCurrency = stellar_currency
        self.shipEnergy = ship_energy
        self.explorationCapability = exploration_capability
        self.reputationValue = reputation_value

    def __dict__(self):
        return {
            "stellarCurrency": self.stellarCurrency,
            "shipEnergy": self.shipEnergy,
            "explorationCapability": self.explorationCapability,
            "reputationValue": self.reputationValue
        }
    
    def get_status(self):
        return self.__dict__()
    def get_value(self, key):
        return getattr(self, key)

    def update(self, key, value):
        setattr(self, key, value)

class BattleStatus:
    def __init__(self, player_hp: int, enemy_hp: int, enemy_attack: int) -> None:
        self.player_hp = player_hp
        self.enemy_hp = enemy_hp
        self.enemy_attack = enemy_attack

    def get_status(self):
        return {
            "player_hp": self.player_hp,
            "enemy_hp": self.enemy_hp
        }
    
    def update_player_hp(self, value):
        self.player_hp += value
    
    def update_enemy_hp(self, value):
        self.enemy_hp -= value
    
    def get_player_hp(self):
        return self.player_hp
    
    def get_enemy_hp(self):
        return self.enemy_hp


# 战斗结果枚举
class BattleResult(Enum):
    PLAYER_WIN = 1
    ENEMY_WIN = 2
    RESOURCE_NOT_ENOUGH = 3
    NOT_FINISHED = 4

# 游戏进程枚举
class GameStatus(Enum):
    NOT_START = 1
    EVENT_GOING = 2
    EVENT_END = 3
    GAME_OVER = 4

class PlayerStatus:
    def __init__(self, resource: Resource, battle_status: BattleStatus) -> None:
        self.resource = resource
        self.battle_status = battle_status
        self.current_event = None
        self.game_status = GameStatus.NOT_START
        self.game_time = 0
        self.history = []
    def set_cur_event(self, event: Event):
        self.current_event = event
    def get_cur_event(self) -> Event:
        return self.current_event
    def add_history(self, event_id):
        self.history.append(event_id)
    def is_in_history(self, event_id) -> bool:
        return event_id in self.history
    def get_history(self)->list:
        return self.history
    def get_game_status(self) -> GameStatus:
        return self.game_status
    def set_game_status(self, status: GameStatus):
        self.game_status = status
    def get_game_time(self) -> int:
        return self.game_time
    def add_game_time(self):
        self.game_time += 1
    def get_resource(self)->Resource:
        return self.resource
    def update_resource(self, awards):
        if self.current_event.used:
            logger.info("had update status, not need update again")
            return
        for i in awards:
            key, value = i["key"], i["value"]
            if key is not None:
                logger.info(f"award: key: {key}, value: {value}")
                new_value = self.resource.get_value(key) + value
                logger.info(f"status update: key: {key}, new_value: {new_value}")
                self.resource.update(key, new_value)
        self.current_event.used = True
    def get_battle_status(self)->BattleStatus: 
        return self.battle_status
    def update_battle_status(self, awards):
        # 资源存量检查
        for i in awards:
            key, value = i["key"], i["value"]
            if key is not None:
                logger.info(f"award: key: {key}, value: {value}")
                if key != "player_hp" and key != "enemy_hp":
                    new_value = self.resource.get_value(key) + value
                    if new_value < 0:
                        logger.warning(f"{key} is not enough")
                        return BattleResult.RESOURCE_NOT_ENOUGH, f"{key} is not enough"
        for i in awards:
            key, value = i["key"], i["value"]
            if key is not None:
                # 先判断value是否是数字还是字符串
                if isinstance(value, str):
                    value = self.get_resource().get_value(value)
                if key == "player_hp":
                    logger.info(f"battle update: key: {key}, add_value: {value}")
                    self.battle_status.update_player_hp(value)
                elif key == "enemy_hp":
                    logger.info(f"battle update: key: {key}, add_value: {value}")
                    self.battle_status.update_enemy_hp(value)
                else:
                    new_value = self.resource.get_value(key) + value
                    logger.info(f"status update: key: {key}, new_value: {new_value}")
                    self.resource.update(key, new_value)
        # 敌人状态判定
        if self.battle_status.get_enemy_hp() <= 0:
            logger.info("player win")
            return BattleResult.PLAYER_WIN, "恭喜你获得了胜利"
        # 敌人攻击
        self.battle_status.update_player_hp(self.battle_status.enemy_attack * -1)
        if self.battle_status.get_player_hp() <= 0:
            logger.info("player lose")
            return BattleResult.ENEMY_WIN, "很遗憾，你输了"
        return BattleResult.NOT_FINISHED, f"敌人进行了反击，造成了{self.battle_status.enemy_attack}点伤害"
    def set_battle_status(self, player_hp=100, enemy_hp=100, enemy_attack=10):
        self.battle_status = BattleStatus(player_hp, enemy_hp, enemy_attack)

    def get_gallery(self):
        self.current_event.get_gallery()

class StatusManager:
    def __init__(self):
        # 缓存一天
        self.status_cache = cachetools.TTLCache(maxsize=100, ttl=86400)
    def get_status_with_session(self, session) -> PlayerStatus:
        status = self.status_cache.get(session, None)
        if status is None:
            logger.info("status is None, create new status")
            status = PlayerStatus(Resource(100, 50, 10, 0), BattleStatus(100, 100, 20))
            self.set_status_with_session(session, status)
        return status
    
    def set_status_with_session(self, session, status: PlayerStatus):
        self.status_cache[session] = status