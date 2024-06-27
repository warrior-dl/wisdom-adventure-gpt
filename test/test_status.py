import unittest
from unittest.mock import patch

from status import Resource

class TestResource(unittest.TestCase):

    def setUp(self):
        self.resource = Resource(100, 50, 3, 20)

    def test_init(self):
        self.assertEqual(self.resource.stellarCurrency, 100)
        self.assertEqual(self.resource.shipEnergy, 50)
        self.assertEqual(self.resource.explorationCapability, 3)
        self.assertEqual(self.resource.reputationValue, 20)

    def test_get_status(self):
        status = self.resource.get_status()
        self.assertEqual(status, {
            "stellarCurrency": 100,
            "shipEnergy": 50,
            "explorationCapability": 3,
            "reputationValue": 20
        })

    def test_get_value(self):
        self.assertEqual(self.resource.get_value("stellarCurrency"), 100)
        self.assertEqual(self.resource.get_value("shipEnergy"), 50)
        self.assertEqual(self.resource.get_value("explorationCapability"), 3)
        self.assertEqual(self.resource.get_value("reputationValue"), 20)

    def test_update(self):
        self.resource.update("stellarCurrency", 200)
        self.assertEqual(self.resource.stellarCurrency, 200)
        self.resource.update("shipEnergy", 100)
        self.assertEqual(self.resource.shipEnergy, 100)
        self.resource.update("explorationCapability", 5)
        self.assertEqual(self.resource.explorationCapability, 5)
        self.resource.update("reputationValue", 50)
        self.assertEqual(self.resource.reputationValue, 50)



if __name__ == '__main__':
    unittest.main()