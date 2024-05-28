
from loguru import logger
from event import Event
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

class PlayerStatus:
    def __init__(self, resource: Resource) -> None:
        self.resource = resource
        self.current_event = None
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
    def get_resource(self):
        return self.resource
    def update_resource(self, key, value):
        if self.current_event.used:
            logger.info("had update status, not need update again")
            return
        event = self.current_event
        if event is None:
            logger.info("current event is None")
            return
        if key is not None:
            logger.info(f"status update: key: {key}, value: {value}")
            self.resource.update(key, value)
        self.current_event.used = True

class StatusManager:
    def __init__(self):
        # 缓存一天
        self.status_cache = cachetools.TTLCache(maxsize=100, ttl=86400)
    def get_status_with_session(self, session) -> PlayerStatus:
        status = self.status_cache.get(session, None)
        if status is None:
            logger.info("status is None, create new status")
            status = PlayerStatus(Resource(100, 50, 10, 0))
            self.set_status_with_session(session, status)
        return status
    
    def set_status_with_session(self, session, status: PlayerStatus):
        self.status_cache[session] = status