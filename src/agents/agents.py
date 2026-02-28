from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING
import random
import math
from src.agents.agent_constants import *

if TYPE_CHECKING:
    from src.world.world import World

def add_packs(world: World, num_packs: int, pack_size: int):
    packs = []
    agents = []
    for i in range(num_packs):
        pack = []
        pack_center = [random.uniform(0, len(world)), random.uniform(0, len(world[0]))]
        genome = None
        age = 0
        for _ in range(pack_size):
            position = [
                pack_center[0] + random.uniform(-2, 2),
                pack_center[1] + random.uniform(-2, 2)
            ]
            energy = random.uniform(0.5, 1)
            agent_instance = agent(position, [0, 0], energy, age, genome, i)
            agent_instance.genome = agent_instance.random_genome()
            pack.append(agent_instance)
            agents.append(agent_instance)
        packs.append(pack)
    return packs, agents

class agent:
    def __init__(self, position: list[float], velocity: list[float], energy: float, age: float,genome: dict | None = None,pack: int | None =None):
        self.position = position
        self.velocity = velocity
        self.energy = energy
        self.thirst = 0
        self.genome = genome if genome is not None else self.random_genome()
        self.age = age
        self.dead = False
        self.pack = pack
        self.dead_time = 0
        self.target = None
        self.eating_time = 0
        self.mating = False
        self.waiting = False
        self.target_type = None
        self.target_plant = None
        self.target_dir = random.randint(0, 360)
        self.colour = (255, 0, 255)
        self.mated = [False, 0]
        self.leader = False
        self.pack_speed = 1.0
        self.base_speed = None
        self.heading = random.uniform(0, 2* math.pi)
        self.speed = 0.5

    def random_genome(self, parents_genome:dict | None = None):
        if parents_genome is None:
            attributes = np.array([
                random.uniform(0.1,3), # size
                random.uniform(0.5,1), # speed
                random.uniform(3,10), # vision range
                random.uniform(0.0001,0.001), # metabolism rate
                random.uniform(1,10), # max age
            ])
            network_weights = np.random.randn(112) * 0.5
            return np.concatenate([attributes,network_weights])

        else:
            attributes = np.array([
                parents_genome[random.randint(0,1)][GENOME_SIZE] + random.uniform(-0.05, 0.1),
                parents_genome[random.randint(0,1)][GENOME_SPEED] + random.uniform(-0.05, 0.1),
                parents_genome[random.randint(0,1)][GENOME_VISION] + random.uniform(-0.05, 0.1),
                parents_genome[random.randint(0,1)][GENOME_METABOLISM] + random.uniform(-0.0005, 0.001),
                parents_genome[random.randint(0,1)][GENOME_MAX_AGE] + random.uniform(-0.05, 0.1),
            ])
            mask = np.random.random(112) > 0.5
            network_weights = np.where(mask, parents_genome[0][GENOME_NETWORK_START:], parents_genome[1][GENOME_NETWORK_START:])
            network_weights += np.random.randn(112) * 0.05
        return np.concatenate([attributes, network_weights])


    #def sense_danger(self):
        #for other_agent in world.agents:
            #if other_agent is not self and np.linalg.norm(np.array(other_agent.position) - np.array(self.position)) < self.genome[2]:
                # Implement logic to determine if the other agent is a threat
        #return False

    def remove_from_world(self, world: World):
        if self in world.agents:
            world.agents.remove(self)
        for pack in world.packs:
            if self in pack:
                pack.remove(self)
                break

    def pick_random_target(self, world: World):
        max_row = len(world.grid)
        max_col = len(world.grid[0])
        vision = int(self.genome[GENOME_VISION])

        angle_change = np.random.normal(loc=0, scale=15)
        self.target_dir = (self.target_dir + angle_change) % 360

        rad = math.radians(self.target_dir)
        target_row = int(self.position[0] + math.sin(rad) * vision) % max_row
        target_col = int(self.position[1] + math.cos(rad) * vision) % max_col

        self.target = [target_row, target_col]
        self.target_type = 'wander'

    def seek_resource(self, world: World, resource_type: str):
        vision = int(self.genome[GENOME_VISION])
        current_closest = None
        current_closest_dist = float('inf')

        for i in range(-vision, vision + 1):
            for j in range(-vision, vision + 1):
                if np.sqrt(i ** 2 + j ** 2) > vision:
                    continue
                check_tile = [int(self.position[0]) + i, int(self.position[1]) + j]
                if not (0 <= check_tile[0] < len(world.grid) and
                        0 <= check_tile[1] < len(world.grid[0])):
                    continue

                tile = world.grid[check_tile[0]][check_tile[1]]
                dist = np.linalg.norm(np.array(check_tile) - np.array(self.position))

                if resource_type == 'food':
                    if tile in (0, 3):
                        plants_here = world.plants[1][check_tile[0]][check_tile[1]]
                        for plant in plants_here:
                            if plant.age > 0.1 and dist < current_closest_dist:
                                current_closest = check_tile
                                current_closest_dist = dist
                                current_plant = plant

                elif resource_type == 'water':
                    if tile == 1 and dist < current_closest_dist:
                        current_closest = check_tile
                        current_closest_dist = dist

                elif resource_type == 'mate':
                    for a in world.agents:
                        if a is self or not a.mating:
                            continue
                        dist = self.wrapped_distance(a.position, world)
                        if dist <= vision and dist < current_closest_dist:
                            current_closest = a.position
                            current_closest_dist = dist

        if current_closest is not None:
            self.target = current_closest
            self.target_type = resource_type
            self.target_plant = current_plant if resource_type == 'food' else None
            return True
        return False

    def looking_for_mate(self, world: World):
        self.colour = (255, 105, 180)

        if self.target_type != 'mate' or self.target is None:
            found = self.seek_resource(world, 'mate')
            if not found:
                return

        if self.target_type == 'mate' and self.target is not None:
            distance = self.wrapped_distance(self.target, world)
            if distance < 0.5:
                partner = None
                closest = 1.0
                for a in world.agents:
                    if a is self or not a.mating:
                        continue
                    d = self.wrapped_distance(a.position, world)
                    if d < closest:
                        closest = d
                        partner = a

                if partner is not None:
                    number_of_children = random.choices([1, 2, 3], weights=[0.65, 0.25, 0.1])[0]
                    for _ in range(number_of_children):
                        child_genome = self.random_genome([partner.genome, self.genome])
                        child_position = [(self.position[0] + partner.position[0]) / 2,
                                          (self.position[1] + partner.position[1]) / 2]
                        child_agent = agent(child_position, [0, 0], 1.0, 0, child_genome)
                        world.agents.append(child_agent)
                        for pack in world.packs:
                            if self in pack:
                                pack.append(child_agent)
                                break
                        print(f"New agent born at {child_position} with genome: {child_genome}")

                    self.mating = False
                    partner.mating = False
                    self.colour = (255, 0, 255)
                    partner.colour = (255, 0, 255)
                    self.mated = [True, 0]
                    partner.mated = [True, 0]
                    self.target = None
                    self.target_type = None
                    partner.target = None
                    partner.target_type = None

    def wrapped_distance(self, target: list[float], world: World):
        max_row = len(world.grid)
        max_col = len(world.grid[0])
        dr = abs(self.position[0] - target[0])
        dc = abs(self.position[1] - target[1])
        dr = min(dr, max_row - dr)
        dc = min(dc, max_col - dc)
        return math.sqrt(dr ** 2 + dc ** 2)

    def check_follow_leader(self, world: World):
        leader = next((a for a in world.packs[self.pack] if a.leader), None)
        following = [a for a in world.packs[self.pack] if a.target_type in ('wander', 'return', 'leader') and not a.dead]
        if following:
            self.pack_speed = min(a.base_speed for a in following)
        else:
            self.pack_speed = self.base_speed

        if self.leader:
            self.colour = (255, 215, 0)
            pack_members = [a for a in world.packs[self.pack] if a is not self and not a.dead]
            if pack_members:
                max_dist = max(self.wrapped_distance(a.position, world) for a in pack_members)
                if max_dist > 8:
                    self.pack_speed = 0
                    return
            self.pick_random_target(world)

        elif leader is not None:
            dist_to_leader = self.wrapped_distance(leader.position, world)

            if dist_to_leader > 5:
                self.target = [
                    leader.position[0] % len(world.grid),
                    leader.position[1] % len(world.grid[0])
                ]
                self.target_type = 'return'
                self.pack_speed = self.base_speed
            else:
                self.target = [
                    (self.position[0] + random.uniform(-2, 2)) % len(world.grid),
                    (self.position[1] + random.uniform(-2, 2)) % len(world.grid[0])
                ]
                self.target_type = 'wander'
        else:
            self.pick_random_target(world)

    def get_neural_inputs(self, world: World):
        nearest_food_angle = 0.0
        nearest_food_distance = 1.0
        nearest_predator_angle = 0.0
        nearest_predator_distance = 1.0
        predator_visible = 0.0
        nearest_herdmate_angle = 0.0
        nearest_herdmate_distance = 1.0

        vision = self.genome[GENOME_VISION]
        best_food_dist = float('inf')
        best_predator_dist = float('inf')
        best_herdmate_dist = float('inf')

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

            if a.pack != self.pack:
                if dist < best_predator_dist:
                    best_predator_dist = dist
                    nearest_predator_angle = self._angle_to(a.position)
                    nearest_predator_distance = dist / vision
                    predator_visible = 1.0
            else:
                if dist < best_herdmate_dist:
                    best_herdmate_dist = dist
                    nearest_herdmate_angle = self._angle_to(a.position)
                    nearest_herdmate_distance = dist / vision

        return [
            nearest_predator_angle,
            nearest_predator_distance,
            predator_visible,
            nearest_food_angle,
            nearest_food_distance,
            nearest_herdmate_angle,
            nearest_herdmate_distance,
            self.energy,
        ]

    def _angle_to(self, target_position: list[float]):
        dr = target_position[0] - self.position[0]
        dc = target_position[1] - self.position[1]
        angle = math.degrees(math.atan2(dc, dr))
        return angle / 180.0


    def neural_network_decision(self, inputs):
        W1 = self.genome[GENOME_NETWORK_START:GENOME_NETWORK_START+80].reshape(10, 8)
        b1 = self.genome[GENOME_NETWORK_START+80:GENOME_NETWORK_START+90]
        W2 = self.genome[GENOME_NETWORK_START+90:GENOME_NETWORK_START+110].reshape(2, 10)
        b2 = self.genome[GENOME_NETWORK_START+110:GENOME_NETWORK_START+112]
        hidden = np.tanh(W1 @ inputs + b1)
        output = np.tanh(W2 @ hidden + b2)
        return output

    def apply_outputs(self, outputs: list[float], dt_scaled: float):
        self.heading += outputs[0] * max_turn_rate * dt_scaled
        self.speed = np.clip(self.speed + outputs[1] * 0.1,0.1, self.genome[GENOME_SPEED])

        self.velocity[0] = math.sin(self.heading) * self.speed
        self.velocity[1] = math.cos(self.heading) * self.speed

    def update(self, world: World, dt: float):
        dt_scaled = dt / 100  # convert ms to seconds

        if self.dead:
            self.dead_time += dt_scaled
            if self.dead_time > 0.05:
                self.remove_from_world(world)
            return

        self.age += 0.001 * dt_scaled
        if self.age >= self.genome[GENOME_MAX_AGE]:
            self.remove_from_world(world)
            return

        if not self.waiting:
            self.energy -= self.genome[GENOME_METABOLISM] * dt_scaled
            self.thirst += self.genome[GENOME_METABOLISM] * 0.5 * dt_scaled

        if self.energy <= 0 and not self.dead:
            self.dead = True
            self.colour = (0, 0, 0)

        if self.thirst > 1:
            self.dead = True


        current_speed = self.base_speed

        if self.energy < 0.2:
            current_speed = max(0.1, self.genome[GENOME_SPEED] * (self.energy / 0.2))

        if self.age > self.genome[GENOME_MAX_AGE] * 0.75:
            if self.mating:
                self.mating = False
                self.colour = (255, 0, 255)
                self.target = None
                self.target_type = None
            if self.leader:
                self.leader = False
                assign_pack_leader(world, self.pack)
            age_factor = 1 - (self.age - self.genome[GENOME_MAX_AGE] * 0.75) / (self.genome[GENOME_MAX_AGE] * 0.25)
            current_speed = max(0.1, current_speed * age_factor)
        self.pack_speed = current_speed

        if self.genome[GENOME_MAX_AGE] * 0.4 < self.age <= self.genome[GENOME_MAX_AGE] * 0.75:
            self.mating = True

        if self.mated[0]:
            self.mated[1] += dt_scaled
            if self.mated[1] > self.genome[GENOME_MAX_AGE] * 0.1:
                self.mated = [False, 0]

        if self.waiting:
            if self.target_type == 'food' and self.target_plant is not None:
                self.eating_time += 0.01 * dt_scaled
                if self.eating_time >= self.target_plant.size * 0.5:
                    self.energy = min(1.0, self.energy + self.target_plant.size * 0.5)
                    if self.target_plant in world.plants[0]:
                        world.plants[0].remove(self.target_plant)
                        world.plants[1][int(self.target_plant.position[0])][
                            int(self.target_plant.position[1])].remove(self.target_plant)
                    self.target_plant = None
                    self.eating_time = 0
                    self.waiting = False
                    self.target = None
                    self.target_type = None
                    self.colour = (255, 0, 255)
            elif self.target_type == 'water':
                self.thirst = max(0, self.thirst - 0.01 * dt_scaled)
                if self.thirst == 0:
                    self.waiting = False
                    self.target = None
                    self.target_type = None
                    self.colour = (255, 0, 255)
            return

        food_threshold = 0.5 * (self.genome[GENOME_METABOLISM] / 0.0005)
        water_threshold = 0.5 * (self.genome[GENOME_METABOLISM] / 0.0005)

        if self.thirst > water_threshold and self.target_type != 'water':
            self.colour = (0, 0, 255)
            self.pack_speed = self.base_speed
            self.seek_resource(world, 'water')

        if self.energy < food_threshold and self.target_type != 'food':
            self.colour = (255, 0, 0)
            self.pack_speed = self.base_speed
            self.seek_resource(world, 'food')

        if self.mating and not self.mated[0]:
            self.pack_speed = self.genome[GENOME_SPEED]
            self.looking_for_mate(world)

        if self.target is None and not self.waiting and not self.dead:
            inputs = self.get_neural_inputs(world)
            outputs = self.neural_network_decision(inputs)
            self.apply_outputs(outputs, dt_scaled)

        if self.target is None:
            if self.pack is not None:
                self.check_follow_leader(world)

        if self.target is not None:
            distance = self.wrapped_distance(self.target, world)
            if distance > 0.5:
                direction = np.array(self.target) - np.array(self.position)
                max_row = len(world.grid)
                max_col = len(world.grid[0])
                if abs(direction[0]) > max_row / 2:
                    direction[0] -= math.copysign(max_row, direction[0])
                if abs(direction[1]) > max_col / 2:
                    direction[1] -= math.copysign(max_col, direction[1])
                direction = direction / np.linalg.norm(direction)
                self.velocity = (direction * self.genome[GENOME_SPEED]).tolist()
            else:
                if self.target_type in ('food', 'water'):
                    self.waiting = True
                    self.velocity = [0, 0]
                else:
                    self.target = None
                    self.target_type = None

        new_row = self.position[0] + self.velocity[0] * self.pack_speed * dt_scaled
        new_col = self.position[1] + self.velocity[1] * self.pack_speed * dt_scaled
        self.position[0] = new_row % len(world.grid)
        self.position[1] = new_col % len(world.grid[0])


def assign_pack_leader(world: World, pack_number: int =None):
    packs_to_assign = [world.packs[pack_number]] if pack_number is not None else world.packs
    for pack in packs_to_assign:
        if not pack:
            continue
        for a in pack:
            a.base_speed = a.genome[GENOME_SPEED]
            a.leader = False
        leader = max(pack, key=lambda a: a.genome[GENOME_SIZE])
        leader.leader = True
