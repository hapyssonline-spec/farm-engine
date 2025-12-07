import pygame

from core.engine import Engine
from core.input_handler import InputHandler


def main():
    pygame.init()
    pygame.display.set_caption("Farm Engine — v0.4")

    window_size = (1280, 720)
    screen = pygame.display.set_mode(window_size)

    clock = pygame.time.Clock()
    engine = Engine(screen)
    input_handler = InputHandler(engine)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        running = input_handler.process_events()
        engine.update(dt)
        engine.render()

    pygame.quit()


if __name__ == "__main__":
    main()
