"""
Kabelroutering Career Day – paddenstoelen, kattekoppen en kabels per lengte.

Rooster van 0,5 m over het plein. Kabels mogen NOOIT over de groene loper.
Kosten per cel (hoe lager, hoe liever de kabel daar ligt):
  onder / achter stands 1,2  (langs ruglijn, onder standvloer)
  tussengang            1,0
  faciliteiten (zones)  2,0
  buiten de tent        2,5
  looppad (gang)        4,0  -> waar een kabel een gang kruist komt een kabelbrug
  loading bay           6,0
  groene loper          verboden (incl. 0,25 m marge)
Elke bocht kost 1,0 extra, zodat de tracés rechte lijnen volgen.
"""
from __future__ import annotations

import heapq
import math

RES = 0.5
X0, X1 = -5.0, 96.0
Y0, Y1 = -5.0, 47.0
NX = int(round((X1 - X0) / RES))
NY = int(round((Y1 - Y0) / RES))

KABELS = [5, 10, 15, 40]          # beschikbare lengtes (m)
SPELING = 1.5                      # extra lengte (opstijgen naar kattekop / speling)
CAP = 9                            # max. aansluitingen per paddenstoel


def cel(x, y):
    return int((x - X0) / RES), int((y - Y0) / RES)


def pt(i, j):
    return X0 + (i + 0.5) * RES, Y0 + (j + 0.5) * RES


def loper_rects(punten, breedte):
    h = breedte / 2
    out = []
    for (xa, ya), (xb, yb) in zip(punten, punten[1:]):
        out.append((min(xa, xb) - h, min(ya, yb) - h, max(xa, xb) + h, max(ya, yb) + h))
    return out


def in_rect(x, y, r, m=0.0):
    return r[0] - m <= x <= r[2] + m and r[1] - m <= y <= r[3] + m


class Rooster:
    def __init__(self, stands, zones, tenten, tussengang, loper_pts, loper_b):
        self.kost = [[4.0] * NY for _ in range(NX)]
        lop = loper_rects(loper_pts, loper_b)
        self.soort = [["gang"] * NY for _ in range(NX)]
        for i in range(NX):
            for j in range(NY):
                x, y = pt(i, j)
                k, s = 4.0, "gang"
                if not any(in_rect(x, y, t) for t in tenten):
                    k, s = (1.0, "tussengang") if in_rect(x, y, tussengang) else (2.5, "buiten")
                for (_n, zx0, zy0, zx1, zy1, laag) in zones:
                    if in_rect(x, y, (zx0, zy0, zx1, zy1)):
                        k, s = (6.0, "loading") if "LOADING" in _n else (2.0, "zone")
                for st in stands:
                    if in_rect(x, y, (st["x0"], st["y0"], st["x1"], st["y1"])):
                        k, s = 1.2, "stand"
                if any(in_rect(x, y, r, 0.25) for r in lop):
                    k, s = math.inf, "loper"
                self.kost[i][j] = k
                self.soort[i][j] = s

    def dijkstra(self, start, max_len=None):
        """Goedkoopste paden vanaf start (x,y); toestand = (cel, richting) voor bochtkost.
        best[(i,j)] = (kost, richting, lengte in m). max_len: zoekradius (tracélengte)."""
        si, sj = cel(*start)
        dist, lens, prev, best = {}, {}, {}, {}
        pq = []
        for d in range(4):
            dist[(si, sj, d)] = 0.0
            lens[(si, sj, d)] = 0.0
            heapq.heappush(pq, (0.0, si, sj, d))
        stappen = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        while pq:
            c, i, j, d = heapq.heappop(pq)
            if dist.get((i, j, d), math.inf) < c:
                continue
            ln = lens[(i, j, d)]
            if (i, j) not in best or c < best[(i, j)][0]:
                best[(i, j)] = (c, d, ln)
            for nd, (di, dj) in enumerate(stappen):
                ni, nj = i + di, j + dj
                if not (0 <= ni < NX and 0 <= nj < NY):
                    continue
                k = self.kost[ni][nj]
                if k == math.inf:
                    continue
                nl = ln + RES
                if max_len is not None and nl > max_len:
                    continue
                nc = c + k * RES + (1.0 if nd != d else 0.0)
                if nc < dist.get((ni, nj, nd), math.inf):
                    dist[(ni, nj, nd)] = nc
                    lens[(ni, nj, nd)] = nl
                    prev[(ni, nj, nd)] = (i, j, d)
                    heapq.heappush(pq, (nc, ni, nj, nd))
        return best, prev, dist

    @staticmethod
    def pad(best, prev, doel):
        gi, gj = cel(*doel)
        if (gi, gj) not in best:
            return None, math.inf
        c, d, _l = best[(gi, gj)]
        st = (gi, gj, d)
        cellen = [(gi, gj)]
        while st in prev:
            st = prev[st]
            cellen.append((st[0], st[1]))
        cellen.reverse()
        return cellen, c


