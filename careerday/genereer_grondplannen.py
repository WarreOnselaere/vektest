"""
Careerday – grondplannen (algemeen, elektriciteit, noodplan)
============================================================

Genereert een AutoCAD-tekening (DXF, R2018) met:
  * modelruimte in METER, schaal 1:1
  * twee tenten van 20 m x 90 m, met de lange zijde tegen elkaar (samen 40 m x 90 m)
  * alles netjes op lagen (BASIS-, ALG-, ELEK-, NOOD-, KADER-)
  * drie layouts (A1, schaal 1:200), elk met een viewport waarin de juiste lagen
    bevroren zijn:  01 Algemeen grondplan / 02 Elektriciteitsplan / 03 Noodplan

Gebruik:   python3 genereer_grondplannen.py
Resultaat: Careerday_grondplannen.dxf  (+ 3 losse DXF's per plan)

Assenstelsel: oorsprong (0,0) = zuidwestelijke hoek van tent A.
  X = lengterichting tenten (0 → 90 m), Y = breedterichting (0 → 40 m)
  Tent A: y 0 → 20 m   |   Tent B: y 20 → 40 m   |   koppeling/goot op y = 20 m
"""

from __future__ import annotations

import math
from pathlib import Path

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment, MTextEntityAlignment

OUT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Afmetingen – indeling Career Day 25-26 (Sint-Pietersplein, Gent)
# ---------------------------------------------------------------------------
L = 90.0          # lengte tent
B = 20.0          # breedte één tent
GANG = 2.0        # tussengang tussen de twee tenten
T2 = (0.0, B)                     # tent 2 (logistiek, bar)
T1 = (B + GANG, 2 * B + GANG)     # tent 1 (ingang, vestiaire)
BT = 2 * B + GANG                 # totale breedte 42 m
PAAL_STAP = 5.0   # traveeafstand tentstructuur (indicatief)

STANDEN_JSON = OUT / "data" / "stands_2526.json"

# Zones (naam, x0, y0, x1, y1, laag) – uit grondplan 25-26
ZONES = [
    ("INKOM", 0.0, 22.0, 5.0, 42.0, "ALG-ONTHAAL"),
    ("VESTIAIRE", 5.0, 22.0, 14.0, 32.0, "ALG-ONTHAAL"),
    ("", 14.0, 22.0, 20.9, 25.5, "ALG-ONTHAAL"),
    ("CV-CHECK", 5.0, 34.0, 11.0, 42.0, "ALG-ONTHAAL"),
    ("LANYARDS", 16.0, 34.0, 23.0, 35.2, "ALG-ONTHAAL"),
    ("GOODIES", 26.6, 30.8, 28.2, 33.6, "ALG-ONTHAAL"),
    ("RECRUITERS ZONE", 48.1, 22.3, 65.7, 25.6, "ALG-ZONES"),
    ("LOADING BAY", 86.5, 22.0, 90.0, 42.0, "ALG-LOGISTIEK"),
    ("LOGISTIEKE ZONE", 0.0, 0.0, 10.0, 20.0, "ALG-LOGISTIEK"),
    ("BAR", 10.5, 3.9, 13.5, 15.0, "ALG-CATERING"),
    ("LOADING BAY", 14.2, 0.0, 17.7, 20.0, "ALG-LOGISTIEK"),
    ("CV-SCREENING", 20.6, 16.7, 27.6, 19.7, "ALG-ZONES"),
    ("PHOTOBOOTH", 29.7, 16.7, 35.7, 19.7, "ALG-ZONES"),
    ("RECRUITERS ZONE", 48.1, 16.5, 65.7, 19.7, "ALG-ZONES"),
]

# Uitgangen: (code, wand, middenpositie, breedte, omschrijving)
#   wand: S = y 0 (tent 2), N = y 42 (tent 1), W = x 0 (ingangszijde), O = x 90
UITGANGEN = [
    ("IN", "W", 39.5, 3.0, "Ingang"),
    ("UIT", "W", 24.5, 3.0, "Uitgang"),
    ("NU1", "N", 28.0, 2.4, ""),
    ("NU2", "N", 57.5, 2.4, ""),
    ("NU3", "S", 33.0, 2.4, ""),
    ("NU4", "S", 57.0, 2.4, ""),
    ("NU5", "S", 82.5, 2.4, ""),
    ("NU6", "O", 32.0, 2.4, ""),
    ("NU7", "O", 10.0, 2.4, ""),
    ("NU8", "W", 10.0, 2.4, ""),
]

# ---------------------------------------------------------------------------
# Lagen: naam -> (kleur ACI, linetype, lijndikte [1/100 mm], omschrijving, plot)
# ---------------------------------------------------------------------------
LAGEN = {
    # --- basis (gemeenschappelijk voor alle plannen)
    "BASIS-TENT":             (7,   "Continuous", 50, "Tentwanden en contour tenten", True),
    "BASIS-TENT-KOPPELING":   (8,   "DASHED",     25, "Koppeling / goot tussen tent A en B", True),
    "BASIS-TENT-PALEN":       (7,   "Continuous", 35, "Staanders tentstructuur (h.o.h. 5 m)", True),
    "BASIS-STRAMIEN":         (9,   "CENTER",     13, "Stramienassen", True),
    "BASIS-STRAMIEN-TEKST":   (9,   "Continuous", 18, "Stramienbollen en -nummers", True),
    "BASIS-OMGEVING":         (8,   "Continuous", 18, "Terreingrens, wegen, omgeving", True),
    "BASIS-OMGEVING-TEKST":   (8,   "Continuous", 18, "Tekst omgeving", True),
    # --- algemeen grondplan
    "ALG-STANDS":             (5,   "Continuous", 35, "Standcontouren 3 x 3 m", True),
    "ALG-STANDS-ARCERING":    (151, "Continuous", 0,  "Vulling stands", True),
    "ALG-STANDNUMMERS":       (7,   "Continuous", 18, "Standnummers", True),
    "ALG-ONTHAAL":            (3,   "Continuous", 35, "Onthaal, vestiaire, infobalie", True),
    "ALG-CATERING":           (30,  "Continuous", 35, "Bar en cateringzone", True),
    "ALG-ZONES":              (3,   "Continuous", 25, "Recruiters zone, CV-screening, photobooth", True),
    "ALG-LOGISTIEK":          (8,   "Continuous", 25, "Logistieke zone, loading bays, heat-units", True),
    "ALG-SANITAIR":           (4,   "Continuous", 35, "Sanitaire voorzieningen", True),
    "ALG-ZONES-TEKST":        (7,   "Continuous", 25, "Benaming zones en gangen", True),
    "ALG-MAATVOERING":        (7,    "Continuous", 18, "Maatvoering", True),
    # --- elektriciteitsplan
    "ELEK-HOOFDVOEDING":      (1,   "Continuous", 50, "Aggregaat / netaansluiting en hoofdverdeelbord", True),
    "ELEK-VOEDINGSKABELS":    (1,   "DASHDOT",    35, "Voedingskabels HVB -> SVB (bovengronds langs goot)", True),
    "ELEK-VERDEELBORDEN":     (1,   "Continuous", 35, "Subverdeelborden (SVB)", True),
    "ELEK-KABELS-STANDS":     (6,   "Continuous", 25, "Kabeltracé standvoeding (vloer, langs ruglijn stands)", True),
    "ELEK-STOPCONTACTEN":     (6,   "Continuous", 25, "Stopcontacten 230 V / 16 A per stand", True),
    "ELEK-CEE-400V":          (1,   "Continuous", 25, "CEE-contactdozen 400 V / 32 A", True),
    "ELEK-VERLICHTING":       (40,  "Continuous", 25, "Verlichtingsarmaturen tent", True),
    "ELEK-KABELS-VERLICHTING": (40, "DASHED",     18, "Verlichtingskringen (bovengronds)", True),
    "ELEK-KABELBRUGGEN":      (30,  "Continuous", 25, "Kabelbruggen / kabelmatten over looppaden", True),
    "ELEK-TEKST":             (7,   "Continuous", 18, "Benaming kringen en borden", True),
    # --- noodplan
    "NOOD-UITGANGEN":         (3,   "Continuous", 50, "Nooduitgangen en hoofdingangen", True),
    "NOOD-VLUCHTWEGEN":       (3,   "Continuous", 35, "Vluchtrichting (pijlen)", True),
    "NOOD-NOODVERLICHTING":   (94,  "Continuous", 25, "Nood- en evacuatieverlichting", True),
    "NOOD-BLUSMIDDELEN":      (1,   "Continuous", 25, "Brandblussers en blusdeken", True),
    "NOOD-EHBO":              (3,   "Continuous", 35, "EHBO-post en AED", True),
    "NOOD-VERZAMELPLAATS":    (3,   "Continuous", 35, "Verzamelplaats", True),
    "NOOD-HULPDIENSTEN":      (1,   "DASHED",     35, "Toegangsweg hulpdiensten / hydrant", True),
    "NOOD-HOOFDSCHAKELAAR":   (1,   "Continuous", 35, "Hoofdschakelaar / noodstop elektriciteit", True),
    "NOOD-TEKST":             (7,   "Continuous", 18, "Tekst noodplan", True),
    # --- kader / papierruimte
    "KADER-TITELBLOK":        (7,   "Continuous", 35, "Kader en titelblok", True),
    "KADER-LEGENDE":          (7,   "Continuous", 18, "Legende en notities", True),
    "KADER-VIEWPORT":         (8,   "Continuous", 13, "Viewportkaders (niet plotten)", False),
}

