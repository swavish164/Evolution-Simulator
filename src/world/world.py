import pygame
from numpy import random

from src.analysis.anaysis import LiveAnalysis
from src.analysis.logging import StatsLogger
from src.world.mapGeneration import generate_initial_map, generate_map
from src.plants.plants import add_plants
from src.agents.agents import add_packs, assign_pack_leader
import csv

grass = (21, 122, 17)
water = (0, 0, 255)
forest = (5, 71, 3)
sand = (255, 255, 0)

class World:
    def __init__(
            self,
            food: list,
            grid=None,
            screen=None,
            map_width: int = 100,
            map_height: int = 100,
            plant_probability: float = 0.025,
            wind: list[float] | None = None,
            increasing_direction: bool = True,
            increasing_change: bool = True,
            seeds: list | None = None,
            max_agent_id = 0,
            world_tick = 0,
            stats_logger: StatsLogger | None = None
    ):
        if wind is None:
            wind = [0.0, 0.0]
        if seeds is None:
            seeds = []

        self.food = list(food)
        self.map_width = int(map_width)
        self.map_height = int(map_height)

        self.screen = screen or pygame.display.set_mode((1400, 700))
        self.screen_width, self.screen_height = (700,700)

        self.tile_size = max(
            1, min(self.screen_width // self.map_width, self.screen_height // self.map_height)
        )
        self.offset_x = (self.screen_width - (self.tile_size * self.map_width)) // 2
        self.offset_y = (self.screen_height - (self.tile_size * self.map_height)) // 2
        self.max_agent_id = max_agent_id
        self.world_tick = world_tick
        self.grid = grid or generate_map(
            generate_initial_map(self.map_height, self.map_width)
        )
        self.packs, self.agents = add_packs(self, num_packs=random.randint(2, 5), pack_size=random.randint(5, 10), is_predator=False)
        self.plants = add_plants(self.grid, plant_probability)
        self.predators = [self.map_height // 2, self.map_width // 2]
        self.seeds = seeds
        self.wind = wind
        self.increasingChange = increasing_change
        self.increasingDirection = increasing_direction
        self.stats_logger = stats_logger
        self.live_analysis = LiveAnalysis(self.screen, panel_x=700)

    def each_tick(self, dt: float):
        self.update_wind(self.wind)
        self.update_plants(dt)
        self.update_agents(dt)
        self.make_map()
        self.live_analysis.update(self.world_tick)
        pygame.display.flip()

    def display_plants(self, plants: list):
        for plant in plants[0]:
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

    def display_agents(self):
        for agent in self.agents:
            pygame.draw.circle(
                self.screen,
                agent.colour,
                (
                    int(self.offset_x + agent.position[1] * self.tile_size + self.tile_size // 2),
                    int(self.offset_y + agent.position[0] * self.tile_size + self.tile_size // 2),
                ),
                max(1, self.tile_size // 4),
            )

    def display_seeds(self):
        for seed in self.seeds:
            pygame.draw.circle(
                self.screen,
                (150, 75, 0),
                (
                    int(self.offset_x + seed.position[1] * self.tile_size + self.tile_size // 2),
                    int(self.offset_y + seed.position[0] * self.tile_size + self.tile_size // 2),
                ),
                max(1, self.tile_size // 8),
            )

    def make_map(self, map_width: int | None = None, map_height: int | None = None):
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
        self.display_seeds()
        self.display_agents()
        screen_width, screen_height = self.screen.get_size()
        pygame.draw.circle(
            self.screen,
            (255, 0, 0),
            (
                int(self.offset_x + self.predators[1] * self.tile_size + self.tile_size // 2),
                int(self.offset_y + self.predators[0] * self.tile_size + self.tile_size // 2),
        ),
            self.tile_size//4,
        )

    def update_wind(self, wind: list[float]):
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

    def update_agents(self, dt: float):
        for agent in list(self.agents):
            agent.update(self, dt)

    def update_plants(self, dt: float):
        for plant in list(self.plants[0]):
            plant.update(self, dt)
        for seed in list(self.seeds):
            seed.update(self, dt)

clock = pygame.time.Clock()
FPS = 60
dt = 16
pygame.init()

done = False
with StatsLogger() as logger:
    newWorld = World([], map_width=100, map_height=100, stats_logger=logger)
    assign_pack_leader(newWorld)
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        newWorld.each_tick(dt)
        newWorld.world_tick += 1
        dt = clock.tick(FPS)

pygame.quit()
