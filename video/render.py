"""Certainty vs Chance: LinkedIn film, 1080x1350, 30 fps.

Design: editorial data-journalism. Warm paper, ink text, left-aligned on a 90 px margin grid,
running header and source line on every frame. EB Garamond headlines and Inter labels (as DeskBar).
Colour carries meaning and nothing else: OCHRE = chance (prizes), TEAL = certainty (guaranteed rewards).
Every number is read from the project's data files.
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1350, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "video", "fonts")
OUT = os.path.join(ROOT, "video", "out")
os.makedirs(OUT, exist_ok=True)

PAPER = (245, 242, 235)
INK = (22, 22, 24)
MUTED = (112, 108, 100)
FAINT = (160, 155, 146)
RULE = (218, 213, 203)
CHANCE = (196, 130, 22)     # ochre
CERT = (16, 98, 112)        # deep teal
M = 90                      # outer margin
SS = 2                      # supersampling for charts


# ---------- fonts ----------
@lru_cache(None)
def serif(size, italic=False, weight=400):
    f = ImageFont.truetype(f"{FONTS}/EBGaramond{'-Italic' if italic else ''}[wght].ttf", int(size))
    f.set_variation_by_axes([weight])
    return f


@lru_cache(None)
def sans(size, weight=400):
    f = ImageFont.truetype(f"{FONTS}/Inter.ttf", int(size))
    f.set_variation_by_axes([min(max(size, 14), 32), weight])
    return f


clamp = lambda x: max(0.0, min(1.0, x))
ease_out = lambda x: 1 - (1 - clamp(x)) ** 3
ease = lambda x: (lambda c: c * c * (3 - 2 * c))(clamp(x))


def mix(c, a, bg=PAPER):
    """Colour c at opacity a over the paper (keeps everything in RGB, crisp)."""
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))


def text(d, xy, s, f, c, a=1.0, anchor="ls", tracking=0):
    if a <= 0.01:
        return
    col = mix(c, a)
    if not tracking:
        d.text(xy, s, font=f, fill=col, anchor=anchor)
        return
    w = f.getlength(s) + tracking * (len(s) - 1)
    x, y = xy
    if anchor[0] == "m":
        x -= w / 2
    elif anchor[0] == "r":
        x -= w
    for ch in s:
        d.text((x, y), ch, font=f, fill=col, anchor="l" + anchor[1])
        x += f.getlength(ch) + tracking


# ---------- headline: left-aligned, words rise into place line by line ----------
def headline(d, markup, size, y, t, leave=0.0):
    """markup: '|' new line, *italic*, ^teal^, ~ochre~. Each word rises 26 px and fades in, 0.06 s apart."""
    n = 0
    flags = {"*": False, "^": False, "~": False}
    for li, line in enumerate(markup.split("|")):
        x = M
        base = y + li * size * 1.08
        for raw in line.split(" "):
            word = raw
            for ch in "*^~":
                if word.startswith(ch):
                    flags[ch] = True
            clean = word.strip("*^~")
            it, col = flags["*"], CERT if flags["^"] else CHANCE if flags["~"] else INK
            if col != INK:
                it = True
            for ch in "*^~":
                if word.endswith(ch):
                    flags[ch] = False
            p = ease_out((t - n * 0.06) / 0.5)
            a = p * (1 - leave)
            f = serif(size, it)
            text(d, (x, base + 26 * (1 - p) - 20 * leave), clean, f, col, a)
            x += f.getlength(clean + " ")
            n += 1


def kicker(d, s, y, a, col=MUTED):
    d.rectangle([M, y - 34, M + 36, y - 30], fill=mix(CHANCE, a))
    text(d, (M, y), s.upper(), sans(21, 600), col, a, tracking=3.2)


def chrome(d, idx, total_scenes, src, a=1.0):
    """Running header + source line, like a publication page."""
    text(d, (M, 74), "Certainty vs Chance", sans(20, 650), INK)
    text(d, (W - M, 74), "UK · UAE · 2019–2026", sans(20, 500), MUTED, anchor="rs")
    d.line([(M, 96), (W - M, 96)], fill=RULE, width=2)
    d.line([(M, H - 104), (W - M, H - 104)], fill=RULE, width=2)
    text(d, (M, H - 66), src, sans(19, 400), MUTED, a)
    text(d, (W - M, H - 66), f"{idx:02d} / {total_scenes:02d}", sans(19, 600), MUTED, anchor="rs")


# ---------- data ----------
trends = pd.read_csv(f"{ROOT}/data/raw/trends_long.csv", parse_dates=["date"])
sel = trends[trends["date"].dt.month.isin([8, 9, 10]) & trends["date"].dt.year.isin([2019, 2026])]
ao = sel.groupby(["country", "term", sel["date"].dt.year])["interest"].mean().unstack()
pct = ((ao[2026] + 1) / (ao[2019] + 1) * 100 - 100).round(0)
_fy = trends[(trends.country == "GB") & trends["date"].dt.year.isin([2019, 2025])]
_fy = _fy.groupby(["term", _fy["date"].dt.year])["interest"].mean().unstack()
_pct = ((_fy[2025] + 1) / (_fy[2019] + 1) * 100 - 100).round(0)
import yaml as _yaml
_side = {x["term"]: x["side"] for x in _yaml.safe_load(open(f"{ROOT}/config/terms.yaml", encoding="utf-8"))["countries"]["GB"]["terms"]}
_grp = pd.DataFrame({"pct": _pct, "side": _pct.index.map(_side)})
_grp = _grp[_grp["side"].isin(["chance", "certainty"]) & (_grp.index != "voucher code")]
AVG_CHANCE, AVG_CERT = _grp.groupby("side")["pct"].mean()[["chance", "certainty"]]
UK_BARS = [(k, _pct[k], CHANCE) for k in ["giveaway", "instant win", "competitions"]] + \
          [(k, _pct[k], CERT) for k in ["loyalty points", "free gift", "cashback"]]
cb = trends[(trends.country == "GB") & (trends.term == "cashback")].set_index("date")["interest"]
CB = cb["2025-01-01":"2026-10-01"]
_ae = trends[(trends.country == "AE") & (trends.term == "cashback")].set_index("date")["interest"]
CMP = pd.DataFrame({"GB": cb["2025-12-01":"2026-10-01"], "AE": _ae["2025-12-01":"2026-10-01"]})
CB_PRE = cb["2025-12-01":"2026-02-01"].mean()
CB_POST = cb["2026-03-01":"2026-09-01"].mean()
plc = pd.read_csv(f"{ROOT}/outputs/tables/placebo_draws.csv")
PLACEBO = np.sort(plc[plc.country == "GB"]["jump"].to_numpy())
REAL = float(pd.read_csv(f"{ROOT}/outputs/tables/placebo.csv").set_index("country").loc["GB", "real_jump_mar2026"])
qs = pd.read_csv(f"{ROOT}/data/processed/query_shares.csv").set_index(["country", "year"])
UAE = [("Groceries & supermarkets", qs.loc[("AE", 2025), "savings_groceries_pct"], qs.loc[("AE", 2026), "savings_groceries_pct"]),
       ("Bank & credit-card offers", qs.loc[("AE", 2025), "savings_cash_bank_pct"], qs.loc[("AE", 2026), "savings_cash_bank_pct"])]
ML_ACC = float(pd.read_csv(f"{ROOT}/outputs/tables/ml_results.csv").iloc[0]["accuracy"])
N_TERMS = trends["term"].nunique() if False else 32
N_MONTHS = trends["date"].nunique()


def leave_of(t, dur, length=0.35):
    return ease((t - (dur - length)) / length)


def hi(img):
    """Start a supersampled drawing layer for smooth lines and dots."""
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    return big, ImageDraw.Draw(big)


def lo(img, big):
    img.alpha_composite(big.resize((W, H), Image.LANCZOS))


# ---------- scenes ----------
def s_hook(img, d, t, dur):
    lv = leave_of(t, dur)
    kicker(d, "A question", 360, 1 - lv)
    headline(d, "£5 ^guaranteed,^|or a shot at|~£5,000?~", 128, 520, 10, lv)
    a = ease_out((t - 0.8) / 0.4) * (1 - lv)
    text(d, (M, 1000), "Which one people want depends on what", sans(30, 400), MUTED, a)
    text(d, (M, 1044), "kind of pressure they’re under.", sans(30, 400), MUTED, a)
    return "A study of search behaviour in the UK and UAE."


def s_setup(img, d, t, dur):
    lv = leave_of(t, dur)
    kicker(d, "The data", 250, ease_out(t / 0.4) * (1 - lv))
    headline(d, "When money gets tight,|what do we *want?*", 92, 360, t - 0.1, lv)
    stats = [(N_TERMS, "search terms", "English & Arabic"), (N_MONTHS, "months", "Jan 2019 – Oct 2026"),
             (669, "real searches", "read and labelled by Claude")]
    for i, (v, lab, sub) in enumerate(stats):
        y = 690 + i * 165
        p = ease_out((t - 0.9 - i * 0.25) / 0.6)
        a = clamp(p * 2) * (1 - lv)
        d.line([(M, y - 70), (M + (W - 2 * M) * p, y - 70)], fill=mix(RULE, 1 - lv), width=2)
        text(d, (M, y + 22), f"{v * p:.0f}", serif(104), INK, a)
        text(d, (M + 250, y - 6), lab, sans(32, 600), INK, a)
        text(d, (M + 250, y + 34), sub, sans(26, 400), MUTED, a)
    wa = ease_out((t - 1.9) / 0.4) * (1 - lv)
    text(d, (M, 1196), "Same war, two routes: the UAE was hit directly,", sans(28, 500), INK, wa)
    text(d, (M, 1234), "the UK through fuel and energy prices.", sans(28, 500), INK, wa)
    return "Source: Google Trends. Queries labelled by Claude against a fixed codebook."


def s_uk(img, d, t, dur):
    lv = leave_of(t, dur)
    kicker(d, "UK · before the 2026 shock", 200, ease_out(t / 0.4) * (1 - lv))
    headline(d, "In a slow squeeze,|we chased ~prizes.~", 92, 300, t - 0.1, lv)
    ea = ease_out((t - 0.6) / 0.4) * (1 - lv)
    text(d, (M, 545), "How searches for each one changed", sans(28, 400), MUTED, ea)
    text(d, (M, 583), "between 2019 and 2025:", sans(28, 400), MUTED, ea)
    zero, scale, rh = M + 230, 3.6, 72
    groups = [("Chances to win", CHANCE, 672, UK_BARS[:3]), ("Guaranteed rewards", CERT, 925, UK_BARS[3:])]
    k = 0
    for gi, (gname, gcol, gy, bars) in enumerate(groups):
        ga = ease_out((t - 0.9 - gi * 0.7) / 0.35) * (1 - lv)
        text(d, (M, gy - 26), gname.upper(), sans(22, 700), gcol, ga, tracking=2.5)
        for j, (term, v, col) in enumerate(bars):
            y = gy + j * rh
            p = ease_out((t - 1.0 - k * 0.18) / 0.7)
            a = clamp((t - 1.0 - k * 0.18) / 0.25) * (1 - lv)
            k += 1
            L = v * scale * p
            x0, x1 = (zero, zero + L) if v > 0 else (zero + L, zero)
            text(d, ((zero - 22) if v > 0 else (zero + v * scale - 16), y + 24), f"“{term}”", sans(26, 600), INK, a, anchor="rs")
            if a > 0:
                d.rectangle([x0, y - 2, max(x1, x0 + 1), y + 34], fill=mix(col, a))
            word = "more" if v > 0 else "fewer"
            num = f"{abs(v) * p:.0f}% {word}"
            text(d, ((x1 + 18) if v > 0 else (zero + 18), y + 28), num, serif(40), col, a)
    la = ease_out((t - 0.9) / 0.3) * (1 - lv)
    for gy in (672, 925):
        d.line([(zero, gy - 14), (zero, gy + 2 * rh + 48)], fill=mix(INK, 0.45 * la), width=2)
    ca = ease_out((t - 2.4) / 0.4) * (1 - lv)
    text(d, (M, 1180), f"On average, prize searches rose {AVG_CHANCE:.0f}%.", sans(30, 600), CHANCE, ca)
    text(d, (M, 1220), f"Guaranteed rewards rose just {AVG_CERT:.0f}%.", sans(30, 600), CERT, ca)
    return "Google Trends, UK, full-year averages. Voucher codes left out: the wording changed."


def s_shock(img, d, t, dur):
    lv = leave_of(t, dur)
    kicker(d, "UK · March 2026", 200, ease_out(t / 0.4) * (1 - lv))
    headline(d, "Then a sudden shock|^swung it back.^", 92, 300, t - 0.1, lv)
    x0, x1, y0, y1 = M + 60, W - M - 10, 610, 1080
    n = len(CB)
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * v / 100
    fa = ease_out((t - 0.7) / 0.4) * (1 - lv)
    mi = list(CB.index).index(pd.Timestamp("2026-03-01"))
    si = list(CB.index).index(pd.Timestamp("2026-09-01"))
    # shaded post-shock period
    sa = ease_out((t - 2.4) / 0.4) * (1 - lv)
    if sa > 0:
        d.rectangle([X(mi) - 10, y0 - 10, X(si) + 10, y1], fill=mix(CERT, 0.08 * sa))
    for v in [0, 25, 50, 75, 100]:
        d.line([(x0, Y(v)), (x1, Y(v))], fill=mix(RULE if v else MUTED, fa), width=2 if v else 2)
        text(d, (x0 - 14, Y(v) + 9), str(v), sans(25, 500), MUTED, fa, anchor="rs")
    for lab, i in [("Jan ’25", 0), ("Jul", 6), ("Jan ’26", 12), ("Jul", 18), ("Oct", n - 1)]:
        text(d, (X(i), y1 + 42), lab, sans(25, 500), MUTED, fa, anchor="ms")
    text(d, (M, 532), "How often people in the UK searched “cashback”,", sans(28, 400), MUTED, fa)
    text(d, (M, 570), "month by month. 100 = the busiest month.", sans(28, 400), MUTED, fa)
    big, bd = hi(img)
    prog = ease((t - 0.9) / 2.2) * (n - 1)
    pts = []
    for i in range(n):
        if i <= prog:
            pts.append((X(i) * SS, Y(CB.iloc[i]) * SS))
        else:
            f = prog - (i - 1)
            if f > 0:
                pts.append(((X(i - 1) + (X(i) - X(i - 1)) * f) * SS, (Y(CB.iloc[i - 1]) + (Y(CB.iloc[i]) - Y(CB.iloc[i - 1])) * f) * SS))
            break
    la = 1 - lv
    if len(pts) > 1:
        bd.line(pts, fill=CERT + (int(255 * la),), width=6 * SS, joint="curve")
        for i in range(min(int(prog) + 1, n)):
            r = 7 * SS
            bd.ellipse([X(i) * SS - r, Y(CB.iloc[i]) * SS - r, X(i) * SS + r, Y(CB.iloc[i]) * SS + r],
                       fill=PAPER + (int(255 * la),), outline=CERT + (int(255 * la),), width=3 * SS)
    lo(img, big)
    d = ImageDraw.Draw(img)
    # averages
    ba = ease_out((t - 3.2) / 0.4) * (1 - lv)
    pre0 = list(CB.index).index(pd.Timestamp("2025-12-01"))
    for (i0, i1, v, col, lab, dy) in [(pre0, mi - 1, CB_PRE, MUTED, f"Winter avg {CB_PRE:.0f}", 120),
                                      (mi, si, CB_POST, CERT, f"Mar–Sep avg {CB_POST:.0f}", 64)]:
        for xx in range(int(X(i0)), int(X(i1)), 14):
            d.line([(xx, Y(v)), (xx + 7, Y(v))], fill=mix(col, ba), width=3)
        text(d, (X(i0) + 14 if col == CERT else X(i0) - 150, Y(v) + dy), lab, sans(26, 650), col, ba)
    # event marker with leader
    ea = ease_out((t - 2.4) / 0.4) * (1 - lv)
    d.line([(X(mi), y0 - 10), (X(mi), y1)], fill=mix(INK, 0.6 * ea), width=2)
    text(d, (X(mi) + 16, y1 - 60), "Iran war begins,", sans(25, 650), INK, ea)
    text(d, (X(mi) + 16, y1 - 24), "energy prices jump", sans(25, 400), INK, ea)
    ca = ease_out((t - 4.2) / 0.4) * (1 - lv)
    text(d, (M, 1215), "Within a month, twice as many cashback searches as winter.", sans(30, 500), INK, ca)
    return "Source: Google Trends, UK, monthly, Jan 2025 – Oct 2026."


_ms = cb[cb.index.month.isin(range(3, 10))]
YOY = _ms.groupby(_ms.index.year).mean()          # UK cashback, Mar-Sep average, each year


def s_proof(img, d, t, dur):
    """Same months, every year: is 2026 just the time of year?"""
    lv = leave_of(t, dur)
    kicker(d, "Was it just the time of year?", 200, ease_out(t / 0.4) * (1 - lv))
    headline(d, "Same months, every year.|Only ^2026^ stands out.", 88, 300, t - 0.1, lv)
    fa = ease_out((t - 0.7) / 0.4) * (1 - lv)
    text(d, (M, 572), "Cashback searches, March to September, each year.", sans(28, 400), MUTED, fa)
    text(d, (M, 610), "Taller bar = more people searching.", sans(28, 400), MUTED, fa)
    x0, x1, base, top = M + 10, W - M - 10, 1060, 680
    n = len(YOY)
    slot = (x1 - x0) / n
    bw = slot * 0.62
    Y = lambda v: base - (base - top) * v / 100
    for v in [0, 50, 100]:
        d.line([(x0, Y(v)), (x1, Y(v))], fill=mix(RULE if v else MUTED, fa), width=2)
    for i, (yr, v) in enumerate(YOY.items()):
        p = ease_out((t - 1.0 - i * 0.12 - (0.5 if yr == 2026 else 0)) / 0.6)
        a = clamp(p * 2) * (1 - lv)
        cx = x0 + slot * (i + 0.5)
        col = CERT if yr == 2026 else FAINT
        h = (base - Y(v)) * p
        if a > 0:
            d.rectangle([cx - bw / 2, base - h, cx + bw / 2, base], fill=mix(col, a))
        text(d, (cx, base + 40), str(yr), sans(25, 650 if yr == 2026 else 500), INK if yr == 2026 else MUTED, fa, anchor="ms")
        text(d, (cx, base - h - 14), f"{v * p:.0f}", serif(46 if yr == 2026 else 40), CERT if yr == 2026 else MUTED, a, anchor="ms")
    # call out 2022, the cost-of-living spring
    i22 = list(YOY.index).index(2022)
    ca = ease_out((t - 2.6) / 0.4) * (1 - lv)
    cx22 = x0 + slot * (i22 + 0.5)
    d.line([(cx22, Y(YOY[2022]) - 62), (cx22, Y(YOY[2022]) - 150)], fill=mix(MUTED, ca), width=2)
    text(d, (cx22 - 10, Y(YOY[2022]) - 172), "2022: cost-of-living crisis", sans(24, 600), INK, ca)
    ra = ease_out((t - 3.3) / 0.4) * (1 - lv)
    text(d, (M, 1196), f"2026 was almost three times any year since 2019.", sans(30, 500), INK, ra)
    return "Source: Google Trends, UK, monthly. Average of March to September each year."


def s_uae(img, d, t, dur):
    """UK vs UAE on the same measure: cashback searches, month by month."""
    lv = leave_of(t, dur)
    kicker(d, "UK vs UAE · same war, two routes", 200, ease_out(t / 0.4) * (1 - lv))
    headline(d, "Same shock.|^Different speed.^", 92, 300, t - 0.1, lv)
    fa = ease_out((t - 0.6) / 0.4) * (1 - lv)
    text(d, (M, 532), "Searches for “cashback” in each country, month by", sans(28, 400), MUTED, fa)
    text(d, (M, 570), "month. 100 = that country’s busiest month.", sans(28, 400), MUTED, fa)
    x0, x1, y0, y1 = M + 60, W - M - 70, 640, 990
    n = len(CMP)
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y1 - (y1 - y0) * v / 100
    for v in [0, 50, 100]:
        d.line([(x0, Y(v)), (x1, Y(v))], fill=mix(RULE if v else MUTED, fa), width=2)
        text(d, (x0 - 14, Y(v) + 9), str(v), sans(25, 500), MUTED, fa, anchor="rs")
    for lab, i in [("Dec ’25", 0), ("Mar", 3), ("Jun", 6), ("Sep", 9)]:
        text(d, (X(i), y1 + 40), lab, sans(25, 500), MUTED, fa, anchor="ms")
    mi = 3
    ea = ease_out((t - 1.0) / 0.4) * (1 - lv)
    d.line([(X(mi) - (X(1) - X(0)) * 0.1, y0 - 10), (X(mi) - (X(1) - X(0)) * 0.1, y1)], fill=mix(INK, 0.5 * ea), width=2)
    text(d, (X(mi) - (X(1) - X(0)) * 0.1 - 10, y1 - 16), "War begins", sans(22, 600), INK, ea, anchor="rs")
    big, bd = hi(img)
    for k, (c, col) in enumerate([("GB", CERT), ("AE", INK)]):
        prog = ease((t - 1.2 - k * 0.5) / 2.0) * (n - 1)
        vals = CMP[c].tolist()
        pts = []
        for i in range(n):
            if i <= prog:
                pts.append((X(i) * SS, Y(vals[i]) * SS))
            else:
                f = prog - (i - 1)
                if f > 0:
                    pts.append(((X(i - 1) + (X(i) - X(i - 1)) * f) * SS, (Y(vals[i - 1]) + (Y(vals[i]) - Y(vals[i - 1])) * f) * SS))
                break
        la = 1 - lv
        if len(pts) > 1:
            bd.line(pts, fill=col + (int(255 * la),), width=6 * SS, joint="curve")
            for i in range(min(int(prog) + 1, n)):
                r = 6 * SS
                bd.ellipse([X(i) * SS - r, Y(vals[i]) * SS - r, X(i) * SS + r, Y(vals[i]) * SS + r],
                           fill=PAPER + (int(255 * la),), outline=col + (int(255 * la),), width=3 * SS)
    lo(img, big)
    d = ImageDraw.Draw(img)
    ua = ease_out((t - 2.6) / 0.4) * (1 - lv)
    text(d, (X(3) - 40, y0 - 22), "UK jumped in a month", sans(25, 700), CERT, ua)
    aa = ease_out((t - 3.4) / 0.4) * (1 - lv)
    text(d, (X(5) - 10, Y(CMP["AE"].iloc[5]) + 52), "UAE climbed for months", sans(25, 700), INK, aa)
    ra = ease_out((t - 4.0) / 0.4) * (1 - lv)
    g25, g26 = UAE[0][1], UAE[0][2]
    text(d, (M, 1110), f"UAE “offers” searches also turned to food shopping:", sans(26, 400), MUTED, ra)
    text(d, (M, 1146), f"{g25:.0f}% of them in 2025, {g26:.0f}% in 2026.", sans(26, 400), MUTED, ra)
    text(d, (M, 1215), "Both turned to guaranteed rewards. The UK just did it faster.", sans(29, 600), INK, ra)
    return "Google Trends, monthly. UAE cashback searches were already rising before 2026."


def s_method(img, d, t, dur):
    lv = leave_of(t, dur)
    kicker(d, "Method", 200, ease_out(t / 0.4) * (1 - lv))
    headline(d, "How it was *built.*", 92, 300, t - 0.1, lv)
    steps = [("Collected", f"Google Trends: {N_TERMS} terms, {N_MONTHS} months, UK and UAE"),
             ("Labelled", "Claude classified 669 real searches against a fixed codebook"),
             ("Checked", f"A simple model trained on those labels agreed {ML_ACC * 100:.0f}% of the time"),
             ("Tested", "Regression with Ramadan control, re-run seven other ways")]
    for i, (verb, s) in enumerate(steps):
        y = 520 + i * 150
        p = ease_out((t - 0.6 - i * 0.25) / 0.5)
        a = clamp(p * 1.6) * (1 - lv)
        d.line([(M, y - 40), (M + (W - 2 * M) * p, y - 40)], fill=mix(RULE, 1 - lv), width=2)
        text(d, (M, y + 14), f"{i + 1:02d}", serif(46), CHANCE, a)
        text(d, (M + 90, y + 2), verb, sans(28, 650), INK, a)
        words, line, ly = s.split(), "", y + 42
        for w_ in words:
            if sans(25).getlength(line + w_) > W - 2 * M - 90:
                text(d, (M + 90, ly), line.strip(), sans(25, 400), MUTED, a)
                line, ly = "", ly + 34
            line += w_ + " "
        text(d, (M + 90, ly), line.strip(), sans(25, 400), MUTED, a)
    ca = ease_out((t - 2.0) / 0.4) * (1 - lv)
    text(d, (M, 1196), "Searches show what people wanted, not what they bought.", sans(26, 500), INK, ca)
    return "Full method, data and code on GitHub."


def s_cta(img, d, t, dur):
    kicker(d, "Your turn", 360, ease_out(t / 0.4))
    headline(d, "^Guaranteed^ £5,|or a shot at ~£5,000?~", 108, 500, t - 0.1)
    a = ease_out((t - 1.2) / 0.4)
    text(d, (M, 860), "Tell me in the comments.", sans(32, 500), INK, a)
    d.line([(M, 930), (M + (W - 2 * M) * a, 930)], fill=RULE, width=2)
    text(d, (M, 990), "Code, data and method", sans(24, 600), MUTED, a)
    text(d, (M, 1036), "github.com/Osman246/certainty-vs-chance", sans(30, 600), CERT, a)
    text(d, (M, 1110), "Sahil Osman", sans(24, 600), INK, ease_out((t - 1.6) / 0.4))
    return "Independent research using public data. Not affiliated with my employer."


SCENES = [("01_hook", s_hook, 3.8), ("02_setup", s_setup, 3.8), ("03_uk", s_uk, 7.2), ("04_shock", s_shock, 7.6),
          ("05_proof", s_proof, 6.2), ("06_uae", s_uae, 7.4), ("07_method", s_method, 5.6), ("08_cta", s_cta, 5.0)]


def frame(fn, t, dur, idx):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)
    src = fn(img, d, t, dur)
    d = ImageDraw.Draw(img)
    chrome(d, idx, len(SCENES), src, ease_out((t - 0.6) / 0.4) * (1 - leave_of(t, dur) if idx < len(SCENES) else 1))
    return img.convert("RGB")


def render_scene(idx, name, fn, dur):
    tmp, final = f"{OUT}/{name}.tmp.mp4", f"{OUT}/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for k in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, k / FPS, dur, idx).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, final)


if __name__ == "__main__":
    if sys.argv[1:2] == ["stills"]:
        for i, (name, fn, dur) in enumerate(SCENES, 1):
            frame(fn, dur - 0.5, dur, i).save(f"{OUT}/still_{name}.jpg", quality=92)
    else:
        only = sys.argv[1:]
        for i, (name, fn, dur) in enumerate(SCENES, 1):
            if not only or name in only:
                render_scene(i, name, fn, dur)
                print("rendered", name, flush=True)