GROEPEN = {
    "ALG": [n for n in LAGEN if n.startswith("ALG-")],
    "ELEK": [n for n in LAGEN if n.startswith("ELEK-")],
    "NOOD": [n for n in LAGEN if n.startswith("NOOD-")],
}

TXT = "ARIAL"


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def add_rect(space, x0, y0, x1, y1, layer, **attr):
    return space.add_lwpolyline(rect(x0, y0, x1, y1), close=True,
                                dxfattribs={"layer": layer, **attr})


def add_fill(space, pts, layer, color=256, transparency=None):
    h = space.add_hatch(color=color, dxfattribs={"layer": layer})
    h.paths.add_polyline_path(pts, is_closed=True)
    if transparency is not None:
        h.transparency = transparency
    return h


def add_txt(space, text, pos, h, layer, align=TextEntityAlignment.MIDDLE_CENTER,
            rot=0.0, color=256):
    t = space.add_text(text, height=h, rotation=rot,
                       dxfattribs={"layer": layer, "style": TXT, "color": color})
    t.set_placement(pos, align=align)
    return t


def add_mtxt(space, text, pos, h, width, layer,
             attach=MTextEntityAlignment.TOP_LEFT):
    m = space.add_mtext(text, dxfattribs={"layer": layer, "style": TXT,
                                          "char_height": h, "width": width})
    m.set_location(pos, attachment_point=attach)
    return m


def ins(space, block, pos, layer, rot=0.0, scale=1.0):
    return space.add_blockref(block, pos, dxfattribs={
        "layer": layer, "rotation": rot,
        "xscale": scale, "yscale": scale})


# ---------------------------------------------------------------------------
# Document en lagen
# ---------------------------------------------------------------------------
def nieuw_document():
    doc = ezdxf.new("R2018", setup=True)
    doc.units = units.M
    doc.header["$INSUNITS"] = 6        # meter
    doc.header["$MEASUREMENT"] = 1     # metrisch
    doc.header["$LUNITS"] = 2          # decimaal
    doc.header["$LUPREC"] = 2
    doc.header["$LTSCALE"] = 2.0       # streepjes ± 1 m in model = 5 mm op papier (1:200)
    doc.header["$PSLTSCALE"] = 0
    doc.header["$LWDISPLAY"] = 1

    if TXT not in doc.styles:
        doc.styles.add(TXT, font="arial.ttf")

    for naam, (kleur, lt, lw, oms, plot) in LAGEN.items():
        laag = doc.layers.add(naam, color=kleur, linetype=lt,
                              lineweight=lw if lw else -3)
        laag.description = oms
        if not plot:
            laag.dxf.plot = 0

    # maatvoeringsstijl (meter, decimale komma)
    doc.dimstyles.new("CAREERDAY", dxfattribs={
        "dimtxt": 0.45, "dimasz": 0.35, "dimexe": 0.3, "dimexo": 0.3,
        "dimgap": 0.12, "dimdec": 2, "dimdsep": ord(","), "dimtad": 1,
        "dimtxsty": TXT, "dimblk": "ARCHTICK", "dimclrd": 256,
        "dimclre": 256, "dimclrt": 256, "dimlfac": 1.0, "dimzin": 8,
        "dimpost": "<> m",
    })
    maak_blokken(doc)
    return doc


