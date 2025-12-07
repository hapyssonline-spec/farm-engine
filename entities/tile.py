class Tile:
    """Один тайл карты: биом + состояние (земля, грядка, растение)."""

    def __init__(self, ground_type: str = "grass"):
        # Базовый тип поверхности: обычная трава, сухая трава и т.п.
        # Не меняется при копке / посадке.
        self.ground_type = ground_type  # "grass" | "dry_grass"

        # Текущее состояние клетки:
        # "ground" — нет грядки, просто поверхность
        # "soil"   — вскопанная грядка
        # "crop"   — растущая культура
        self.type = "ground"

        self.crop_type = None  # "wheat" | "tomato" | None
        self.growth_stage = 0
        self.growth_timer = 0.0

    def reset_crop(self):
        # После сбора возвращаемся к состоянию "soil", но не трогаем ground_type.
        self.type = "soil"
        self.crop_type = None
        self.growth_stage = 0
        self.growth_timer = 0.0
