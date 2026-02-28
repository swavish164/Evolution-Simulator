import csv
import os
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

    def close(self):
        self.prey_file.close()
        self.predator_file.close()
        self.console_logs.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()