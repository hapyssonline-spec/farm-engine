import math
import pygame

from entities.player import Player
from ui.inventory import Inventory
from world.map import World
from graphics.animations import oscillate
from .renderer import Renderer


class Engine:
    def __init__(self, screen):
        self.screen = screen

        # базовые настройки
        self.windowed_size = screen.get_size()
        self.fullscreen = False

        self.tile_size = 48
        self.world = World(50, 50, self.tile_size)
        self.player = Player(self.world.width_px // 2, self.world.height_px // 2)
        self.inventory = Inventory()

        self.renderer = Renderer(self.screen, self.world, self.player, self.inventory)

        self.camera_x = 0.0
        self.camera_y = 0.0

        # взаимодействие
        self.current_action = None
        self.action_menu = None
        self.interact_range_tiles = 3.0

        # зум
        self.zoom = 1.0
        self.zoom_min = 0.6
        self.zoom_max = 2.0

        # время
        self.global_time = 0.0
        self.time_of_day = 0.0
        self.day_length = 120.0  # полный цикл, сек

    # --- служебные методы ---

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)
        self.renderer.screen = self.screen

    def handle_mousewheel(self, delta: int):
        self.zoom += 0.1 * delta
        self.zoom = max(self.zoom_min, min(self.zoom_max, self.zoom))

    def tile_in_range(self, tile_x: int, tile_y: int) -> bool:
        ts = self.tile_size
        px, py = self.player.pos
        center_x = (tile_x + 0.5) * ts
        center_y = (tile_y + 0.5) * ts
        dist = math.hypot(px - center_x, py - center_y)
        return dist <= self.interact_range_tiles * ts

    # --- обработка событий ---

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_left_click(event.pos)
            elif event.button == 3:
                self.handle_right_click(event.pos)

    def handle_left_click(self, pos):
        # сначала HUD
        if self.renderer.hud.handle_click(pos, self.inventory):
            return

        # затем элементы контекстного меню
        if self.action_menu:
            rect = self.action_menu["rect"]
            if rect.collidepoint(pos):
                index = (pos[1] - rect.y - 5) // self.action_menu["option_height"]
                if 0 <= index < len(self.action_menu["options"]):
                    option = self.action_menu["options"][index]
                    self.execute_action(option["id"])
            self.action_menu = None

    def handle_right_click(self, pos):
        # открываем контекстное меню
        self.open_action_menu(pos)

    # --- логика контекстного меню и действий ---

    def open_action_menu(self, screen_pos):
        mx, my = screen_pos
        # учёт зума при переводе в мировые координаты
        world_x = self.camera_x + mx / self.zoom
        world_y = self.camera_y + my / self.zoom

        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)

        if not self.world.in_bounds(tile_x, tile_y):
            self.action_menu = None
            return

        if not self.tile_in_range(tile_x, tile_y):
            self.action_menu = None
            return

        options = []
        tile = self.world.get_tile(tile_x, tile_y)

        if self.world.can_dig(tile_x, tile_y):
            options.append({"id": "dig", "label": "Выкопать грядку", "tile_x": tile_x, "tile_y": tile_y})

        # посадка семян
        for crop_type, label in (("wheat", "Посадить пшеницу"), ("tomato", "Посадить томаты")):
            if self.world.can_plant(tile_x, tile_y, crop_type, self.inventory):
                options.append({
                    "id": f"plant_{crop_type}",
                    "label": label,
                    "tile_x": tile_x,
                    "tile_y": tile_y,
                })

        # сбор урожая
        if self.world.can_harvest(tile_x, tile_y):
            options.append({"id": "harvest", "label": "Собрать урожай", "tile_x": tile_x, "tile_y": tile_y})

        if not options:
            self.action_menu = None
            return

        # прямоугольник меню
        option_height = 26
        width = 200
        height = 10 + option_height * len(options)
        rect = pygame.Rect(mx, my, width, height)

        self.action_menu = {
            "rect": rect,
            "options": options,
            "option_height": option_height,
        }

    def execute_action(self, action_id: str):
        if action_id == "dig":
            tx = self.action_menu["options"][0]["tile_x"]
            ty = self.action_menu["options"][0]["tile_y"]
            self.start_dig(tx, ty)
        elif action_id == "harvest":
            opt = next(o for o in self.action_menu["options"] if o["id"] == "harvest")
            self.start_harvest(opt["tile_x"], opt["tile_y"])
        elif action_id.startswith("plant_"):
            crop_type = action_id.split("_", 1)[1]
            opt = next(o for o in self.action_menu["options"] if o["id"] == action_id)
            self.start_plant(opt["tile_x"], opt["tile_y"], crop_type)

        self.action_menu = None

    def start_dig(self, tile_x: int, tile_y: int):
        if not self.tile_in_range(tile_x, tile_y):
            return
        if not self.world.can_dig(tile_x, tile_y):
            return
        self.current_action = {
            "kind": "dig",
            "tile_x": tile_x,
            "tile_y": tile_y,
            "elapsed": 0.0,
            "duration": 1.5,
        }

    def start_plant(self, tile_x: int, tile_y: int, crop_type: str):
        if not self.tile_in_range(tile_x, tile_y):
            return
        # посадка мгновенная, но можно позже добавить прогресс
        self.world.plant(tile_x, tile_y, crop_type, self.inventory)

    def start_harvest(self, tile_x: int, tile_y: int):
        if not self.tile_in_range(tile_x, tile_y):
            return
        if not self.world.can_harvest(tile_x, tile_y):
            return
        self.current_action = {
            "kind": "harvest",
            "tile_x": tile_x,
            "tile_y": tile_y,
            "elapsed": 0.0,
            "duration": 2.0,
        }

    # --- цикл обновления ---

    def update(self, dt: float):
        self.global_time += dt
        self.time_of_day = (self.time_of_day + dt) % self.day_length

        # действия: пока копаем/собираем, герой не двигается
        keys = pygame.key.get_pressed()

        if self.current_action is not None:
            self.current_action["elapsed"] += dt
            if self.current_action["elapsed"] >= self.current_action["duration"]:
                self.finish_current_action()
        else:
            self.player.update(dt, self.world, keys)

        self.world.update(dt)
        self.update_camera()

    def finish_current_action(self):
        if self.current_action is None:
            return
        kind = self.current_action["kind"]
        tx = self.current_action["tile_x"]
        ty = self.current_action["tile_y"]

        if kind == "dig":
            self.world.dig(tx, ty)
        elif kind == "harvest":
            self.world.harvest(tx, ty, self.inventory)

        self.current_action = None

    def update_camera(self):
        ts = self.tile_size
        px, py = self.player.pos
        screen_w, screen_h = self.screen.get_size()

        view_w = screen_w / self.zoom
        view_h = screen_h / self.zoom

        cx = px - view_w / 2
        cy = py - view_h / 2

        max_x = max(0.0, self.world.width_px - view_w)
        max_y = max(0.0, self.world.height_px - view_h)

        self.camera_x = max(0.0, min(cx, max_x))
        self.camera_y = max(0.0, min(cy, max_y))

    def render(self):
        self.renderer.render(
            self.camera_x,
            self.camera_y,
            self.current_action,
            self.action_menu,
            self.global_time,
            self.zoom,
            self.time_of_day,
            self.day_length,
        )
