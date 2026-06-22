"""
规则版配色方案生成（后续可替换为 GA / NSGA-II）
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.models.scheme import (
    ColorScheme,
    ColorSchemeItem,
    ColorSchemeWithId,
    SchemeScores,
)
from app.services import color_objectives

# 与前端 MapStyle.vue 可配置图层 id 一致
SCHEME_LAYER_ORDER: Tuple[str, ...] = (
    "background",
    "water",
    "road-level-1",
    "road-level-2",
    "road-level-3",
    "building",
    "landuse",
)

LAYER_ID_TO_SEMANTIC: Dict[str, str] = {
    "background": "base",
    "water": "water",
    "road-level-1": "roadnet",
    "road-level-2": "roadnet",
    "road-level-3": "roadnet",
    "building": "architecture",
    "landuse": "green",
}

SEMANTIC_DEFAULT_HEX: Dict[str, str] = {
    "base": "#F3EFEC",
    "water": "#4A90D9",
    "roadnet": "#E6E6E8",
    "architecture": "#D4CBBE",
    "green": "#C5E1A5",
    "landmark": "#5C5C5C",
}


def _normalize_scheme_layers(base: ColorScheme, layer_semantics: Optional[Dict[str, str]] = None) -> ColorScheme:
    """Keep only visible map style controls, in panel order."""
    overrides = layer_semantics or {}
    by_id = {item.id: item for item in base.layers}
    n = len(SCHEME_LAYER_ORDER)
    w = 1.0 / n if n else 0.0
    layers: List[ColorSchemeItem] = []
    for lid in SCHEME_LAYER_ORDER:
        sem = overrides.get(lid) or LAYER_ID_TO_SEMANTIC[lid]
        item = by_id.get(lid)
        layers.append(
            ColorSchemeItem(
                id=lid,
                color=item.color if item else SEMANTIC_DEFAULT_HEX.get(sem, "#888888"),
                weight=w,
                semantic=sem,
            )
        )
    return ColorScheme(layers=layers)


def default_color_scheme() -> ColorScheme:
    """Pipeline 无前端方案时使用的基底（图层 id 与前端一致）。"""
    ids = list(SCHEME_LAYER_ORDER)
    n = len(ids)
    w = 1.0 / n if n else 0.0
    layers: List[ColorSchemeItem] = []
    for lid in ids:
        sem = LAYER_ID_TO_SEMANTIC[lid]
        hex_c = SEMANTIC_DEFAULT_HEX.get(sem, "#888888")
        layers.append(ColorSchemeItem(id=lid, color=hex_c, weight=w, semantic=sem))
    return ColorScheme(layers=layers)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    s = hex_color.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return 128.0, 128.0, 128.0
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _rgb_to_hsl(r: float, g: float, b: float) -> Tuple[float, float, float]:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d + (6.0 if g < b else 0.0)) / 6.0
    elif mx == g:
        h = ((b - r) / d + 2.0) / 6.0
    else:
        h = ((r - g) / d + 4.0) / 6.0
    return h % 1.0, s, l


def _hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    if s == 0:
        v = int(round(l * 255))
        return v, v, v

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = hue_to_rgb(p, q, h + 1 / 3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1 / 3)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def _shift_layer_color(hex_color: str, scheme_index: int, total_schemes: int) -> str:
    """无调色板时：按方案序号做小幅色相旋转，保留明暗关系。"""
    r, g, b = _hex_to_rgb(hex_color)
    h, s, l = _rgb_to_hsl(r, g, b)
    delta = (scheme_index + 1) / max(total_schemes, 1) * 0.35
    nh = (h + delta) % 1.0
    ns = min(1.0, max(0.15, s * (0.92 + 0.08 * math.sin(scheme_index))))
    nr, ng, nb = _hsl_to_rgb(nh, ns, l)
    return _rgb_to_hex(nr, ng, nb)


def _adjust_hsl(hex_color: str, hue_delta: float = 0.0, sat_mul: float = 1.0, light_delta: float = 0.0) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    h, s, l = _rgb_to_hsl(r, g, b)
    nr, ng, nb = _hsl_to_rgb(
        (h + hue_delta) % 1.0,
        min(1.0, max(0.0, s * sat_mul)),
        min(0.96, max(0.08, l + light_delta)),
    )
    return _rgb_to_hex(nr, ng, nb)


def _fallback_layer_color(item: ColorSchemeItem, scheme_index: int, total_schemes: int) -> str:
    base = item.color or SEMANTIC_DEFAULT_HEX.get(_layer_semantic(item) or "", "#888888")
    phase = (scheme_index + 1) / max(total_schemes, 1)
    hue = 0.08 * phase
    if item.id == "background":
        return _adjust_hsl(base, hue_delta=hue * 0.35, sat_mul=0.85, light_delta=0.015 * scheme_index)
    if item.id == "building":
        return _adjust_hsl(base, hue_delta=hue * 0.7, sat_mul=1.05, light_delta=-0.02 + 0.012 * scheme_index)
    if item.id == "road-level-1":
        return _adjust_hsl(base, hue_delta=hue, sat_mul=1.15, light_delta=-0.10)
    if item.id == "road-level-2":
        return _adjust_hsl(base, hue_delta=hue, sat_mul=1.05, light_delta=-0.04)
    if item.id == "road-level-3":
        return _adjust_hsl(base, hue_delta=hue, sat_mul=0.95, light_delta=0.04)
    return _shift_layer_color(base, scheme_index, total_schemes)


def _contrast_pair(c1: str, c2: str) -> float:
    """简化可读性：两色相对亮度差，归一化到 0~1。"""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    lum = lambda r, g, b: 0.2126 * r + 0.7152 * g + 0.0722 * b
    d = abs(lum(r1, g1, b1) - lum(r2, g2, b2)) / 255.0
    return min(1.0, d * 2.0)


def _load_palettes_from_cluster_dir(cluster_dir: str) -> Dict[str, List[Tuple[int, int, int, int]]]:
    """semantic -> [(R,G,B,count), ...] 按簇大小 **count 降序**；NSGA 基因下标与行对应，且 **count** 传入 f1/f2 加权。"""
    root = Path(cluster_dir)
    if not root.is_dir():
        return {}
    out: Dict[str, List[Tuple[int, int, int, int]]] = {}
    for csv_path in sorted(root.glob("palette_*.csv")):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sem = row.get("semantic") or ""
                try:
                    r, g, b = int(row["R"]), int(row["G"]), int(row["B"])
                    cnt = int(row.get("count") or 0)
                except (KeyError, ValueError):
                    continue
                out.setdefault(sem, []).append((r, g, b, cnt))
    for sem in out:
        out[sem].sort(key=lambda x: -x[3])
    return out


def _pick_palette_for_scheme(
    palettes: Dict[str, List[Tuple[int, int, int, int]]], scheme_index: int
) -> Dict[str, Tuple[int, int, int]]:
    chosen: Dict[str, Tuple[int, int, int]] = {}
    for sem, rows in palettes.items():
        if not rows:
            continue
        idx = scheme_index % len(rows)
        r, g, b, _ = rows[idx]
        chosen[sem] = (r, g, b)
    return chosen


def _semantic_fit_score(palettes: Dict[str, List[Tuple[int, int, int, int]]], chosen: Dict[str, Tuple[int, int, int]]) -> float:
    """与调色板主色（每语义 count 最大簇）的贴合度，按 **簇 count** 加权平均。"""
    if not chosen:
        return 0.0
    total = 0.0
    w = 0.0
    for sem, (r, g, b) in chosen.items():
        rows = palettes.get(sem) or []
        if not rows:
            continue
        top = rows[0]
        d = math.sqrt((r - top[0]) ** 2 + (g - top[1]) ** 2 + (b - top[2]) ** 2)
        fit = max(0.0, 1.0 - d / 441.0)
        cnt = float(top[3] + 1)
        total += fit * cnt
        w += cnt
    return total / w if w else 0.0


def _readability_score(layers: List[ColorSchemeItem]) -> float:
    water = next((x.color for x in layers if x.id == "water"), None)
    building = next((x.color for x in layers if x.id == "building"), None)
    if water and building:
        return _contrast_pair(water, building)
    if len(layers) >= 2:
        return _contrast_pair(layers[0].color, layers[1].color)
    return 0.5


def _background_hex_from_layers(layers: List[ColorSchemeItem]) -> str:
    bg = next((x.color for x in layers if x.id == "background"), None)
    return bg or SEMANTIC_DEFAULT_HEX["base"]


def _layers_to_objective_palette(layers: List[ColorSchemeItem]) -> Dict[str, List[Tuple[str, float]]]:
    palette: Dict[str, List[Tuple[str, float]]] = {}
    for item in layers:
        if item.id == "background":
            continue
        sem = _layer_semantic(item)
        if not sem:
            continue
        palette.setdefault(sem, []).append((item.color, max(float(item.weight or 0.0), 1.0)))
    return palette


def _dual_objective_scores(layers: List[ColorSchemeItem], cluster_dir: Optional[str]) -> Tuple[float, Optional[float]]:
    foreground = [item for item in layers if item.id != "background"]
    colors = [item.color for item in foreground]
    weights = [max(float(item.weight or 0.0), 1.0) for item in foreground]
    try:
        harmony = color_objectives.harmony_score_from_hexes(colors, weights)
    except Exception:
        harmony = 0.0

    if not cluster_dir:
        return harmony, None

    try:
        place = color_objectives.place_representativeness_score(
            _layers_to_objective_palette(layers),
            color_objectives.build_cluster_csv_paths(cluster_dir),
            background_semantic="base",
            background_hex=_background_hex_from_layers(layers),
        )
        return harmony, float(place["overall"])
    except Exception:
        return harmony, 0.0


def _layer_semantic(item: ColorSchemeItem) -> Optional[str]:
    if item.semantic:
        return item.semantic
    return LAYER_ID_TO_SEMANTIC.get(item.id)


def _apply_palette_to_scheme(
    base: ColorScheme,
    palette_rgb: Dict[str, Tuple[int, int, int]],
    scheme_index: int = 0,
    total_schemes: int = 1,
) -> List[ColorSchemeItem]:
    new_layers: List[ColorSchemeItem] = []
    for item in base.layers:
        sem = _layer_semantic(item)
        if sem and sem in palette_rgb:
            r, g, b = palette_rgb[sem]
            new_layers.append(
                ColorSchemeItem(
                    id=item.id,
                    color=_rgb_to_hex(r, g, b),
                    weight=item.weight,
                    semantic=sem,
                )
            )
        else:
            new_layers.append(
                ColorSchemeItem(
                    id=item.id,
                    color=_fallback_layer_color(item, scheme_index, total_schemes),
                    weight=item.weight,
                    semantic=sem,
                )
            )
    return new_layers


def _global_palette_rows(palettes: Dict[str, List[Tuple[int, int, int, int]]]) -> List[Tuple[str, int, int, int, int]]:
    rows: List[Tuple[str, int, int, int, int]] = []
    for sem, values in palettes.items():
        for r, g, b, cnt in values:
            rows.append((sem, int(r), int(g), int(b), int(cnt)))
    rows.sort(key=lambda x: -x[4])
    return rows


def _apply_global_palette_to_scheme(
    base: ColorScheme,
    palettes: Dict[str, List[Tuple[int, int, int, int]]],
    scheme_index: int,
    total_schemes: int,
    population: int,
    generations: int,
) -> List[ColorSchemeItem]:
    rows = _global_palette_rows(palettes)
    if not rows:
        return _apply_palette_to_scheme(base, {}, scheme_index, total_schemes)
    offset = (scheme_index * max(1, population // 8) + generations) % len(rows)
    out: List[ColorSchemeItem] = []
    for idx, item in enumerate(base.layers):
        _, r, g, b, _ = rows[(offset + idx * 3) % len(rows)]
        out.append(
            ColorSchemeItem(
                id=item.id,
                color=_rgb_to_hex(r, g, b),
                weight=item.weight,
                semantic=_layer_semantic(item),
            )
        )
    return out


class SchemeGenerateService:
    def generate(
        self,
        base: ColorScheme,
        count: int,
        job_id: Optional[str] = None,
        jobs_base_dir: str = "data/jobs",
        semantic_mode: str = "local",
        layer_semantics: Optional[Dict[str, str]] = None,
        population: int = 40,
        generations: int = 25,
    ) -> List[ColorSchemeWithId]:
        base = _normalize_scheme_layers(base, layer_semantics)
        cluster_dir: Optional[str] = None
        if job_id:
            p = Path(jobs_base_dir) / job_id / "cluster"
            if p.is_dir():
                cluster_dir = str(p)

        palettes = _load_palettes_from_cluster_dir(cluster_dir) if cluster_dir else {}

        schemes: List[ColorSchemeWithId] = []
        for i in range(count):
            if palettes:
                chosen = _pick_palette_for_scheme(palettes, i)
                if semantic_mode == "global":
                    layers = _apply_global_palette_to_scheme(base, palettes, i, count, population, generations)
                else:
                    layers = _apply_palette_to_scheme(base, chosen, i, count)
                sem_fit = _semantic_fit_score(palettes, chosen)
                read = _readability_score(layers)
                div = min(1.0, i / max(count - 1, 1)) if count > 1 else 1.0
                harmony, place = _dual_objective_scores(layers, cluster_dir)
                scores = SchemeScores(
                    semantic_fit=sem_fit,
                    readability=read,
                    diversity=div,
                    harmony=harmony,
                    place_representativeness=place,
                )
                sid = f"scheme_job_{job_id or 'local'}_rule_{i:02d}"
            else:
                layers = [
                    ColorSchemeItem(
                        id=x.id,
                        color=_shift_layer_color(x.color, i, count),
                        weight=x.weight,
                        semantic=_layer_semantic(x),
                    )
                    for x in base.layers
                ]
                harmony, place = _dual_objective_scores(layers, cluster_dir)
                scores = SchemeScores(
                    semantic_fit=0.4,
                    readability=_readability_score(layers),
                    diversity=min(1.0, i / max(count - 1, 1)) if count > 1 else 1.0,
                    harmony=harmony,
                    place_representativeness=place,
                )
                sid = f"scheme_hsl_rule_{i:02d}"

            schemes.append(ColorSchemeWithId(id=sid, layers=layers, scores=scores))

        if len(schemes) >= 2 and palettes:
            self._annotate_diversity_vs_first(schemes)

        return schemes

    def _annotate_diversity_vs_first(self, schemes: List[ColorSchemeWithId]) -> None:
        first = schemes[0]
        for i, sc in enumerate(schemes):
            if i == 0:
                if sc.scores:
                    sc.scores.diversity = 1.0
                continue
            dists = []
            for a, b in zip(first.layers, sc.layers):
                if a.id != b.id:
                    continue
                r1, g1, b1 = _hex_to_rgb(a.color)
                r2, g2, b2 = _hex_to_rgb(b.color)
                dists.append(math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2))
            avg = sum(dists) / len(dists) if dists else 0.0
            div = min(1.0, avg / 180.0)
            if sc.scores:
                sc.scores.diversity = div

    def save_schemes_json(self, schemes: List[ColorSchemeWithId], out_dir: str) -> List[str]:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        paths: List[str] = []
        import json

        for sc in schemes:
            path = str(Path(out_dir) / f"{sc.id}.json")
            payload = sc.model_dump(mode="json")
            Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            paths.append(path)
        return paths