def vereenvoudig(cellen):
    pts = [pt(*c) for c in cellen]
    if len(pts) <= 2:
        return pts
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            out.append(b)
    out.append(pts[-1])
    return out


def lengte(poly):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(poly, poly[1:]))


def kabelklasse(l):
    """Kortste kabel(combinatie) uit KABELS die lengte l dekt."""
    for k in KABELS:
        if l <= k:
            return [k]
    rest = l
    combo = []
    while rest > 40:
        combo.append(40)
        rest -= 40
    combo.append(next(k for k in KABELS if rest <= k))
    return combo


def gangruns(rooster, cellen):
    """Aaneengesloten stukken 'gang' op een tracé -> kabelbruggen (midden, richting, lengte)."""
    runs, huidig = [], []
    for c in cellen:
        if rooster.soort[c[0]][c[1]] == "gang":
            huidig.append(c)
        elif huidig:
            runs.append(huidig)
            huidig = []
    if huidig:
        runs.append(huidig)
    out = []
    for r in runs:
        a, b = pt(*r[0]), pt(*r[-1])
        horiz = abs(b[0] - a[0]) >= abs(b[1] - a[1])
        out.append((((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), horiz, len(r) * RES))
    return out


def plaats_paddenstoelen(rooster, punten, n):
    """k-means op de aansluitpunten, daarna naar de dichtste vrije gangcel naast een stand."""
    pts = sorted(punten)
    centra = [pts[int((k + 0.5) * len(pts) / n)] for k in range(n)]
    for _ in range(20):
        groepen = [[] for _ in centra]
        for p in pts:
            groepen[min(range(n), key=lambda k: (centra[k][0] - p[0]) ** 2 + (centra[k][1] - p[1]) ** 2)].append(p)
        centra = [(sum(q[0] for q in g) / len(g), sum(q[1] for q in g) / len(g)) if g else c
                  for g, c in zip(groepen, centra)]
    res = []
    for cx, cy in centra:
        res.append(_vrije_plek(rooster, cx, cy, streng=True) or _vrije_plek(rooster, cx, cy, streng=False))
    return res


def _vrije_plek(rooster, cx, cy, streng):
    """streng: gangcel naast een stand; anders: elke vrije cel (gang, zone, tussengang, buiten)."""
    if True:
        ci, cj = cel(cx, cy)
        best = None
        for r in range(0, 40):
            for i in range(ci - r, ci + r + 1):
                for j in range(cj - r, cj + r + 1):
                    if max(abs(i - ci), abs(j - cj)) != r or not (0 < i < NX - 1 and 0 < j < NY - 1):
                        continue
                    soort = rooster.soort[i][j]
                    if streng and soort != "gang":
                        continue
                    if soort in ("loper", "stand", "loading"):
                        continue
                    buren = [rooster.soort[i + a][j + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    if streng and "stand" not in buren:
                        continue
                    # niet vlak naast de loper (1 m)
                    if any(rooster.soort[i + a][j + b] == "loper"
                           for a in range(-2, 3) for b in range(-2, 3)):
                        continue
                    d = (i - ci) ** 2 + (j - cj) ** 2
                    if best is None or d < best[0]:
                        best = (d, i, j)
            if best:
                break
        return pt(best[1], best[2]) if best else None


MAX_TRACE = 15 - SPELING        # tracé zodat een kabel van 15 m volstaat
KETTING = 3                     # max. paddenstoelen per doorgeluste streng


def kandidaten(rooster, stap=3):
    out = []
    for i in range(2, NX - 2, stap):
        for j in range(2, NY - 2, stap):
            if rooster.soort[i][j] not in ("gang", "tussengang", "zone"):
                continue
            if any(rooster.soort[i + a][j + b] == "loper" for a in range(-2, 3) for b in range(-2, 3)):
                continue
            buren = [rooster.soort[i + a][j + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if rooster.soort[i][j] == "gang" and "stand" not in buren:
                continue
            out.append(pt(i, j))
    return out


def ontwerp(rooster, aansluitingen, hvbs, _n=None):
    """1) paddenstoelen kiezen (gretige set-cover): elke aansluiting binnen MAX_TRACE m tracé,
       max CAP per paddenstoel; 2) toewijzen; 3) voeding: strengen van max KETTING paddenstoelen,
       eerste paddenstoel van elke streng vanaf een hoofdbord, de rest doorgelust."""
    doelen = [cel(*a["pos"]) for a in aansluitingen]
    bereik = {}
    for k in kandidaten(rooster):
        best, _p, _d = rooster.dijkstra(k, max_len=MAX_TRACE)
        bereik[k] = {ai: best[c][2] for ai, c in enumerate(doelen) if c in best}
    ongedekt = set(range(len(aansluitingen)))
    ps = []
    while ongedekt:
        k = max(bereik, key=lambda k: (min(CAP, len(ongedekt & bereik[k].keys())),
                                        -sum(sorted(bereik[k][a] for a in ongedekt & bereik[k].keys())[:CAP])))
        gedekt = sorted(ongedekt & bereik[k].keys(), key=lambda a: bereik[k][a])[:CAP]
        if not gedekt:
            break                                   # rest onbereikbaar binnen MAX_TRACE
        ps.append(k)
        ongedekt -= set(gedekt)
    # volledige zoekbomen voor toewijzing en voeding
    boom = [rooster.dijkstra(p) for p in ps]
    paren = []
    for ai, c in enumerate(doelen):
        for pi, (best, _p, _d) in enumerate(boom):
            if c in best:
                paren.append((best[c][2] + 0.01 * best[c][0], ai, pi))
    paren.sort()
    toegewezen, last = {}, [0] * len(ps)
    for _c, ai, pi in paren:
        if ai in toegewezen or last[pi] >= CAP:
            continue
        toegewezen[ai] = pi
        last[pi] += 1
    kabels = []
    for ai, a in enumerate(aansluitingen):
        pi = toegewezen[ai]
        best, prev, _d = boom[pi]
        cellen, _c = Rooster.pad(best, prev, a["pos"])
        poly = vereenvoudig(cellen)
        poly[0] = ps[pi]
        poly[-1] = a["pos"]
        l = lengte(poly) + SPELING
        kabels.append(dict(van=pi, naar=a["naam"], poly=poly, lengte=l, klasse=kabelklasse(l),
                           bruggen=gangruns(rooster, cellen)))
    # voeding (Prim met strenglimiet)
    hb = {naam: (pos, rooster.dijkstra(pos)) for naam, pos in hvbs}

    def route(bron_boom, bron_pos, doel):
        best, prev, _d = bron_boom
        cellen, _c = Rooster.pad(best, prev, doel)
        poly = vereenvoudig(cellen)
        poly[0], poly[-1] = bron_pos, doel
        return cellen, poly, lengte(poly) + 2.0

    verbonden = {}          # pi -> (bron, streng-id, diepte)
    strengen = {}
    voeding = [None] * len(ps)
    while len(verbonden) < len(ps):
        opties = []
        for pi in range(len(ps)):
            if pi in verbonden:
                continue
            c = cel(*ps[pi])
            for naam, (pos, bb) in hb.items():
                if c in bb[0]:
                    opties.append((bb[0][c][2], pi, naam, None))
            for qi, (bron, sid, diep) in verbonden.items():
                if strengen[sid] < KETTING and c in boom[qi][0]:
                    opties.append((boom[qi][0][c][2], pi, f"P{qi + 1}", qi))
        l, pi, bron, qi = min(opties)
        if qi is None:
            sid = len(strengen)
            strengen[sid] = 1
            cellen, poly, ln = route(hb[bron][1], hb[bron][0], ps[pi])
        else:
            sid = verbonden[qi][1]
            strengen[sid] += 1
            cellen, poly, ln = route(boom[qi], ps[qi], ps[pi])
        verbonden[pi] = (bron, sid, 0)
        voeding[pi] = dict(van=bron, naar=pi, poly=poly, lengte=ln, klasse=kabelklasse(ln),
                           bruggen=gangruns(rooster, cellen), streng=sid)
    return ps, kabels, voeding, last
