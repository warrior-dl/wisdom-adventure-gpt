import os
import json
import random
import copy
from loguru import logger
from enum import Enum

class EventType(Enum):
    # characterInteraction|choice|resourceDecision
    characterInteraction = 1
    choice = 2
    resourceDecision = 3

class Event:
    def __init__(self, id, event_json):
        self.content = event_json
        self.id = id
        self.used = False
    def get_id(self):
        return self.id
    def get_option_award(self, id) -> list:
        for option in self.content["eventOptions"]:
            if option["optionId"] == id:
                return option["award"]
        return None
    def get_event_award(self):
        return self.content["eventAward"]
    def get_type(self):
        return self.content["eventType"]
    def get_background(self):
        return self.content["eventCharacters"]["background"]
    def get_purpose(self):
        return self.content["eventCharacters"]["purpose"]
    def get_content(self):
        return self.content
    def get_enemy_info(self):
        return self.content["enemyInfo"]
    def get_self_introduction(self):
        return self.content["eventCharacters"]["selfIntroduction"]

class EventManager:
    def __init__(self, event_list_path, original_event_path, battle_path):
        self.event_list = []
        self.original_event = []
        self.battle_list = []
        self.load_event_list(event_list_path)
        self.load_original_event(original_event_path)
        self.load_battle_event(battle_path)

    def load_event_list(self, path):
        if path is None:
            logger.warning('event path is None')
            return
        with open(path, 'r', encoding='utf-8') as f:
            try:
                self.event_list = json.load(f)
            except json.decoder.JSONDecodeError:
                logger.warning('JSONDecodeError: {}'.format(path))
                self.event_list = []

    def load_original_event(self, path):
        if path is None:
            logger.warning('original event path is None')
            return
        with open(path, 'r', encoding='utf-8') as f:
            try:
                self.original_event = json.load(f)
            except json.decoder.JSONDecodeError:
                logger.warning('JSONDecodeError: {}'.format(path))
                self.original_event = []

    def load_battle_event(self, path):
        if path is None:
            logger.warning('battle path is None')
            return
        with open(path, 'r', encoding='utf-8') as f:
            try:
                self.battle_list = json.load(f)
            except json.decoder.JSONDecodeError:
                logger.warning('JSONDecodeError: {}'.format(path))
                self.battle_list = []
    def get_event_random(self):
        if len(self.event_list) == 0:
            return None
        index = random.randint(0, len(self.event_list)-1)
        return index, Event(index, self.event_list[index])
    
    def get_original_event_by_index(self, index):
        if index < 0 or index >= len(self.original_event):
            return None
        return self.original_event[index]
    
    def get_battle_by_index(self, index):
        if index < 0 or index >= len(self.battle_list):
            return None
        return index, Event(index, self.battle_list[index])
        