# ---------------------------------------------------------------------------
# Blokken (symbolen) – getekend in meter, op laag 0 / BYLAYER zodat ze de laag
# van de invoeging overnemen.
# ---------------------------------------------------------------------------
def maak_blokken(doc):
    b = doc.blocks

    blk = b.new("PAAL")
    blk.add_lwpolyline(rect(-0.125, -0.125, 0.125, 0.125), close=True)
    add_fill(blk, rect(-0.125, -0.125, 0.125, 0.125), "0")

    blk = b.new("STRAMIENBOL")
    blk.add_circle((0, 0), 0.9)

    # stopcontact 230 V (halve cirkel + aansluitstreep, AREI-stijl)
    blk = b.new("STOPCONTACT_230V")
    blk.add_arc((0, 0), 0.3, 0, 180)
    blk.add_line((-0.3, 0), (0.3, 0))
    blk.add_line((0, 0), (0, -0.25))
    add_fill(blk, [(0.3, 0), (0.21, 0.21), (0, 0.3), (-0.21, 0.21), (-0.3, 0)], "0")

    # CEE 400 V: halve cirkel + 3 streepjes (driefasig)
    blk = b.new("CEE_400V")
    blk.add_arc((0, 0), 0.4, 0, 180)
    blk.add_line((-0.4, 0), (0.4, 0))
    blk.add_line((0, 0), (0, -0.35))
    for dx in (-0.12, 0.0, 0.12):
        blk.add_line((dx - 0.06, -0.12), (dx + 0.06, -0.24))

    # subverdeelbord: rechthoek met halve vulling
    blk = b.new("VERDEELBORD")
    blk.add_lwpolyline(rect(-0.5, -0.25, 0.5, 0.25), close=True)
    add_fill(blk, [(-0.5, -0.25), (0.5, -0.25), (0.5, 0.25)], "0")

    # hoofdverdeelbord: volledig gevuld
    blk = b.new("HOOFDVERDEELBORD")
    blk.add_lwpolyline(rect(-0.75, -0.4, 0.75, 0.4), close=True)
    add_fill(blk, rect(-0.75, -0.4, 0.75, 0.4), "0")

    # aggregaat
    blk = b.new("AGGREGAAT")
    blk.add_lwpolyline(rect(-3.0, -1.2, 3.0, 1.2), close=True)
    blk.add_circle((0, 0), 0.9)
    blk.add_text("G", height=0.9, dxfattribs={"style": TXT}).set_placement(
        (0, 0), align=TextEntityAlignment.MIDDLE_CENTER)

    # verlichtingsarmatuur: cirkel met kruis
    blk = b.new("ARMATUUR")
    blk.add_circle((0, 0), 0.4)
    r = 0.4 / math.sqrt(2)
    blk.add_line((-r, -r), (r, r))
    blk.add_line((-r, r), (r, -r))

    # kabelbrug 1 m x 1 m (wordt geschaald in y-richting)
    blk = b.new("KABELBRUG")
    blk.add_lwpolyline(rect(-0.35, -0.5, 0.35, 0.5), close=True)
    h = blk.add_hatch(color=256)
    h.paths.add_polyline_path(rect(-0.35, -0.5, 0.35, 0.5), is_closed=True)
    h.set_pattern_fill("ANSI31", scale=0.04)

    # nooduitgang (groen vak met pijl), 1,6 x 0,8 m, pijl wijst naar +x
    blk = b.new("NOODUITGANG")
    blk.add_lwpolyline(rect(-0.8, -0.4, 0.8, 0.4), close=True)
    add_fill(blk, rect(-0.8, -0.4, 0.8, 0.4), "0")
    pijl = [(-0.55, -0.08), (0.15, -0.08), (0.15, -0.25), (0.6, 0.0),
            (0.15, 0.25), (0.15, 0.08), (-0.55, 0.08)]
    add_fill(blk, pijl, "0", color=7)

    # vluchtrichting-pijl 3 m, wijst naar +x
    blk = b.new("VLUCHTPIJL")
    pts = [(-1.5, -0.15), (0.6, -0.15), (0.6, -0.45), (1.5, 0.0),
           (0.6, 0.45), (0.6, 0.15), (-1.5, 0.15)]
    blk.add_lwpolyline(pts, close=True)
    add_fill(blk, pts, "0")

    # noodverlichting: rechthoek met kruis + gevulde stip
    blk = b.new("NOODVERLICHTING")
    blk.add_lwpolyline(rect(-0.35, -0.2, 0.35, 0.2), close=True)
    blk.add_line((-0.35, -0.2), (0.35, 0.2))
    blk.add_line((-0.35, 0.2), (0.35, -0.2))
    blk.add_circle((0, 0), 0.08)

    # brandblusser: gevulde cirkel
    blk = b.new("BLUSSER")
    blk.add_circle((0, 0), 0.35)
    h = blk.add_hatch(color=256)
    h.paths.add_edge_path().add_arc((0, 0), 0.35, 0, 360)
    blk.add_lwpolyline(rect(-0.07, 0.35, 0.07, 0.6), close=True)

    # blusdeken
    blk = b.new("BLUSDEKEN")
    blk.add_lwpolyline(rect(-0.35, -0.35, 0.35, 0.35), close=True)
    blk.add_line((-0.35, -0.35), (0.35, 0.35))
    blk.add_line((-0.35, 0.35), (0.35, -0.35))

    # EHBO: groen vierkant met wit kruis
    blk = b.new("EHBO")
    blk.add_lwpolyline(rect(-0.5, -0.5, 0.5, 0.5), close=True)
    add_fill(blk, rect(-0.5, -0.5, 0.5, 0.5), "0")
    kruis = [(-0.12, -0.35), (0.12, -0.35), (0.12, -0.12), (0.35, -0.12),
             (0.35, 0.12), (0.12, 0.12), (0.12, 0.35), (-0.12, 0.35),
             (-0.12, 0.12), (-0.35, 0.12), (-0.35, -0.12), (-0.12, -0.12)]
    add_fill(blk, kruis, "0", color=7)

    # AED: groen vierkant met hartje (vereenvoudigd) + bliksem
    blk = b.new("AED")
    blk.add_lwpolyline(rect(-0.5, -0.5, 0.5, 0.5), close=True)
    add_fill(blk, rect(-0.5, -0.5, 0.5, 0.5), "0")
    add_fill(blk, [(0, -0.33), (-0.33, 0.02), (-0.3, 0.25), (-0.14, 0.32),
                   (0, 0.2), (0.14, 0.32), (0.3, 0.25), (0.33, 0.02)], "0", color=7)

    # verzamelplaats: vierkant met 4 pijlen naar binnen + mannetjes (stip)
    blk = b.new("VERZAMELPLAATS")
    blk.add_lwpolyline(rect(-1.5, -1.5, 1.5, 1.5), close=True)
    for ang in (0, 90, 180, 270):
        a = math.radians(ang)
        def rot(p):
            return (p[0] * math.cos(a) - p[1] * math.sin(a),
                    p[0] * math.sin(a) + p[1] * math.cos(a))
        tri = [rot(p) for p in [(1.35, 0.0), (0.85, 0.3), (0.85, -0.3)]]
        add_fill(blk, tri, "0")
    for dx, dy in [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)]:
        blk.add_circle((dx, dy), 0.12)

    # hydrant
    blk = b.new("HYDRANT")
    blk.add_circle((0, 0), 0.5)
    blk.add_text("H", height=0.5, dxfattribs={"style": TXT}).set_placement(
        (0, 0), align=TextEntityAlignment.MIDDLE_CENTER)

    # hoofdschakelaar / noodstop
    blk = b.new("NOODSTOP")
    blk.add_circle((0, 0), 0.45)
    add_fill(blk, rect(-0.15, -0.3, 0.15, 0.3), "0")

    # noordpijl (papierruimte, mm)
    blk = b.new("NOORDPIJL")
    blk.add_circle((0, 0), 10)
    add_fill(blk, [(0, 9), (-4, -6), (0, -3)], "0")
    blk.add_lwpolyline([(0, 9), (4, -6), (0, -3)], close=True)
    blk.add_text("N", height=5, dxfattribs={"style": TXT}).set_placement(
        (0, 14), align=TextEntityAlignment.MIDDLE_CENTER)


# ---------------------------------------------------------------------------
# Geometrie: stands (posities uit grondplan Career Day 25-26)
# ---------------------------------------------------------------------------
import json as _json


def stands():
    """Lijst van stands: dict(code, x0, y0, x1, y1, tent)."""
    res = []
    for s in _json.loads(STANDEN_JSON.read_text()):
        res.append(dict(code=str(s["nr"]), nr=s["nr"], x0=s["x"], y0=s["y"],
                        x1=s["x"] + s["w"], y1=s["y"] + s["h"],
                        tent="1" if s["tent"] == "A" else "2"))
    return res


def bezet(x, y, marge=0.6):
    """True als punt (x,y) in een stand of zone valt (incl. marge)."""
    for s in stands_cache():
        if s["x0"] - marge < x < s["x1"] + marge and s["y0"] - marge < y < s["y1"] + marge:
            return True
    for _, x0, y0, x1, y1, _l in ZONES:
        if x0 - marge < x < x1 + marge and y0 - marge < y < y1 + marge:
            return True
    return False


_CACHE = []


def stands_cache():
    if not _CACHE:
        _CACHE.extend(stands())
    return _CACHE


