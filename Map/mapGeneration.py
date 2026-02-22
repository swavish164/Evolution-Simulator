import random

def generate_initial_map(window_height, window_width):
    map = []
    for i in range(window_height):
        row = []
        for j in range(window_width):
            row.append(0)
        map.append(row)
    return map

water_probability = 0.0005
forest_probability = 0.001

def check_surrounding(map, x, y, tile_type):
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            if i != 0 and j != 0:  # skip diagonals
                continue
            if x+i >= 0 and x+i < len(map) and y+j >= 0 and y+j < len(map[0]):
                if map[x+i][y+j] == tile_type:
                    count += 1
    return count

def getting_probability(surrounding_count, base_probability, multipliers=[1, 2, 3, 4]):
    match surrounding_count:
        case 0: p = base_probability * multipliers[0]
        case 1: p = base_probability * multipliers[1]
        case 2: p = base_probability * multipliers[2]
        case 3: p = base_probability * multipliers[3]
        case _: p = 1.0
    return min(1.0, p)

def add_water(map, probability):
    for i in range (len(map)):
        for j in range (len(map[i])):
            surrounding = check_surrounding(map, i, j, tile_type = 1)

            p = getting_probability(surrounding, probability, [1, 500, 1000, 3000])

            if surrounding >= 4 or random.random() < min(1.0, p):
                map[i][j] = 1

def add_sand(grid, x, y):
    if(grid[x][y] == 1):
        return
    if check_surrounding(grid, x, y, tile_type=1) > 0:
        grid[x][y] = 2

def add_forest(grid, x, y):
    if (grid[x][y] == 1) or (grid[x][y] == 2):
        return
    surrounding_forest = check_surrounding(grid, x, y, tile_type=3)
    p = getting_probability(surrounding_forest, forest_probability, [1, 300, 600, 800])
    if random.random() < p:
        grid[x][y] = 3

def enforce_borders(map):
    rows, cols = len(map), len(map[0])
    for i in range(rows):
        for j in range(cols):
            if i == 0 or j == 0 or i == rows - 1 or j == cols - 1:
                map[i][j] = 0

def generate_map(map):
    for _ in range(3):
        add_water(map, water_probability)
    rows, cols = len(map), len(map[0])
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            add_sand(map, i, j)
    for _ in range(5):
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                add_forest(map, i, j)

    enforce_borders(map)
    return map

if __name__ == "__main__":
    print(generate_map(generate_initial_map(100, 100)))
