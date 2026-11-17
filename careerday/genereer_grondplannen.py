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
# Afmetingen
# ---------------------------------------------------------------------------
L = 90.0          # lengte tent
B = 20.0          # breedte één tent
BT = 2 * B        # totale breedte
PAAL_STAP = 5.0   # traveeafstand tentstructuur

STAND_B = 3.0     # standbreedte (langs de gang)
STAND_D = 3.0     # standdiepte
BLOK1 = (12.0, 42.0)   # x-bereik standenblok west
BLOK2 = (46.0, 76.0)   # x-bereik standenblok oost
DWARSGANG = (42.0, 46.0)

# y-indeling per tent A (tent B = spiegelbeeld rond y = 20)
#   0-3 wandstands | 3-7 gang | 7-13 eilandstands (rug aan rug) | 13-17 gang | 17-20 gootstands
RIJEN_A = [  # (y0, y1, ruglijn-y, naam)
    (0.0, 3.0, 0.0, "wand"),
    (7.0, 10.0, 10.0, "eiland-z"),
    (10.0, 13.0, 10.0, "eiland-n"),
    (17.0, 20.0, 20.0, "goot"),
]
GANGEN_Y = [5.0, 15.0, 25.0, 35.0]   # aslijnen van de langsgangen (4 m breed)

