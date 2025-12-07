import math


def oscillate(t: float, speed: float = 1.0, magnitude: float = 1.0) -> float:
    """Простая синусоида для покачиваний и анимаций."""
    return math.sin(t * speed * 2.0 * math.pi) * magnitude
