import os
import argparse
from typing import Dict, List, Tuple

import cv2
import numpy as np


def read_image(image_path: str) -> np.ndarray:
    """读取图像并转换为 RGB。"""
    raw = np.fromfile(image_path, dtype=np.uint8)
    img_bgr = cv2.imdecode(raw, cv2.IMREAD_COLOR) if raw.size else None
    if img_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def save_image(image_path: str, img_rgb: np.ndarray) -> None:
    """保存 RGB 图像。"""
    img_bgr = cv2.cvtColor(np.clip(img_rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    ext = os.path.splitext(image_path)[1] or ".png"
    ok, encoded = cv2.imencode(ext, img_bgr)
    if not ok:
        raise RuntimeError(f"Cannot encode image: {image_path}")
    encoded.tofile(image_path)


def gray_world_white_balance(img_rgb: np.ndarray) -> np.ndarray:
    """灰世界白平衡。"""
    img = img_rgb.astype(np.float32)

    mean_r = np.mean(img[:, :, 0])
    mean_g = np.mean(img[:, :, 1])
    mean_b = np.mean(img[:, :, 2])
    mean_gray = (mean_r + mean_g + mean_b) / 3.0

    img[:, :, 0] *= mean_gray / (mean_r + 1e-6)
    img[:, :, 1] *= mean_gray / (mean_g + 1e-6)
    img[:, :, 2] *= mean_gray / (mean_b + 1e-6)

    return np.clip(img, 0, 255).astype(np.uint8)


def single_scale_retinex(img: np.ndarray, sigma: float) -> np.ndarray:
    """单尺度 Retinex。"""
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return np.log10(img + 1.0) - np.log10(blur + 1.0)


def multi_scale_retinex(img: np.ndarray, sigma_list: list) -> np.ndarray:
    """多尺度 Retinex。"""
    retinex = np.zeros_like(img, dtype=np.float32)
    for sigma in sigma_list:
        retinex += single_scale_retinex(img, sigma)
    return retinex / len(sigma_list)


def color_restoration(img: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """MSRCR 颜色恢复项。"""
    img_sum = np.sum(img, axis=2, keepdims=True)
    return beta * (np.log10(alpha * img + 1.0) - np.log10(img_sum + 1.0))


def simplest_color_balance(img: np.ndarray, low_clip: float, high_clip: float) -> np.ndarray:
    """简单色彩平衡。"""
    result = np.zeros_like(img, dtype=np.float32)

    for c in range(img.shape[2]):
        channel = img[:, :, c]
        low_val = np.percentile(channel, low_clip)
        high_val = np.percentile(channel, 100.0 - high_clip)

        if high_val - low_val < 1e-6:
            result[:, :, c] = np.clip(channel, 0, 255)
        else:
            channel = np.clip(channel, low_val, high_val)
            result[:, :, c] = (channel - low_val) / (high_val - low_val) * 255.0

    return result


def extract_image_features(img_rgb: np.ndarray) -> dict:
    """
    提取用于判断 MSRCR 强度档位的图像特征。
    返回:
        mean_v: 平均亮度
        dark_ratio: 暗部比例
        texture_strength: 纹理强度
    """
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    v = hsv[:, :, 2].astype(np.float32)

    mean_v = float(np.mean(v))
    dark_ratio = float(np.mean(v < 70))

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    texture_strength = float(np.std(lap))

    return {
        "mean_v": mean_v,
        "dark_ratio": dark_ratio,
        "texture_strength": texture_strength,
    }


def choose_msrcr_params(features: Dict) -> Tuple[str, Dict]:
    """
    根据图像特征自动选择弱/中/强三档参数。
    规则说明:
    - 图像偏暗且暗部比例高 -> 强
    - 图像中等偏暗或光照一般 -> 中
    - 图像较亮或纹理复杂 -> 弱
    """
    mean_v = features["mean_v"]
    dark_ratio = features["dark_ratio"]
    texture_strength = features["texture_strength"]

    # 弱参数：更稳，更适合颜色提取
    weak = {
        "sigma_list": [50, 120, 250],
        "alpha": 100.0,
        "beta": 18.0,
        "gain": 110.0,
        "offset": 8.0,
        "low_clip": 1.0,
        "high_clip": 1.0,
    }

    # 中参数：折中
    medium = {
        "sigma_list": [30, 100, 200],
        "alpha": 110.0,
        "beta": 28.0,
        "gain": 145.0,
        "offset": 12.0,
        "low_clip": 1.0,
        "high_clip": 1.0,
    }

    # 强参数：适合较暗场景
    strong = {
        "sigma_list": [20, 80, 180],
        "alpha": 125.0,
        "beta": 38.0,
        "gain": 180.0,
        "offset": 18.0,
        "low_clip": 1.0,
        "high_clip": 1.0,
    }

    # 纹理复杂时，尽量避免过强增强
    if texture_strength > 35:
        if mean_v < 95 and dark_ratio > 0.35:
            return "medium", medium
        return "weak", weak

    # 一般规则
    if mean_v < 90 and dark_ratio > 0.40:
        return "strong", strong
    elif mean_v < 130 or dark_ratio > 0.25:
        return "medium", medium
    else:
        return "weak", weak


def msrcr(img_rgb: np.ndarray, params: dict) -> np.ndarray:
    """按给定参数执行 MSRCR。"""
    img = img_rgb.astype(np.float32) + 1.0

    msr = multi_scale_retinex(img, params["sigma_list"])
    cr = color_restoration(img, params["alpha"], params["beta"])
    out = params["gain"] * (msr * cr + params["offset"] / 255.0)

    for c in range(out.shape[2]):
        channel = out[:, :, c]
        out[:, :, c] = (channel - np.min(channel)) / (np.max(channel) - np.min(channel) + 1e-6) * 255.0

    out = simplest_color_balance(out, params["low_clip"], params["high_clip"])
    return np.clip(out, 0, 255).astype(np.uint8)


def process_image(image_path: str, output_dir: str) -> None:
    """单张图像处理：白平衡 -> 特征分析 -> 自动选档 -> MSRCR。"""
    os.makedirs(output_dir, exist_ok=True)

    img = read_image(image_path)
    wb_img = gray_world_white_balance(img)

    features = extract_image_features(wb_img)
    level, params = choose_msrcr_params(features)

    msrcr_img = msrcr(wb_img, params)

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    save_image(os.path.join(output_dir, f"{base_name}_wb.png"), wb_img)
    save_image(os.path.join(output_dir, f"{base_name}_msrcr_{level}.png"), msrcr_img)

    print("Image features:", features)
    print("Selected level:", level)
    print("Selected params:", params)


def process_image_to_path(image_path: str, output_path: str) -> str:
    """处理单张图并保存到指定路径，返回所选参数档位。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    img = read_image(image_path)
    wb_img = gray_world_white_balance(img)
    features = extract_image_features(wb_img)
    level, params = choose_msrcr_params(features)
    msrcr_img = msrcr(wb_img, params)
    save_image(output_path, msrcr_img)
    return level


def iter_image_files(root_dir: str, recursive: bool = False) -> List[str]:
    """收集图像文件路径，默认只扫描当前目录。"""
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    image_paths: List[str] = []
    if recursive:
        for current_root, _, files in os.walk(root_dir):
            for name in files:
                if os.path.splitext(name)[1].lower() in exts:
                    image_paths.append(os.path.join(current_root, name))
    else:
        for name in os.listdir(root_dir):
            path = os.path.join(root_dir, name)
            if os.path.isfile(path) and os.path.splitext(name)[1].lower() in exts:
                image_paths.append(path)
    return image_paths


def process_dataset(
    data_root: str,
    img_dir_name: str = "img",
    out_dir_name: str = "enhanced",
    recursive: bool = False,
) -> None:
    """
    处理 data_root 下每个地区目录中的 img 子目录，
    并把结果保存到与 img 同级的 enhanced 子目录。
    """
    if not os.path.isdir(data_root):
        raise FileNotFoundError(f"Data root not found: {data_root}")

    region_dirs = [
        os.path.join(data_root, name)
        for name in sorted(os.listdir(data_root))
        if os.path.isdir(os.path.join(data_root, name))
    ]

    total_images = 0
    total_ok = 0

    for region_dir in region_dirs:
        region_name = os.path.basename(region_dir)
        img_dir = os.path.join(region_dir, img_dir_name)
        out_dir = os.path.join(region_dir, out_dir_name)

        if not os.path.isdir(img_dir):
            print(f"[skip] {region_name}: no '{img_dir_name}' directory")
            continue

        image_paths = iter_image_files(img_dir, recursive=recursive)
        if not image_paths:
            print(f"[skip] {region_name}: no images under '{img_dir_name}'")
            continue

        region_ok = 0
        print(f"[region] {region_name}: {len(image_paths)} images")

        for src_path in image_paths:
            total_images += 1
            rel_path = os.path.relpath(src_path, img_dir)
            dst_path = os.path.join(out_dir, rel_path)

            try:
                level = process_image_to_path(src_path, dst_path)
                region_ok += 1
                total_ok += 1
                print(f"  [ok] {rel_path} -> level={level}")
            except Exception as e:
                print(f"  [fail] {rel_path}: {e}")

        print(f"[done] {region_name}: {region_ok}/{len(image_paths)}")

    print("=" * 60)
    print(f"All done: {total_ok}/{total_images} images processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch enhance images with Gray-World + MSRCR.")
    parser.add_argument(
        "--data-root",
        type=str,
        default=r"E:\code\data",
        help="Path to data root directory (contains region folders).",
    )
    parser.add_argument(
        "--img-dir-name",
        type=str,
        default="img",
        help="Image folder name under each region directory.",
    )
    parser.add_argument(
        "--out-dir-name",
        type=str,
        default="enhanced",
        help="Output folder name (sibling of img).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively process images under img/**.",
    )
    args = parser.parse_args()

    process_dataset(
        data_root=args.data_root,
        img_dir_name=args.img_dir_name,
        out_dir_name=args.out_dir_name,
        recursive=args.recursive,
    )