# ---------------------------------------------------------------------------
# Basis: tent, palen, stramien, omgeving
# ---------------------------------------------------------------------------
def teken_basis(msp):
    add_rect(msp, 0, T2[0], L, T2[1], "BASIS-TENT")
    add_rect(msp, 0, T1[0], L, T1[1], "BASIS-TENT")
    # tussengang (open aan ingangszijde x 0-10 en achteraan x 85-90)
    for y in (T2[1] + 1.0,):
        msp.add_line((10.0, y), (85.0, y), dxfattribs={"layer": "BASIS-TENT-KOPPELING"})
    add_txt(msp, "TUSSENGANG 2,00 m", (47.0, 21.0), 0.5, "BASIS-OMGEVING-TEKST")
    add_txt(msp, "TENT 1  (20 m x 90 m)", (45.0, BT + 2.2), 0.9, "BASIS-OMGEVING-TEKST")
    add_txt(msp, "TENT 2  (20 m x 90 m)", (20.0, -5.0), 0.9, "BASIS-OMGEVING-TEKST")

    for i in range(int(L / PAAL_STAP) + 1):
        x = i * PAAL_STAP
        for y in (T2[0], T2[1], T1[0], T1[1]):
            ins(msp, "PAAL", (x, y), "BASIS-TENT-PALEN")
    for x in (0.0, L):
        for y in (B / 2, T1[0] + B / 2):
            ins(msp, "PAAL", (x, y), "BASIS-TENT-PALEN")

    # stramien: assen 1..19 (x) en A..D (y)
    for i in range(int(L / PAAL_STAP) + 1):
        x = i * PAAL_STAP
        msp.add_line((x, -6.5), (x, BT + 1.5), dxfattribs={"layer": "BASIS-STRAMIEN"})
        ins(msp, "STRAMIENBOL", (x, -7.4), "BASIS-STRAMIEN-TEKST")
        add_txt(msp, str(i + 1), (x, -7.4), 0.7, "BASIS-STRAMIEN-TEKST")
    for y, lbl in ((T2[0], "A"), (T2[1], "B"), (T1[0], "C"), (T1[1], "D")):
        msp.add_line((-6.5, y), (L + 1.5, y), dxfattribs={"layer": "BASIS-STRAMIEN"})
        ins(msp, "STRAMIENBOL", (-7.4 if lbl in "AD" else -9.4, y), "BASIS-STRAMIEN-TEKST")
        add_txt(msp, lbl, (-7.4 if lbl in "AD" else -9.4, y), 0.7, "BASIS-STRAMIEN-TEKST")

    add_rect(msp, -15, -12, 108, 64, "BASIS-OMGEVING")
    add_txt(msp, "SINT-PIETERSPLEIN, GENT  (omgeving indicatief)", (-14.5, 63.2), 0.8,
            "BASIS-OMGEVING-TEKST", align=TextEntityAlignment.MIDDLE_LEFT)
    msp.add_line((-15, 50), (108, 50), dxfattribs={"layer": "BASIS-OMGEVING"})
    msp.add_line((-15, 54), (108, 54), dxfattribs={"layer": "BASIS-OMGEVING"})
    add_txt(msp, "DOORGANG PLEIN (min. 4 m vrij)", (70, 52), 0.7, "BASIS-OMGEVING-TEKST")


# ---------------------------------------------------------------------------
# Algemeen grondplan
# ---------------------------------------------------------------------------
def teken_algemeen(msp):
    for naam, x0, y0, x1, y1, laag in ZONES:
        add_rect(msp, x0, y0, x1, y1, laag)
        if laag in ("ALG-ZONES", "ALG-LOGISTIEK") or naam in ("CV-CHECK",):
            h = msp.add_hatch(color=256, dxfattribs={"layer": laag})
            h.paths.add_polyline_path(rect(x0, y0, x1, y1), is_closed=True)
            h.set_pattern_fill("ANSI31", scale=0.06)
            h.transparency = 0.7
        if naam:
            breed, hoog = x1 - x0, y1 - y0
            rot = 90 if hoog > breed * 1.6 and breed < 5 else 0
            hgt = 0.55 if min(breed, hoog) > 2 else 0.4
            if naam == "RECRUITERS ZONE":
                add_txt(msp, naam, (x0 + 0.3, (y0 + y1) / 2), 0.4, "ALG-ZONES-TEKST",
                        align=TextEntityAlignment.MIDDLE_LEFT)
                continue
            add_txt(msp, naam, ((x0 + x1) / 2, (y0 + y1) / 2), hgt, "ALG-ZONES-TEKST", rot=rot)

    for s in stands_cache():
        pts = rect(s["x0"], s["y0"], s["x1"], s["y1"])
        add_fill(msp, pts, "ALG-STANDS-ARCERING", transparency=0.6)
        add_rect(msp, s["x0"], s["y0"], s["x1"], s["y1"], "ALG-STANDS")
        add_txt(msp, s["code"], ((s["x0"] + s["x1"]) / 2, (s["y0"] + s["y1"]) / 2),
                0.55, "ALG-STANDNUMMERS")

    # sanitair en verwarming buiten (uit plan 25-26)
    add_rect(msp, 78.4, 46.0, 86.4, 49.0, "ALG-SANITAIR")
    add_txt(msp, "TOILETTEN", (82.4, 47.5), 0.55, "ALG-SANITAIR")
    for x, y in ((37.7, -3.45), (69.3, -3.45), (69.3, 42.1), (15.4, 42.1)):
        add_rect(msp, x, y, x + 3.5, y + 3.35, "ALG-LOGISTIEK")
        add_txt(msp, "HEAT", (x + 1.75, y + 1.67), 0.45, "ALG-ZONES-TEKST")
    add_txt(msp, "INGANG", (-2.0, 39.5), 0.7, "ALG-ZONES-TEKST", rot=90)
    add_txt(msp, "UITGANG", (-2.0, 24.5), 0.7, "ALG-ZONES-TEKST", rot=90)
    add_txt(msp, "Standaard stand 2 x 3 m, 30 cm van de tentwand", (55.0, 47.5), 0.5,
            "ALG-ZONES-TEKST")

    dims = [((0, -3.2), (0, 0), (L, 0), 0)]
    for base, p1, p2, ang in (
            ((L + 6.0, 0), (L, 0), (L, BT), 90),
            ((L + 4.0, 0), (L, T2[0]), (L, T2[1]), 90),
            ((L + 4.0, 0), (L, T2[1]), (L, T1[0]), 90),
            ((L + 4.0, 0), (L, T1[0]), (L, T1[1]), 90)):
        dims.append((base, p1, p2, ang))
    for base, p1, p2, ang in dims:
        d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="CAREERDAY",
                               dxfattribs={"layer": "ALG-MAATVOERING"})
        d.render()


# ---------------------------------------------------------------------------
# Elektriciteitsplan
# ---------------------------------------------------------------------------
HVB_POS = (93.5, 21.0)
AGG_POS = (100.0, 21.0)
N_SVB = 10


