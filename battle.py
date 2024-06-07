import json
import random

class Battle:
    def __init__(self):
        self.player_hp = 100
        self.enemy_hp = 100

    def roll_dice(self):
        return random.randint(1, 100)

    def apply_effects(self, effects):
        for key, value in effects.items():
            if key in self.player:
                self.player[key] += value
            elif key in self.enemy:
                self.enemy[key] += value

    def make_choice(self, choice):
        stage = self.data["stages"][self.current_stage]
        if choice not in stage["choices"]:
            raise ValueError("Invalid choice")
        
        choice_data = stage["choices"][choice]
        roll = self.roll_dice()
        success_threshold = choice_data["success"]["roll"]

        # Apply costs
        for key, value in choice_data["cost"].items():
            if key in self.player:
                self.player[key] -= value

        # Determine success or failure
        if roll <= success_threshold:
            self.apply_effects(choice_data["success"]["effect"])
            return "success", roll
        else:
            self.apply_effects(choice_data["failure"]["effect"])
            return "failure", roll

    def next_stage(self):
        if self.current_stage < len(self.data["stages"]) - 1:
            self.current_stage += 1
        else:
            raise ValueError("No more stages")

    def get_status(self):
        return {
            "player": self.player,
            "enemy": self.enemy,
            "current_stage": self.data["stages"][self.current_stage]["name"]
        }
