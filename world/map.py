import random

from entities.tile import Tile
from entities.crop import MAX_GROWTH_STAGE, GROWTH_STAGE_TIME, roll_harvest_amount


class World:
    def __init__(self, width: int, height: int, tile_size: int):
        self.width = width
        self.height = height
        self.tile_size = tile_size

        self.width_px = self.width * self.tile_size
        self.height_px = self.height * self.tile_size

        # Базово заполняем обычной травой
        self.tiles = [
            [Tile("grass") for _ in range(self.width)]
            for _ in range(self.height)
        ]

        # Генерируем островки сухой травы как другой биом
        self._generate_dry_grass_patches()

    # --- генерация биомов ---

    def _generate_dry_grass_patches(self):
        patches = max(4, (self.width * self.height) // 150)
        for _ in range(patches):
            cx = random.randint(0, self.width - 1)
            cy = random.randint(0, self.height - 1)
            radius = random.randint(3, 7)

            for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
                for x in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                        self.tiles[y][x].ground_type = "dry_grass"

    # --- доступ к тайлам ---

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int):
        if not self.in_bounds(x, y):
            return None
        return self.tiles[y][x]

    # --- логика грядок и роста ---

    def can_dig(self, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        # Копать можно только по "чистой" поверхности (трава / сухая трава)
        return tile is not None and tile.type == "ground"

    def dig(self, x: int, y: int) -> bool:
        if not self.can_dig(x, y):
            return False
        tile = self.get_tile(x, y)
        tile.type = "soil"
        tile.crop_type = None
        tile.growth_stage = 0
        tile.growth_timer = 0.0
        return True

    def can_plant(self, x: int, y: int, crop_type: str, inventory) -> bool:
        tile = self.get_tile(x, y)
        if tile is None:
            return False
        if tile.type not in ("soil", "crop"):
            return False
        if tile.crop_type is not None and tile.growth_stage > 0:
            return False
        if not inventory.can_plant(crop_type):
            return False
        return True

    def plant(self, x: int, y: int, crop_type: str, inventory) -> bool:
        if not self.can_plant(x, y, crop_type, inventory):
            return False
        tile = self.get_tile(x, y)
        tile.type = "crop"
        tile.crop_type = crop_type
        tile.growth_stage = 1
        tile.growth_timer = 0.0
        inventory.use_seed(crop_type)
        return True

    def can_harvest(self, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        return (
            tile is not None
            and tile.type == "crop"
            and tile.crop_type is not None
            and tile.growth_stage >= MAX_GROWTH_STAGE
        )

    def harvest(self, x: int, y: int, inventory) -> bool:
        tile = self.get_tile(x, y)
        if tile is None or not self.can_harvest(x, y):
            return False

        amount = roll_harvest_amount()
        inventory.add_harvest(tile.crop_type, amount)

        # поле остаётся вспаханным
        tile.reset_crop()
        return True

    def update(self, dt: float):
        for row in self.tiles:
            for tile in row:
                if (
                    tile.type == "crop"
                    and tile.crop_type is not None
                    and 1 <= tile.growth_stage < MAX_GROWTH_STAGE
                ):
                    tile.growth_timer += dt
                    if tile.growth_timer >= GROWTH_STAGE_TIME:
                        tile.growth_timer = 0.0
                        tile.growth_stage = min(
                            MAX_GROWTH_STAGE, tile.growth_stage + 1
                        )