def svb_posities():
    """Verdeel de stands in N_SVB groepen (k-means op standcentra) en zoek per groep
    een vrij punt in een gang nabij het zwaartepunt voor de verdeelkast (32 A)."""
    pts = [((s["x0"] + s["x1"]) / 2, (s["y0"] + s["y1"]) / 2, s) for s in stands_cache()]
    # startcentra: verdeeld over tent 1 en tent 2 op gelijke x-afstand
    centra = []
    for tent in ("1", "2"):
        sub = sorted([p for p in pts if p[2]["tent"] == tent], key=lambda p: p[0])
        n = N_SVB // 2
        for k in range(n):
            blok = sub[k * len(sub) // n:(k + 1) * len(sub) // n]
            centra.append((sum(p[0] for p in blok) / len(blok), sum(p[1] for p in blok) / len(blok), tent))
    for _ in range(15):
        groepen = [[] for _ in centra]
        for p in pts:
            i = min((i for i, c in enumerate(centra) if c[2] == p[2]["tent"]),
                    key=lambda i: (centra[i][0] - p[0]) ** 2 + (centra[i][1] - p[1]) ** 2)
            groepen[i].append(p)
        centra = [(sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g), c[2])
                  if g else c for g, c in zip(groepen, centra)]
    res = []
    for (cx, cy, tent), g in zip(centra, groepen):
        ty0, ty1 = T1 if tent == "1" else T2
        best = None
        for dx in [i * 0.5 for i in range(-16, 17)]:
            for dy in [i * 0.5 for i in range(-16, 17)]:
                x, y = round(cx + dx, 1), round(cy + dy, 1)
                if not (ty0 + 0.6 < y < ty1 - 0.6 and 1 < x < 89):
                    continue
                if bezet(x, y, 0.9):
                    continue
                d = dx * dx + dy * dy
                if best is None or d < best[0]:
                    best = (d, x, y)
        res.append(((best[1], best[2]), [p[2] for p in g]))
    res.sort(key=lambda r: (r[0][1] < 21, r[0][0]))
    return res


def teken_elektriciteit(msp):
    lay = "ELEK-TEKST"
    ins(msp, "AGGREGAAT", AGG_POS, "ELEK-HOOFDVOEDING", rot=90)
    add_txt(msp, "AGGREGAAT / NETAANSLUITING", (AGG_POS[0] + 2.3, AGG_POS[1]), 0.5, lay, rot=90)
    add_txt(msp, "(ELEK-doorsteek plein: te bevestigen)", (AGG_POS[0] + 3.2, AGG_POS[1]), 0.4, lay, rot=90)
    ins(msp, "HOOFDVERDEELBORD", HVB_POS, "ELEK-HOOFDVOEDING", rot=90)
    add_txt(msp, "HVB 125 A", (HVB_POS[0], HVB_POS[1] + 2.0), 0.5, lay)
    msp.add_line((AGG_POS[0] - 1.2, AGG_POS[1]), (HVB_POS[0] + 0.4, HVB_POS[1]),
                 dxfattribs={"layer": "ELEK-HOOFDVOEDING"})

    # voeding door de tussengang (y = 21) naar elke verdeelkast
    svbs = svb_posities()
    xmin = min(p[0] for p, _ in svbs)
    msp.add_line((HVB_POS[0] - 0.4, 21.0), (min(xmin, 0.8), 21.0),
                 dxfattribs={"layer": "ELEK-VOEDINGSKABELS"})
    add_txt(msp, "hoofdkabel 125 A door tussengang (kabelgoot / bovengronds)", (47.0, 21.55),
            0.38, lay)
    for i, ((x, y), groep) in enumerate(svbs, start=1):
        naam = f"32-{i}"
        msp.add_line((x, 21.0), (x, y), dxfattribs={"layer": "ELEK-VOEDINGSKABELS"})
        ins(msp, "VERDEELBORD", (x, y), "ELEK-VERDEELBORDEN")
        add_txt(msp, naam, (x, y + (0.75 if y > 21 else -0.75)), 0.45, lay)
        for s in groep:
            cx = (s["x0"] + s["x1"]) / 2
            cy = (s["y0"] + s["y1"]) / 2
            # stopcontact aan de rugzijde: kant verst van de dichtste gang ~ kant dichtst bij kast
            ox = cx
            oy = s["y0"] + 0.45 if y < cy else s["y1"] - 0.45
            ins(msp, "STOPCONTACT_230V", (ox, oy), "ELEK-STOPCONTACTEN",
                rot=0 if y < cy else 180)
            msp.add_lwpolyline([(x, y), (x, oy), (ox, oy)],
                               dxfattribs={"layer": "ELEK-KABELS-STANDS"})

    # algemeen: onthaal / vestiaire / CV-check / bar
    sp = {"layer": "ELEK-KABELS-STANDS"}
    ins(msp, "VERDEELBORD", (1.0, 21.0), "ELEK-VERDEELBORDEN", rot=90)
    add_txt(msp, "63-1 algemeen", (1.6, 20.3), 0.45, lay, align=TextEntityAlignment.MIDDLE_LEFT)
    for p in ((4.5, 30.0), (8.0, 38.0), (19.5, 34.6)):
        msp.add_lwpolyline([(1.0, 21.0), (1.0, p[1]), p], dxfattribs=sp)
        ins(msp, "STOPCONTACT_230V", p, "ELEK-STOPCONTACTEN", rot=90)
    for p in ((12.0, 15.5), (12.0, 3.4)):
        msp.add_lwpolyline([(1.0, 21.0), (1.0, 18.0), (12.0, 18.0), p], dxfattribs=sp)
        ins(msp, "CEE_400V", p, "ELEK-CEE-400V", rot=90 if p[1] > 10 else -90)
    add_txt(msp, "bar 400 V / 32 A", (13.9, 16.4), 0.38, lay, align=TextEntityAlignment.MIDDLE_LEFT)

    # verlichting: armaturen h.o.h. 10 m, 2 lijnen per tent
    xs = [5.0 + 10.0 * i for i in range(9)]
    for k, y in enumerate((5.0, 15.0, 27.0, 37.0), start=1):
        msp.add_line((0.4, y), (xs[-1], y), dxfattribs={"layer": "ELEK-KABELS-VERLICHTING"})
        for x in xs:
            ins(msp, "ARMATUUR", (x, y), "ELEK-VERLICHTING")
        add_txt(msp, f"L{k}", (xs[-1] + 1.2, y), 0.55, lay, align=TextEntityAlignment.MIDDLE_LEFT)
    msp.add_line((0.4, 5.0), (0.4, 37.0), dxfattribs={"layer": "ELEK-KABELS-VERLICHTING"})

    # verwarming: aansluiting per heat-unit
    for x, y in ((39.45, -0.4), (71.05, -0.4), (71.05, 42.4), (17.15, 42.4)):
        ins(msp, "STOPCONTACT_230V", (x, y), "ELEK-STOPCONTACTEN", rot=180 if y < 0 else 0)


# ---------------------------------------------------------------------------
# Noodplan
# ---------------------------------------------------------------------------
def uitgang_pos(wand, m, off=0.0):
    """Positie + rotatie (pijl naar buiten) van een uitgang. off>0 = naar binnen."""
    if wand == "S":
        return (m, 0.0 + off), -90
    if wand == "N":
        return (m, BT - off), 90
    if wand == "W":
        return (0.0 + off, m), 180
    return (L - off, m), 0


def uitgang_punt(u):
    code, wand, m, br, oms = u
    return uitgang_pos(wand, m, 0.0)[0]


def in_tent(y):
    return "1" if y > 21 else "2"


