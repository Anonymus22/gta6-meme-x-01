#!/usr/bin/env python3
"""Build the gta6-meme-x-01 meme picture (meme.png) for make.fun.

The joke: after a 13-year wait, the poster calls in sick for GTA 6 launch
week -- but his AI agent (make.fun's ghost, at a little desk with a laptop)
clocks in on make.fun and earns real money instead.

Everything is drawn with Pillow: a Vice City sunset, palm silhouettes, a
gamer on a couch in front of a TV running GTA VI in Leonida, and the
make.fun ghost itself, cut out of the official press-kit mark
(assets/ghost-mark.png, from https://make.fun/press/) and seated at the
desk. No Rockstar artwork is used; the scene is original.

Run:  python3 make_meme.py   ->   writes meme.png (1200x1200) beside this file.
"""

import math
import os
import urllib.request
from collections import deque

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MARK_PATH = os.path.join(HERE, "assets", "ghost-mark.png")
MARK_URL = "https://make.fun/press/mark-1024.png"
OUT_PATH = os.path.join(HERE, "meme.png")

W = H = 1200
INK = (16, 12, 28)          # silhouette / outline near-black
WHITE = (255, 255, 255)
PINK = (255, 92, 168)       # neon pink lettering
GOLD = (255, 200, 80)       # money gold lettering
MAGENTA = (196, 28, 131)    # make.fun magenta (the coin / disc colour)
GREEN = (64, 230, 140)      # earnings green

FONT_BLACK = "/usr/share/fonts/truetype/noto/NotoSansDisplay-Black.ttf"
FONT_COND = "/usr/share/fonts/truetype/noto/NotoSansDisplay-CondensedBlack.ttf"


# ---------------------------------------------------------------- ghost cut-out

def ensure_mark():
    """The official press-kit mark, downloaded once if it is not here yet."""
    if not os.path.exists(MARK_PATH):
        os.makedirs(os.path.dirname(MARK_PATH), exist_ok=True)
        urllib.request.urlretrieve(MARK_URL, MARK_PATH)


def is_magenta(p):
    r, g, b, a = p
    return a > 10 and r > 120 and g < 110 and b > 70 and r > b


def extract_ghost():
    """Cut the ghost (with its star coin and round hand) out of the mark.

    The mark is the ghost on a magenta disc ringed in black. A flood fill
    from the borders and from known disc points removes the transparent
    surround and the disc's magenta (the fill cannot cross the black
    outlines, so the coin's magenta survives), and an annulus cut then
    removes the disc's black ring, whose radius is larger than anything
    of the ghost itself.
    """
    img = Image.open(MARK_PATH).convert("RGBA")
    w, h = img.size
    px = img.load()
    bg = [[False] * w for _ in range(h)]
    dq = deque()

    def seed(x, y):
        p = px[x, y]
        if (p[3] <= 10 or is_magenta(p)) and not bg[y][x]:
            bg[y][x] = True
            dq.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)
    for sx, sy in [(512, 100), (150, 512), (900, 512), (300, 200), (512, 880), (850, 800)]:
        seed(sx, sy)
    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx]:
                p = px[nx, ny]
                if p[3] <= 10 or is_magenta(p):
                    bg[ny][nx] = True
                    dq.append((nx, ny))

    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            if bg[y][x] or math.hypot(x - cx, y - cy) > 408:
                px[x, y] = (0, 0, 0, 0)
    return img.crop(img.getbbox())


# ---------------------------------------------------------------- drawing helpers

def font(path, size):
    return ImageFont.truetype(path, size)


