"""
按语义类别进行颜色聚类服务
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import numpy as np
from sklearn.cluster import KMeans


class PaletteClusterService:
    def cluster_by_semantic(
        self,
        records: List[Dict],
        out_dir: str,
        k_min: int,
        k_max: int,
    ) -> List[str]:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        grouped: Dict[str, List[List[int]]] = {}
        for rec in records:
            sem = rec["coarse_semantic"]
            if sem == "unknown":
                continue
            grouped.setdefault(sem, []).append([rec["R"], rec["G"], rec["B"]])

        output_files: List[str] = []
        for sem, colors_list in grouped.items():
            colors = np.array(colors_list, dtype=np.float32)
            n = len(colors)
            if n == 0:
                continue
            k_auto = int(max(k_min, min(k_max, np.sqrt(n))))
            k = max(1, min(k_auto, n))

            kmeans = KMeans(n_clusters=k, random_state=42, n_init=3)
            labels = kmeans.fit_predict(colors)
            centroids = kmeans.cluster_centers_.astype(int)
            counts = np.bincount(labels, minlength=k)

            out_path = str(Path(out_dir) / f"palette_k{k}_{sem}.csv")
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["semantic", "cluster_id", "R", "G", "B", "count"])
                for i in range(k):
                    r, g, b = centroids[i].tolist()
                    writer.writerow([sem, i, int(r), int(g), int(b), int(counts[i])])
            output_files.append(out_path)

        return output_files
