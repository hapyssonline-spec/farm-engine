class Inventory:
    def __init__(self):
        # стартовые значения
        self.seeds_wheat = 4
        self.seeds_tomato = 4
        self.harvest_wheat = 0
        self.harvest_tomato = 0

        # выбранный тип семян ("wheat" или "tomato")
        self.selected_seed = "wheat"

    # --- семена ---

    def can_plant(self, crop_type: str) -> bool:
        if crop_type == "wheat":
            return self.seeds_wheat > 0
        elif crop_type == "tomato":
            return self.seeds_tomato > 0
        return False

    def use_seed(self, crop_type: str) -> bool:
        if not self.can_plant(crop_type):
            return False
        if crop_type == "wheat":
            self.seeds_wheat -= 1
        elif crop_type == "tomato":
            self.seeds_tomato -= 1
        return True

    # --- урожай ---

    def add_harvest(self, crop_type: str, amount: int):
        if crop_type == "wheat":
            self.harvest_wheat += amount
        elif crop_type == "tomato":
            self.harvest_tomato += amount
