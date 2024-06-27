
from loguru import logger
from event import Event
from enum import Enum
import cachetools
import time
from cachetools import TTLCache
from typing import Optional, Tuple, List, Dict, Union
class Resource:
    def __init__(
        self,
        stellar_currency: int,
        ship_energy: int,
        exploration_capability: int,
        reputation_value: int
    ) -> None:
        """
        Initialize a Resource object.

        Args:
            stellar_currency (int): The amount of stellar currency.
            ship_energy (int): The amount of ship energy.
            exploration_capability (int): The exploration capability.
            reputation_value (int): The reputation value.
        """
        self.stellarCurrency = stellar_currency
        self.shipEnergy = ship_energy
        self.explorationCapability = exploration_capability
        self.reputationValue = reputation_value

    @property
    def __dict__(self) -> Dict[str, int]:
        """
        Get the dictionary representation of the Resource object.

        Returns:
            Dict[str, int]: A dictionary containing the keys 'stellarCurrency', 'shipEnergy', 
            'explorationCapability', and 'reputationValue', with their corresponding values.
        """
        return {
            "stellarCurrency": self.stellarCurrency,
            "shipEnergy": self.shipEnergy,
            "explorationCapability": self.explorationCapability,
            "reputationValue": self.reputationValue
        }
    
    def get_status(self) -> Dict[str, int]:
        """
        Get the status of the Resource object.

        Returns:
            Dict[str, int]: A dictionary containing the keys 'stellarCurrency', 'shipEnergy', 
            'explorationCapability', and 'reputationValue', with their corresponding values.
        """
        return self.__dict__
    def get_value(self, key: str) -> int:
        """
        Get the value of a specific key in the Resource object.

        Args:
            key (str): The key of the value to retrieve.

        Returns:
            int: The value associated with the given key.
        """
        return getattr(self, key)

    def update(self, key: str, value: int) -> None:
        """
        Update the value of a specific key in the Resource object.

        Args:
            key (str): The key of the value to update.
            value (int): The new value to set for the given key.

        Returns:
            None
        """
        setattr(self, key, value)

