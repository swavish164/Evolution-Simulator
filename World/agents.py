import numpy as np


class agent:
    def __init__(self, position, velocity, energy, genone, age):
        self.position = position
        self.velocity = velocity
        self.energy = energy
        self.genone = np.array()
        self.age = age
        update(world)
        draw

