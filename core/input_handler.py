import pygame


class InputHandler:
    def __init__(self, engine):
        self.engine = engine

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                # полноэкранный режим: F11 или Alt+Enter
                if event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                ):
                    self.engine.toggle_fullscreen()

            if event.type == pygame.MOUSEWHEEL:
                self.engine.handle_mousewheel(event.y)

            # Передаём событие в движок для обработки кликов и др.
            self.engine.handle_event(event)

        return True
