@dataclass
class SimulationConfig:
    metabolism_base_rate: float = 0.0005
    death_delay: float = 0.05
    mating_age_start: float = 0.4