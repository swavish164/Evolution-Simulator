import numpy as np
import random

def add_agents(world, num_agents):
    agents = []
    for _ in range(num_agents):
        position = [random.uniform(0, len(world)), random.uniform(0, len(world[0]))]
        velocity = [0, 0]
        energy = random.uniform(0.5, 1)
        genone = None
        age = 0
        agent_instance = agent(position, velocity, energy, genone, age)
        agent_instance.genone = agent_instance.random_genome()
        agents.append(agent_instance)
    return agents


class agent:
    def __init__(self, position, velocity, energy, genone, age):
        self.position = position
        self.velocity = velocity
        self.energy = energy
        self.thirst = 0
        self.genone = genone if genone is not None else self.random_genome()
        self.age = age
        self.dead = False
        self.pack = None
        self.deadTime = 0
        self.target = None
        self.target_type = None
        self.colour = (255, 0, 255)

    def random_genome(self, parent_genome=None):
        if parent_genome is None:
            size = random.uniform(0.1, 3)
            speed = random.uniform(0.1, 1)
            vision_range = random.uniform(3, 10)
            metabolism_rate = random.uniform(0.0001, 0.001)
            max_age = random.uniform(10, 100)

        else:
            size = parent_genome.size + random.uniform(-0.05, 0.1)
            speed = parent_genome.speed + random.uniform(-0.05, 0.1)
            vision_range = parent_genome.vision_range + random.uniform(-0.05, 0.1)
            metabolism_rate = parent_genome.metabolism_rate + random.uniform(-0.0005, 0.001)
            max_age = parent_genome.max_age + random.uniform(-0.05, 0.1)
        return {'size': size, 'speed': speed, 'vision_range': vision_range, 'metabolism_rate': metabolism_rate, 'max_age': max_age}


    #def sense_danger(self):
        #for other_agent in world.agents:
            #if other_agent is not self and np.linalg.norm(np.array(other_agent.position) - np.array(self.position)) < self.genone['vision_range']:
                # Implement logic to determine if the other agent is a threat
        #return False

    def pick_random_target(self, world):
        random_y = random.randint(max(0, int(self.position[1]) - int(self.genone['vision_range'])), min(len(world.grid[0]) - 1, int(self.position[1]) + int(self.genone['vision_range'])))
        random_x = random.randint(max(0, int(self.position[0]) - int(self.genone['vision_range'])), min(len(world.grid) - 1, int(self.position[0]) + int(self.genone['vision_range'])))
        self.target = [random_x, random_y]
        self.target_type = 'wander'

    def seek_resource(self, world, resource_type):
        vision = int(self.genone['vision_range'])
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
                            if plant.size > 0.5 and dist < current_closest_dist:
                                current_closest = check_tile
                                current_closest_dist = dist

                elif resource_type == 'water':
                    if tile == 1 and dist < current_closest_dist:
                        current_closest = check_tile
                        current_closest_dist = dist

        if current_closest is not None:
            self.target = current_closest
            self.target_type = resource_type
            return True
        return False

    def update(self, world):
        self.age += 0.001
        if self.age >= self.genone['max_age']:
            world.agents.remove(self)
            return
        self.energy -= self.genone['metabolism_rate']
        self.thirst += self.genone['metabolism_rate'] * 0.5

        if self.energy <= 0 and not self.dead:
            self.dead = True
            self.colour = (0, 0, 0)
            return

        if self.energy < 0.2:
            self.genone['speed'] = max(0.1, self.genone['speed'] * (self.energy / 0.2))

        if self.dead:
            self.deadTime += 0.001
            if self.deadTime > 0.05:
                world.agents.remove(self)
            return
        if self.thirst > 0.5:
            self.colour = (0,0,255)
            self.seek_resource(world, 'water')
        if self.energy < 0.5:
            self.colour = (255,0,0)
            self.seek_resource(world, 'food')
        # If danger is sensed, try to flee
        #if self.sense_danger():
            ## Flee from danger
            #pass
        if self.target is None:
            self.pick_random_target(world)
        if self.target is not None:
            direction = np.array(self.target) - np.array(self.position)
            distance = np.linalg.norm(direction)
            if distance > 0.5:
                direction = direction / distance
                self.velocity = (direction * self.genone['speed']).tolist()
            else:
                if self.target_type == 'food':
                    self.energy = min(1.0, self.energy + 0.5)
                elif self.target_type == 'water':
                    self.thirst = 0
                self.colour = (255, 0, 255)
                self.target = None
                self.target_type = None
                self.velocity = [0, 0]

        self.position[0] += self.velocity[0] * self.genone['speed']
        self.position[1] += self.velocity[1] * self.genone['speed']

