import os
import json
import random
import copy
from loguru import logger
from enum import Enum

class EventType(Enum):
    # characterInteraction|choice|battle
    characterInteraction = 1
    choice = 2
    battle = 3

class Event:
    def __init__(self, id, event_json, images):
        self.content = event_json
        self.id = id
        self.used = False
        self.images = images
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

    def get_images(self):
        return self.images

class EventManager:
    def __init__(self, event_list_path, original_event_path, battle_path, event_image_path, battle_images_path):
        self.event_list = []
        self.original_event = []
        self.battle_list = []
        self.load_event_list(event_list_path)
        self.load_original_event(original_event_path)
        self.load_battle_event(battle_path)
        self.event_image_path = event_image_path
        self.battle_images_path = battle_images_path

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
        
        original_images =self.original_event[index]["images"]
        images_path = []
        if len(original_images) != 0:
            # 从original_images列表中的类似"../Images/figure_0131_0297.jpg"中提取文件名
            images_name = [os.path.basename(filename) for filename in original_images]
            # 组合self.image_path
            images_path = [os.path.join(self.event_image_path, name) for name in images_name]
        return index, Event(index, self.event_list[index], images_path)
    
    def get_original_event_by_index(self, index):
        if index < 0 or index >= len(self.original_event):
            return None
        return self.original_event[index]
    
    def get_battle_by_index(self, index):
        if index < 0 or index >= len(self.battle_list):
            return None
        battle = self.battle_list[index]
        images_path = [os.path.join(self.battle_images_path, i) for i in battle["images"]]
        return index, Event(index, battle, images_path)
    
