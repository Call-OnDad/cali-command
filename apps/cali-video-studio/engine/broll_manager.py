"""
broll_manager.py - Generates and manages high-retention 9:16 vertical B-roll visual plates
and motion assets for faceless YouTube Shorts and TikToks.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
BROLL_DIR = BASE_DIR / "assets" / "broll"
BROLL_DIR.mkdir(parents=True, exist_ok=True)

THEME_COLORS = {
    "diy_trades": {
        "bg_top": (15, 23, 42),      # Dark slate
        "bg_bottom": (30, 41, 59),   # Slate
        "accent": (245, 158, 11),     # Amber / Warning yellow
        "secondary": (14, 165, 233),  # Cyan
        "icon": "[TRADES]",
        "title": "UK HOME & TRADES DIAGNOSTIC"
    },
    "budget_finance": {
        "bg_top": (6, 78, 59),       # Deep emerald
        "bg_bottom": (15, 23, 42),   # Dark slate
        "accent": (16, 185, 129),    # Bright emerald
        "secondary": (234, 179, 8),   # Gold
        "icon": "[FINANCE]",
        "title": "HOUSEHOLD BUDGET & SURVIVAL"
    },
    "consumer_rights": {
        "bg_top": (15, 23, 42),      # Deep navy
        "bg_bottom": (67, 56, 202),  # Indigo
        "accent": (239, 68, 68),     # Alert red
        "secondary": (56, 189, 248),  # Sky blue
        "icon": "[RIGHTS]",
        "title": "UK CONSUMER RIGHTS & BILLS"
    },
    "tech_agency": {
        "bg_top": (10, 14, 23),      # Charcoal
        "bg_bottom": (19, 78, 74),   # Deep teal
        "accent": (20, 184, 166),    # Teal
        "secondary": (99, 102, 241), # Indigo
        "icon": "[STUDIO]",
        "title": "CALI INTELLIGENT SYSTEMS"
    }
}

def create_gradient_plate(width: int, height: int, color_top: tuple, color_bottom: tuple) -> Image.Image:
    """Creates a smooth vertical gradient base image."""
    base = Image.new("RGB", (width, height), color_top)
    top_r, top_g, top_b = color_top
    bot_r, bot_g, bot_b = color_bottom
    
    draw = ImageDraw.Draw(base)
    for y in range(height):
        factor = y / height
        r = int(top_r + (bot_r - top_r) * factor)
        g = int(top_g + (bot_g - top_g) * factor)
        b = int(top_b + (bot_b - top_b) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base

def generate_faceless_broll_scene(
    theme: str,
    scene_index: int,
    headline: str,
    guide_slug: str = "boiler-pressure-dropping",
    width: int = 1080,
    height: int = 1920
) -> Path:
    """
    Renders a high-retention 9:16 vertical visual plate designed specifically
    for faceless short-form video retention (YouTube Shorts / TikTok / Reels).
    """
    theme_cfg = THEME_COLORS.get(theme, THEME_COLORS["diy_trades"])
    out_file = BROLL_DIR / f"{theme}_scene_{scene_index}.png"
    
    # 1. Base Gradient
    img = create_gradient_plate(width, height, theme_cfg["bg_top"], theme_cfg["bg_bottom"])
    draw = ImageDraw.Draw(img)

    # 2. Modern Grid & Blueprint Pattern
    grid_spacing = 80
    grid_color = (255, 255, 255, 12)
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill=(40, 50, 70))
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill=(40, 50, 70))

    # 3. Top Channel Header Bar
    draw.rectangle([(60, 100), (width - 60, 200)], fill=(15, 23, 42), outline=theme_cfg["accent"], width=3)
    
    try:
        font_header = ImageFont.truetype("arialbd.ttf", 36)
        font_headline = ImageFont.truetype("arialbd.ttf", 52)
        font_badge = ImageFont.truetype("arialbd.ttf", 30)
        font_cta = ImageFont.truetype("arialbd.ttf", 32)
        font_sub = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font_header = font_headline = font_badge = font_cta = font_sub = ImageFont.load_default()

    # Draw Top Header Text
    draw.text((width / 2, 150), f"{theme_cfg['icon']}  {theme_cfg['title']}", font=font_header, fill=(255, 255, 255), anchor="mm")

    # 4. Central Diagnostic / Info Card (Above Subtitle Safe Zone)
    card_top = 280
    card_bottom = 980
    draw.rounded_rectangle([(70, card_top), (width - 70, card_bottom)], radius=24, fill=(17, 24, 39), outline=(55, 65, 81), width=4)
    
    # Category / Alert Pill
    pill_w = 420
    pill_h = 56
    draw.rounded_rectangle([(width/2 - pill_w/2, card_top + 40), (width/2 + pill_w/2, card_top + 40 + pill_h)], radius=12, fill=theme_cfg["accent"])
    draw.text((width / 2, card_top + 40 + pill_h/2), f"STEP 0{scene_index}: ESSENTIAL ACTION", font=font_badge, fill=(15, 23, 42), anchor="mm")

    # Topic Headline wrapped in card
    words = headline.split()
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(" ".join(curr)) > 26:
            lines.append(" ".join(curr[:-1]))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    y_text = card_top + 160
    for line in lines[:4]:
        draw.text((width / 2, y_text), line, font=font_headline, fill=(255, 255, 255), anchor="mm")
        y_text += 70

    # Modern Infographic Elements / Checkpoints
    checks = [
        "● Safe Isolation: Verified Zero Risk",
        "● Visual Check: Gauge between 1.0 - 1.5 Bar",
        "● Instant Fix: Do not call emergency until checked"
    ]
    if scene_index == 2:
        checks = [
            "● Filling Loop: Locate braided silver hose",
            "● Dual Valves: Turn 90 degrees simultaneously",
            "● Target: Stop immediately when needle hits 1.3"
        ]
    elif scene_index >= 3:
        checks = [
            "● External Pipe: Clear 21.5mm ice plug with warm water",
            "● Fair UK Benchmark: Standard reset fee is £60 - £85",
            "● Complete Print-Off: Download full A4 checklist"
        ]

    check_y = y_text + 40
    for c in checks:
        draw.rounded_rectangle([(110, check_y - 8), (width - 110, check_y + 44)], radius=8, fill=(31, 41, 55))
        draw.text((130, check_y + 16), c, font=font_sub, fill=(229, 231, 235), anchor="lm")
        check_y += 68

    # 5. Pinned Lower-Third Shop Banner (Above TikTok/Shorts UI controls)
    banner_top = height - 365
    banner_bottom = height - 225
    draw.rounded_rectangle([(60, banner_top), (width - 60, banner_bottom)], radius=18, fill=(20, 184, 166), outline=(255, 255, 255), width=3)
    
    # Banner Text - Line 1: Badge Title
    draw.text((width / 2, banner_top + 38), "OFFICIAL PRINT-OFF CHECKLIST • £1.99", font=font_badge, fill=(15, 23, 42), anchor="mm")

    # Banner Text - Line 2: URL Callout with Dynamic Font Scaling to Guarantee Zero Overflow
    short_slug = guide_slug[:30].rstrip("-")
    cta_display = f"Get A4 Sheet: call-on.shop/guides/{short_slug}"
    
    cta_size = 28
    curr_cta_font = font_cta
    while cta_size >= 16:
        try:
            curr_cta_font = ImageFont.truetype("arialbd.ttf", cta_size)
        except Exception:
            curr_cta_font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), cta_display, font=curr_cta_font)
        if (bbox[2] - bbox[0]) <= (width - 180): # Must fit within 900px safe width
            break
        cta_size -= 2

    draw.text((width / 2, banner_top + 88), cta_display, font=curr_cta_font, fill=(15, 23, 42), anchor="mm")

    # 6. Subtle Safety Watermark at Bottom
    draw.text((width / 2, height - 120), "Call-On Dad & Mom Community Network | Verified Non-Profit Standards", font=font_sub, fill=(156, 163, 175), anchor="mm")

    img.save(out_file)
    return out_file

def prepare_faceless_storyboard(
    theme: str,
    topic: str,
    guide_slug: str,
    duration: float
) -> list:
    """
    Creates a multi-scene storyboard of 3 alternating high-retention visual plates
    timed to match the total audio narration duration.
    """
    scene_dur = duration / 3.0
    guide_cta = f"call-on.shop/guides/{guide_slug}"
    
    scenes = []
    for i in range(1, 4):
        plate_path = generate_faceless_broll_scene(
            theme=theme,
            scene_index=i,
            headline=topic if i == 1 else ("Diagnostic Reset & Pressure Lockout" if i == 2 else "Fair UK Price & Action Plan"),
            guide_slug=guide_slug
        )
        scenes.append({
            "image_path": str(plate_path).replace("\\", "/"),
            "duration": round(scene_dur, 2)
        })
    return scenes
