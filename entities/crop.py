import random

# Количество фаз роста
MAX_GROWTH_STAGE = 5

# Время на переход между фазами (секунд)
GROWTH_STAGE_TIME = 12.0

# Распределение урожая
# 50% -> 1, 35% -> 2, 15% -> 3
HARVEST_DISTRIBUTION = [
    (0.50, 1),
    (0.85, 2),
    (1.00, 3),
]


def roll_harvest_amount() -> int:
    r = random.random()
    for threshold, amount in HARVEST_DISTRIBUTION:
        if r <= threshold:
            return amount
    return 1
