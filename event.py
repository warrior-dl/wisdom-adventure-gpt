import os
import json
import random
from loguru import logger

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
        return index, self.event_list[index]
    
    def get_award(self, event, id) -> tuple:
        if event is None:
            return None
        for option in event["eventOptions"]:
            if option["optionId"] == id:
                return option["award"]["key"], option["award"]["value"]
        return None
    
    def get_original_event_by_index(self, index):
        if index < 0 or index >= len(self.original_event):
            return None
        return self.original_event[index]
        
        
