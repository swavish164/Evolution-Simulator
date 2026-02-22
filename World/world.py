import pygame
from numpy import random
from Map.mapGeneration import generate_initial_map, generate_map
from World.plants import add_plants

grass = (21, 122, 17)
water = (0, 0, 255)
forest = (5, 71, 3)
sand = (255, 255, 0)

class World:
    def __init__(
        self,
        agents,
        food,
        grid=None,
        screen=None,
        map_width=100,
        map_height=100,
        plant_probability=0.025,
        wind=None,
        increasingDirection = True,
        increasingChange = True,
        seeds = []
    ):
        if wind is None:
            wind = [0, 0]
        self.agents = list(agents)
        self.food = list(food)
        self.map_width = int(map_width)
        self.map_height = int(map_height)

        self.screen = screen or pygame.display.set_mode((700, 700))
        screen_width, screen_height = self.screen.get_size()

        self.tile_size = max(
            1, min(screen_width // self.map_width, screen_height // self.map_height)
        )
        self.offset_x = (screen_width - (self.tile_size * self.map_width)) // 2
        self.offset_y = (screen_height - (self.tile_size * self.map_height)) // 2

        self.grid = grid or generate_map(
            generate_initial_map(self.map_height, self.map_width)
        )
        self.plants = add_plants(self.grid, plant_probability)
        self.seeds = seeds
        self.wind = wind
        self.increasingChange = increasingChange
        self.increasingDirection = increasingDirection

    def update(self):
        for agent in self.agents:
            agent.update(self)

    def draw(self):
        self.make_map()
        for agent in self.agents:
            agent.draw()
        for food in self.food:
            food.draw()
        pygame.display.flip()

    def each_tick(self):
        self.update()
        self.draw()
        self.update_wind(self.wind)
        self.update_plants()

    def display_plants(self, plants):
        for plant in plants:
            pixel_x = (self.offset_x
                       + plant.position[1] * self.tile_size
                       + int(plant.tile_offset[1] * self.tile_size))
            pixel_y = (self.offset_y
                       + plant.position[0] * self.tile_size
                       + int(plant.tile_offset[0] * self.tile_size))

            pygame.draw.rect(
                self.screen,
                plant.colour,
                (
                    pixel_x - self.tile_size // 8,
                    pixel_y - int(plant.size * self.tile_size),
                    self.tile_size // 4,
                    int(plant.size * self.tile_size),
                ),
            )

    def display_seeds(self, seeds):
        for seed in seeds:
            pygame.draw.circle(
                self.screen,
                (150, 75, 0),
                (
                    self.offset_x + seed.position[1] * self.tile_size + self.tile_size // 2,
                    self.offset_y + seed.position[0] * self.tile_size + self.tile_size // 2,
                ),
                self.tile_size // 8,
            )

    def make_map(self, map_width=None, map_height=None):
        map_width = int(map_width) if map_width is not None else self.map_width
        map_height = int(map_height) if map_height is not None else self.map_height

        self.screen.fill((255, 255, 255))
        for y in range(map_height):
            for x in range(map_width):
                tile = self.grid[y][x]
                if tile == 0:
                    color = grass
                elif tile == 1:
                    color = water
                elif tile == 2:
                    color = sand
                elif tile == 3:
                    color = forest
                else:
                    color = (0, 0, 0)
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        self.offset_x + x * self.tile_size,
                        self.offset_y + y * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    ),
                )
        self.display_plants(self.plants)
        self.display_seeds(self.seeds)
        pygame.display.flip()

    def update_wind(self, wind):
        switch_probability = 0.1
        if random.random() < switch_probability:
            self.increasingDirection = not self.increasingDirection
        if random.random() < switch_probability:
            self.increasingChange = not self.increasingChange

        direction_change = abs(random.normal(loc=0, scale=1.5))
        direction_change = direction_change if self.increasingDirection else -direction_change
        wind_direction = (wind[0] + direction_change) % 360

        strength_change = abs(random.normal(loc=0.001, scale=0.01))
        strength_change = strength_change if self.increasingChange else -strength_change
        wind_strength = max(0.1, min(1.0, wind[1] + strength_change))

        self.wind[0] = wind_direction
        self.wind[1] = wind_strength
        #print(f"Wind direction: {wind_direction:.2f} degrees, Wind strength: {wind_strength:.2f}")


    def update_plants(self):
        for plant in self.plants:
            plant.update(self)
        for seed in self.seeds:
            seed.update(self)
    def update_prey(self):
        # Placeholder for prey update logic
        pass

    def update_predators(self):
        # Placeholder for predator update logic
        pass

newWorld = World([], [], None, map_width=100, map_height=100)


done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
    newWorld.each_tick()
    newWorld.draw()

