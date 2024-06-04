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
    def get_award(self, id) -> tuple:
        for option in self.content["eventOptions"]:
            if option["optionId"] == id:
                return option["award"]["key"], option["award"]["value"]
        return None
    def get_type(self):
        return self.content["eventType"]
    def get_background(self):
        return self.content["eventCharacters"]["background"]
    def get_purpose(self):
        return self.content["eventCharacters"]["purpose"]
    def get_content(self):
        return self.content

class EventManager:
    def __init__(self, event_list_path, original_event_path):
        self.event_list = []
        self.original_event = []
        self.load_event_list(event_list_path)
        self.load_original_event(original_event_path)

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

    def get_event_random(self):
        if len(self.event_list) == 0:
            return None
        index = random.randint(0, len(self.event_list)-1)
        return index, Event(index, self.event_list[index])
    
    def get_original_event_by_index(self, index):
        if index < 0 or index >= len(self.original_event):
            return None
        return self.original_event[index]
        
        
