import numpy as np
import random
import math

def add_packs(world, num_packs, pack_size):
    packs = []
    agents = []
    for i in range(num_packs):
        pack = []
        pack_center = [random.uniform(0, len(world)), random.uniform(0, len(world[0]))]
        genome = None
        age = 0
        for _ in range(pack_size):
            # Each agent gets their own position with small offset from pack center
            position = [
                pack_center[0] + random.uniform(-2, 2),
                pack_center[1] + random.uniform(-2, 2)
            ]
            energy = random.uniform(0.5, 1)
            agent_instance = agent(position, [0, 0], energy, genome, age, i)
            agent_instance.genome = agent_instance.random_genome()
            pack.append(agent_instance)
            agents.append(agent_instance)
        packs.append(pack)
    return packs, agents


class agent:
    def __init__(self, position, velocity, energy, genome, age,pack=None):
        self.position = position
        self.velocity = velocity
        self.energy = energy
        self.thirst = 0
        self.genome = genome if genome is not None else self.random_genome()
        self.age = age
        self.dead = False
        self.pack = None
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

    def random_genome(self, parents_genome =None):
        if parents_genome is None:
            size = random.uniform(0.1, 3)
            speed = random.uniform(0.1, 1)
            vision_range = random.uniform(3, 10)
            metabolism_rate = random.uniform(0.0001, 0.001)
            max_age = random.uniform(1, 10)

        else:
            size = parents_genome[random.randint(0,1)]['size'] + random.uniform(-0.05, 0.1)
            speed = parents_genome[random.randint(0,1)]['speed'] + random.uniform(-0.05, 0.1)
            vision_range = parents_genome[random.randint(0,1)]['vision_range'] + random.uniform(-0.05, 0.1)
            metabolism_rate = parents_genome[random.randint(0,1)]['metabolism_rate'] + random.uniform(-0.0005, 0.001)
            max_age = parents_genome[random.randint(0,1)]['max_age'] + random.uniform(-0.05, 0.1)
        return {'size': size, 'speed': speed, 'vision_range': vision_range, 'metabolism_rate': metabolism_rate, 'max_age': max_age}


    #def sense_danger(self):
        #for other_agent in world.agents:
            #if other_agent is not self and np.linalg.norm(np.array(other_agent.position) - np.array(self.position)) < self.genome['vision_range']:
                # Implement logic to determine if the other agent is a threat
        #return False

    def remove_from_world(self, world):
        if self in world.agents:
            world.agents.remove(self)
        for pack in world.packs:
            if self in pack:
                pack.remove(self)
                break

    def pick_random_target(self, world):
        max_row = len(world.grid)
        max_col = len(world.grid[0])
        vision = int(self.genome['vision_range'])

        angle_change = np.random.normal(loc=0, scale=15)
        self.target_dir = (self.target_dir + angle_change) % 360

        rad = math.radians(self.target_dir)
        target_row = int(self.position[0] + math.sin(rad) * vision) % max_row
        target_col = int(self.position[1] + math.cos(rad) * vision) % max_col

        self.target = [target_row, target_col]
        self.target_type = 'wander'

    def seek_resource(self, world, resource_type):
        vision = int(self.genome['vision_range'])
        current_closest = None
        current_closest_dist = float('inf')

        for i in range(-vision, vision + 1):
            for j in range(-vision, vision + 1):
                # Circle check
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

    def looking_for_mate(self, world):
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
                        child_agent = agent(child_position, [0, 0], 1.0, child_genome, 0)
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

    def wrapped_distance(self, target, world):
        max_row = len(world.grid)
        max_col = len(world.grid[0])
        dr = abs(self.position[0] - target[0])
        dc = abs(self.position[1] - target[1])
        dr = min(dr, max_row - dr)
        dc = min(dc, max_col - dc)
        return math.sqrt(dr ** 2 + dc ** 2)

    def update(self, world):
        self.age += 0.001
        if self.age >= self.genome['max_age']:
            self.remove_from_world(world)
            return

        if not self.waiting:
            self.energy -= self.genome['metabolism_rate']
            self.thirst += self.genome['metabolism_rate'] * 0.5

        if self.energy <= 0 and not self.dead:
            self.dead = True
            self.colour = (0, 0, 0)

        if self.thirst > 1:
            self.dead = True

        if self.dead:
            self.dead_time += 0.001
            if self.dead_time > 0.05:
                self.remove_from_world(world)
            return

        if self.energy < 0.2:
            self.genome['speed'] = max(0.1, self.genome['speed'] * (self.energy / 0.2))

        if self.age > self.genome['max_age'] * 0.75:
            self.genome['speed'] = max(0.1, self.genome['speed'] * (
                        1 - (self.age - self.genome['max_age'] * 0.75) / (self.genome['max_age'] * 0.25)))

        if self.genome['max_age'] * 0.4 < self.age <= self.genome['max_age'] * 0.75:
            self.mating = True

        if self.mating and not self.mated[0]:
            self.looking_for_mate(world)

        if self.mated[0]:
            self.mated[1] += 0.001
            if self.mated[1] > self.genome['max_age']*0.1:
                self.mated = [False, 0]

        if self.waiting:
            if self.target_type == 'food' and self.target_plant is not None:
                self.eating_time += 0.002
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
                self.thirst = max(0, self.thirst - 0.01)
                if self.thirst <= 0:
                    self.waiting = False
                    self.target = None
                    self.target_type = None
                    self.colour = (255, 0, 255)
            return

        if self.thirst > 0.5:
            self.colour = (0, 0, 255)
            self.seek_resource(world, 'water')
        if self.energy < 0.5:
            self.colour = (255, 0, 0)
            self.seek_resource(world, 'food')

        if self.target is None:
            self.pick_random_target(world)

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
                self.velocity = (direction * self.genome['speed']).tolist()
            else:
                if self.target_type in ('food', 'water'):
                    self.waiting = True
                    self.velocity = [0, 0]
                else:
                    self.target = None
                    self.target_type = None

        new_row = self.position[0] + self.velocity[0] * self.genome['speed']
        new_col = self.position[1] + self.velocity[1] * self.genome['speed']
        self.position[0] = new_row % len(world.grid)
        self.position[1] = new_col % len(world.grid[0])