# Nooduitgangen: (code, wand, middenpositie, breedte, omschrijving)
UITGANGEN = [
    ("HI-A", "W", 10.0, 4.0, "Hoofdingang A"),
    ("HI-B", "W", 30.0, 4.0, "Hoofdingang B"),
    ("NU1", "S", 6.0, 2.4, ""),
    ("NU2", "S", 44.0, 2.4, ""),
    ("NU3", "S", 82.0, 2.4, ""),
    ("NU4", "N", 6.0, 2.4, ""),
    ("NU5", "N", 44.0, 2.4, ""),
    ("NU6", "N", 82.0, 2.4, ""),
    ("NU7", "O", 10.0, 2.4, ""),
    ("NU8", "O", 30.0, 2.4, ""),
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
    "ALG-MEUBILAIR":          (8,   "Continuous", 18, "Statafels en meubilair", True),
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
# Geometrie: stands
# ---------------------------------------------------------------------------
def stands():
    """Lijst van stands: dict(code, x0, y0, x1, y1, rug_y)."""
    res = []
    for tent, spiegel in (("A", False), ("B", True)):
        nr = 1
        rijen = RIJEN_A
        for y0, y1, rug, naam in rijen:
            if spiegel:
                y0, y1, rug = BT - y1, BT - y0, BT - rug
            for bx0, bx1 in (BLOK1, BLOK2):
                n = int(round((bx1 - bx0) / STAND_B))
                for i in range(n):
                    x0 = bx0 + i * STAND_B
                    res.append(dict(code=f"{tent}{nr:02d}", x0=x0, y0=y0,
                                    x1=x0 + STAND_B, y1=y1, rug=rug, rij=naam,
                                    tent=tent))
                    nr += 1
    return res


# ---------------------------------------------------------------------------
# Basis: tent, palen, stramien, omgeving
# ---------------------------------------------------------------------------
def teken_basis(msp):
    # tenten
    add_rect(msp, 0, 0, L, B, "BASIS-TENT")
    add_rect(msp, 0, B, L, BT, "BASIS-TENT")
    msp.add_line((0, B), (L, B), dxfattribs={"layer": "BASIS-TENT-KOPPELING"})
    add_txt(msp, "TENT A  (20 m x 90 m)", (25.0, -5.0), 0.9, "BASIS-OMGEVING-TEKST")
    add_txt(msp, "TENT B  (20 m x 90 m)", (25.0, BT + 2.2), 0.9, "BASIS-OMGEVING-TEKST")

    # staanders: langs lange zijden en goot h.o.h. 5 m, kopgevels tussenpaal
    for i in range(int(L / PAAL_STAP) + 1):
        x = i * PAAL_STAP
        for y in (0.0, B, BT):
            ins(msp, "PAAL", (x, y), "BASIS-TENT-PALEN")
    for x in (0.0, L):
        for y in (B / 2, B + B / 2):
            ins(msp, "PAAL", (x, y), "BASIS-TENT-PALEN")

    # stramien: assen 1..19 (x) en A..C (y)
    for i in range(int(L / PAAL_STAP) + 1):
        x = i * PAAL_STAP
        msp.add_line((x, -6.5), (x, BT + 1.5), dxfattribs={"layer": "BASIS-STRAMIEN"})
        ins(msp, "STRAMIENBOL", (x, -7.4), "BASIS-STRAMIEN-TEKST")
        add_txt(msp, str(i + 1), (x, -7.4), 0.7, "BASIS-STRAMIEN-TEKST")
    for j, (y, lbl) in enumerate(((0.0, "A"), (B, "B"), (BT, "C"))):
        msp.add_line((-6.5, y), (L + 1.5, y), dxfattribs={"layer": "BASIS-STRAMIEN"})
        ins(msp, "STRAMIENBOL", (-7.4, y), "BASIS-STRAMIEN-TEKST")
        add_txt(msp, lbl, (-7.4, y), 0.7, "BASIS-STRAMIEN-TEKST")

    # omgeving
    add_rect(msp, -15, -12, 108, 64, "BASIS-OMGEVING")
    add_txt(msp, "TERREINGRENS (indicatief)", (-14.5, 63.2), 0.8,
            "BASIS-OMGEVING-TEKST", align=TextEntityAlignment.MIDDLE_LEFT)
    # weg noordzijde (ook toegang hulpdiensten)
    msp.add_line((-15, 44), (108, 44), dxfattribs={"layer": "BASIS-OMGEVING"})
    msp.add_line((-15, 48), (108, 48), dxfattribs={"layer": "BASIS-OMGEVING"})
    add_txt(msp, "TOEGANGSWEG (verhard, 4 m)", (70, 44.9), 0.7, "BASIS-OMGEVING-TEKST")


# ---------------------------------------------------------------------------
# Algemeen grondplan
# ---------------------------------------------------------------------------
def teken_algemeen(msp):
    # stands
    for s in stands():
        pts = rect(s["x0"], s["y0"], s["x1"], s["y1"])
        add_fill(msp, pts, "ALG-STANDS-ARCERING", transparency=0.6)
        add_rect(msp, s["x0"], s["y0"], s["x1"], s["y1"], "ALG-STANDS")
        add_txt(msp, s["code"], ((s["x0"] + s["x1"]) / 2, (s["y0"] + s["y1"]) / 2),
                0.55, "ALG-STANDNUMMERS")

    # gangen benoemen
    for y in GANGEN_Y:
        for xm in ((BLOK1[0] + BLOK1[1]) / 2, (BLOK2[0] + BLOK2[1]) / 2):
            add_txt(msp, "GANG  4,00 m", (xm, y), 0.6, "ALG-ZONES-TEKST")
    add_txt(msp, "DWARSGANG 4,00 m", (44, 17.5), 0.6, "ALG-ZONES-TEKST", rot=90)
    add_txt(msp, "DWARSGANG 4,00 m", (44, 37.0), 0.6, "ALG-ZONES-TEKST", rot=90)

    # --- onthaalzone (x 0 - 12)
    add_txt(msp, "ONTHAAL / INKOMHAL", (6.2, 33.8), 0.6, "ALG-ZONES-TEKST")
    # balies
    add_rect(msp, 6.0, 13.5, 7.0, 18.5, "ALG-ONTHAAL")
    add_rect(msp, 6.0, 21.5, 7.0, 26.5, "ALG-ONTHAAL")
    add_txt(msp, "ONTHAALBALIE", (6.5, 16.0), 0.45, "ALG-ONTHAAL", rot=90)
    add_txt(msp, "REGISTRATIE", (6.5, 24.0), 0.45, "ALG-ONTHAAL", rot=90)
    # vestiaire
    add_rect(msp, 0.0, 0.0, 4.0, 5.0, "ALG-ONTHAAL")
    add_rect(msp, 3.0, 0.5, 3.6, 4.5, "ALG-ONTHAAL")
    add_txt(msp, "VESTIAIRE", (1.5, 2.5), 0.45, "ALG-ONTHAAL", rot=90)
    # EHBO-ruimte (algemeen weergegeven, symbool in noodplan)
    add_rect(msp, 0.0, 35.0, 4.0, 40.0, "ALG-ONTHAAL")
    add_txt(msp, "EHBO", (2.0, 38.6), 0.5, "ALG-ONTHAAL")
    # ingangen labels
    add_txt(msp, "INGANG", (1.8, 10.0), 0.7, "ALG-ZONES-TEKST", rot=90)
    add_txt(msp, "INGANG", (1.8, 30.0), 0.7, "ALG-ZONES-TEKST", rot=90)

    # --- cateringzone (x 76 - 90)
    add_txt(msp, "CATERING / NETWERKZONE", (83.2, 38.0), 0.5, "ALG-ZONES-TEKST")
    add_rect(msp, 86.0, 14.0, 87.2, 26.0, "ALG-CATERING")          # toog
    add_rect(msp, 87.2, 14.0, 90.0, 26.0, "ALG-CATERING")          # achterbar
    add_txt(msp, "BAR", (86.6, 20.0), 0.6, "ALG-CATERING", rot=90)
    add_txt(msp, "achterbar /\\Pkoeling", (88.6, 22.8), 0.4, "ALG-CATERING", rot=90)
    for x in (80.0, 83.0):
        for y in (5.0, 9.0, 13.0, 27.0, 31.0, 35.0):
            msp.add_circle((x, y), 0.4, dxfattribs={"layer": "ALG-MEUBILAIR"})
    add_txt(msp, "statafels Ø 0,80 m", (81.5, 2.5), 0.4, "ALG-MEUBILAIR")

    # --- sanitair (buiten, westzijde)
    add_rect(msp, -10.5, 31.0, -7.5, 41.0, "ALG-SANITAIR")
    add_txt(msp, "SANITAIRE UNIT", (-9.0, 36.0), 0.55, "ALG-SANITAIR", rot=90)
    msp.add_lwpolyline([(0, 32.5), (-7.5, 32.5)], dxfattribs={"layer": "ALG-SANITAIR"})
    msp.add_lwpolyline([(0, 34.5), (-7.5, 34.5)], dxfattribs={"layer": "ALG-SANITAIR"})
    add_txt(msp, "overdekte loopzone", (-3.75, 33.5), 0.35, "ALG-SANITAIR")

    # --- maatvoering
    dims = []
    dims.append(((0, -3.2), (0, 0), (L, 0), 0))
    # ketting x
    xs = [0, BLOK1[0], BLOK1[1], BLOK2[0], BLOK2[1], L]
    for a, b_ in zip(xs, xs[1:]):
        dims.append(((0, -1.6), (a, 0), (b_, 0), 0))
    # breedte totaal + per tent
    dims.append(((L + 6.0, 0), (L, 0), (L, BT), 90))
    dims.append(((L + 4.0, 0), (L, 0), (L, B), 90))
    dims.append(((L + 4.0, 0), (L, B), (L, BT), 90))
    # ketting y in blok 2 (x = 76)
    ys = [0, 3, 7, 13, 17, 20, 23, 27, 33, 37, 40]
    for a, b_ in zip(ys, ys[1:]):
        dims.append(((-4.0, 0), (0, a), (0, b_), 90))
    for base, p1, p2, ang in dims:
        d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang,
                               dimstyle="CAREERDAY",
                               dxfattribs={"layer": "ALG-MAATVOERING"})
        d.render()


