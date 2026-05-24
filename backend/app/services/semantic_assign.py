"""
语义对齐与超像素语义投票服务
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from PIL import Image


CITYSCAPES_COLORS = np.array(
    [
        [128, 64, 128],   # 0 road
        [244, 35, 232],   # 1 sidewalk
        [70, 70, 70],     # 2 building
        [102, 102, 156],  # 3 wall
        [190, 153, 153],  # 4 fence
        [153, 153, 153],  # 5 pole
        [250, 170, 30],   # 6 traffic light
        [220, 220, 0],    # 7 traffic sign
        [107, 142, 35],   # 8 vegetation
        [152, 251, 152],  # 9 terrain
        [70, 130, 180],   # 10 sky
        [220, 20, 60],    # 11 person
        [255, 0, 0],      # 12 rider
        [0, 0, 142],      # 13 car
        [0, 0, 70],       # 14 truck
        [0, 60, 100],     # 15 bus
        [0, 80, 100],     # 16 train
        [0, 0, 230],      # 17 motorcycle
        [119, 11, 32],    # 18 bicycle
    ],
    dtype=np.int16,
)

# 0=architecture,1=roadnet,2=green,3=landmark,4=water(sky),255=unknown
CITYSCAPES_TO_COARSE_ID = {
    0: 1, 1: 1,        # roadnet
    2: 0, 3: 0, 4: 0,  # architecture
    5: 3, 6: 3, 7: 3,  # landmark
    8: 2, 9: 2,        # green
    10: 4,             # sky -> water
}

COARSE_ID_TO_NAME = {
    0: "architecture",
    1: "roadnet",
    2: "green",
    3: "landmark",
    4: "water",
    255: "unknown",
}

COARSE_COLORS = np.array(
    [
        [180, 120, 120],  # architecture
        [120, 120, 120],  # roadnet
        [4, 200, 3],      # green
        [255, 82, 0],     # landmark
        [9, 7, 230],      # water
    ],
    dtype=np.uint8,
)


class SemanticAssignService:
    def decode_cityscapes_color_to_train_id(self, sem_rgb: np.ndarray) -> np.ndarray:
        pixels = sem_rgb.reshape(-1, 3).astype(np.int16)
        # N x 19
        dists = ((pixels[:, None, :] - CITYSCAPES_COLORS[None, :, :]) ** 2).sum(axis=2)
        ids = np.argmin(dists, axis=1).astype(np.uint8)
        return ids.reshape(sem_rgb.shape[:2])

    def to_coarse_map(self, train_id_map: np.ndarray) -> np.ndarray:
        coarse = np.full_like(train_id_map, fill_value=255, dtype=np.uint8)
        for src_id, dst_id in CITYSCAPES_TO_COARSE_ID.items():
            coarse[train_id_map == src_id] = dst_id
        return coarse

    def save_coarse_outputs(self, coarse_map: np.ndarray, id_out: str, color_out: str) -> None:
        Path(id_out).parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(coarse_map).save(id_out)

        color = np.zeros((*coarse_map.shape, 3), dtype=np.uint8)
        for cid in range(5):
            color[coarse_map == cid] = COARSE_COLORS[cid]
        color[coarse_map == 255] = np.array([0, 0, 0], dtype=np.uint8)
        Image.fromarray(color).save(color_out)

    def assign_superpixel_semantics(
        self,
        image_path: str,
        segments: np.ndarray,
        coarse_map: np.ndarray,
        image_id: str,
    ) -> List[Dict]:
        img_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        records: List[Dict] = []
        for seg_id in np.unique(segments):
            mask = segments == seg_id
            coarse_vals = coarse_map[mask]
            valid = coarse_vals[coarse_vals != 255]
            if valid.size == 0:
                coarse_id = 255
            else:
                coarse_id = Counter(valid.tolist()).most_common(1)[0][0]

            pixels = img_rgb[mask]
            mean_rgb = pixels.mean(axis=0).astype(np.uint8)
            records.append(
                {
                    "image_id": image_id,
                    "segment": int(seg_id),
                    "R": int(mean_rgb[0]),
                    "G": int(mean_rgb[1]),
                    "B": int(mean_rgb[2]),
                    "coarse_id": int(coarse_id),
                    "coarse_semantic": COARSE_ID_TO_NAME.get(int(coarse_id), "unknown"),
                }
            )
        return records
