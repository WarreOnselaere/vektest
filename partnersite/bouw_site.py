"""
Bouwt partnersite/index.html uit site_template.html + careerday/data/stands_2526.json.

De standposities komen uit het grondplan Career Day 25-26 (vectoren uit de PDF),
in meter: X = lengte tent (0 = ingangszijde, 90 = achterkant), Y = breedte
(tent 2: 0-20 m, tussengang 20-22 m, tent 1: 22-42 m).

Gebruik:  python3 bouw_site.py
"""
import json
import math
from pathlib import Path

HIER = Path(__file__).resolve().parent
DATA = HIER.parent / "careerday" / "data" / "stands_2526.json"

TENTEN = {"1": (22.0, 42.0), "2": (0.0, 20.0)}
INGANG = (0.0, 40.0)
TOL = 0.35


def overlap(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def verrijk(stands):
    for s in stands:
        s["tent"] = "1" if s["tent"] == "A" else "2"
    for s in stands:
        x0, x1, y0, y1 = s["x"], s["x"] + s["w"], s["y"], s["y"] + s["h"]
        ty0, ty1 = TENTEN[s["tent"]]
        zijden = {"links": True, "rechts": True, "onder": True, "boven": True}
        tegen_wand = y0 - ty0 < 0.8 or ty1 - y1 < 0.8 or x1 > 89.2
        if y0 - ty0 < 0.8:
            zijden["onder"] = False
        if ty1 - y1 < 0.8:
            zijden["boven"] = False
        if x1 > 89.2:
            zijden["rechts"] = False
        for o in stands:
            if o is s:
                continue
            ox0, ox1, oy0, oy1 = o["x"], o["x"] + o["w"], o["y"], o["y"] + o["h"]
            if overlap(y0, y1, oy0, oy1) > 0.5:
                if abs(ox1 - x0) < TOL:
                    zijden["links"] = False
                if abs(ox0 - x1) < TOL:
                    zijden["rechts"] = False
            if overlap(x0, x1, ox0, ox1) > 0.5:
                if abs(oy1 - y0) < TOL:
                    zijden["onder"] = False
                if abs(oy0 - y1) < TOL:
                    zijden["boven"] = False
        n_open = sum(zijden.values())
        if tegen_wand:
            soort = "Wandstand"
        elif n_open >= 3:
            soort = "Kopstand"
        else:
            soort = "Eilandstand"
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        afstand = math.hypot(cx - INGANG[0], cy - INGANG[1])
        if s["tent"] == "2":          # via tussengang (opening aan de ingangszijde)
            afstand = math.hypot(cx - 5, cy - 21) + math.hypot(5, 19)
        s["open"] = n_open
        s["soort"] = soort
        s["ingang"] = int(round(afstand / 5.0) * 5)
    return stands


def main():
    stands = verrijk(json.loads(DATA.read_text()))
    compact = [[s["nr"], round(s["x"], 2), round(s["y"], 2), s["w"], s["h"],
                s["tent"], s["soort"], s["open"], s["ingang"]] for s in stands]
    tpl = (HIER / "site_template.html").read_text()
    html = tpl.replace("/*__STANDEN__*/[]", json.dumps(compact, separators=(",", ":")))
    # 1) losse website (GitHub Pages / Netlify ...): volledig HTML-document
    kop = ('<!doctype html>\n<html lang="nl">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
    (HIER / "index.html").write_text(kop + html + "\n</html>\n")
    # 2) fragment voor een claude.ai-artifact (preview); skelet wordt daar toegevoegd
    (HIER / "artifact_preview.html").write_text(html)
    from collections import Counter
    print("index.html geschreven:", len(stands), "standen",
          dict(Counter(s["soort"] for s in stands)))


if __name__ == "__main__":
    main()