# ---------------------------------------------------------------------------
# Elektriciteitsplan
# ---------------------------------------------------------------------------
SVB = {   # naam: (positie, omschrijving)
    "SVB-0": ((0.6, 20.0), "Algemeen: verlichting + onthaal"),
    "SVB-1": ((11.0, 20.0), "Stands blok west (A/B 01-10, ...)"),
    "SVB-2": ((77.0, 20.0), "Stands blok oost"),
    "SVB-C": ((89.4, 20.0), "Catering / bar"),
}
HVB_POS = (93.5, 20.0)
AGG_POS = (100.0, 20.0)


def teken_elektriciteit(msp):
    lay = "ELEK-TEKST"
    # hoofdvoeding
    ins(msp, "AGGREGAAT", AGG_POS, "ELEK-HOOFDVOEDING", rot=90)
    add_txt(msp, "AGGREGAAT 250 kVA", (AGG_POS[0] + 2.3, 20), 0.6, lay, rot=90)
    add_txt(msp, "(of tijdelijke netaansluiting)", (AGG_POS[0] + 3.2, 20), 0.45, lay, rot=90)
    ins(msp, "HOOFDVERDEELBORD", HVB_POS, "ELEK-HOOFDVOEDING", rot=90)
    add_txt(msp, "HVB", (HVB_POS[0], 22.0), 0.6, lay)
    msp.add_line((AGG_POS[0] - 1.2, 20), (HVB_POS[0] + 0.4, 20),
                 dxfattribs={"layer": "ELEK-HOOFDVOEDING"})
    add_txt(msp, "afstand tot tent ≥ 5 m", (AGG_POS[0], 15.5), 0.4, lay)

    # voedingskabels HVB -> SVB's (bovengronds langs goot)
    msp.add_line((HVB_POS[0] - 0.4, 20.0), (SVB["SVB-0"][0][0] + 0.25, 20.0),
                 dxfattribs={"layer": "ELEK-VOEDINGSKABELS"})
    add_txt(msp, "voeding HVB \u2192 SVB's", (81.5, 20.3), 0.4, lay,
            align=TextEntityAlignment.BOTTOM_CENTER)
    add_txt(msp, "bovengronds langs goot (h \u2265 3 m)", (81.5, 19.7), 0.4, lay,
            align=TextEntityAlignment.TOP_CENTER)
    for naam, (pos, oms) in SVB.items():
        rot = 90 if naam in ("SVB-0", "SVB-C") else 0
        ins(msp, "VERDEELBORD", pos, "ELEK-VERDEELBORDEN", rot=rot)
    add_txt(msp, "SVB-0", (1.9, 21.6), 0.5, lay)
    add_txt(msp, "SVB-1", (10.2, 21.6), 0.5, lay)
    add_txt(msp, "SVB-2", (77.8, 21.6), 0.5, lay)
    add_txt(msp, "SVB-C", (89.4, 26.8), 0.5, lay)

    # kabeltracés stands vanuit SVB-1 en SVB-2
    for svb, (xa, xb) in (("SVB-1", BLOK1), ("SVB-2", BLOK2)):
        xs = SVB[svb][0][0]
        far = xa if svb == "SVB-2" else xb
        sp = {"layer": "ELEK-KABELS-STANDS"}
        # goot-ruglijn y=20
        msp.add_line((xs, 20.0), (far, 20.0), dxfattribs=sp)
        # vertikale verdeling langs kop blok
        msp.add_line((xs, 0.15), (xs, BT - 0.15), dxfattribs=sp)
        for y in (0.15, 10.0, 30.0, BT - 0.15):
            msp.add_line((xs, y), (far, y), dxfattribs=sp)
        # kabelbruggen over de langsgangen
        for yg in GANGEN_Y:
            msp.add_blockref("KABELBRUG", (xs, yg), dxfattribs={
                "layer": "ELEK-KABELBRUGGEN", "xscale": 1.0, "yscale": 4.4})

    # stopcontacten per stand, tegen de rugzijde
    for s in stands():
        xm = (s["x0"] + s["x1"]) / 2
        if abs(s["rug"] - s["y0"]) < 1e-6:     # rug onderaan -> symbool naar boven
            pos, rot = (xm, s["y0"] + 0.55), 0
        else:                                  # rug bovenaan
            pos, rot = (xm, s["y1"] - 0.55), 180
        ins(msp, "STOPCONTACT_230V", pos, "ELEK-STOPCONTACTEN", rot=rot)

    add_txt(msp, "standkringen SVB-1", (27.0, 5.9), 0.45, lay)
    add_txt(msp, "standkringen SVB-2", (61.0, 5.9), 0.45, lay)

    # onthaal / algemeen vanuit SVB-0
    sp = {"layer": "ELEK-KABELS-STANDS"}
    msp.add_lwpolyline([(0.3, 20.0), (0.3, 6.5)], dxfattribs=sp)
    msp.add_lwpolyline([(0.3, 20.0), (0.3, 33.5)], dxfattribs=sp)
    msp.add_lwpolyline([(0.6, 20.0), (5.6, 20.0), (5.6, 16.0)], dxfattribs=sp)
    msp.add_lwpolyline([(5.6, 20.0), (5.6, 24.0)], dxfattribs=sp)
    ins(msp, "STOPCONTACT_230V", (5.6, 16.0), "ELEK-STOPCONTACTEN", rot=90)
    ins(msp, "STOPCONTACT_230V", (5.6, 24.0), "ELEK-STOPCONTACTEN", rot=90)
    ins(msp, "STOPCONTACT_230V", (0.3, 6.5), "ELEK-STOPCONTACTEN", rot=-90)
    ins(msp, "STOPCONTACT_230V", (0.3, 33.5), "ELEK-STOPCONTACTEN", rot=-90)
    ins(msp, "KABELBRUG", (3.0, 20.0), "ELEK-KABELBRUGGEN", rot=90)

    # catering vanuit SVB-C
    msp.add_lwpolyline([(89.4, 19.4), (89.4, 15.5), (88.3, 15.5)], dxfattribs=sp)
    msp.add_lwpolyline([(89.4, 20.6), (89.4, 24.5), (88.3, 24.5)], dxfattribs=sp)
    ins(msp, "CEE_400V", (88.3, 15.5), "ELEK-CEE-400V", rot=90)
    ins(msp, "CEE_400V", (88.3, 24.5), "ELEK-CEE-400V", rot=90)
    msp.add_lwpolyline([(89.4, 17.5), (87.7, 17.5)], dxfattribs=sp)
    msp.add_lwpolyline([(89.4, 22.5), (87.7, 22.5)], dxfattribs=sp)
    ins(msp, "STOPCONTACT_230V", (87.7, 17.5), "ELEK-STOPCONTACTEN", rot=90)
    ins(msp, "STOPCONTACT_230V", (87.7, 22.5), "ELEK-STOPCONTACTEN", rot=90)
    add_txt(msp, "400V/32A", (88.6, 13.3), 0.35, lay)

    # verlichting: armaturen h.o.h. 10 m, 4 lijnen, kringen L1-L4 vanuit SVB-0
    xs = [5.0 + 10.0 * i for i in range(9)]
    for k, y in enumerate((5.0, 15.0, 25.0, 35.0), start=1):
        msp.add_line((1.6, y), (xs[-1], y),
                     dxfattribs={"layer": "ELEK-KABELS-VERLICHTING"})
        for x in xs:
            ins(msp, "ARMATUUR", (x, y), "ELEK-VERLICHTING")
        add_txt(msp, f"L{k}", (xs[-1] + 1.2, y), 0.55, lay,
                align=TextEntityAlignment.MIDDLE_LEFT)
    msp.add_line((1.6, 5.0), (1.6, 35.0),
                 dxfattribs={"layer": "ELEK-KABELS-VERLICHTING"})
    msp.add_line((0.6, 20.4), (1.6, 20.4),
                 dxfattribs={"layer": "ELEK-KABELS-VERLICHTING"})


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