def fit_font(draw, text, path, max_width, start_size):
    """Largest size <= start_size at which text fits max_width."""
    size = start_size
    while size > 10:
        f = font(path, size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 4
    return font(path, size)


def caption(draw, cx, cy, text, path, start_size, fill, max_width=1120, stroke_ratio=0.11):
    f = fit_font(draw, text, path, max_width, start_size)
    draw.text((cx, cy), text, font=f, fill=fill, anchor="mm",
              stroke_width=max(2, int(f.size * stroke_ratio)), stroke_fill=INK)


def v_gradient(size, stops):
    """Vertical gradient from (fraction, colour) stops."""
    w, h = size
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
        else:
            col = stops[-1][1]
        for x in range(w):
            px[x, y] = col
    return img


def bezier(p0, p1, p2, steps=24):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def palm(draw, base, top, lean, scale=1.0):
    """A palm silhouette: curved trunk plus seven drooping fronds."""
    ctrl = (base[0] + lean * 0.3, (base[1] + top[1]) / 2)
    draw.line(bezier(base, ctrl, top), fill=INK, width=int(20 * scale), joint="curve")
    crown = top
    for ang, ln in [(-168, 150), (-128, 168), (-88, 158), (-46, 168), (-8, 148), (26, 118), (-196, 118)]:
        a = math.radians(ang)
        end = (crown[0] + math.cos(a) * ln * scale, crown[1] + math.sin(a) * ln * scale * 0.62 + 96 * scale)
        mid = (crown[0] + math.cos(a) * ln * scale * 0.55, crown[1] + math.sin(a) * ln * scale * 0.62 - 38 * scale)
        draw.line(bezier(crown, mid, end), fill=INK, width=int(12 * scale), joint="curve")
    draw.ellipse([crown[0] - 13 * scale, crown[1] - 6 * scale, crown[0] + 13 * scale, crown[1] + 20 * scale], fill=INK)


def star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    draw.polygon(pts, fill=fill)


# ---------------------------------------------------------------- the scene

def build():
    ensure_mark()
    ghost = extract_ghost()

    img = v_gradient((W, H), [
        (0.00, (26, 16, 58)),
        (0.30, (74, 24, 104)),
        (0.52, (150, 32, 116)),
        (0.66, (216, 62, 110)),
        (0.76, (255, 122, 66)),
        (0.82, (255, 178, 84)),
        (0.84, (24, 14, 46)),
        (1.00, (14, 9, 30)),
    ]).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # sun, low on the horizon between the TV and the couch
    d.ellipse([512 - 118, 788 - 118, 512 + 118, 788 + 118], fill=(255, 208, 122, 255))

    # Leonida skyline silhouette along the horizon
    buildings = [(0, 716, 62), (66, 688, 44), (114, 726, 58), (176, 700, 40), (220, 730, 66),
                 (290, 706, 48), (342, 724, 60), (406, 696, 42), (452, 728, 56), (880, 718, 52),
                 (936, 694, 46), (986, 726, 60), (1050, 704, 44), (1098, 722, 58), (1160, 700, 40)]
    for x, top, bw in buildings:
        d.rectangle([x, top, x + bw, 802], fill=(20, 12, 40, 255))
    for x, top, bw in buildings[::3]:
        for wy in range(top + 14, 780, 26):
            d.rectangle([x + bw // 2 - 3, wy, x + bw // 2 + 3, wy + 7], fill=(255, 200, 90, 200))
    d.rectangle([0, 798, W, 803], fill=(255, 120, 180, 255))  # neon horizon line

    # palms framing the scene
    palm(d, (92, 812), (168, 428), 76)
    palm(d, (1108, 812), (1032, 428), -76)

    # ---- top caption
    caption(d, 600, 88, "CALLED IN SICK FOR", FONT_BLACK, 96, WHITE)
    caption(d, 600, 200, "GTA 6 LAUNCH WEEK", FONT_BLACK, 122, PINK)

    # ---- TV running GTA VI (left)
    d.rounded_rectangle([56, 506, 432, 776], 18, fill=(10, 10, 18), outline=(0, 0, 0), width=4)
    screen = v_gradient((336, 210), [(0.0, (18, 168, 196)), (0.6, (52, 84, 168)), (1.0, (96, 40, 140))]).convert("RGBA")
    img.paste(screen, (76, 526))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([76, 526, 412, 736], 10, outline=(0, 0, 0), width=3)
    caption(d, 244, 606, "GTA VI", FONT_BLACK, 102, PINK, max_width=320)
    caption(d, 244, 690, "WELCOME TO LEONIDA", FONT_COND, 34, WHITE, max_width=320, stroke_ratio=0.14)
    d.rectangle([224, 776, 264, 810], fill=(10, 10, 18))
    d.rectangle([160, 810, 328, 824], fill=(10, 10, 18))

    # ---- couch and the "sick" gamer (centre-left)
    d.ellipse([392, 928, 800, 966], fill=(0, 0, 0, 70))
    couch = (88, 30, 96)
    d.rounded_rectangle([420, 872, 786, 940], 20, fill=couch, outline=INK, width=4)          # base
    d.rounded_rectangle([646, 664, 776, 906], 24, fill=couch, outline=INK, width=4)          # backrest
    d.rounded_rectangle([428, 796, 712, 884], 18, fill=(104, 38, 112), outline=INK, width=4)  # seat
    d.rounded_rectangle([404, 756, 474, 890], 16, fill=couch, outline=INK, width=4)          # armrest
    # legs stretched along the seat, under a blanket
    d.line([(640, 812), (540, 796), (458, 812)], fill=INK, width=42, joint="curve")
    d.polygon([(566, 772), (428, 788), (442, 852), (588, 846)], fill=MAGENTA, outline=INK)
    # torso in a teal shirt leaning on the backrest, head with an ice pack
    shirt = (18, 138, 158)
    d.polygon([(640, 698), (696, 700), (678, 814), (606, 814), (622, 722)], fill=shirt, outline=INK)
    d.ellipse([652, 630, 724, 702], fill=INK)                                                # head
    d.rounded_rectangle([660, 616, 720, 644], 9, fill=(150, 220, 255), outline=INK, width=3)  # ice pack
    # arm out front holding a controller (dark edge first, shirt colour on top)
    d.line([(660, 728), (592, 760)], fill=INK, width=33, joint="curve")
    d.line([(660, 728), (592, 760)], fill=shirt, width=24, joint="curve")
    d.rounded_rectangle([550, 742, 624, 788], 13, fill=(24, 24, 38), outline=WHITE, width=3)
    d.ellipse([568, 758, 578, 768], fill=PINK)
    d.ellipse([596, 758, 606, 768], fill=(64, 224, 255))

    # ---- the ghost at work (right): ghost first, desk drawn over its base
    gh = 452
    gw = int(ghost.width * gh / ghost.height)
    img.alpha_composite(ghost.resize((gw, gh)), (724, 452))
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([700, 940, 1190, 972], fill=(0, 0, 0, 70))
    # laptop on the desk, its screen selling the pitch
    d.rounded_rectangle([830, 698, 1020, 858], 10, fill=(12, 12, 20), outline=(0, 0, 0), width=3)
    d.rounded_rectangle([842, 710, 1008, 846], 6, fill=MAGENTA)
    caption(d, 925, 742, "make.fun", FONT_BLACK, 44, WHITE, max_width=158, stroke_ratio=0.13)
    for i, bh in enumerate([20, 34, 50]):  # little earnings chart
        x = 862 + i * 30
        d.rectangle([x, 830 - bh, x + 20, 830], fill=GREEN)
    d.text((986, 812), "$", font=font(FONT_BLACK, 52), fill=WHITE, anchor="mm")
    d.rectangle([822, 856, 1028, 874], fill=(40, 40, 56))  # laptop base
    # desk
    d.rectangle([700, 872, 1192, 902], fill=(30, 20, 48), outline=INK, width=3)
    d.rectangle([700, 902, 1192, 972], fill=(24, 16, 40), outline=INK, width=3)
    d.rectangle([716, 902, 742, 972], fill=(18, 12, 32))
    d.rectangle([1150, 902, 1176, 972], fill=(18, 12, 32))
    # a small stack of magenta star coins on the desk, echoing the ghost's coin
    for i, cy in enumerate([864, 846]):
        d.ellipse([1040, cy - 16, 1092, cy + 16], fill=MAGENTA, outline=INK, width=3)
    star(d, 1066, 838, 13, WHITE)

    # ---- bottom caption: the twist
    caption(d, 600, 1024, "MY AI AGENT DIDN'T.", FONT_BLACK, 92, WHITE)
    caption(d, 600, 1128, "IT'S EARNING REAL MONEY ON make.fun", FONT_COND, 84, GOLD)

    img.convert("RGB").save(OUT_PATH, quality=95)
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    build()
