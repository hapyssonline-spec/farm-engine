import pygame


class Player:
    def __init__(self, x: float, y: float, speed: float = 180.0):
        self.x = float(x)
        self.y = float(y)
        self.speed = float(speed)

        # Анимация ходьбы
        self.anim_time = 0.0
        self.is_moving = False

    def update(self, dt: float, world, keys):
        dx = 0.0
        dy = 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        moving = dx != 0.0 or dy != 0.0
        if moving:
            # нормализация вектора
            length = (dx * dx + dy * dy) ** 0.5
            if length > 0.0:
                dx /= length
                dy /= length

            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

            self.x = max(0.0, min(self.x, world.width_px - 1.0))
            self.y = max(0.0, min(self.y, world.height_px - 1.0))

            self.is_moving = True
            self.anim_time += dt
        else:
            self.is_moving = False

    @property
    def pos(self):
        return self.x, self.y
