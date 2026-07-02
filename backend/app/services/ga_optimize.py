"""
离散 NSGA-II：在每语义聚类候选中选下标组合，双目标最大化
  - f1: 颜色和谐度（color_objectives.harmony_score_from_hexes）
  - f2: 地方表征性 overall（color_objectives.place_representativeness_score）

输出 Pareto 第一前沿上若干套 ColorSchemeWithId。
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence, Tuple

from app.models.scheme import ColorScheme, ColorSchemeItem, ColorSchemeWithId, SchemeScores
from app.services import color_objectives
from app.services.scheme_generate import (
    _apply_palette_to_scheme,
    _load_palettes_from_cluster_dir,
    _normalize_scheme_layers,
    _rgb_to_hex,
    default_color_scheme,
)

DEFAULT_BACKGROUND_HEX = "#F3EFEC"


def _chromosome_to_palette_dict(
    palettes: Dict[str, List[Tuple[int, int, int, int]]],
    semantics: List[str],
    genes: Tuple[int, ...],
) -> Dict[str, List[Tuple[str, float]]]:
    """每语义一条 (hex, count)，与 `_load_palettes_from_cluster_dir` 该行簇大小一致，供 f1/f2 按簇大小加权。"""
    out: Dict[str, List[Tuple[str, float]]] = {}
    for sem, g in zip(semantics, genes):
        rows = palettes.get(sem) or []
        if not rows:
            continue
        idx = int(g) % len(rows)
        r, g0, b, cnt = rows[idx]
        hx = _rgb_to_hex(int(r), int(g0), int(b))
        out[sem] = [(hx, float(max(cnt, 1)))]
    return out


def _chromosome_to_rgb_map(
    palettes: Dict[str, List[Tuple[int, int, int, int]]],
    semantics: List[str],
    genes: Tuple[int, ...],
) -> Dict[str, Tuple[int, int, int]]:
    m: Dict[str, Tuple[int, int, int]] = {}
    for sem, g in zip(semantics, genes):
        rows = palettes.get(sem) or []
        if not rows:
            continue
        idx = int(g) % len(rows)
        r, g0, b, _ = rows[idx]
        m[sem] = (int(r), int(g0), int(b))
    return m


def _evaluate(
    genes: Tuple[int, ...],
    semantics: List[str],
    palettes: Dict[str, List[Tuple[int, int, int, int]]],
    csv_paths: Dict[str, str],
    background_semantic: str,
    background_hex: str,
) -> Tuple[float, float]:
    pal = _chromosome_to_palette_dict(palettes, semantics, genes)
    if len(pal) < 1:
        return 0.0, 0.0
    try:
        place = color_objectives.place_representativeness_score(
            pal,
            csv_paths,
            background_semantic,
            background_hex=background_hex,
        )
        f2 = float(place["overall"])
    except Exception:
        f2 = 0.0
    hexes = [pal[s][0][0] for s in semantics if s in pal]
    wts = [pal[s][0][1] for s in semantics if s in pal]
    f1 = color_objectives.harmony_score_from_hexes(hexes, wts)
    return f1, f2


def _background_hex_from_scheme(scheme: ColorScheme) -> str:
    for layer in scheme.layers:
        if layer.id == "background" and layer.color:
            return layer.color
    return DEFAULT_BACKGROUND_HEX


def _lock_background_layer(layers: List[ColorSchemeItem], background_hex: str) -> List[ColorSchemeItem]:
    out: List[ColorSchemeItem] = []
    has_background = False
    for layer in layers:
        if layer.id == "background":
            has_background = True
            out.append(
                ColorSchemeItem(
                    id=layer.id,
                    color=background_hex,
                    weight=layer.weight,
                    semantic=layer.semantic,
                )
            )
        else:
            out.append(layer)
    if not has_background:
        out.insert(0, ColorSchemeItem(id="background", color=background_hex, weight=0.0))
    return out


def _dominates(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    """a、b 均为最大化。"""
    return (a[0] >= b[0] and a[1] >= b[1]) and (a[0] > b[0] or a[1] > b[1])


def _fast_non_dominated_sort(
    objectives: List[Tuple[float, float]],
) -> List[List[int]]:
    n = len(objectives)
    S_set: List[List[int]] = [[] for _ in range(n)]
    n_dom = [0] * n
    fronts: List[List[int]] = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if _dominates(objectives[p], objectives[q]):
                S_set[p].append(q)
            elif _dominates(objectives[q], objectives[p]):
                n_dom[p] += 1
        if n_dom[p] == 0:
            fronts[0].append(p)

    rank_front = 0
    while fronts[rank_front]:
        nxt: List[int] = []
        for p in fronts[rank_front]:
            for q in S_set[p]:
                n_dom[q] -= 1
                if n_dom[q] == 0:
                    nxt.append(q)
        rank_front += 1
        fronts.append(nxt)
    fronts.pop()
    return fronts


def _crowding_distance(front: List[int], objectives: List[Tuple[float, float]]) -> Dict[int, float]:
    dist = {i: 0.0 for i in front}
    if len(front) <= 2:
        for i in front:
            dist[i] = float("inf")
        return dist
    m = 2
    for obj_idx in range(m):
        order = sorted(front, key=lambda idx: objectives[idx][obj_idx])
        dist[order[0]] = float("inf")
        dist[order[-1]] = float("inf")
        fmin = objectives[order[0]][obj_idx]
        fmax = objectives[order[-1]][obj_idx]
        span = fmax - fmin if fmax != fmin else 1e-9
        for k in range(1, len(order) - 1):
            prev_v = objectives[order[k - 1]][obj_idx]
            next_v = objectives[order[k + 1]][obj_idx]
            dist[order[k]] += (next_v - prev_v) / span
    return dist


def _tournament_select(
    pop: List[Tuple[int, ...]],
    objectives: List[Tuple[float, float]],
    ranks: List[int],
    crowding: Dict[int, float],
    k: int = 2,
) -> Tuple[int, ...]:
    idxs = random.sample(range(len(pop)), min(k, len(pop)))
    best = idxs[0]
    for j in idxs[1:]:
        if ranks[j] < ranks[best]:
            best = j
        elif ranks[j] == ranks[best] and crowding.get(j, 0) > crowding.get(best, 0):
            best = j
    return pop[best]


def run_nsga2_schemes(
    cluster_dir: str,
    base_scheme: Optional[ColorScheme] = None,
    population: int = 40,
    generations: int = 25,
    output_count: int = 5,
    background_semantic: str = "green",
    seed: Optional[int] = None,
    scheme_id_prefix: str = "",
) -> List[ColorSchemeWithId]:
    """
    在 cluster_dir 的 palette CSV 上运行 NSGA-II，返回至多 output_count 套互不支配解（先取第一前沿再截断）。
    """
    if seed is not None:
        random.seed(seed)

    palettes = _load_palettes_from_cluster_dir(cluster_dir)
    csv_paths = color_objectives.build_cluster_csv_paths(cluster_dir)
    semantics = sorted(palettes.keys())
    if not semantics:
        return []

    bounds = [max(1, len(palettes[s])) for s in semantics]

    def random_individual() -> Tuple[int, ...]:
        return tuple(random.randrange(0, bounds[i]) for i in range(len(semantics)))

    pop = [random_individual() for _ in range(population)]
    base = _normalize_scheme_layers(base_scheme) if base_scheme else default_color_scheme()
    background_hex = _background_hex_from_scheme(base)

    for _gen in range(generations):
        objs = [_evaluate(ind, semantics, palettes, csv_paths, background_semantic, background_hex) for ind in pop]
        fronts = _fast_non_dominated_sort(objs)
        rank_of = [10**9] * len(pop)
        for r, fr in enumerate(fronts):
            for idx in fr:
                rank_of[idx] = r
        crowding_all: Dict[int, float] = {}
        for fr in fronts:
            cd = _crowding_distance(fr, objs)
            crowding_all.update(cd)

        offspring: List[Tuple[int, ...]] = []
        while len(offspring) < population:
            p1 = _tournament_select(pop, objs, rank_of, crowding_all)
            p2 = _tournament_select(pop, objs, rank_of, crowding_all)
            c1, c2 = list(p1), list(p2)
            if random.random() < 0.9:
                cx = random.randrange(1, len(semantics))
                c1 = list(p1[:cx]) + list(p2[cx:])
                c2 = list(p2[:cx]) + list(p1[cx:])
            for bit in range(len(semantics)):
                if random.random() < 0.15:
                    c1[bit] = random.randrange(0, bounds[bit])
                if random.random() < 0.15:
                    c2[bit] = random.randrange(0, bounds[bit])
            c1_t = tuple(min(c1[i], bounds[i] - 1) for i in range(len(semantics)))
            c2_t = tuple(min(c2[i], bounds[i] - 1) for i in range(len(semantics)))
            offspring.append(c1_t)
            if len(offspring) < population:
                offspring.append(c2_t)

        combined = pop + offspring
        comb_objs = [
            _evaluate(ind, semantics, palettes, csv_paths, background_semantic, background_hex)
            for ind in combined
        ]
        fronts2 = _fast_non_dominated_sort(comb_objs)
        new_pop: List[Tuple[int, ...]] = []
        for fr in fronts2:
            if len(new_pop) + len(fr) <= population:
                for idx in fr:
                    new_pop.append(combined[idx])
            else:
                cd = _crowding_distance(fr, comb_objs)
                fr_sorted = sorted(fr, key=lambda i: -cd.get(i, 0))
                for idx in fr_sorted:
                    if len(new_pop) >= population:
                        break
                    new_pop.append(combined[idx])
            if len(new_pop) >= population:
                break
        pop = new_pop[:population]

    final_objs = [_evaluate(ind, semantics, palettes, csv_paths, background_semantic, background_hex) for ind in pop]
    fronts3 = _fast_non_dominated_sort(final_objs)
    first = fronts3[0] if fronts3 else []
    cd = _crowding_distance(first, final_objs) if first else {}
    first_sorted = sorted(first, key=lambda i: -cd.get(i, 0))

    schemes: List[ColorSchemeWithId] = []
    for rank, idx in enumerate(first_sorted[:output_count]):
        genes = pop[idx]
        rgb_map = _chromosome_to_rgb_map(palettes, semantics, genes)
        layers = _lock_background_layer(_apply_palette_to_scheme(base, rgb_map), background_hex)
        f1, f2 = final_objs[idx]
        scores = SchemeScores(
            semantic_fit=f2,
            readability=f1,
            diversity=min(1.0, rank / max(output_count - 1, 1)),
            harmony=f1,
            place_representativeness=f2,
        )
        prefix = f"{scheme_id_prefix}_" if scheme_id_prefix else ""
        schemes.append(
            ColorSchemeWithId(
                id=f"scheme_{prefix}nsga2_{rank:02d}",
                layers=layers,
                scores=scores,
            )
        )
    return schemes
