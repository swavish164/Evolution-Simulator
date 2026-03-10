from __future__ import annotations

from typing import TYPE_CHECKING
import math
import random
from src.agents.agents import agent
from src.agents.agent_constants import *

if TYPE_CHECKING:
    from src.world.world import World


class Prey(agent):

    def __init__(self, position: list[float], velocity: list[float], energy: float, age: float,
                 generation: int, agent_id: int, genome: dict | None = None, pack: int | None = None):
        super().__init__(position, velocity, energy, age, is_predator=False, generation=generation,
                        agent_id=agent_id, genome=genome, pack=pack)

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
        best_predator_dist = float('inf')
        best_herdmate_dist = float('inf')

        if self.predator_alert is not None:
            alert_position = self.predator_alert[0]
            alert_received = 1.0
            self.predator_alert[1] += 1.0
            if self.predator_alert[1] > 5.0:
                self.predator_alert = None
                alert_received = 0.0
            else:
                nearest_predator_angle = self._angle_to(alert_position)
                dist = self.wrapped_distance(alert_position, world)
                nearest_predator_distance = min(1.0, dist / vision)

        for i in range(-int(vision), int(vision) + 1):
            for j in range(-int(vision), int(vision) + 1):
                if i * i + j * j > vision * vision:
                    continue
                row = (int(self.position[0]) + i) % len(world.grid)
                col = (int(self.position[1]) + j) % len(world.grid[0])

                plants_here = world.plants[1][row][col]
                for plant in plants_here:
                    if plant.age > 0.1:
                        dist = math.sqrt(i * i + j * j)
                        if dist < best_food_dist:
                            best_food_dist = dist
                            nearest_food_angle = self._angle_to(plant.position)
                            nearest_food_distance = dist / vision

        for a in world.agents:
            if a is self:
                continue
            dist = self.wrapped_distance(a.position, world)
            if dist > vision:
                continue

            if a.is_predator:
                if dist < best_predator_dist:
                    best_predator_dist = dist
                    nearest_predator_angle = self._angle_to(a.position)
                    nearest_predator_distance = dist / vision
                    predator_visible = 1.0
                    self.broadcast_predator_alert(a.position, a.speed, world)
            else:
                if dist < best_herdmate_dist:
                    best_herdmate_dist = dist
                    nearest_herdmate_angle = self._angle_to(a.position)
                    nearest_herdmate_distance = dist / vision

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


def add_packs(world: World, num_packs: int, pack_size: int):
    packs = []
    agents = []
    for i in range(num_packs):
        pack = []
        pack_center = [random.uniform(0, len(world.grid)), random.uniform(0, len(world.grid[0]))]
        genome = None
        age = 0
        for _ in range(pack_size):
            position = [
                pack_center[0] + random.uniform(-2, 2),
                pack_center[1] + random.uniform(-2, 2)
            ]
            energy = random.uniform(0.5, 1)
            world.max_agent_id += 1
            agent_instance = Prey(position, [0, 0], energy, age, 0, world.max_agent_id, genome, i)
            agent_instance.genome = agent_instance.random_genome()
            pack.append(agent_instance)
            agents.append(agent_instance)
            world.stats_logger.log_agent(agent_instance, world.world_tick, agent_instance.is_predator)
            world.stats_logger.log_writer.writerow([world.world_tick, (f"New {agent_instance.is_predator}")])
        packs.append(pack)
    return packs, agents

