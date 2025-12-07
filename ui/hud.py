import pygame


class HUD:
    def __init__(self):
        self.font_title = pygame.font.SysFont("arial", 20, bold=True)
        self.font_text = pygame.font.SysFont("arial", 16)
        self.font_button = pygame.font.SysFont("arial", 16, bold=True)

        # геометрия панели
        self.margin = 12
        self.height = 120

    def _draw_panel_background(self, surface: pygame.Surface, rect: pygame.Rect):
        # Градиент коричневого
        top_color = (40, 26, 16)
        mid_color = (58, 38, 24)
        bottom_color = (26, 16, 10)

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        w, h = rect.size
        for y in range(h):
            t = y / max(1, h - 1)
            if t < 0.5:
                k = t / 0.5
                r = int(top_color[0] * (1 - k) + mid_color[0] * k)
                g = int(top_color[1] * (1 - k) + mid_color[1] * k)
                b = int(top_color[2] * (1 - k) + mid_color[2] * k)
            else:
                k = (t - 0.5) / 0.5
                r = int(mid_color[0] * (1 - k) + bottom_color[0] * k)
                g = int(mid_color[1] * (1 - k) + bottom_color[1] * k)
                b = int(mid_color[2] * (1 - k) + bottom_color[2] * k)
            pygame.draw.line(panel, (r, g, b), (0, y), (w, y))

        # Лёгкое свечение сверху
        glow = pygame.Surface((w, h // 3), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 25))
        panel.blit(glow, (0, 0))

        # Обводка и внутренний светлый контур
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, (15, 8, 4), rect, 2)
        inner = rect.inflate(-6, -6)
        pygame.draw.rect(surface, (110, 80, 50), inner, 1)

    def _draw_button(self, surface: pygame.Surface, rect: pygame.Rect, label: str, active: bool):
        # Фон кнопки с градиентом
        if active:
            top = (208, 178, 104)
            bottom = (166, 120, 64)
        else:
            top = (70, 52, 32)
            bottom = (52, 38, 24)

        btn = pygame.Surface(rect.size, pygame.SRCALPHA)
        w, h = rect.size
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            pygame.draw.line(btn, (r, g, b), (0, y), (w, y))

        # Имитируем нажатие: активная кнопка чуть "утоплена"
        if active:
            shadow = pygame.Surface((w, h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 40))
            btn.blit(shadow, (0, 0))

        surface.blit(btn, rect.topleft)
        pygame.draw.rect(surface, (0, 0, 0), rect, 1)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(surface, (220, 200, 160) if active else (150, 130, 100), inner, 1)

        # Текст
        text_surf = self.font_button.render(label, True, (25, 18, 10))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    def draw(self, screen: pygame.Surface, inventory):
        sw, sh = screen.get_size()
        panel_rect = pygame.Rect(self.margin, sh - self.height - self.margin,
                                 sw - self.margin * 2, self.height)

        self._draw_panel_background(screen, panel_rect)

        # Заголовок
        title_surf = self.font_title.render("Инвентарь", True, (250, 230, 200))
        screen.blit(title_surf, (panel_rect.x + 12, panel_rect.y + 8))

        # Текст слева
        text_x = panel_rect.x + 12
        text_y = panel_rect.y + 40
        line_h = 20

        def draw_line(caption, value):
            nonlocal text_y
            surf = self.font_text.render(f"{caption}: {value}", True, (240, 220, 200))
            screen.blit(surf, (text_x, text_y))
            text_y += line_h

        draw_line("Семена пшеницы", inventory.seeds_wheat)
        draw_line("Семена томатов", inventory.seeds_tomato)
        draw_line("Урожай пшеницы", inventory.harvest_wheat)
        draw_line("Урожай томатов", inventory.harvest_tomato)

        # Кнопки выбора семян справа
        button_width = 180
        button_height = 32
        spacing = 10

        btn_x = panel_rect.right - button_width - 18
        btn_y1 = panel_rect.y + 40
        btn_y2 = btn_y1 + button_height + spacing

        wheat_rect = pygame.Rect(btn_x, btn_y1, button_width, button_height)
        tomato_rect = pygame.Rect(btn_x, btn_y2, button_width, button_height)

        self._draw_button(
            screen,
            wheat_rect,
            "Семена пшеницы",
            inventory.selected_seed == "wheat",
        )
        self._draw_button(
            screen,
            tomato_rect,
            "Семена томатов",
            inventory.selected_seed == "tomato",
        )

        # Сохраняем, чтобы обработчик кликов знал области
        self.wheat_button_rect = wheat_rect
        self.tomato_button_rect = tomato_rect

    def handle_click(self, pos, inventory):
        if hasattr(self, "wheat_button_rect") and self.wheat_button_rect.collidepoint(pos):
            inventory.selected_seed = "wheat"
            return True
        if hasattr(self, "tomato_button_rect") and self.tomato_button_rect.collidepoint(pos):
            inventory.selected_seed = "tomato"
            return True
        return False
