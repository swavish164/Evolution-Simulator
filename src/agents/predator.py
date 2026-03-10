from __future__ import annotations

from typing import TYPE_CHECKING
import random
from src.agents.agents import agent
from src.agents.agent_constants import *

if TYPE_CHECKING:
    from src.world.world import World


class Predator(agent):

    def __init__(self, position: list[float], velocity: list[float], energy: float, age: float,
                 generation: int, agent_id: int, genome: dict | None = None, pack: int | None = None):
        super().__init__(position, velocity, energy, age, is_predator=True, generation=generation,
                        agent_id=agent_id, genome=genome, pack=pack)
        if genome is None:
            self.genome[GENOME_METABOLISM] *= 0.5

    def get_neural_inputs(self, world: World):
        nearest_food_angle = 0.0
        nearest_food_distance = 1.0
        nearest_predator_angle = 0.0
        nearest_predator_distance = 1.0
        predator_visible = 0.0
        nearest_herdmate_angle = 0.0
        nearest_herdmate_distance = 1.0
        alert_received = 0.0

        vision = self.genome[GENOME_VISION]
        best_food_dist = float('inf')

        for a in world.agents:
            if a is self or a.is_predator or a.dead:
                continue
            dist = self.wrapped_distance(a.position, world)
            if dist <= vision and dist < best_food_dist:
                best_food_dist = dist
                nearest_food_angle = self._angle_to(a.position)
                nearest_food_distance = dist / vision

        return [
            nearest_predator_angle,
            nearest_predator_distance,
            predator_visible,
            alert_received,
            nearest_food_angle,
            nearest_food_distance,
            nearest_herdmate_angle,
            nearest_herdmate_distance,
            self.energy,
        ]


def add_predators(world: World, num_predators: int):
    predator_packs = []
    all_predators = []

    num_packs = random.randint(1, 2)
    predators_per_pack = num_predators // num_packs

    for pack_idx in range(num_packs):
        pack = []
        pack_center = [random.uniform(0, len(world.grid)), random.uniform(0, len(world.grid[0]))]

        for _ in range(predators_per_pack):
            position = [
                pack_center[0] + random.uniform(-5, 5),
                pack_center[1] + random.uniform(-5, 5)
            ]
            energy = random.uniform(0.5, 1)
            world.max_agent_id += 1
            predator_instance = Predator(position, [0, 0], energy, 0, 0, world.max_agent_id, pack=pack_idx)
            predator_instance.genome = predator_instance.random_genome()
            pack.append(predator_instance)
            all_predators.append(predator_instance)
            world.agents.append(predator_instance)
            world.stats_logger.log_agent(predator_instance, world.world_tick, predator_instance.is_predator)
            world.stats_logger.log_writer.writerow([world.world_tick, (f"New {predator_instance.is_predator}")])

        predator_packs.append(pack)

    world.packs.extend(predator_packs)
    return all_predators