def teken_noodplan(msp):
    lay = "NOOD-TEKST"
    for code, wand, m, br, oms in UITGANGEN:
        if wand in ("S", "N"):
            y = 0.0 if wand == "S" else BT
            msp.add_line((m - br / 2, y), (m + br / 2, y),
                         dxfattribs={"layer": "NOOD-UITGANGEN", "lineweight": 100})
        else:
            x = 0.0 if wand == "W" else L
            msp.add_line((x, m - br / 2), (x, m + br / 2),
                         dxfattribs={"layer": "NOOD-UITGANGEN", "lineweight": 100})
        pos, rot = uitgang_pos(wand, m, off=-1.0)
        ins(msp, "NOODUITGANG", pos, "NOOD-UITGANGEN", rot=rot)
        tpos, _ = uitgang_pos(wand, m, off=-2.6 if wand in ("S", "N") else -3.2)
        label = (oms.upper() + " " if oms else code + "  ") + f"{br:.2f} m".replace(".", ",")
        add_txt(msp, label, tpos, 0.5, lay, rot=90 if wand in ("W", "O") else 0)
        npos, _ = uitgang_pos(wand, m, off=0.5)
        ins(msp, "NOODVERLICHTING", npos, "NOOD-NOODVERLICHTING",
            rot=0 if wand in ("S", "N") else 90)

    # vluchtrichting: op een raster van vrije punten, pijl naar de dichtste uitgang
    # in dezelfde tent (tent 2 mag ook via de tussengang-opening aan de ingang)
    for x in [6.0 + 8.0 * i for i in range(11)]:
        for y in (3.0, 9.0, 15.0, 26.5, 32.5, 38.5):
            if bezet(x, y, 0.8):
                continue
            kand = [u for u in UITGANGEN if in_tent(uitgang_punt(u)[1] if u[1] in "WO" else
                                                    (1 if u[1] == "S" else 41)) == in_tent(y)]
            ux, uy = min((uitgang_punt(u) for u in kand),
                         key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
            hoek = math.degrees(math.atan2(uy - y, ux - x))
            ins(msp, "VLUCHTPIJL", (x, y), "NOOD-VLUCHTWEGEN", rot=hoek, scale=0.8)
            if (x - 6) % 16 == 0:
                ins(msp, "NOODVERLICHTING", (x, y + 1.3), "NOOD-NOODVERLICHTING")

    # blussers: naast elke uitgang, aan elke verdeelkast, bar, HVB
    for code, wand, m, br, oms in UITGANGEN:
        p, _ = uitgang_pos(wand, m, off=0.6)
        p = (m + br / 2 + 0.6, p[1]) if wand in ("S", "N") else (p[0], m + br / 2 + 0.6)
        ins(msp, "BLUSSER", p, "NOOD-BLUSMIDDELEN")
    for (x, y), _g in svb_posities():
        ins(msp, "BLUSSER", (x + 0.9, y), "NOOD-BLUSMIDDELEN")
    ins(msp, "BLUSDEKEN", (12.0, 16.0), "NOOD-BLUSMIDDELEN")
    ins(msp, "BLUSSER", (12.0, 2.9), "NOOD-BLUSMIDDELEN")
    ins(msp, "BLUSSER", (96.5, 24.5), "NOOD-BLUSMIDDELEN")
    add_txt(msp, "CO₂ 5 kg", (96.5, 25.5), 0.35, lay)

    ins(msp, "NOODSTOP", (HVB_POS[0], 19.0), "NOOD-HOOFDSCHAKELAAR")
    add_txt(msp, "HOOFDSCHAKELAAR", (HVB_POS[0], 17.9), 0.4, lay)

    ins(msp, "EHBO", (2.5, 33.5), "NOOD-EHBO", scale=1.4)
    add_txt(msp, "EHBO-POST", (2.5, 32.2), 0.4, lay)
    ins(msp, "AED", (2.5, 36.5), "NOOD-EHBO")
    add_txt(msp, "AED", (3.4, 36.5), 0.4, lay, align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(msp, "VEILIGHEIDSCOÖRDINATOR @ INKOM", (2.5, 28.0), 0.35, lay, rot=90)

    add_rect(msp, 32.0, 56.0, 56.0, 63.0, "NOOD-VERZAMELPLAATS")
    ins(msp, "VERZAMELPLAATS", (44.0, 59.5), "NOOD-VERZAMELPLAATS")
    add_txt(msp, "VERZAMELPLAATS (positie i.o.m. stad Gent)", (44.0, 62.3), 0.6, lay)
    for x in (28.0, 57.5):
        msp.add_lwpolyline([(x, BT + 2.0), (x, 49.0), (44.0, 56.0)],
                           dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(-3.5, 24.5), (-12.0, 24.5), (-12.0, 49.0), (32.0, 59.5)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(33.0, -2.0), (33.0, -9.0), (-12.0, -9.0), (-12.0, 24.5)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(82.5, -2.0), (82.5, -9.0), (33.0, -9.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})

    msp.add_lwpolyline([(-15, 52), (108, 52)], dxfattribs={"layer": "NOOD-HULPDIENSTEN"})
    add_txt(msp, "TOEGANG HULPDIENSTEN – VRIJ HOUDEN (min. 4 m)", (20.0, 52.6), 0.6,
            lay, align=TextEntityAlignment.BOTTOM_CENTER)
    add_txt(msp, "brandkraan brandweer: zie situatieplan stad Gent", (-14.0, 48.0), 0.4, lay,
            align=TextEntityAlignment.MIDDLE_LEFT)


# ---------------------------------------------------------------------------
# Papierruimte: kader, titelblok, legende, viewport
# ---------------------------------------------------------------------------
PW, PH = 841.0, 594.0        # A1 liggend
SCHAAL = 200                  # 1:200 -> 1 m = 5 mm
VP_X0, VP_Y0, VP_X1, VP_Y1 = 15.0, 195.0, 640.0, 579.0
MODEL_CENTER = (46.5, 26.0)


def legende_items(plan):
    alg = [
        ("rect", "ALG-STANDS", "Stand 2 x 3 m met standnummer"),
        ("rect", "ALG-ONTHAAL", "Inkom, vestiaire, CV-check, lanyards, goodies"),
        ("rect", "ALG-ZONES", "Recruiters zone, CV-screening, photobooth"),
        ("rect", "ALG-LOGISTIEK", "Logistieke zone, loading bay, heat-unit"),
        ("rect", "ALG-CATERING", "Bar"),
        ("rect", "ALG-SANITAIR", "Toiletten"),
        ("PAAL", "BASIS-TENT-PALEN", "Staander tentstructuur (indicatief)"),
        ("line", "BASIS-TENT-KOPPELING", "Tussengang tent 1 - tent 2"),
        ("line", "BASIS-STRAMIEN", "Stramienas"),
    ]
    elek = [
        ("HOOFDVERDEELBORD", "ELEK-HOOFDVOEDING", "Hoofdverdeelbord 125 A (HVB)"),
        ("VERDEELBORD", "ELEK-VERDEELBORDEN", "Verdeelkast 32 A / 63 A, differentieel 30 mA"),
        ("line", "ELEK-VOEDINGSKABELS", "Voedingskabel HVB - verdeelkast (tussengang)"),
        ("line", "ELEK-KABELS-STANDS", "Kabeltracé vloer (stands / onthaal)"),
        ("STOPCONTACT_230V", "ELEK-STOPCONTACTEN", "Stopcontact 230 V / 16 A (1 per stand)"),
        ("CEE_400V", "ELEK-CEE-400V", "CEE-contactdoos 400 V / 32 A"),
        ("ARMATUUR", "ELEK-VERLICHTING", "LED-armatuur (± 400 W) aan tentstructuur"),
        ("line", "ELEK-KABELS-VERLICHTING", "Verlichtingskring L1-L4 (bovengronds)"),
    ]
    nood = [
        ("NOODUITGANG", "NOOD-UITGANGEN", "Nooduitgang / ingang (vrije breedte)"),
        ("VLUCHTPIJL", "NOOD-VLUCHTWEGEN", "Vluchtrichting"),
        ("line", "NOOD-VLUCHTWEGEN", "Vluchtweg naar verzamelplaats"),
        ("NOODVERLICHTING", "NOOD-NOODVERLICHTING", "Nood-/evacuatieverlichting (pictogram ISO 7010)"),
        ("BLUSSER", "NOOD-BLUSMIDDELEN", "Brandblusser 6 kg ABC (CO₂ 5 kg bij SVB/HVB)"),
        ("BLUSDEKEN", "NOOD-BLUSMIDDELEN", "Blusdeken (bar)"),
        ("EHBO", "NOOD-EHBO", "EHBO-post"),
        ("AED", "NOOD-EHBO", "AED-toestel"),
        ("NOODSTOP", "NOOD-HOOFDSCHAKELAAR", "Hoofdschakelaar elektriciteit"),
        ("VERZAMELPLAATS", "NOOD-VERZAMELPLAATS", "Verzamelplaats"),
        ("line", "NOOD-HULPDIENSTEN", "Toegangsweg hulpdiensten"),
    ]
    return {"ALG": alg, "ELEK": alg[:1] + elek, "NOOD": alg[:1] + nood}[plan]


NOTITIES = {
    "ALG": (
        "{\\fArial|b1;ALGEMENE NOTITIES}\\P"
        "1. Twee tenten van 20 m x 90 m naast elkaar met tussengang van 2,00 m (open aan beide koppen).\\P"
        "2. Indeling en 128 standposities overgenomen van grondplan Career Day 25-26 (stad Gent, 17/02/2026).\\P"
        "3. Standaard stand 2 x 3 m op 30 cm van de tentwand; standnummers 1-73 tent 1, 74-128 tent 2.\\P"
        "4. Maatvoering in meter. Oorsprong (0,0) = hoek tent 2 aan de ingangszijde (stramien 1/A).\\P"
        "5. Ventilatieroosters ondergrondse parking en vaste paaltjes op het plein altijd vrijhouden.\\P"
        "6. Posities staanders indicatief (h.o.h. 5 m) – te controleren met plan tentverhuurder."
    ),
    "ELEK": (
        "{\\fArial|b1;ELEKTRISCHE NOTITIES}\\P"
        "1. Installatie volgens AREI; keuring door erkend organisme vóór openstelling.\\P"
        "2. 10 verdeelkasten 32 A (32-1 ... 32-10) voor de stands + 63-1 algemeen; elke kast differentieel 30 mA.\\P"
        "3. Groepering stands per kast automatisch op afstand; kabels langs ruglijn stands, op looppaden kabelbrug.\\P"
        "4. Hoofdkabel 125 A door de tussengang; aansluiting via ELEK-doorsteek plein of aggregaat.\\P"
        "5. Indicatieve vermogensbalans: stands 128 x 1,5 kW x 0,6 = 115 kW | verlichting 36 x 0,4 = 14 kW |\\P"
        "    bar 2 x 22 kW x 0,8 = 35 kW | heat-units 4 x 3 kW = 12 kW | onthaal 5 kW  →  ± 180 kW.\\P"
        "6. Kabelsecties en beveiligingen te bepalen door de installateur."
    ),
    "NOOD": (
        "{\\fArial|b1;NOODPLAN – NOTITIES}\\P"
        "1. Ingang + uitgang (2 x 3,00 m) + 8 nooduitgangen (8 x 2,40 m): totale uitgangsbreedte 25,2 m.\\P"
        "2. Uitgangen tijdens het event nooit afsluiten; tentzeilen opgerold/vastgezet, drempelvrij.\\P"
        "3. Evacuatie: volg pijlen naar dichtstbijzijnde uitgang, daarna naar de VERZAMELPLAATS op het plein.\\P"
        "4. Bij brand/incident: alarm via veiligheidscoördinator (inkom) – bel 112.\\P"
        "5. Elektriciteit uitschakelen via hoofdschakelaar aan HVB (achterzijde tenten).\\P"
        "6. Max. bezetting, noodverlichting en blusmiddelen af te stemmen met brandweer/preventiedienst."
    ),
}

TITELS = {
    "ALG": "ALGEMEEN GRONDPLAN",
    "ELEK": "ELEKTRICITEITSPLAN",
    "NOOD": "NOODPLAN / EVACUATIEPLAN",
}


def teken_layout(doc, plan, nr):
    naam = {"ALG": "01 Algemeen grondplan", "ELEK": "02 Elektriciteitsplan", "NOOD": "03 Noodplan"}[plan]
    psp = doc.layouts.new(naam)
    psp.page_setup(size=(PW, PH), margins=(0, 0, 0, 0), units="mm",
                   name="ISO_full_bleed_A1_(841.00_x_594.00_MM)",
                   device="DWG To PDF.pc3")
    K = "KADER-TITELBLOK"
    LG = "KADER-LEGENDE"
    add_rect(psp, 0, 0, PW, PH, K, lineweight=13)
    add_rect(psp, 10, 10, PW - 10, PH - 10, K, lineweight=70)

    # viewport
    vp = psp.add_viewport(
        center=((VP_X0 + VP_X1) / 2, (VP_Y0 + VP_Y1) / 2),
        size=(VP_X1 - VP_X0, VP_Y1 - VP_Y0),
        view_center_point=MODEL_CENTER,
        view_height=(VP_Y1 - VP_Y0) / (1000.0 / SCHAAL),
        dxfattribs={"layer": "KADER-VIEWPORT"},
    )
    bevroren = []
    for g in ("ELEK", "NOOD"):
        if g != plan:
            bevroren += GROEPEN[g]
    if plan != "ALG":
        bevroren += ["ALG-MAATVOERING"]
        if plan == "NOOD":
            bevroren += ["ALG-SANITAIR"]
    bevroren = sorted(set(bevroren) - set(GROEPEN[plan]))
    vp.frozen_layers = bevroren
    vp.dxf.flags = vp.dxf.flags | 16384    # viewport vergrendeld
    # in elek- en noodplan worden basis en stands grijs weergegeven (VP-override)
    if plan != "ALG":
        for lnaam in ["ALG-STANDS", "ALG-STANDNUMMERS", "ALG-ONTHAAL",
                      "ALG-CATERING", "ALG-ZONES-TEKST", "ALG-SANITAIR",
                      "BASIS-TENT-PALEN"]:
            ov = doc.layers.get(lnaam).get_vp_overrides()
            ov.set_color(vp.dxf.handle, 8)
            ov.commit()
        ov = doc.layers.get("ALG-STANDS-ARCERING").get_vp_overrides()
        ov.set_color(vp.dxf.handle, 254)
        ov.commit()

    # kolom rechts: legende
    x0, x1 = 650.0, PW - 15.0
    add_rect(psp, x0, 150.0, x1, PH - 15.0, K)
    add_txt(psp, "LEGENDE", (x0 + 5, PH - 24.0), 5.0, LG,
            align=TextEntityAlignment.MIDDLE_LEFT)
    psp.add_line((x0, PH - 30.0), (x1, PH - 30.0), dxfattribs={"layer": K})
    y = PH - 40.0
    for kind, laag, oms in legende_items(plan):
        cx = x0 + 14.0
        if kind == "rect":
            add_rect(psp, cx - 7, y - 3.5, cx + 7, y + 3.5, laag)
            if laag == "ALG-STANDS":
                add_fill(psp, rect(cx - 7, y - 3.5, cx + 7, y + 3.5),
                         "ALG-STANDS-ARCERING", transparency=0.6)
                add_txt(psp, "A01", (cx, y), 2.5, "ALG-STANDNUMMERS")
        elif kind == "circ":
            psp.add_circle((cx, y), 2.5, dxfattribs={"layer": laag})
        elif kind == "line":
            psp.add_line((cx - 9, y), (cx + 9, y), dxfattribs={
                "layer": laag, "linetype": "BYLAYER",
                "ltscale": 0.5 if LAGEN[laag][1] != "Continuous" else 1.0})
        else:
            s = 5.0 if kind not in ("VERZAMELPLAATS", "NOODUITGANG", "KABELBRUG") else 4.0
            if kind == "VLUCHTPIJL":
                s = 5.0
            if kind == "KABELBRUG":
                psp.add_blockref(kind, (cx, y), dxfattribs={
                    "layer": laag, "xscale": 5, "yscale": 9})
            else:
                ins(psp, kind, (cx, y), laag, scale=s)
        add_txt(psp, oms, (x0 + 28.0, y), 2.6, LG,
                align=TextEntityAlignment.MIDDLE_LEFT)
        y -= 13.0 if kind == "VERZAMELPLAATS" else 10.0

    # lagenoverzicht onderaan legende
    y -= 4.0
    add_txt(psp, "Actieve lagengroepen in deze viewport:", (x0 + 5, y), 2.5, LG,
            align=TextEntityAlignment.MIDDLE_LEFT)
    y -= 6.0
    groepen = {"ALG": "BASIS-*  +  ALG-*",
               "ELEK": "BASIS-*  +  ALG-* (grijs)  +  ELEK-*",
               "NOOD": "BASIS-*  +  ALG-* (grijs)  +  NOOD-*"}[plan]
    add_txt(psp, groepen, (x0 + 5, y), 2.5, LG, align=TextEntityAlignment.MIDDLE_LEFT)

    # titelblok
    add_rect(psp, x0, 15.0, x1, 145.0, K)
    rows = [125.0, 105.0, 85.0, 65.0, 50.0, 35.0]
    for r in rows:
        psp.add_line((x0, r), (x1, r), dxfattribs={"layer": K})
    xm = (x0 + x1) / 2
    psp.add_line((xm, 15.0), (xm, 65.0), dxfattribs={"layer": K})
    add_txt(psp, "CAREER DAY 26\u201327", (x0 + 5, 135.0), 7.0, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "Sint-Pietersplein Gent \u2013 2 x (20 m x 90 m)", (x0 + 5, 128.5), 2.8, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "PLAN", (x0 + 3, 121.5), 2.0, K, align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, TITELS[plan], (x0 + 5, 113.0), 5.5, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "INHOUD", (x0 + 3, 101.5), 2.0, K, align=TextEntityAlignment.MIDDLE_LEFT)
    inhoud = {"ALG": "128 stands, inkom, vestiaire, bar, logistiek",
              "ELEK": "Voeding, verdeelkasten, stopcontacten, verlichting",
              "NOOD": "Uitgangen, vluchtwegen, blusmiddelen, EHBO"}[plan]
    add_txt(psp, inhoud, (x0 + 5, 93.0), 3.0, K, align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "PROJECT / LOCATIE", (x0 + 3, 81.5), 2.0, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "Sint-Pietersplein, 9000 Gent", (x0 + 5, 73.0), 3.0, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    cellen = [("SCHAAL", "1:200", x0, 65.0), ("FORMAAT", "A1 liggend", xm, 65.0),
              ("DATUM", "17/11/2026", x0, 50.0), ("BLAD", f"{nr} / 3", xm, 50.0),
              ("GETEKEND", "...............", x0, 35.0),
              ("REVISIE", "A \u2013 eerste uitgave", xm, 35.0)]
    for lbl, val, cx0, top in cellen:
        add_txt(psp, lbl, (cx0 + 3, top - 3.0), 2.0, K,
                align=TextEntityAlignment.MIDDLE_LEFT)
        add_txt(psp, val, (cx0 + 5, top - 10.0), 3.2, K,
                align=TextEntityAlignment.MIDDLE_LEFT)

    # notitieblok onder viewport
    add_rect(psp, VP_X0, 15.0, VP_X1, 185.0, K)
    add_mtxt(psp, NOTITIES[plan], (VP_X0 + 5, 180.0), 3.2, 400.0, LG)

    # schaalstok 0-20 m
    sx, sy = VP_X0 + 440.0, 160.0
    add_txt(psp, "SCHAAL 1:200", (sx, sy + 12.0), 3.0, LG,
            align=TextEntityAlignment.MIDDLE_LEFT)
    for i in range(4):
        x_a = sx + i * 25.0
        pts = rect(x_a, sy, x_a + 25.0, sy + 4.0)
        psp.add_lwpolyline(pts, close=True, dxfattribs={"layer": LG})
        if i % 2 == 0:
            add_fill(psp, pts, LG)
        add_txt(psp, f"{i * 5}", (x_a, sy - 4.0), 2.5, LG)
    add_txt(psp, "20 m", (sx + 100.0, sy - 4.0), 2.5, LG)
    # noordpijl (Y-as model = noord, indicatief)
    ins(psp, "NOORDPIJL", (sx + 160.0, sy + 2.0), LG)
    add_txt(psp, "(indicatief)", (sx + 160.0, sy - 14.0), 2.2, LG)
    return psp


# ---------------------------------------------------------------------------
# Opbouw
# ---------------------------------------------------------------------------
def bouw(plannen, bestandsnaam):
    doc = nieuw_document()
    msp = doc.modelspace()
    teken_basis(msp)
    teken_algemeen(msp)           # stands zijn ondergrond voor alle plannen
    if "ELEK" in plannen:
        teken_elektriciteit(msp)
    if "NOOD" in plannen:
        teken_noodplan(msp)
    for i, p in enumerate(plannen, start=1):
        teken_layout(doc, p, {"ALG": 1, "ELEK": 2, "NOOD": 3}[p])
    if "Layout1" in doc.layouts:
        doc.layouts.delete("Layout1")
    # ongebruikte lagen van andere plannen verwijderen in losse bestanden
    if len(plannen) == 1:
        gebruikt = {e.dxf.layer for e in msp} | {"0", "KADER-VIEWPORT"}
        for lay in doc.layouts:
            gebruikt |= {e.dxf.layer for e in lay}
        for naam in list(LAGEN):
            g = naam.split("-")[0]
            if g in ("ELEK", "NOOD") and g not in plannen and naam not in gebruikt:
                doc.layers.remove(naam)
    doc.set_modelspace_vport(height=80, center=MODEL_CENTER)
    pad = OUT / bestandsnaam
    doc.saveas(pad)
    return pad


if __name__ == "__main__":
    print(bouw(["ALG", "ELEK", "NOOD"], "Careerday_grondplannen.dxf"))
    print(bouw(["ALG"], "Careerday_01_algemeen_grondplan.dxf"))
    print(bouw(["ELEK"], "Careerday_02_elektriciteitsplan.dxf"))
    print(bouw(["NOOD"], "Careerday_03_noodplan.dxf"))
