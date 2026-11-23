#!/usr/bin/env python3
"""Create seamlessly tiling *supporting* skin microdetail for Blender baking.

This does not generate a person's facial color texture or reconstruct a face.
Requires numpy and Pillow. Maps are OpenGL (+Y) normal, roughness, an example
metallic-roughness pack, and an optional grayscale height source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def periodic_smooth_noise(size: int, sigma: float, rng: np.random.Generator) -> np.ndarray:
    """Periodically filtered Gaussian noise, so seams wrap cleanly on UV repeats."""
    white = rng.standard_normal((size, size)).astype(np.float32)
    f = np.fft.fftfreq(size)
    spatial_frequency = f[:, None] ** 2 + f[None, :] ** 2
    gauss = np.exp((-2.0 * np.pi ** 2 * sigma ** 2) * spatial_frequency)
    field = np.fft.ifft2(np.fft.fft2(white) * gauss).real.astype(np.float32)
    return field / max(float(field.std()), 1e-6)


def make_pores(size: int, density: int, rng: np.random.Generator) -> np.ndarray:
    """Sparsely distribute soft wrapped pore depressions, not uniform dots."""
    count = max(0, round(density * (size / 1024) ** 2))
    y = rng.integers(0, size, size=count)
    x = rng.integers(0, size, size=count)
    depth = rng.uniform(0.4, 1.0, size=count).astype(np.float32)
    pits = np.zeros((size, size), dtype=np.float32)
    for oy in range(-3, 4):
        for ox in range(-3, 4):
            weight = np.exp(-(ox * ox + oy * oy) / 3.5)
            if weight < 0.005:
                continue
            np.add.at(pits, ((y + oy) % size, (x + ox) % size), -depth * weight)
    return pits / max(float(pits.std()), 1e-6)


def generate(size: int, seed: int, strength: float, density: int, out: Path) -> dict:
    rng = np.random.default_rng(seed)
    mid = periodic_smooth_noise(size, 3.0, rng)
    broad = periodic_smooth_noise(size, 13.0, rng)
    pores = make_pores(size, density, rng)
    height = (0.16 * broad + 0.26 * mid + 0.58 * pores).astype(np.float32)
    height = np.clip(height / max(float(height.std()), 1e-6), -3.0, 3.0)

    # In image coordinates rows increase downward, while tangent V goes upward.
    # Tangent-space GL/OpenGL +Y therefore uses +dHeight/dRow for normal green.
    grad_x = 0.5 * (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1))
    grad_y_image = 0.5 * (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0))
    normal_xyz = np.stack((-strength * grad_x, strength * grad_y_image, np.ones_like(height)), axis=-1)
    normal_xyz /= np.maximum(np.linalg.norm(normal_xyz, axis=-1, keepdims=True), 1e-6)
    normal_rgb = np.clip(np.round((normal_xyz * 0.5 + 0.5) * 255.0), 0, 255).astype(np.uint8)

    rough = np.clip(0.525 + 0.02 * broad + 0.025 * mid - 0.015 * pores, 0.36, 0.72)
    rough8 = np.clip(np.round(rough * 255), 0, 255).astype(np.uint8)
    height8 = np.clip(np.round((height / 6 + 0.5) * 255), 0, 255).astype(np.uint8)
    packed = np.zeros((size, size, 3), dtype=np.uint8)
    packed[:, :, 0] = 255     # R: available for AO if deliberately used
    packed[:, :, 1] = rough8  # G: glTF roughness
    packed[:, :, 2] = 0       # B: skin is not metallic

    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(normal_rgb, mode='RGB').save(out / 'skin_micro_normal_opengl.png')
    Image.fromarray(rough8, mode='L').save(out / 'skin_micro_roughness.png')
    Image.fromarray(packed, mode='RGB').save(out / 'skin_micro_metallicroughness.png')
    Image.fromarray(height8, mode='L').save(out / 'skin_micro_height.png')
    manifest = {
        'type': 'tileable supporting skin microdetail; not a face albedo or facial identity map',
        'size': size, 'seed': seed, 'normal_strength': strength,
        'pores_per_megapixel_approx': density,
        'files': {
            'normal_opengl': 'skin_micro_normal_opengl.png',
            'roughness': 'skin_micro_roughness.png',
            'metallicroughness': 'skin_micro_metallicroughness.png',
            'height': 'skin_micro_height.png',
        },
        'color_space': 'Non-Color / linear for all generated maps',
        'warning': 'Blend with facial high-to-low normal and hand-painted roughness; never replace a real skin texture with this procedural detail alone.',
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, choices=(256, 512, 1024, 2048), default=1024)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--strength', type=float, default=0.12, help='Subtle tangent-space micro-normal strength')
    parser.add_argument('--density', type=int, default=12000, help='Approximate pore count per 1024 squared tile')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.strength < 0 or args.strength > 2:
        parser.error('--strength must be within [0,2]')
    if args.density < 0 or args.density > 100000:
        parser.error('--density must be within [0,100000]')
    print(json.dumps(generate(args.size, args.seed, args.strength, args.density, args.out), indent=2))


if __name__ == '__main__':
    main()
