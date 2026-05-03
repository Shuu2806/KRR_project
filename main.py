"""
main.py
3D Symbolic Region Puzzle — Python wrapper

run_generator(c, n, m, k, w, filomino, h, use_clingo) :
    use_clingo=True  → générateur ASP  (lent, garanti valide par construction ASP)
    use_clingo=False → générateur Python constructif (< 2 ms, beaucoup plus rapide)

run_solver(use_hints, h_limit, timeout) :
    use_hints=False          → Standard (ignore les cell_size_hint)
    use_hints=True, h_limit=N → Filomino avec N indices seulement
    use_hints=True            → Filomino avec tous les indices

Ne modifie jamais `facts` après la génération — run_solver peut être appelé plusieurs fois.

Utilisation :
    python main.py
"""

import clingo
import time
from pathlib import Path

import benchmark.constructive_generator as _cg

_BASE = Path(__file__).parent / "3DSRP"

# Faits de l'instance courante (remplis par run_generator)
facts: list[str] = []


def run_generator(c: int, n: int, m: int, k: int, w: int,
                  filomino: int = 0, h: int = 3,
                  timeout: int = 60,
                  use_clingo: bool = True,
                  print_out: bool = False) -> bool:
    """Génère une instance 3DSRP et remplit la liste globale `facts`.

    use_clingo=True  : générateur ASP (generator.lp) — lent mais fidèle au modèle ASP.
    use_clingo=False : générateur Python constructif   — quasi-instantané.
    Retourne True si succès, False si timeout ou paramètres impossibles.
    """
    global facts
    facts = []

    if not use_clingo:
        try:
            cube_list, symbol_dict, wall_list, region_map = _cg.generate(c, n, m, k, w)
        except (ValueError, RuntimeError):
            return False
        facts = _cg.to_facts(cube_list, symbol_dict, wall_list, region_map,
                              m, k, filomino=bool(filomino), h=h)
        if print_out:
            print(" ".join(f.rstrip(".") for f in facts))
        return True

    # ── Générateur ASP ──
    ctl = clingo.Control([
        "--models=1", "-t", "4",
        "-c", f"c={c}",
        "-c", f"n={n}",
        "-c", f"m={m}",
        "-c", f"k={k}",
        "-c", f"w={w}",
        "-c", f"filomino={filomino}",
        "-c", f"h={h}",
    ])
    ctl.load(str(_BASE / "generator.lp"))
    ctl.ground([("base", [])])

    instance: list[str] = []

    def collect(model):
        nonlocal instance
        instance = [str(a) + "." for a in model.symbols(shown=True)]

    with ctl.solve(on_model=collect, async_=True) as handle:
        finished = handle.wait(timeout)
        if not finished:
            handle.cancel()
            handle.get()
            return False
        handle.get()

    if not instance:
        return False

    facts = instance
    if print_out:
        print(" ".join(f.rstrip(".") for f in facts))
    return True


def run_solver(use_hints: bool = True,
               h_limit: int | None = None,
               timeout: int = 120,
               print_out: bool = False) -> float:
    """Résout l'instance dans `facts` via solver.lp.

    use_hints=False          → Standard (cell_size_hint retirés).
    use_hints=True, h_limit=N → Filomino avec seulement les N premiers indices.
    use_hints=True            → Filomino avec tous les indices.
    Ne modifie pas `facts`.
    Retourne le temps en secondes, ou float('inf') si timeout.
    """
    hints     = [f for f in facts if f.startswith("cell_size_hint")]
    non_hints = [f for f in facts if not f.startswith("cell_size_hint")]

    if not use_hints:
        instance = non_hints
    elif h_limit is not None:
        instance = non_hints + hints[:h_limit]
    else:
        instance = facts

    ctl = clingo.Control(["--models=1", "-t", "4"])
    ctl.load(str(_BASE / "solver.lp"))
    ctl.add("base", [], "\n".join(instance))
    ctl.ground([("base", [])])

    def noop(model):
        pass

    def print_model(model):
        print(" ".join(str(a) for a in model.symbols(shown=True)))

    start = time.perf_counter()
    with ctl.solve(on_model=print_model if print_out else noop, async_=True) as handle:
        finished = handle.wait(timeout)
        if not finished:
            handle.cancel()
            handle.get()
            return float("inf")
        handle.get()
    return time.perf_counter() - start


if __name__ == "__main__":
    C, N, M, K, W = 40, 6, 3, 3, 10

    for mode, use_clingo in [("Constructif (Python)", False), ("ASP (Clingo)", True)]:
        print(f"\n=== {mode} — génération (c={C}, n={N}, m={M}, k={K}, w={W}) ===")
        t0 = time.perf_counter()
        ok = run_generator(C, N, M, K, W, filomino=1, h=3,
                           use_clingo=use_clingo, timeout=30)
        t_gen = time.perf_counter() - t0
        if not ok:
            print("Génération échouée.")
            continue
        print(f"Génération : {t_gen*1000:.1f} ms  ({len(facts)} faits)")
        t_solve = run_solver(use_hints=False, timeout=60)
        print(f"Standard   : {t_solve*1000:.1f} ms")
        t_solve = run_solver(use_hints=True, timeout=60)
        print(f"Filomino   : {t_solve*1000:.1f} ms")
