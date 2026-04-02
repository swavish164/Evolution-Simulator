# Evolution Simulator

A simulation where prey and predators evolve to survive in a procedurally generated world. Watch as populations adapt their behavior, hunting strategies, and physical traits over generations.

## What's happening

Two species inhabit the world:
- **Prey** - herbivores that eat plants, drink water, and form packs for protection
- **Predators** - carnivores that hunt prey and work together in packs

Each agent has a genome controlling their size, speed, vision range, metabolism, and lifespan. Neural networks drive their decision-making, and these traits are inherited and mutated in offspring. Over time, successful traits become more common in the population.

## Key features

- **Procedural terrain** - grass, forest, sand, and water tiles affect movement
- **Realistic mechanics** - energy/metabolism, thirst, aging, and injury
- **Pack behavior** - group coordination with pack leaders
- **Mating & genetics** - offspring inherit and mutate parent traits
- **Live stats** - track population data and individual agent info as the sim runs

## Video Demo

https://github.com/user-attachments/assets/5a69fc60-d205-4cf8-8fdb-d3c990b34ccd

## Getting started

```bash
pip install -r requirements.txt
python -m src.world.world
```

Uses pygame for visualization and numpy for neural network computations.