class BattleStatus:
    def __init__(self, player_hp: int, enemy_hp: int, enemy_attack: int) -> None:
        """
        Initialize the BattleStatus object.

        Args:
            player_hp (int): The maximum health points of the player.
            enemy_hp (int): The maximum health points of the enemy.
            enemy_attack (int): The attack points of the enemy.

        Returns:
            None
        """
        self.enemy_max_hp: int = enemy_hp
        self.player_max_hp: int = player_hp
        self.player_hp: int = player_hp
        self.enemy_hp: int = enemy_hp 
        self.enemy_attack: int = enemy_attack

    def get_status(self) -> Dict[str, int]:
        """
        Get the current status of the battle.

        Returns:
            Dict[str, int]: A dictionary representing the current status of the battle.
                The dictionary has the following keys:
                - "player_hp" (int): The current health points of the player.
                - "enemy_hp" (int): The current health points of the enemy.
        """
        return {
            "player_hp": self.player_hp,
            "enemy_hp": self.enemy_hp
        }
    
    def update_player_hp(self, value: int) -> None:
        """
        Update the player's health points.

        Args:
            value (int): The amount by which to increase the player's health points.

        Returns:
            None
        """
        self.player_hp += value
        if self.player_hp < 0:
            self.player_hp = 0
    
    def update_enemy_hp(self, value: int) -> None:
        """
        Update the enemy's health points.

        Args:
            value (int): The amount by which to decrease the enemy's health points.

        Returns:
            None
        """
        self.enemy_hp -= value
        if self.enemy_hp < 0:
            self.enemy_hp = 0
    
    def get_player_hp(self) -> int:
        """
        Get the current health points of the player.

        Returns:
            int: The current health points of the player.
        """
        return self.player_hp
    def get_enemy_hp(self) -> int:
        """
        Get the current health points of the enemy.

        Returns:
            int: The current health points of the enemy.
        """
        return self.enemy_hp

    def get_player_max_hp(self) -> int:
        """
        Get the maximum health points of the player.

        Returns:
            int: The maximum health points of the player.
        """
        return self.player_max_hp  # type: int
    
    def get_enemy_max_hp(self) -> int:
        """
        Get the maximum health points of the enemy.

        Returns:
            int: The maximum health points of the enemy.
        """
        return self.enemy_max_hp  # type: int

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
    def __init__(
        self, 
        resource: 'Resource', 
        battle_status: 'BattleStatus'
    ) -> None:
        """
        Initialize the PlayerStatus object.

        Args:
            resource (Resource): The resource object.
            battle_status (BattleStatus): The battle status object.

        Returns:
            None
        """
        self.resource: 'Resource' = resource
        self.battle_status: 'BattleStatus' = battle_status
        self.current_event: Optional['Event'] = None
        self.game_status: GameStatus = GameStatus.NOT_START
        self.game_time: int = 0
        self.history: List[int] = []
        self.tts_queue: List[str] = []
        self.tts_queue_timer: int = 0
        self.record: List[Dict[str, Union[str, int]]] = []
    def set_cur_event(self, event: 'Event') -> None:
        """
        Set the current event.

        Args:
            event (Event): The event to set as the current event.
        """
        self.current_event = event
    def get_cur_event(self) -> 'Event':
        """
        Get the current event.

        Returns:
            Event: The current event.
        """
        return self.current_event
    def add_history(self, event_id: int) -> None:
        """
        Add an event ID to the history.

        Args:
            event_id (int): The ID of the event to add to the history.
        """
        self.history.append(event_id)
    def is_in_history(self, event_id: int) -> bool:
        """
        Check if an event ID is in the history.

        Args:
            event_id (int): The ID of the event to check.

        Returns:
            bool: True if the event ID is in the history, False otherwise.
        """
        return event_id in self.history
    def get_history(self) -> List[int]:
        """
        Get the history of event IDs.

        Returns:
            List[int]: The history of event IDs.
        """
        return self.history
    def get_game_status(self) -> GameStatus:
        """
        Get the game status.

        Returns:
            GameStatus: The game status.
        """
        return self.game_status
    def set_game_status(self, status: GameStatus) -> None:
        """
        Set the game status.

        Args:
            status (GameStatus): The game status to set.
        """
        self.game_status = status
    def get_game_time(self) -> int:
        """
        Get the current game time.

        Returns:
            int: The current game time.
        """
        return self.game_time
    def add_game_time(self) -> None:
        """
        Add one to the game time.

        Returns:
            None
        """
        self.game_time += 1
    def get_resource(self) -> Resource:
        """
        Get the player's resource.

        Returns:
            Resource: The player's resource.
        """
        return self.resource
    def update_resource(self, awards: List[Dict[str, Union[str, int]]]) -> None:
        """
        Update the player's resource based on the given awards.

        Args:
            awards (List[Dict[str, Union[str, int]]]): A list of dictionaries representing the awards.
                Each dictionary should have the following keys:
                - "key" (str): The key of the award.
                - "value" (int): The value of the award.

        Returns:
            None
        """
        if self.current_event is None:
            logger.warning("no current event, can not update resource")
            return
        if self.current_event.used:
            logger.info("had update status, not need update again")
            return
        for award in awards:
            key, value = award["key"], award["value"]
            if key is not None:
                logger.info(f"award: key: {key}, value: {value}")
                new_value = self.resource.get_value(key) + value
                logger.info(f"status update: key: {key}, new_value: {new_value}")
                self.resource.update(key, new_value)
                self.push_record(key, value)
        self.current_event.used = True
    def get_battle_status(self) -> BattleStatus:
        """
        Get the battle status of the player.

        Returns:
            BattleStatus: The battle status of the player.
        """
        return self.battle_status
    def update_battle_status(
        self, awards: List[Dict[str, Union[str, int]]]
    ) -> Tuple[BattleResult, str]:
        """
        Update the battle status based on the given awards.

        Args:
            awards (List[Dict[str, Union[str, int]]]): A list of dictionaries representing the awards.
                Each dictionary should have the following keys:
                - "key" (str): The key of the award.
                - "value" (int): The value of the award.

        Returns:
            Tuple[BattleResult, str]: A tuple containing the result of the battle and a message.
                The result can be one of BattleResult.PLAYER_WIN, BattleResult.ENEMY_WIN, or BattleResult.NOT_FINISHED.
                The message is a string describing the result of the battle.
        """
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
        return (
            BattleResult.NOT_FINISHED,
            f"敌人进行了反击，造成了{self.battle_status.enemy_attack}点伤害",
        )
    def set_battle_status(
        self, *, player_hp: int = 100, enemy_hp: int = 100, enemy_attack: int = 10
    ) -> None:
        """
        Set the battle status of the player.

        Args:
            player_hp (int): The player's health points.
            enemy_hp (int): The enemy's health points.
            enemy_attack (int): The enemy's attack points.

        Returns:
            None
        """
        self.battle_status = BattleStatus(player_hp, enemy_hp, enemy_attack)

    def get_gallery(self) -> List[str]:
        """
        Get the gallery of the current event.

        Returns:
            List[str]: The list of images in the gallery.
        """
        return self.current_event.get_gallery()

    def pop_tts_queue(self) -> Optional[Tuple[str, float]]:
        """
        Pop and return the first item from the tts_queue.

        Returns:
            Optional[Tuple[str, float]]: A tuple containing the TTS text and duration.
                                       If the queue is empty, returns None.
        """
        if not self.tts_queue:
            return None, None

        tts, duration = self.tts_queue.pop(0)
        return tts, duration
    def push_tts(self, tts: str, duration: float) -> None:
        """
        Push a TTS message into the tts_queue.

        Args:
            tts (str): The text to speech message.
            duration (float): The duration of the TTS message.

        Returns:
            None
        """
        self.tts_queue.append((tts, duration))

    def clear_tts_queue(self) -> None:
        """
        Clear the TTS queue.

        Args:
            None

        Returns:
            None
        """
        self.tts_queue.clear()
    
    def get_tts_queue_timer(self) -> int:
        """
        Get the timer of the TTS queue.

        Returns:
            int: The timer of the TTS queue.
        """
        return self.tts_queue_timer
    def update_tts_queue_timer(self, time: float) -> None:
        """
        Update the timer of the TTS queue.

        Args:
            time (float): The new value for the timer.

        Returns:
            None
        """
        self.tts_queue_timer = time

    def get_record(self) -> List[str]:
        """
        Get the record of player's status changes.

        Returns:
            List[str]: The record of player's status changes.
        """
        return self.record
    
    def push_record(self, key: str, value: int) -> None:
        """
        Push a record of player's status changes to the record list.

        Args:
            key (str): The key of the status change.
            value (int): The value of the status change.

        Returns:
            None
        """
        msg = ""
        match key:
            case "stellarCurrency":
                if value > 0:
                    msg = f"获得了 {value} 个星际货币"
                else:
                    msg = f"消耗了 {value} 个星际货币"
            case "shipEnergy":
                if value > 0:
                    msg = f"飞船能量增加了 {value} "
                else:
                    msg = f"飞船能量消耗了 {value} "
            case "explorationCapability":
                if value > 0:
                    msg = f"探索能力提升了 {value} "
                else:
                    msg = f"探索能力降低了 {value} "
            case "reputationValue":
                if value > 0:
                    msg = f"获得了 {value} 声望"
                else:
                    msg = f"消耗了 {value} 声望"
        # msg前添加时间
        msg = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {msg}"
        self.record.append(msg)
    
    def calculate_score(self) -> int:
        """
        Calculate the player's score based on their resource.

        Returns:
            int: The player's score.
        """
        score = 0
        score += self.resource.stellarCurrency  # type: int
        score += self.resource.shipEnergy * 10  # type: int
        score += self.resource.explorationCapability * 100  # type: int
        score += self.resource.reputationValue * 100  # type: int
        return score

class StatusManager:
    def __init__(self) -> None:
        """
        Initializes the StatusManager with an empty cache.

        Returns:
            None
        """
        # 缓存一天
        self.status_cache: cachetools.TTLCache[str, PlayerStatus] = cachetools.TTLCache(
            maxsize=100, ttl=86400
        )
    def get_status_with_session(self, session: str) -> PlayerStatus:
        """
        Get the PlayerStatus associated with the given session.

        Args:
            session (str): The session ID.

        Returns:
            PlayerStatus: The PlayerStatus associated with the session, or a new PlayerStatus if none is found.
        """
        status: PlayerStatus = self.status_cache.get(session, None)
        if status is None:
            logger.info("status is None, create new status")
            status = PlayerStatus(Resource(100, 50, 10, 0), BattleStatus(100, 100, 20))
            self.set_status_with_session(session, status)
        return status
    
    def set_status_with_session(self, session: str, status: PlayerStatus) -> None:
        """
        Set the PlayerStatus associated with the given session.

        Args:
            session (str): The session ID.
            status (PlayerStatus): The PlayerStatus to set.

        Returns:
            None
        """
        self.status_cache[session] = status