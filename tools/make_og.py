#!/usr/bin/env python3
"""Writes assets/og.png (1200x630 social share image). Run once; the PNG is committed."""
import math, os
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 630
BG, GOLD, TXT, MUT = (10, 12, 16), (242, 184, 75), (233, 237, 243), (142, 153, 170)
im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
F = "/usr/share/fonts/truetype/dejavu/"
big = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 78); mid = ImageFont.truetype(F + "DejaVuSans.ttf", 36); small = ImageFont.truetype(F + "DejaVuSansMono.ttf", 28)
cx, cy, r = 150, 200, 70
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=12)
d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=GOLD)
for a in range(0, 180, 45):
    x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
    d.line([cx - x, cy - y, cx + x, cy + y], fill=GOLD, width=5)
d.text((260, 150), "FLYWHEEL", font=big, fill=TXT); d.text((260 + d.textlength("FLYWHEEL ", font=big), 150), "CLOCK", font=big, fill=GOLD)
d.text((80, 340), "How the biggest companies and", font=mid, fill=TXT)
d.text((80, 390), "commodities actually work.", font=mid, fill=TXT)
d.text((80, 500), "Live money clocks. Every figure sourced.", font=small, fill=MUT)
d.text((80, 545), "flywheelclock.com", font=small, fill=GOLD)
im.save(os.path.join(os.path.dirname(__file__), "..", "assets", "og.png"), optimize=True)
