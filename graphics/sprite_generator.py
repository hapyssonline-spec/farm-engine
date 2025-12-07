import math
import random
import pygame

from entities.crop import MAX_GROWTH_STAGE


def _smooth_noise(surface, passes: int = 1):
    """Лёгкое сглаживание, чтобы убрать жёсткие пиксели."""
    w, h = surface.get_size()
    for _ in range(passes):
        for y in range(h):
            for x in range(w):
                r, g, b, a = surface.get_at((x, y))
                acc_r = r
                acc_g = g
                acc_b = b
                count = 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            nr, ng, nb, na = surface.get_at((nx, ny))
                            acc_r += nr
                            acc_g += ng
                            acc_b += nb
                            count += 1
                surface.set_at((x, y), (acc_r // count, acc_g // count, acc_b // count, a))



def _make_grass_like_tile(tile_size: int, top_color, bottom_color, noise_strength: float = 0.35) -> pygame.Surface:
    """Генератор бесшовной травы без мыльных градиентов.

    Делаем тайл на основе тайлового шума:
    1. Генерируем случайный шум на области (2*size x 2*size).
    2. Для каждой точки итогового тайла усредняем 4 значения шума:
       (x, y), (x + size, y), (x, y + size), (x + size, y + size).
       Так края автоматически совпадают и швов не будет.
    3. Полученный шум используем как коэффициент смешивания между top_color и bottom_color.

    В итоге текстура получается:
    • без крупного вертикального градиента;
    • без видимой "сеточки" или диагональных узоров;
    • с мелким "зерном" травы, которое выглядит более HD.
    """
    size = tile_size
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # детерминированный генератор, чтобы при каждом запуске
    # трава выглядела одинаково
    seed = (top_color[0] * 17 + top_color[1] * 31 + top_color[2] * 13 +
            bottom_color[0] * 23 + bottom_color[1] * 7 + bottom_color[2] * 29)
    rng = random.Random(seed)

    # предварительно генерируем шум на области 2*size x 2*size
    big_w = size * 2
    big_h = size * 2
    noise = [[rng.random() for _ in range(big_w)] for _ in range(big_h)]

    for y in range(size):
        for x in range(size):
            # усредняем 4 значения шума – так текстура будет тайлиться
            v = (
                noise[y][x] +
                noise[y][x + size] +
                noise[y + size][x] +
                noise[y + size][x + size]
            ) * 0.25

            # слегка сужаем диапазон, чтобы трава не была "кислотной"
            v = 0.5 + (v - 0.5) * noise_strength * 2.0
            if v < 0.0:
                v = 0.0
            elif v > 1.0:
                v = 1.0

            r = int(top_color[0] * (1.0 - v) + bottom_color[0] * v)
            g = int(top_color[1] * (1.0 - v) + bottom_color[1] * v)
            b = int(top_color[2] * (1.0 - v) + bottom_color[2] * v)

            surf.set_at((x, y), (r, g, b, 255))

    return surf


def create_grass_tile(tile_size: int) -> pygame.Surface:
    """Обычная трава с большим количеством оттенков зелёного."""
    top = (60, 138, 72)
    bottom = (28, 90, 50)
    return _make_grass_like_tile(tile_size, top, bottom, noise_strength=0.18)


def create_dry_grass_tile(tile_size: int) -> pygame.Surface:
    """Сухая трава — более жёлто-коричневый биом."""
    top = (168, 150, 86)
    bottom = (124, 104, 62)
    return _make_grass_like_tile(tile_size, top, bottom, noise_strength=0.20)


def create_soil_tile(tile_size: int) -> pygame.Surface:
    """Грядка: тёмная земля с аккуратной травой по периметру."""
    surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)

    # базовый вертикальный градиент земли
    top = (118, 78, 52)
    bottom = (72, 44, 28)
    for y in range(tile_size):
        t = y / max(1, tile_size - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)

        # небольшой шум по X, чтобы убрать идеальные полосы
        n = math.sin(2.5 * math.pi * (y / tile_size)) * 0.06
        k = 1.0 + n
        rr = max(0, min(255, int(r * k)))
        gg = max(0, min(255, int(g * k)))
        bb = max(0, min(255, int(b * k)))

        pygame.draw.line(surf, (rr, gg, bb), (0, y), (tile_size, y))

    # борозды
    for y in range(5, tile_size, 7):
        pygame.draw.line(surf, (52, 32, 20), (3, y), (tile_size - 3, y), 1)

    # лёгкий подсвет в центре
    center_rect = pygame.Rect(4, 4, tile_size - 8, tile_size - 8)
    center = pygame.Surface((center_rect.width, center_rect.height), pygame.SRCALPHA)
    center.fill((162, 118, 76, 40))
    surf.blit(center, center_rect.topleft)

    # аккуратные пучки травы по периметру
    grass_colors = [
        (44, 120, 66),
        (32, 96, 52),
        (70, 142, 84),
    ]

    def draw_edge(side: str):
        count = 6
        for _ in range(count):
            color = random.choice(grass_colors)
            length = random.randint(5, 9)
            thickness = 2

            if side == "top":
                x = random.randint(2, tile_size - 3)
                y2 = random.randint(3, 5)
                y1 = y2 + length
                pygame.draw.line(surf, color, (x, y1), (x, y2), thickness)
            elif side == "bottom":
                x = random.randint(2, tile_size - 3)
                y1 = tile_size - random.randint(4, 6)
                y2 = y1 - length
                pygame.draw.line(surf, color, (x, y1), (x, y2), thickness)
            elif side == "left":
                y = random.randint(4, tile_size - 4)
                x2 = random.randint(3, 5)
                x1 = x2 + length
                pygame.draw.line(surf, color, (x1, y), (x2, y), thickness)
            elif side == "right":
                y = random.randint(4, tile_size - 4)
                x1 = tile_size - random.randint(4, 6)
                x2 = x1 - length
                pygame.draw.line(surf, color, (x1, y), (x2, y), thickness)

    for side in ("top", "bottom", "left", "right"):
        draw_edge(side)

    return surf


# --- КУЛЬТУРЫ ---


def _draw_wheat_stage(surface: pygame.Surface, tile_size: int, stage: int):
    """Пшеница с 5 фазами: от зелёных ростков до полностью золотых колосьев."""
    base_y = tile_size - 4
    center_x = tile_size // 2

    # постепенный переход оттенков стеблей и колосьев
    stem_green = (70, 122, 64)
    stem_yellow = (170, 132, 60)
    head_green = (124, 170, 88)
    head_yellow = (230, 208, 112)

    t = (stage - 1) / max(1, MAX_GROWTH_STAGE - 1)
    # На ранних стадиях больше зелени, на поздних — полностью жёлтое
    stem_color = (
        int(stem_green[0] * (1 - t) + stem_yellow[0] * t),
        int(stem_green[1] * (1 - t) + stem_yellow[1] * t),
        int(stem_green[2] * (1 - t) + stem_yellow[2] * t),
    )
    head_color = (
        int(head_green[0] * (1 - t) + head_yellow[0] * t),
        int(head_green[1] * (1 - t) + head_yellow[1] * t),
        int(head_green[2] * (1 - t) + head_yellow[2] * t),
    )

    # высота и плотность увеличиваются с фазой
    min_h = int(tile_size * 0.20)
    max_h = int(tile_size * 0.55)
    height = min_h + int((max_h - min_h) * t)

    # количество стеблей
    stalks = 2 + stage
    offsets = [int((i - (stalks - 1) / 2.0) * 3) for i in range(stalks)]

    for offset in offsets:
        x = center_x + offset
        pygame.draw.line(surface, stem_color, (x, base_y), (x, base_y - height), 2)

        # колосья
        head_segments = 3 + stage
        for i in range(head_segments):
            w = 4
            h = 3
            seg_y = base_y - height - i * 3
            rect = pygame.Rect(x - w // 2, seg_y, w, h)
            pygame.draw.ellipse(surface, head_color, rect)


def _draw_tomato_stage(surface: pygame.Surface, tile_size: int, stage: int):
    """Куст томатов с 5 фазами роста."""
    base_y = tile_size - 3
    center_x = tile_size // 2

    # зелёные тона листвы
    dark = (24, 70, 34)
    mid = (46, 118, 62)
    light = (86, 160, 96)

    # стебель
    stem_height = int(tile_size * (0.18 + 0.06 * stage))
    pygame.draw.line(surface, mid, (center_x, base_y), (center_x, base_y - stem_height), 3)

    # крона куста
    crown_h = int(tile_size * (0.20 + 0.06 * stage))
    crown_w = int(tile_size * (0.38 + 0.05 * stage))
    crown_rect = pygame.Rect(0, 0, crown_w, crown_h)
    crown_rect.midbottom = (center_x, base_y - stem_height + crown_h // 2)

    pygame.draw.ellipse(surface, mid, crown_rect)
    inner = crown_rect.inflate(-6, -3)
    pygame.draw.ellipse(surface, light, inner)
    shadow = crown_rect.inflate(-crown_rect.width // 3, -crown_rect.height // 3)
    shadow.x += 3
    pygame.draw.ellipse(surface, dark, shadow)

    # плоды появляются с 3-й стадии, постепенно добавляем
    if stage >= 3:
        tomato_base = (204, 40, 40)
        tomato_highlight = (248, 114, 114)

        max_tomatoes = 1 + (stage - 3) * 2  # 1, 3, 5 плодов на 3/4/5 стадиях
        for _ in range(max_tomatoes):
            dx = random.randint(-crown_w // 4, crown_w // 4)
            dy = random.randint(-crown_h // 4, crown_h // 4)
            radius = random.randint(3, 5)  # помидор значительно меньше головы героя
            cx = center_x + dx
            cy = crown_rect.centery + dy
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = (cx, cy)
            pygame.draw.ellipse(surface, tomato_base, rect)

            hl = rect.inflate(-radius, -radius)
            hl.x -= 1
            hl.y -= 1
            pygame.draw.ellipse(surface, tomato_highlight, hl)


def create_crop_sprites(tile_size: int):
    """Создаём HD-спрайты культур с 5 фазами роста."""
    crops = {
        "wheat": [None] * (MAX_GROWTH_STAGE + 1),
        "tomato": [None] * (MAX_GROWTH_STAGE + 1),
    }

    for crop_type in crops.keys():
        for stage in range(1, MAX_GROWTH_STAGE + 1):
            surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            if crop_type == "wheat":
                _draw_wheat_stage(surf, tile_size, stage)
            else:
                _draw_tomato_stage(surf, tile_size, stage)
            crops[crop_type][stage] = surf

    return crops
