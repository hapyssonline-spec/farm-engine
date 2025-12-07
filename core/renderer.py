import math
import pygame

from graphics.sprite_generator import (
    create_grass_tile,
    create_dry_grass_tile,
    create_soil_tile,
    create_crop_sprites,
)
from graphics.animations import oscillate
from ui.hud import HUD


class Renderer:
    def __init__(self, screen, world, player, inventory):
        self.screen = screen
        self.world = world
        self.player = player
        self.inventory = inventory

        self.tile_size = world.tile_size
        self.grass_tile = create_grass_tile(self.tile_size)
        self.dry_grass_tile = create_dry_grass_tile(self.tile_size)
        self.soil_tile = create_soil_tile(self.tile_size)
        self.crop_sprites = create_crop_sprites(self.tile_size)

        self.hud = HUD()
        self.font_menu = pygame.font.SysFont("arial", 14)

    # --- основной рендер ---

    def render(self, camera_x, camera_y, current_action, action_menu,
               global_time, zoom, time_of_day, day_length):
        screen_w, screen_h = self.screen.get_size()

        # размеры окна мира в зависимости от зума
        view_w = max(1, int(screen_w / zoom))
        view_h = max(1, int(screen_h / zoom))

        world_surface = pygame.Surface((view_w, view_h), pygame.SRCALPHA)

        # Временная подмена self.screen, чтобы использовать существующие методы
        original_screen = self.screen
        self.screen = world_surface

        self.screen.fill((5, 5, 10))
        self.render_world(camera_x, camera_y)
        self.render_player(camera_x, camera_y, global_time, current_action)

        if current_action:
            self.render_action_progress(current_action, camera_x, camera_y)

        # Наложение по времени суток
        self.apply_day_night(world_surface, time_of_day, day_length)

        # Возвращаем основной экран
        self.screen = original_screen

        # Масштабируем мир под фактический размер окна
        scaled_world = pygame.transform.smoothscale(world_surface, (screen_w, screen_h))
        self.screen.blit(scaled_world, (0, 0))

        # HUD и контекстное меню не зависят от зума
        self.hud.draw(self.screen, self.inventory)
        if action_menu:
            self.render_action_menu(action_menu)

        pygame.display.flip()

    # --- день/ночь ---

    def apply_day_night(self, surface: pygame.Surface, time_of_day: float, day_length: float):
        if day_length <= 0:
            return
        t = (time_of_day % day_length) / day_length  # 0..1

        # ключевые точки: утро, день, вечер, ночь
        key = [
            ((255, 225, 190), 80),   # утро
            ((255, 255, 255), 0),    # день
            ((255, 170, 130), 100),  # вечер
            ((20, 40, 80), 160),     # ночь
            ((255, 225, 190), 80),   # утро снова, для плавного цикла
        ]

        pos = t * 4.0
        i = int(pos)
        frac = pos - i
        i = max(0, min(3, i))

        (c1, a1) = key[i]
        (c2, a2) = key[i + 1]

        r = int(c1[0] + (c2[0] - c1[0]) * frac)
        g = int(c1[1] + (c2[1] - c1[1]) * frac)
        b = int(c1[2] + (c2[2] - c1[2]) * frac)
        a = int(a1 + (a2 - a1) * frac)

        if a <= 0:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((r, g, b, a))
        surface.blit(overlay, (0, 0))

    # --- мир ---

    def render_world(self, camera_x, camera_y):
        screen_w, screen_h = self.screen.get_size()
        ts = self.tile_size

        start_x = int(camera_x // ts)
        start_y = int(camera_y // ts)
        end_x = int((camera_x + screen_w) // ts) + 1
        end_y = int((camera_y + screen_h) // ts) + 1

        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                tile = self.world.get_tile(tx, ty)
                if tile is None:
                    continue

                sx = int(tx * ts - camera_x)
                sy = int(ty * ts - camera_y)

                # базовая поверхность (трава / сухая трава)
                base = self.grass_tile
                if getattr(tile, "ground_type", "grass") == "dry_grass":
                    base = self.dry_grass_tile
                self.screen.blit(base, (sx, sy))

                # грядка / растение
                if tile.type in ("soil", "crop"):
                    self.screen.blit(self.soil_tile, (sx, sy))

                if tile.type == "crop" and tile.crop_type and tile.growth_stage > 0:
                    sprites = self.crop_sprites.get(tile.crop_type)
                    if sprites:
                        idx = min(tile.growth_stage, len(sprites) - 1)
                        sprite = sprites[idx]
                        if sprite:
                            rect = sprite.get_rect()
                            rect.midbottom = (sx + ts // 2, sy + ts)
                            self.screen.blit(sprite, rect)

    # --- герой ---

    def render_player(self, camera_x, camera_y, global_time, current_action):
        px, py = self.player.pos
        # позиция ног героя в мировой системе
        world_feet_x = px
        world_feet_y = py

        # перевод в координаты поверхности мира
        screen_feet_x = world_feet_x - camera_x
        screen_feet_y = world_feet_y - camera_y

        moving = getattr(self.player, "is_moving", False)
        anim_t = getattr(self.player, "anim_time", 0.0)

        action_kind = current_action["kind"] if current_action else None
        action_elapsed = current_action["elapsed"] if current_action else 0.0

        # --- параметры анимации ---

        if moving and not action_kind:
            # обычная ходьба
            bob = oscillate(anim_t, speed=4.0, magnitude=3.0)
            leg_swing = oscillate(anim_t, speed=9.0, magnitude=5.0)
            arm_swing = oscillate(anim_t, speed=8.5, magnitude=4.0)
        elif action_kind in ("dig", "harvest"):
            # герой стоит и работает лопатой — без дёрганий ногами
            cycle_period = 0.8
            phase = (action_elapsed % cycle_period) / cycle_period

            # лёгкое приседание при погружении лопаты
            if phase < 0.4:  # опускается
                bob = 4.0 * phase
            elif phase < 0.75:  # поднимается
                bob = 4.0 * (0.75 - phase)
            else:
                bob = 0.0

            leg_swing = 0.0
            arm_swing = 0.0
        else:
            # лёгкое "дыхание" когда стоит
            bob = oscillate(global_time, speed=1.5, magnitude=1.0)
            leg_swing = 0.0
            arm_swing = 0.0

        # рисуем в более высоком разрешении и скейлим вниз
        base_w, base_h = 54, 80
        hero_surf = pygame.Surface((base_w, base_h), pygame.SRCALPHA)

        feet_x = base_w // 2
        feet_y = base_h - 6

        # Цвета
        skin_base = (245, 210, 164)
        skin_shadow = (216, 178, 142)
        skin_highlight = (255, 229, 195)

        shirt_dark = (40, 72, 135)
        shirt_mid = (59, 104, 184)
        shirt_light = (92, 142, 210)

        pants_dark = (27, 30, 40)
        pants_light = (50, 55, 75)

        boot_color = (15, 15, 18)

        hair_dark = (28, 18, 12)
        hair_mid = (46, 30, 20)

        # --- ноги ---
        leg_h = 24
        leg_w = 8
        leg_gap = 4

        if moving and not action_kind:
            left_off = -int(leg_swing)
            right_off = int(leg_swing)
        else:
            left_off = right_off = 0

        left_leg_rect = pygame.Rect(
            feet_x - leg_gap - leg_w, feet_y - leg_h + left_off, leg_w, leg_h
        )
        right_leg_rect = pygame.Rect(
            feet_x + leg_gap, feet_y - leg_h + right_off, leg_w, leg_h
        )

        pygame.draw.rect(hero_surf, pants_dark, left_leg_rect)
        pygame.draw.rect(hero_surf, pants_dark, right_leg_rect)

        # блики на ногах
        for rect in (left_leg_rect, right_leg_rect):
            light = pygame.Rect(rect.x + 1, rect.y + 3, rect.width // 2, rect.height - 6)
            pygame.draw.rect(hero_surf, pants_light, light)

        # ботинки
        boot_h = 6
        left_boot = pygame.Rect(
            left_leg_rect.x - 1, left_leg_rect.bottom - 2, left_leg_rect.width + 2, boot_h
        )
        right_boot = pygame.Rect(
            right_leg_rect.x - 1, right_leg_rect.bottom - 2, right_leg_rect.width + 2, boot_h
        )
        pygame.draw.rect(hero_surf, boot_color, left_boot)
        pygame.draw.rect(hero_surf, boot_color, right_boot)

        # --- тело ---
        body_h = 38
        body_w = 26
        # уменьшаем отступ, чтобы голова точно не вылезала за пределы спрайта
        body_top = int(feet_y - body_h - 10 - bob)
        body_rect = pygame.Rect(feet_x - body_w // 2, body_top, body_w, body_h)

        pygame.draw.rect(hero_surf, shirt_mid, body_rect)

        # плечи
        shoulder_rect = pygame.Rect(body_rect.x, body_rect.y - 8, body_rect.width, 14)
        pygame.draw.ellipse(hero_surf, shirt_mid, shoulder_rect)

        # свет/тень
        light_rect = pygame.Rect(
            body_rect.x + 2, body_rect.y + 3, body_rect.width // 2, body_rect.height - 6
        )
        dark_rect = pygame.Rect(
            body_rect.centerx, body_rect.y + 3, body_rect.width // 2 - 2, body_rect.height - 6
        )
        pygame.draw.rect(hero_surf, shirt_light, light_rect)
        pygame.draw.rect(hero_surf, shirt_dark, dark_rect)

        pygame.draw.rect(hero_surf, (20, 28, 50), body_rect, 1)

        # --- руки ---
        arm_h = 18
        arm_w = 6

        if action_kind in ("dig", "harvest"):
            # руки чуть ниже и статичнее, когда держит лопату
            left_arm_y = body_rect.y + 12
            right_arm_y = body_rect.y + 12
        else:
            left_arm_y = body_rect.y + 10 + int(arm_swing)
            right_arm_y = body_rect.y + 10 - int(arm_swing)

        left_arm_rect = pygame.Rect(body_rect.x - arm_w + 2, left_arm_y, arm_w, arm_h)
        right_arm_rect = pygame.Rect(body_rect.right - 2, right_arm_y, arm_w, arm_h)

        for rect in (left_arm_rect, right_arm_rect):
            pygame.draw.rect(hero_surf, skin_base, rect)
            shadow = pygame.Rect(rect.x + 2, rect.y, rect.width - 2, rect.height)
            pygame.draw.rect(hero_surf, skin_shadow, shadow)

        # --- шея ---
        neck_h = 7
        neck_w = 12
        neck_rect = pygame.Rect(feet_x - neck_w // 2, body_rect.y - neck_h + 3, neck_w, neck_h)
        pygame.draw.rect(hero_surf, skin_base, neck_rect)

        # --- голова ---
        head_w = 30
        head_h = 24
        head_rect = pygame.Rect(feet_x - head_w // 2, neck_rect.y - head_h + 6, head_w, head_h)

        pygame.draw.ellipse(hero_surf, skin_base, head_rect)

        shadow_rect = head_rect.copy()
        shadow_rect.x += head_w // 3
        shadow_rect.width -= head_w // 3
        pygame.draw.ellipse(hero_surf, skin_shadow, shadow_rect)

        highlight_rect = head_rect.inflate(-8, -10)
        highlight_rect.x -= 2
        pygame.draw.ellipse(hero_surf, skin_highlight, highlight_rect)

        # лицо: глаза + лёгкая улыбка
        eye_w, eye_h = 4, 3
        eye_y = head_rect.y + head_rect.height // 2 - 3
        left_eye = pygame.Rect(head_rect.x + 6, eye_y, eye_w, eye_h)
        right_eye = pygame.Rect(head_rect.right - 6 - eye_w, eye_y, eye_w, eye_h)
        pygame.draw.rect(hero_surf, (35, 32, 30), left_eye)
        pygame.draw.rect(hero_surf, (35, 32, 30), right_eye)

        mouth_rect = pygame.Rect(
            head_rect.centerx - 5, head_rect.bottom - 7, 10, 3
        )
        pygame.draw.arc(
            hero_surf, (120, 80, 70), mouth_rect, math.radians(10), math.radians(170), 1
        )

        # волосы
        hair_rect = pygame.Rect(head_rect.x - 2, head_rect.y - 4, head_rect.width + 4, head_rect.height // 2)
        pygame.draw.ellipse(hero_surf, hair_dark, hair_rect)
        hair_light = hair_rect.inflate(-8, -4)
        pygame.draw.ellipse(hero_surf, hair_mid, hair_light)

        # блик на волосах
        shine_rect = pygame.Rect(hair_rect.x + 6, hair_rect.y + 4, 8, 4)
        pygame.draw.ellipse(hero_surf, (210, 190, 150), shine_rect)

        # --- лопата при действиях ---
        if action_kind in ("dig", "harvest"):
            shaft_color = (130, 100, 60)
            blade_color = (190, 190, 200)

            hand_x = right_arm_rect.centerx + 2
            hand_y = right_arm_rect.centery + 2

            cycle_period = 0.8
            phase = (action_elapsed % cycle_period) / cycle_period

            base_len = 42

            if phase < 0.35:  # опускаем лопату в землю
                angle_deg = 110
                k = phase / 0.35
                length = base_len * (0.6 + 0.4 * k)
            elif phase < 0.7:  # поднимаем с землёй
                angle_deg = 75
                k = (phase - 0.35) / 0.35
                length = base_len * (1.0 - 0.2 * k)
            else:  # высыпаем землю вперёд
                angle_deg = 40
                k = (phase - 0.7) / 0.3
                length = base_len * (0.8 - 0.4 * k)

            angle = math.radians(angle_deg)
            dx = math.cos(angle) * length
            dy = math.sin(angle) * length

            end_x = int(hand_x + dx)
            end_y = int(hand_y + dy)

            pygame.draw.line(hero_surf, shaft_color, (hand_x, hand_y), (end_x, end_y), 3)

            blade_rect = pygame.Rect(0, 0, 14, 10)
            blade_rect.center = (end_x, end_y + 4)
            pygame.draw.ellipse(hero_surf, blade_color, blade_rect)
            inner = blade_rect.inflate(-4, -3)
            pygame.draw.ellipse(hero_surf, (230, 230, 240), inner)

        # --- масштабируем и рисуем ---
        # Делаем героя по высоте ~1.5 тайла, чтобы голова и анимация лопаты не обрезались
        target_h = int(self.tile_size * 1.5)
        scale = target_h / float(base_h) if base_h > 0 else 1.0
        disp_w = int(base_w * scale)
        disp_h = target_h
        hero_small = pygame.transform.smoothscale(hero_surf, (disp_w, disp_h))
        dest_rect = hero_small.get_rect()
        dest_rect.midbottom = (screen_feet_x, screen_feet_y)
        self.screen.blit(hero_small, dest_rect)


    def render_action_progress(self, action, camera_x, camera_y):
        tile_x = action["tile_x"]
        tile_y = action["tile_y"]
        elapsed = action["elapsed"]
        duration = max(0.001, action["duration"])
        t = max(0.0, min(1.0, elapsed / duration))

        world_x = tile_x * self.tile_size + self.tile_size // 2
        world_y = tile_y * self.tile_size + 4

        sx = int(world_x - camera_x)
        sy = int(world_y - camera_y) - 24

        bar_width = 70
        bar_height = 9
        bg_rect = pygame.Rect(sx - bar_width // 2, sy, bar_width, bar_height)

        pygame.draw.rect(self.screen, (10, 10, 16), bg_rect)
        inner_rect = pygame.Rect(bg_rect.x + 1, bg_rect.y + 1,
                                 int((bar_width - 2) * t), bar_height - 2)
        pygame.draw.rect(self.screen, (91, 196, 107), inner_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 1)

    # --- контекстное меню ---

    def render_action_menu(self, action_menu):
        rect = action_menu["rect"]
        option_height = action_menu["option_height"]
        options = action_menu["options"]

        pygame.draw.rect(self.screen, (18, 22, 36), rect)
        border_rect = rect.inflate(2, 2)
        pygame.draw.rect(self.screen, (0, 0, 0), border_rect, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

        for idx, opt in enumerate(options):
            oy = rect.y + 5 + idx * option_height
            row_rect = pygame.Rect(rect.x + 4, oy, rect.width - 8, option_height - 4)
            pygame.draw.rect(self.screen, (30, 36, 56), row_rect)

            label_surf = self.font_menu.render(opt["label"], True, (240, 240, 240))
            self.screen.blit(label_surf, (row_rect.x + 6, row_rect.y + 4))