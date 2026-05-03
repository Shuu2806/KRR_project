# 3D Symbolic Region Puzzle (3DSRP)

A Knowledge Representation & Reasoning project implementing a 3D extension of the Symbolic Region Puzzle, solved via Answer Set Programming (Clingo).

## Problem Description

A **3DSRP instance** is defined by:

| Parameter | Meaning |
|-----------|---------|
| `c` | Number of cubes on the board |
| `n` | Bounding box side length (cubes live in an n×n×n grid) |
| `m` | Number of regions to partition the board into |
| `k` | Number of symbol types |
| `w` | Number of walls placed on region boundaries |

### Rules

1. **Coverage** — every cube belongs to exactly one region.
2. **Connectivity** — each region is connected (face-adjacency only; walls block adjacency).
3. **Non-planarity** — each region spans at least 2 distinct values on every axis (x, y, z).
4. **Symbols** — each region contains exactly one cube per symbol type (k cubes carry symbols per region).
5. **Walls** — two cubes separated by a wall must belong to different regions.

### Filomino variant

An optional hint `cell_size_hint(X,Y,Z,S)` annotates a cell with the size of its region. The solver enforces that the region containing `(X,Y,Z)` has exactly `S` cubes.

## Project Structure

```
KRR_project/
├── 3DSRP/
│   ├── generator.lp          # ASP instance generator (Clingo)
│   └── solver.lp             # ASP solver (Clingo)
├── benchmark/
│   ├── benchmark.ipynb       # Benchmark notebook (5 experiments)
│   ├── constructive_generator.py  # Fast Python generator (< 2 ms)
│   └── results/              # CSV and SVG outputs
├── main.py                   # Python wrapper: run_generator / run_solver
└── requirements.txt
```

## Quickstart

```bash
pip install -r requirements.txt
python main.py
```

`main.py` generates an instance and solves it in both Standard and Filomino modes:

```
=== Constructif (Python) — génération (c=40, n=6, m=3, k=3, w=10) ===
Génération : 0.4 ms  (180 faits)
Standard   : 312.1 ms
Filomino   : 48.7 ms

=== ASP (Clingo) — génération (c=40, n=6, m=3, k=3, w=10) ===
Génération : 4823.2 ms  (180 faits)
Standard   : 318.5 ms
Filomino   : 51.2 ms
```

## API (`main.py`)

### `run_generator`

```python
run_generator(c, n, m, k, w,
              filomino=0, h=3,
              timeout=60,
              use_clingo=True,
              print_out=False) -> bool
```

Generates a valid 3DSRP instance and stores it in the global `facts` list.

- `use_clingo=True` — ASP generator (`generator.lp`). Slow but mirrors the ASP model exactly.
- `use_clingo=False` — Constructive Python generator. Near-instant (< 2 ms).
- `filomino=1, h=N` — also generates `N` random `cell_size_hint` facts.
- Returns `True` on success, `False` on timeout or impossible parameters.

### `run_solver`

```python
run_solver(use_hints=True,
           h_limit=None,
           timeout=120,
           print_out=False) -> float
```

Solves the instance currently in `facts`. Does **not** modify `facts`.

- `use_hints=False` — Standard mode (ignores all `cell_size_hint` facts).
- `use_hints=True` — Filomino mode (uses size hints as additional constraints).
- `h_limit=N` — uses only the first `N` hints (useful for progressive experiments).
- Returns elapsed time in seconds, or `float('inf')` on timeout.

### Typical usage

```python
import main as solver

# Generate once, solve twice on the same instance
solver.run_generator(80, 6, 4, 3, 10, filomino=1, h=8, use_clingo=False)
inst = list(solver.facts)

solver.facts = list(inst)
t_std = solver.run_solver(use_hints=False, timeout=60)

solver.facts = list(inst)
t_fil = solver.run_solver(use_hints=True, timeout=60)

print(f"Standard: {t_std*1000:.1f} ms  |  Filomino: {t_fil*1000:.1f} ms")
```

## Generators

### ASP generator (`3DSRP/generator.lp`)

Uses Clingo to search for a valid instance satisfying all 3DSRP constraints. Guarantees structural correctness by construction (ASP). Slow for large `c` (exponential search space).

Accepts constants via `-c`:
```bash
clingo 3DSRP/generator.lp -c c=40 -c n=6 -c m=3 -c k=3 -c w=10 -c filomino=1 -c h=5
```

### Constructive Python generator (`benchmark/constructive_generator.py`)

Builds valid instances directly without search:
1. Distributes `c` cubes across `m` regions with sizes ≥ max(4, k).
2. Grows each region from a seed using a non-planar core + BFS frontier.
3. Places `k` distinct symbols per region.
4. Samples `w` boundary walls between adjacent regions.
5. Optionally samples `h` random cells and annotates each with its region size.

Average generation time < 2 ms for all tested parameters.

## Solver optimisations (Filomino)

The `cell_size_hint` constraint is split into three sub-constraints for better propagation during search:

```prolog
% Upper bound — fires as soon as a region exceeds S cubes (during construction)
:- cell_size_hint(X,Y,Z,S), region(X,Y,Z,R),
   S+1 { region(X',Y',Z',R) : cube(X',Y',Z') }.

% Lower bound
:- cell_size_hint(X,Y,Z,S), region(X,Y,Z,R),
   #count { X',Y',Z' : region(X',Y',Z',R) } < S.

% Mutual exclusion — two hints with different sizes cannot share a region
:- cell_size_hint(X1,Y1,Z1,S1), cell_size_hint(X2,Y2,Z2,S2), S1 != S2,
   region(X1,Y1,Z1,R), region(X2,Y2,Z2,R).
```

The upper-bound cardinality form propagates early (before the region is complete), unlike a plain `#count != S` check.

## Benchmark

Open `benchmark/benchmark.ipynb` with Jupyter. Five experiments, each with separate generation, Standard solve, and Filomino solve blocks.

| Exp | Varied | Fixed | Goal |
|-----|--------|-------|------|
| 0 | `c` | n=4, m=2, k=2, w=2 | ASP generator speed vs board size |
| 1 | `c` | n=6, m=3, k=3, w=4 | Solver speed vs board size |
| 2 | `m × k` | c=60, n=6, w=0 | Complexity heatmap |
| 3 | `w` | c=80, n=6, m=4, k=3 | Effect of walls |
| 4 | `h` | c=80, n=6, m=4, k=3, w=10 | Progressive Filomino hints |

**Key design:** Experiments 1–4 generate instances once with `filomino=1, h=H_MAX`, then solve them separately in Standard mode (hints filtered out) and Filomino mode (hints kept). This guarantees both variants are tested on **identical puzzles**.

Metric: **PAR-2** — timed-out runs count as 2 × TIMEOUT in the average.

## Requirements

- Python ≥ 3.11
- `clingo` (Python API)
- `pandas`, `matplotlib`, `numpy` (benchmark only)

```bash
pip install clingo pandas matplotlib numpy
```
