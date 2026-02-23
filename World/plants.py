import random
import math

def add_plants(world, plant_probability):
    plants = []
    plants_tile = [[[] for _ in range(len(world[i]))] for i in range(len(world))]
    for i in range(len(world)):
        for j in range(len(world[i])):
            if world[i][j] == 0:
                if random.random() < plant_probability:
                    new_plant = NewPlant((i, j))
                    plants.append(new_plant)
                    plants_tile[i][j].append(new_plant)
            if world[i][j] == 3:
                if random.random() < plant_probability * 5:
                    new_plant = NewPlant((i, j))
                    plants.append(new_plant)
                    plants_tile[i][j].append(new_plant)
    return [plants, plants_tile]


class NewPlant:
    def __init__(self, position, genome=None, tile_offset=None):
        self.position = position
        #self.growth_rate = growth_rate
        self.genone = genome if genome is not None else self.random_genome()
        self.size = 0.1
        self.age = 0
        self.tile_offset = tile_offset if tile_offset is not None else (
            random.uniform(0.1, 0.9),
            random.uniform(0.1, 0.9)
        )
        self.pollinated = False
        self.dead = False
        self.deadTime = 0
        self.colour = (11, 224, 4)

    def random_genome(self, parent_genome=None):
        if parent_genome is None:
            growth_rate = random.uniform(0, 0.005)
            max_size = random.uniform(1, 3)
            max_age = random.uniform(1, int(max_size)*random.uniform(1,2))
            pollination_age = random.uniform(max_age/4, max_age * 3/4)
            germination_age = random.uniform(0.01, 0.1)
            seeds_released = 1
        else:
            growth_rate = parent_genome.growth_rate + random.uniform(-0.5, 0.15)
            max_size = parent_genome.max_size + random.uniform(-0.05, 0.1)
            max_age = parent_genome.max_age + random.uniform(-0.05, 0.1)
            pollination_age = parent_genome.pollination_age + random.uniform(-0.05, 0.05)
            germination_age = parent_genome.germination_age + random.uniform(-0.05, 0.005)
            seeds_released = parent_genome.seeds_released + random.choices([-1, 0, 1], weights=[0.05, 0.8, 0.15])[0]
        return {'growth_rate': growth_rate, 'max_size': max_size, 'max_age': max_age, 'pollination_age': pollination_age, 'germination_age': germination_age, 'seeds_released': seeds_released}

    def update(self, world):
        self.age += 0.001
        if self.age >= self.genone['max_age'] and not self.dead:
            self.dead = True
            self.colour = (71, 62, 8)
            self.deadTime = 0
            return
        if self.dead:
            self.deadTime += 0.001
            if self.deadTime > 0.05:
                world.plants[0].remove(self)
                world.plants[1][int(self.position[0])][int(self.position[1])].remove(self)
            return
        if self.age >= self.genone['pollination_age']  and self.pollinated == False:
            wind_direction = world.wind[0]
            wind_speed = world.wind[1]

            wind_rad = math.radians(wind_direction)
            dx = math.sin(wind_rad) * wind_speed
            dy = -math.cos(wind_rad) * wind_speed

            new_row = max(0, min(round(self.position[0] + dy), len(world.grid) - 1))
            new_col = max(0, min(round(self.position[1] + dx), len(world.grid[0]) - 1))

            for _ in range(self.genone['seeds_released']):
                new_seed = NewSeed((new_row + random.uniform(-0.5,0.5), new_col + random.uniform(-0.5,0.5)), self.genone)
                world.seeds.append(new_seed)
            self.pollinated = True

        self.size += self.genone['growth_rate']
        if self.size > self.genone['max_size']:
            self.size = self.genone['max_size']


class NewSeed:
    def __init__(self, position, genome):
        self.position = position
        self.genome = genome
        self.age = 0

    def update(self, world):
        self.age += 0.001
        if self.age >= self.genome['germination_age']:
            clamped_row = max(0, min(int(self.position[0]), len(world.grid) - 1))
            clamped_col = max(0, min(int(self.position[1]), len(world.grid[0]) - 1))
            clamped_position = (clamped_row, clamped_col)

            new_plant = NewPlant(clamped_position, self.genome, tile_offset=(
                random.uniform(0.1, 0.9),
                random.uniform(0.1, 0.9)
            ))
            world.plants[0].append(new_plant)
            world.plants[1][clamped_row][clamped_col].append(new_plant)
            world.seeds.remove(self)