def teken_noodplan(msp):
    lay = "NOOD-TEKST"
    for code, wand, m, br, oms in UITGANGEN:
        # opening in tentwand aanduiden
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
        tpos, _ = uitgang_pos(wand, m, off=-2.6)
        label = f"{code}  {br:.2f} m".replace(".", ",")
        trot = 90 if wand in ("W", "O") else 0
        add_txt(msp, label, tpos, 0.55, lay, rot=trot)
        # noodverlichting boven elke uitgang (binnenzijde)
        npos, nrot = uitgang_pos(wand, m, off=0.5)
        ins(msp, "NOODVERLICHTING", npos, "NOOD-NOODVERLICHTING",
            rot=0 if wand in ("S", "N") else 90)

    # vluchtrichtingen (pijlen)
    pijlen = []
    for y in GANGEN_Y:
        # blok west: splitsing op x = 27
        pijlen += [((20.0, y), 180), ((34.0, y), 0)]
        # blok oost: splitsing op x = 61
        pijlen += [((54.0, y), 180), ((68.0, y), 0)]
    # dwarsgang: naar NU2 (zuid) en NU5 (noord)
    pijlen += [((44.0, 11.0), -90), ((44.0, 4.0), -90),
               ((44.0, 29.0), 90), ((44.0, 36.0), 90)]
    # onthaalzone
    pijlen += [((9.0, 5.0), 180), ((6.0, 2.6), -90), ((9.0, 35.0), 180),
               ((6.0, 37.4), 90), ((9.0, 15.0), 180), ((9.0, 25.0), 180),
               ((3.5, 11.5), 180), ((3.5, 28.5), 180)]
    # cateringzone
    pijlen += [((79.0, 2.6), -90), ((82.0, 2.6), -90), ((79.0, 37.4), 90),
               ((82.0, 37.4), 90), ((84.5, 10.0), 0), ((84.5, 30.0), 0)]
    for pos, rot in pijlen:
        ins(msp, "VLUCHTPIJL", pos, "NOOD-VLUCHTWEGEN", rot=rot)
    # vluchtwegen in de dwarsgang en gangen: hartlijn
    for y in GANGEN_Y:
        msp.add_line((12.0, y), (76.0, y), dxfattribs={
            "layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED", "lineweight": 18})
    msp.add_line((44.0, 0.0), (44.0, BT), dxfattribs={
        "layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED", "lineweight": 18})

    # noodverlichting langs gangen (aan tentstructuur)
    for y in GANGEN_Y:
        for x in (12.0, 27.0, 61.0, 76.0):
            ins(msp, "NOODVERLICHTING", (x, y + 1.2), "NOOD-NOODVERLICHTING")
    for y in (10.0, 20.0, 30.0):
        ins(msp, "NOODVERLICHTING", (44.0, y), "NOOD-NOODVERLICHTING", rot=90)

    # brandblussers: bij elke uitgang (binnen, naast opening), SVB's, bar, aggregaat
    blussers = []
    for code, wand, m, br, oms in UITGANGEN:
        p, _ = uitgang_pos(wand, m, off=0.6)
        if wand in ("S", "N"):
            p = (m + br / 2 + 0.6, p[1])
        else:
            p = (p[0], m + br / 2 + 0.6)
        blussers.append(p)
    blussers += [(11.0, 21.2), (77.0, 18.8), (1.4, 18.0), (44.0, 21.2)]
    for p in blussers:
        ins(msp, "BLUSSER", p, "NOOD-BLUSMIDDELEN")
    ins(msp, "BLUSSER", (88.5, 27.2), "NOOD-BLUSMIDDELEN")
    ins(msp, "BLUSDEKEN", (88.5, 12.8), "NOOD-BLUSMIDDELEN")
    add_txt(msp, "blusdeken", (88.5, 12.0), 0.35, lay)
    ins(msp, "BLUSSER", (96.5, 24.0), "NOOD-BLUSMIDDELEN")
    add_txt(msp, "CO₂ 5 kg", (96.5, 25.0), 0.35, lay)

    # hoofdschakelaar
    ins(msp, "NOODSTOP", (HVB_POS[0], 18.0), "NOOD-HOOFDSCHAKELAAR")
    add_txt(msp, "HOOFDSCHAKELAAR", (HVB_POS[0] + 0.0, 16.9), 0.4, lay)
    add_txt(msp, "AGGREGAAT", (AGG_POS[0], 20), 0.6, lay, rot=90)
    add_rect(msp, AGG_POS[0] - 1.2, 17.0, AGG_POS[0] + 1.2, 23.0,
             "NOOD-HOOFDSCHAKELAAR")

    # EHBO + AED + veiligheidspost
    ins(msp, "EHBO", (2.0, 37.0), "NOOD-EHBO", scale=1.4)
    add_txt(msp, "EHBO-POST", (2.0, 35.6), 0.4, lay)
    ins(msp, "AED", (7.6, 20.0), "NOOD-EHBO")
    add_txt(msp, "AED", (8.6, 20.0), 0.4, lay, align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(msp, "VEILIGHEIDSCOÖRDINATOR", (7.6, 12.6), 0.35, lay)
    add_txt(msp, "@ onthaalbalie", (7.6, 12.0), 0.35, lay)

    # verzamelplaats
    add_rect(msp, 32.0, 51.0, 56.0, 61.0, "NOOD-VERZAMELPLAATS")
    ins(msp, "VERZAMELPLAATS", (44.0, 56.5), "NOOD-VERZAMELPLAATS")
    add_txt(msp, "VERZAMELPLAATS", (44.0, 59.6), 0.8, lay)
    add_txt(msp, "± 240 m²", (44.0, 52.3), 0.5, lay)
    # route naar verzamelplaats
    for x in (6.0, 44.0, 82.0):
        msp.add_lwpolyline([(x, BT + 2.0), (x, 43.5)], dxfattribs={
            "layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(6.0, 49.0), (6.0, 50.0), (32.0, 56.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(82.0, 49.0), (82.0, 50.0), (56.0, 56.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(44.0, 49.0), (44.0, 51.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    add_txt(msp, "vanuit zuidzijde: rond tent via westkant", (-12.0, -9.0), 0.5, lay,
            align=TextEntityAlignment.MIDDLE_LEFT)
    msp.add_lwpolyline([(6.0, -2.0), (6.0, -4.0), (-13.0, -4.0), (-13.0, 46.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(44.0, -2.0), (44.0, -4.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})
    msp.add_lwpolyline([(82.0, -2.0), (82.0, -4.0), (44.0, -4.0)],
                       dxfattribs={"layer": "NOOD-VLUCHTWEGEN", "linetype": "DASHED"})

    # hulpdiensten
    msp.add_lwpolyline([(-15, 46), (108, 46)], dxfattribs={"layer": "NOOD-HULPDIENSTEN"})
    add_txt(msp, "TOEGANG HULPDIENSTEN – VRIJ HOUDEN (min. 4 m)", (20.0, 46.6), 0.6,
            lay, align=TextEntityAlignment.BOTTOM_CENTER)
    ins(msp, "HYDRANT", (-12.0, 49.5), "NOOD-HULPDIENSTEN")
    add_txt(msp, "hydrant (positie te bevestigen)", (-11.2, 49.5), 0.4, lay,
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
        ("rect", "ALG-STANDS", "Stand 3 x 3 m met standnummer"),
        ("rect", "ALG-ONTHAAL", "Onthaal / vestiaire / EHBO-ruimte"),
        ("rect", "ALG-CATERING", "Bar / catering"),
        ("circ", "ALG-MEUBILAIR", "Statafel"),
        ("rect", "ALG-SANITAIR", "Sanitaire unit"),
        ("PAAL", "BASIS-TENT-PALEN", "Staander tentstructuur"),
        ("line", "BASIS-TENT-KOPPELING", "Koppeling / goot tent A - B"),
        ("line", "BASIS-STRAMIEN", "Stramienas"),
    ]
    elek = [
        ("HOOFDVERDEELBORD", "ELEK-HOOFDVOEDING", "Hoofdverdeelbord (HVB)"),
        ("VERDEELBORD", "ELEK-VERDEELBORDEN", "Subverdeelbord (SVB) met differentieel 30 mA"),
        ("line", "ELEK-VOEDINGSKABELS", "Voedingskabel HVB-SVB (bovengronds)"),
        ("line", "ELEK-KABELS-STANDS", "Kabeltracé vloer (stands / onthaal)"),
        ("STOPCONTACT_230V", "ELEK-STOPCONTACTEN", "Stopcontact 230 V / 16 A (1 per stand)"),
        ("CEE_400V", "ELEK-CEE-400V", "CEE-contactdoos 400 V / 32 A"),
        ("ARMATUUR", "ELEK-VERLICHTING", "LED-armatuur (± 400 W) aan tentstructuur"),
        ("line", "ELEK-KABELS-VERLICHTING", "Verlichtingskring L1-L4 (bovengronds)"),
        ("KABELBRUG", "ELEK-KABELBRUGGEN", "Kabelbrug over looppad"),
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
        ("HYDRANT", "NOOD-HULPDIENSTEN", "Hydrant"),
        ("line", "NOOD-HULPDIENSTEN", "Toegangsweg hulpdiensten"),
    ]
    return {"ALG": alg, "ELEK": alg[:1] + elek, "NOOD": alg[:1] + nood}[plan]


NOTITIES = {
    "ALG": (
        "{\\fArial|b1;ALGEMENE NOTITIES}\\P"
        "1. Twee tenten van 20 m x 90 m, lange zijden gekoppeld: totale vloeroppervlakte 3.600 m².\\P"
        "2. 160 stands van 3 x 3 m (80 per tent): wandstands, eilandstands rug-aan-rug en gootstands.\\P"
        "3. Langsgangen en dwarsgang min. 4,00 m vrije breedte; geen materiaal in de gangen.\\P"
        "4. Maatvoering in meter. Oorsprong (0,0) = zuidwestelijke hoek tent A (stramien 1/A).\\P"
        "5. Standnummering: A01-A80 (tent A), B01-B80 (tent B), per rij van west naar oost.\\P"
        "6. Posities staanders indicatief (h.o.h. 5 m) – te controleren met plan tentverhuurder."
    ),
    "ELEK": (
        "{\\fArial|b1;ELEKTRISCHE NOTITIES}\\P"
        "1. Installatie volgens AREI; keuring door erkend organisme vóór openstelling.\\P"
        "2. Elke SVB met differentieelschakelaar 30 mA; elke stand op eigen kring 16 A.\\P"
        "3. Vloerkabels langs ruglijn stands (achter standwanden); op looppaden steeds kabelbrug.\\P"
        "4. Voedingskabels HVB→SVB bovengronds langs goot, min. 3 m hoog, mechanisch bevestigd.\\P"
        "5. Indicatieve vermogensbalans: stands 160 x 1,5 kW x 0,6 = 144 kW | verlichting 36 x 0,4 = 14 kW |\\P"
        "    catering 2 x 22 kW x 0,8 = 35 kW | onthaal 5 kW  →  ± 200 kW  →  aggregaat 250 kVA.\\P"
        "6. Kabelsecties en beveiligingen te bepalen door de installateur."
    ),
    "NOOD": (
        "{\\fArial|b1;NOODPLAN – NOTITIES}\\P"
        "1. 2 hoofdingangen (2 x 4,00 m) + 8 nooduitgangen (8 x 2,40 m): totale uitgangsbreedte 27,2 m.\\P"
        "2. Uitgangen tijdens het event nooit afsluiten; tentzeilen opgerold/vastgezet, drempelvrij.\\P"
        "3. Evacuatie: volg pijlen naar dichtstbijzijnde uitgang, daarna naar VERZAMELPLAATS (noordzijde).\\P"
        "4. Bij brand/incident: alarm via veiligheidscoördinator (onthaalbalie) – bel 112.\\P"
        "5. Elektriciteit uitschakelen via hoofdschakelaar aan HVB (oostzijde).\\P"
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
        bevroren += ["ALG-MAATVOERING", "ALG-MEUBILAIR"]
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
    add_txt(psp, "CAREERDAY", (x0 + 5, 135.0), 7.0, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "Tentconfiguratie 2 x (20 m x 90 m)", (x0 + 5, 128.5), 2.8, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "PLAN", (x0 + 3, 121.5), 2.0, K, align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, TITELS[plan], (x0 + 5, 113.0), 5.5, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "INHOUD", (x0 + 3, 101.5), 2.0, K, align=TextEntityAlignment.MIDDLE_LEFT)
    inhoud = {"ALG": "Inplanting stands, onthaal, catering, sanitair",
              "ELEK": "Voeding, verdeelborden, stopcontacten, verlichting",
              "NOOD": "Uitgangen, vluchtwegen, blusmiddelen, EHBO"}[plan]
    add_txt(psp, inhoud, (x0 + 5, 93.0), 3.0, K, align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "PROJECT / LOCATIE", (x0 + 3, 81.5), 2.0, K,
            align=TextEntityAlignment.MIDDLE_LEFT)
    add_txt(psp, "Careerday – ...........................", (x0 + 5, 73.0), 3.0, K,
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
