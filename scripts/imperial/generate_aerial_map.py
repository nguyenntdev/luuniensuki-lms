#!/usr/bin/env python3
"""Generate authentic high-resolution placeholder aerial image for STTTNNĐ Đại Nội Huế.
Creates a 4096x3072 WebP map showing the architectural layout of the Imperial City and Purple Forbidden City.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def generate_aerial_map():
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "frontend" / "public" / "assets" / "imperial" / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dai-noi-aerial-v1.webp"

    w, h = 4096, 3072
    # Base terrain: gentle warm parchment tone
    img = Image.new("RGB", (w, h), (235, 228, 212))
    draw = ImageDraw.Draw(img)

    # 1. Subtle background grid / coordinates
    grid_color = (220, 212, 195)
    for x in range(0, w, 256):
        draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
    for y in range(0, h, 256):
        draw.line([(0, y), (w, y)], fill=grid_color, width=1)

    # 2. Outer vegetation / gardens surrounding the Citadel
    garden_color = (205, 218, 195)
    draw.rectangle([(200, 150), (w - 200, h - 150)], fill=garden_color)

    # 3. Outer moat (Hộ Thành Hào)
    moat_color = (165, 195, 205)
    moat_inner = (225, 220, 205)
    draw.rectangle([(400, 250), (w - 400, h - 250)], fill=moat_color)
    draw.rectangle([(550, 350), (w - 550, h - 350)], fill=moat_inner)

    # 4. Citadel Brick Wall (Hoàng Thành)
    wall_color = (130, 95, 75)
    draw.rectangle([(550, 350), (w - 550, h - 350)], outline=wall_color, width=18)

    # 5. Inner courtyards and grass plazas
    plaza_grass = (210, 220, 198)
    plaza_stone = (228, 222, 210)
    draw.rectangle([(620, 420), (w - 620, h - 420)], fill=plaza_grass)

    # 6. Lakes: Hồ Thái Dịch (around Cầu Trung Đạo), Hồ Ngũ Dực, Kim Thủy Trì
    # Hồ Thái Dịch: between Ngọ Môn (v=0.85) and Điện Thái Hòa (v=0.64) -> y around 2300-2450
    water_blue = (150, 185, 198)
    water_border = (120, 160, 175)
    # Hồ Thái Dịch left and right
    draw.rectangle([(1100, 2300), (1950, 2430)], fill=water_blue, outline=water_border, width=4)
    draw.rectangle([(2150, 2300), (3000, 2430)], fill=water_blue, outline=water_border, width=4)
    # Hồ Tịnh Tâm / Cung Diên Thọ lakes
    draw.rectangle([(1100, 1150), (1450, 1320)], fill=water_blue, outline=water_border, width=3)
    draw.rectangle([(1050, 750), (1400, 920)], fill=water_blue, outline=water_border, width=3)

    # 7. Central Ceremonial Axis Paving (Trục Thần Đạo)
    stone_road = (215, 208, 192)
    road_border = (185, 175, 155)
    draw.rectangle([(1980, 500), (2120, 2750)], fill=stone_road, outline=road_border, width=3)

    # 8. Purple Forbidden City Wall (Tử Cấm Thành)
    # Bounds: approx u from 0.28 to 0.72, v from 0.18 to 0.58
    pfc_x1 = int(w * 0.28)
    pfc_y1 = int(h * 0.18)
    pfc_x2 = int(w * 0.72)
    pfc_y2 = int(h * 0.58)
    pfc_wall_color = (155, 65, 55)
    draw.rectangle([(pfc_x1, pfc_y1), (pfc_x2, pfc_y2)], fill=(222, 215, 200), outline=pfc_wall_color, width=12)

    # 9. Architectural Complexes footprints (16 Monuments)
    manifest_path = repo_root / "data" / "imperial" / "aerial_map_manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    roof_gold = (210, 155, 45)
    roof_yellow = (230, 185, 60)
    roof_tile = (175, 75, 55)
    roof_ruin = (160, 155, 145)

    for anno in manifest_data["initial_annotations"]:
        u = anno["u"]
        v = anno["v"]
        cx = int(u * w)
        cy = int(v * h)
        name = anno["name_vi"]
        style = anno.get("marker_style", "")

        # Draw building footprint
        if "ruin" in style:
            # Dotted or pale footprint for ruins (Điện Cần Chánh, Điện Phụng Tiên, Đại Cung Môn)
            bw, bh = 140, 90
            draw.rectangle(
                [(cx - bw, cy - bh), (cx + bw, cy + bh)],
                fill=(210, 205, 195),
                outline=roof_ruin,
                width=3,
            )
            # Foundation pillar stones
            for px in [-80, -40, 0, 40, 80]:
                for py in [-50, 0, 50]:
                    draw.ellipse(
                        [(cx + px - 5, cy + py - 5), (cx + px + 5, cy + py + 5)],
                        fill=(140, 135, 125),
                    )
        elif "bridge" in style:
            # Cầu Trung Đạo
            bw, bh = 70, 110
            draw.rectangle([(cx - bw, cy - bh), (cx + bw, cy + bh)], fill=(225, 225, 220), outline=(130, 130, 130), width=4)
            # Bridge railing posts
            for ry in range(cy - bh, cy + bh, 20):
                draw.rectangle([(cx - bw, ry), (cx - bw + 8, ry + 10)], fill=(160, 160, 160))
                draw.rectangle([(cx + bw - 8, ry), (cx + bw, ry + 10)], fill=(160, 160, 160))
        elif "ceremonial_court" in style:
            # Sân Đại Triều Nghi: two tiers
            draw.rectangle([(cx - 240, cy - 80), (cx + 240, cy + 80)], fill=(232, 225, 210), outline=(180, 165, 140), width=3)
            draw.line([(cx - 240, cy), (cx + 240, cy)], fill=(170, 155, 130), width=2)
            # Phẩm tán rows (mandarin markers)
            for ox in [-180, -120, -60, 60, 120, 180]:
                draw.rectangle([(cx + ox - 4, cy - 50), (cx + ox + 4, cy - 42)], fill=(130, 120, 110))
                draw.rectangle([(cx + ox - 4, cy + 30), (cx + ox + 4, cy + 38)], fill=(130, 120, 110))
        elif "monument_primary" in style or "restored_palace" in style:
            # Primary palaces (Điện Thái Hòa, Ngọ Môn, Điện Kiến Trung)
            bw, bh = 180, 120 if "kien-trung" not in anno["site_slug"] else 150
            draw.rectangle([(cx - bw - 15, cy - bh - 15), (cx + bw + 15, cy + bh + 15)], fill=(205, 195, 180))
            draw.rectangle([(cx - bw, cy - bh), (cx + bw, cy + bh)], fill=roof_gold, outline=(150, 100, 20), width=5)
            # Inner ridge roof
            draw.rectangle([(cx - bw + 30, cy - bh + 25), (cx + bw - 30, cy + bh - 25)], fill=roof_yellow, outline=(180, 120, 25), width=3)
        else:
            # Temples, pavilions, residences
            bw, bh = 120, 80
            draw.rectangle([(cx - bw - 10, cy - bh - 10), (cx + bw + 10, cy + bh + 10)], fill=(210, 200, 185))
            draw.rectangle([(cx - bw, cy - bh), (cx + bw, cy + bh)], fill=roof_tile, outline=(120, 50, 35), width=4)

        # Draw subtle label box
        label_bg = (255, 255, 250)
        draw.rectangle([(cx - 80, cy + 95), (cx + 80, cy + 125)], fill=label_bg, outline=(150, 130, 110), width=1)

    # 10. Title Cartouche (Top Left)
    cart_x, cart_y = 650, 480
    draw.rectangle([(cart_x, cart_y), (cart_x + 950, cart_y + 240)], fill=(250, 246, 238), outline=(120, 90, 60), width=4)
    draw.rectangle([(cart_x + 8, cart_y + 8), (cart_x + 942, cart_y + 232)], outline=(190, 160, 120), width=2)

    # 11. Compass Rose / Orientation Indicator (Top Right)
    compass_x, compass_y = w - 850, 580
    r = 80
    draw.ellipse([(compass_x - r, compass_y - r), (compass_x + r, compass_y + r)], outline=(120, 90, 60), width=3)
    # North arrow pointing toward top (North)
    draw.polygon([(compass_x, compass_y - r - 25), (compass_x - 18, compass_y + 10), (compass_x, compass_y - 10)], fill=(160, 40, 30))
    draw.polygon([(compass_x, compass_y - r - 25), (compass_x + 18, compass_y + 10), (compass_x, compass_y - 10)], fill=(210, 80, 70))
    draw.polygon([(compass_x, compass_y + r + 20), (compass_x - 18, compass_y - 10), (compass_x, compass_y + 10)], fill=(120, 120, 120))
    draw.polygon([(compass_x, compass_y + r + 20), (compass_x + 18, compass_y - 10), (compass_x, compass_y + 10)], fill=(180, 180, 180))

    # Save as WebP
    img.save(out_path, format="WEBP", quality=85, method=6)

    # Compute sha256
    file_bytes = out_path.read_bytes()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    print(f"Generated {out_path} ({w}x{h})")
    print(f"SHA-256: {sha256_hash}")

    # Synchronize manifest sha256
    manifest_data["image_sha256"] = sha256_hash
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {manifest_path} image_sha256 to {sha256_hash}")


if __name__ == "__main__":
    generate_aerial_map()
