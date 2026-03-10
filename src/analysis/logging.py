import csv
import os
import pygame
from ..agents.agent_constants import *

class StatsLogger:
    def __init__(self, output_dir: str = "stats"):
        os.makedirs(output_dir, exist_ok=True)

        self._next_id = 0

        self.prey_file = open(f"{output_dir}/prey_stats.csv", 'w', newline='')
        self.predator_file = open(f"{output_dir}/predator_stats.csv", 'w', newline='')
        self.console_logs = open(f"{output_dir}/console_logs.txt", 'w', newline='')

        headers = ['agent_id', 'birth_tick', 'parent_a_id', 'parent_b_id',
                   'generation', 'size', 'speed', 'vision', 'metabolism', 'max_age']

        self.prey_writer = csv.writer(self.prey_file)
        self.predator_writer = csv.writer(self.predator_file)
        self.prey_writer.writerow(headers)
        self.predator_writer.writerow(headers)
        self.log_writer = csv.writer(self.console_logs)
        self.log_writer.writerow(['tick', 'message'])

    def log_agent(self, agent, tick: int, is_predator: bool,
                  parent_a_id: int = None, parent_b_id: int = None) -> int:
        agent_id = self._next_id
        self._next_id += 1

        row = [
            agent_id,
            tick,
            parent_a_id,
            parent_b_id,
            agent.generation,
            round(agent.genome[GENOME_SIZE], 4),
            round(agent.genome[GENOME_SPEED], 4),
            round(agent.genome[GENOME_VISION], 4),
            round(agent.genome[GENOME_METABOLISM], 6),
            round(agent.genome[GENOME_MAX_AGE], 4),
        ]

        writer = self.predator_writer if is_predator else self.prey_writer
        file = self.predator_file if is_predator else self.prey_file
        writer.writerow(row)
        file.flush()
        return agent_id

    def log_population_stats(self, world, tick: int):
        alive_prey = [a for a in world.agents if not a.is_predator and not a.dead]
        if alive_prey:
            avg_size = sum(a.genome[GENOME_SIZE] for a in alive_prey) / len(alive_prey)
            avg_speed = sum(a.genome[GENOME_SPEED] for a in alive_prey) / len(alive_prey)
            avg_vision = sum(a.genome[GENOME_VISION] for a in alive_prey) / len(alive_prey)
            avg_metabolism = sum(a.genome[GENOME_METABOLISM] for a in alive_prey) / len(alive_prey)
            avg_max_age = sum(a.genome[GENOME_MAX_AGE] for a in alive_prey) / len(alive_prey)

            row = [
                -1,
                tick,
                -1,
                -1,
                -1,
                round(avg_size, 4),
                round(avg_speed, 4),
                round(avg_vision, 4),
                round(avg_metabolism, 6),
                round(avg_max_age, 4),
            ]
            self.prey_writer.writerow(row)
            self.prey_file.flush()

        alive_predators = [a for a in world.agents if a.is_predator and not a.dead]
        if alive_predators:
            avg_size = sum(a.genome[GENOME_SIZE] for a in alive_predators) / len(alive_predators)
            avg_speed = sum(a.genome[GENOME_SPEED] for a in alive_predators) / len(alive_predators)
            avg_vision = sum(a.genome[GENOME_VISION] for a in alive_predators) / len(alive_predators)
            avg_metabolism = sum(a.genome[GENOME_METABOLISM] for a in alive_predators) / len(alive_predators)
            avg_max_age = sum(a.genome[GENOME_MAX_AGE] for a in alive_predators) / len(alive_predators)

            row = [
                -1,
                tick,
                -1,
                -1,
                -1,
                round(avg_size, 4),
                round(avg_speed, 4),
                round(avg_vision, 4),
                round(avg_metabolism, 6),
                round(avg_max_age, 4),
            ]
            self.predator_writer.writerow(row)
            self.predator_file.flush()

    def close(self):
        self.prey_file.close()
        self.predator_file.close()
        self.console_logs.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class ConsoleLogDisplay:
    def __init__(self, screen: pygame.Surface, stats_logger: 'StatsLogger' = None, panel_width: int = 400, panel_height: int = 700):
        self.screen = screen
        self.stats_logger = stats_logger
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.panel_x = 0
        self.panel_y = 0

        self.BG = (0, 0, 0)
        self.PREY_COLOR = (0, 255, 0)
        self.PREDATOR_COLOR = (255, 0, 0)
        self.TEXT_COLOR = (200, 200, 200)

        self.font = pygame.font.SysFont('consolas', 10)
        self.line_height = 15
        self.max_lines = self.panel_height // self.line_height

        self.messages = []
        self.last_line_count = 0
        self.last_read_position = 0

    def _parse_message(self, tick: int, message: str) -> tuple[str, tuple]:
        formatted_msg = f"[{tick}] {message}"


        is_predator = False

        if "New True" in message:
            is_predator = True
        elif "New False" in message:
            is_predator = False
        elif "New predator born" in message:
            is_predator = True
        elif "Agent:" in message:
            is_predator = False

        color = self.PREDATOR_COLOR if is_predator else self.PREY_COLOR
        return formatted_msg, color

    def _read_logs(self):

        if self.stats_logger is None or self.stats_logger.console_logs is None:
            return

        try:
            current_pos = self.stats_logger.console_logs.tell()
            self.stats_logger.console_logs.seek(0)

            self.stats_logger.console_logs.seek(0)
            lines = self.stats_logger.console_logs.readlines()

            self.stats_logger.console_logs.seek(current_pos)

            messages = []
            for i, line in enumerate(lines):
                if i == 0:
                    continue

                line = line.strip()
                if not line:
                    continue
                parts = line.split(',', 1)
                if len(parts) >= 2:
                    try:
                        tick = int(parts[0])
                        message = parts[1]
                        formatted, color = self._parse_message(tick, message)
                        messages.append((formatted, color))
                    except (ValueError, IndexError):
                        continue

            self.messages = messages
        except Exception as e:
            pass

    def update(self):
        self._read_logs()

    def render(self):
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, self.BG, panel_rect)
        pygame.draw.rect(self.screen, (60, 60, 60), panel_rect, 2)

        visible_messages = self.messages[-self.max_lines:] if len(self.messages) > 0 else []

        y_offset = self.panel_y + 5
        for msg, color in visible_messages:
            text_surface = self.font.render(msg, True, color)
            self.screen.blit(text_surface, (self.panel_x + 5, y_offset))
            y_offset += self.line_height
