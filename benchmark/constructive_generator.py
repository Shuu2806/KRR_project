"""
constructive_generator.py
Generates 3DSRP puzzle instances by direct construction (no ASP needed).
Adapted for KRR_project: to_facts uses cell_size_hint(X,Y,Z,S) for Filomino hints.
"""

import random
from collections import Counter
from itertools import product


def _neighbors(x, y, z, n):
    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
        nx, ny, nz = x+dx, y+dy, z+dz
        if 1 <= nx <= n and 1 <= ny <= n and 1 <= nz <= n:
            yield nx, ny, nz


def _build_nonplanar_core(seed, n, occupied):
    x, y, z = seed
    core = [seed]
    core_set = {seed}
    for dx, dy, dz in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]:
        placed = False
        for sign in (1, -1):
            nb = (x + sign * dx, y + sign * dy, z + sign * dz)
            if (1 <= nb[0] <= n and 1 <= nb[1] <= n and 1 <= nb[2] <= n
                    and nb not in occupied and nb not in core_set):
                core.append(nb)
                core_set.add(nb)
                placed = True
                break
        if not placed:
            return None
    return core


def _grow_region(seed, target_size, n, occupied):
    core = _build_nonplanar_core(seed, n, occupied)
    if core is None:
        return None

    region     = core[:]
    region_set = set(core)

    if len(region) >= target_size:
        return region[:target_size]

    frontier, frontier_set = [], set()
    for cube in region:
        for nb in _neighbors(*cube, n):
            if nb not in occupied and nb not in region_set and nb not in frontier_set:
                frontier.append(nb)
                frontier_set.add(nb)

    while len(region) < target_size:
        if not frontier:
            return None
        idx = random.randrange(len(frontier))
        cube = frontier[idx]
        frontier[idx] = frontier[-1]
        frontier.pop()
        frontier_set.discard(cube)
        region.append(cube)
        region_set.add(cube)
        for nb in _neighbors(*cube, n):
            if nb not in occupied and nb not in region_set and nb not in frontier_set:
                frontier.append(nb)
                frontier_set.add(nb)

    return region


def generate(c, n, m, k, w, max_attempts=300):
    """Generate a valid 3DSRP instance by construction.

    Returns (cube_list, symbol_dict, wall_list, region_map).
    Raises ValueError if parameters are impossible, RuntimeError if exhausted.
    """
    min_size = max(4, k)

    if c < m * min_size:
        raise ValueError(f"c={c} too small: need at least {m * min_size} cubes")
    if n ** 3 < c:
        raise ValueError(f"Bounding box n={n} has only {n**3} cells but c={c} requested")

    all_positions = list(product(range(1, n + 1), repeat=3))

    for _ in range(max_attempts):
        sizes = [min_size] * m
        for _ in range(c - m * min_size):
            sizes[random.randrange(m)] += 1
        random.shuffle(sizes)

        random.shuffle(all_positions)
        occupied, regions, failed = set(), [], False

        for size in sizes:
            seed = next((p for p in all_positions if p not in occupied), None)
            if seed is None:
                failed = True; break
            region = _grow_region(seed, size, n, occupied)
            if region is None:
                failed = True; break
            occupied.update(region)
            regions.append(region)

        if failed:
            continue

        cube_list, region_map = [], {}
        for r_id, region in enumerate(regions, start=1):
            for cube in region:
                cube_list.append(cube)
                region_map[cube] = r_id

        symbol_dict, sym_failed = {}, False
        for r_id, region in enumerate(regions, start=1):
            free = [c for c in region if c not in symbol_dict]
            if len(free) < k:
                sym_failed = True; break
            for sym_type, cube in enumerate(random.sample(free, k), start=1):
                symbol_dict[cube] = sym_type

        if sym_failed:
            continue

        boundary, seen = [], set()
        for cube in cube_list:
            for nb in _neighbors(*cube, n):
                if nb in region_map and region_map[nb] != region_map[cube]:
                    edge = (min(cube, nb), max(cube, nb))
                    if edge not in seen:
                        boundary.append(edge)
                        seen.add(edge)

        w_actual = min(w, len(boundary))
        wall_list = [
            (a[0], a[1], a[2], b[0], b[1], b[2])
            for a, b in random.sample(boundary, w_actual)
        ]

        return cube_list, symbol_dict, wall_list, region_map

    raise RuntimeError(f"Could not generate after {max_attempts} attempts "
                       f"(c={c}, n={n}, m={m}, k={k}, w={w})")


def to_facts(cube_list, symbol_dict, wall_list, region_map,
             m, k, filomino=False, h=0):
    """Serialise instance to Clingo fact strings.

    filomino=True, h=N : adds N random cell_size_hint(X,Y,Z,S) facts
                         where S is the size of the region containing (X,Y,Z).
    """
    facts = [f"regions({m})."] + [f"symbol_type({s})." for s in range(1, k + 1)]

    for x, y, z in cube_list:
        facts.append(f"cube({x},{y},{z}).")

    for (x, y, z), s in symbol_dict.items():
        facts.append(f"symbol({x},{y},{z},{s}).")

    for x1, y1, z1, x2, y2, z2 in wall_list:
        facts.append(f"wall({x1},{y1},{z1},{x2},{y2},{z2}).")

    if filomino and h > 0:
        sizes = Counter(region_map.values())
        chosen = random.sample(cube_list, min(h, len(cube_list)))
        for x, y, z in chosen:
            s = sizes[region_map[(x, y, z)]]
            facts.append(f"cell_size_hint({x},{y},{z},{s}).")

    return facts
