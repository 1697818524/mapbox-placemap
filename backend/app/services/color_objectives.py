"""
双目标评分：颜色和谐度（色相模板）+ 地方表征性（对齐 my_work/obj_cal/calculate_object1）。

- 和谐度：基于 CIELab→LCh 色相，对无序色对求模板匹配度，按各语义代表色对应的 **簇 count 归一化权重** 做色对 **乘积加权**（与簇大小一致）。
- 地方表征性：移植 objective1 的「图-底 + 前景差异 + 语义一致性（与 cluster CSV）」综合分。
"""
from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 经典配色中常见的色相间隔（度），用于衡量一对颜色是否“和谐”
_HARMONY_HUE_TARGETS = (0, 30, 60, 90, 120, 150, 180)


def hex_to_rgb01(hex_str: str) -> Tuple[float, float, float]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", s):
        raise ValueError(f"Invalid hex: {hex_str}")
    return int(s[0:2], 16) / 255.0, int(s[2:4], 16) / 255.0, int(s[4:6], 16) / 255.0


def rgb01_to_lab(r: float, g: float, b: float) -> Tuple[float, float, float]:
    def pivot(c: float) -> float:
        return c ** (1 / 3) if c > 0.008856 else (7.787 * c + 16 / 116)

    X = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    Y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    Z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    X /= 0.95047
    Z /= 1.08883
    fx, fy, fz = pivot(X), pivot(Y), pivot(Z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b2 = 200 * (fy - fz)
    return L, a, b2


def hex_to_lab(hex_str: str) -> Tuple[float, float, float]:
    r, g, b = hex_to_rgb01(hex_str)
    return rgb01_to_lab(r, g, b)


def lab_to_lch(L: float, a: float, b: float) -> Tuple[float, float, float]:
    C = math.sqrt(a * a + b * b)
    h = math.degrees(math.atan2(b, a)) % 360.0
    return L, C, h


def delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(lab1, lab2)))


def _pair_hue_harmony(h1: float, h2: float, tolerance: float = 40.0) -> float:
    """单对色相和谐度 [0,1]，越高越好。"""
    dh = abs(h1 - h2)
    dh = min(dh, 360.0 - dh)
    best = 0.0
    for t in _HARMONY_HUE_TARGETS:
        best = max(best, 1.0 - min(abs(dh - float(t)) / tolerance, 1.0))
    return best


def harmony_score_from_hexes(
    colors_hex: List[str],
    weights: Optional[List[float]] = None,
) -> float:
    """
    多色整体和谐度：无序色对在 Lab LCh 下与色相模板匹配；权重为各语义簇 **count**（经 GA 传入，与 `_load_palettes` 行一致），
    内部归一化后按 **w_i * w_j** 对色对加权平均。
    """
    if not colors_hex:
        return 0.0
    if len(colors_hex) == 1:
        return 1.0
    hues: List[float] = []
    for hx in colors_hex:
        L, a, b = hex_to_lab(hx)
        _, _, h = lab_to_lch(L, a, b)
        hues.append(h)
    n = len(hues)
    w = weights if weights is not None and len(weights) == n else [1.0] * n
    sw = sum(w) or 1.0
    w = [x / sw for x in w]

    num = 0.0
    den = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            hij = _pair_hue_harmony(hues[i], hues[j])
            wi = w[i] * w[j]
            num += wi * hij
            den += wi
    return num / den if den > 0 else 0.0


def _fig_ground_score(fg_hex: str, bg_hex: str, delta_t: float, delta_l: float) -> float:
    lab_fg = hex_to_lab(fg_hex)
    lab_bg = hex_to_lab(bg_hex)
    de = delta_e(lab_fg, lab_bg)
    dL = abs(lab_fg[0] - lab_bg[0])
    return 0.5 * (min(1.0, de / delta_t) + min(1.0, dL / delta_l))


def _difference_score(hex_i: str, hex_j: str, mu: float) -> float:
    de = delta_e(hex_to_lab(hex_i), hex_to_lab(hex_j))
    return min(1.0, de / mu)


def semantic_consistency_from_csv(
    palette: Dict[str, List[Tuple[str, float]]],
    csv_paths: Dict[str, str],
    rgb_tol_sum: int = 15,
) -> float:
    """
    与 my_work calculate_object1.semantic_consistency 一致：
    每类取 **count 最大** 者为代表色（palette 内第二维为簇大小）；若在对应 CSV 的 RGB 行中存在 L1 差 ≤ rgb_tol_sum 则 s_k=1。
    按各类 **count 总和** 加权平均。
    """
    num = 0.0
    den = 0.0
    for category, colors in palette.items():
        if category not in csv_paths or not colors:
            continue
        rep = max(colors, key=lambda x: x[1])[0]
        wsum = sum(w for _, w in colors)
        try:
            rr, gg, bb = hex_to_rgb01(rep)
            r0, g0, b0 = int(rr * 255), int(gg * 255), int(bb * 255)
            sk = 0
            with open(csv_paths[category], newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "R" in reader.fieldnames:
                    for row in reader:
                        r, g, b = int(row["R"]), int(row["G"]), int(row["B"])
                        if abs(r - r0) + abs(g - g0) + abs(b - b0) <= rgb_tol_sum:
                            sk = 1
                            break
                else:
                    sk = 0
        except Exception:
            sk = 0
        num += wsum * sk
        den += wsum
    return num / den if den > 0 else 0.0


def place_representativeness_score(
    palette: Dict[str, List[Tuple[str, float]]],
    csv_paths: Dict[str, str],
    background_semantic: str,
    delta_t: float = 40.0,
    delta_l: float = 20.0,
    mu: float = 15.0,
) -> Dict[str, float]:
    """
    地方表征性（my_work objective1）：visual_norm 与 semantic_consistency 的算术平均。
    需指定 background_semantic（图-底中的「底」语义，如 green / roadnet）。
    """
    if background_semantic not in palette:
        raise KeyError(f"background semantic not in palette: {background_semantic}")

    def rep_color(cs: List[Tuple[str, float]]) -> str:
        """每语义取 count 最大簇的代表色。"""
        return max(cs, key=lambda x: x[1])[0] if cs else "#808080"

    cats = [c for c in palette if c != background_semantic and palette[c]]
    bg = rep_color(palette[background_semantic])
    fig_sum = sum(_fig_ground_score(rep_color(palette[c]), bg, delta_t, delta_l) for c in cats)
    diff_sum = 0.0
    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            diff_sum += _difference_score(
                rep_color(palette[cats[i]]),
                rep_color(palette[cats[j]]),
                mu,
            )
    n = len(cats)
    max_val = n + n * (n - 1) / 2
    visual_norm = (fig_sum + diff_sum) / max_val if max_val > 0 else 0.0
    sem = semantic_consistency_from_csv(palette, csv_paths) if csv_paths else 0.0
    overall = (visual_norm + sem) / 2.0
    return {"visual": visual_norm, "semantic_consistency": sem, "overall": overall}


def build_cluster_csv_paths(cluster_dir: str) -> Dict[str, str]:
    """palette_k{...}_{semantic}.csv -> semantic -> path"""
    out: Dict[str, str] = {}
    root = Path(cluster_dir)
    if not root.is_dir():
        return out
    for p in sorted(root.glob("palette_*.csv")):
        stem = p.stem  # palette_k10_architecture
        parts = stem.split("_")
        if len(parts) >= 3:
            sem = "_".join(parts[2:])
            out[sem] = str(p)
    return out
