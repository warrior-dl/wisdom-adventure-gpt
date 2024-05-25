
from loguru import logger
class PlayerStatus:
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
        logger.info(f"status update: key: {key}, value: {value}")
        setattr(self, key, value)

