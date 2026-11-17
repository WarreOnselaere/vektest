# Careerday – grondplannen (AutoCAD)

Twee tenten van **20 m × 90 m** op het Sint-Pietersplein (Gent), met een tussengang van 2 m.
Indeling, zones en de 128 standposities zijn overgenomen uit het grondplan **Career Day 25–26**
(posities rechtstreeks uit de vectoren van de PDF gehaald → `data/stands_2526.json`).

## Bestanden

| Bestand | Inhoud |
|---|---|
| `Careerday_grondplannen.dxf` | **Hoofdbestand**: alles in één tekening + 3 layouts (A1, 1:200) |
| `Careerday_01_algemeen_grondplan.dxf` | Enkel algemeen grondplan |
| `Careerday_02_elektriciteitsplan.dxf` | Ondergrond + elektriciteit |
| `Careerday_03_noodplan.dxf` | Ondergrond + noodplan |
| `preview/*.pdf` / `*.png` | Voorbeeldplots van de 3 layouts |
| `genereer_grondplannen.py` | Script dat de DXF's genereert (`pip install ezdxf`) |

Openen in AutoCAD: gewoon de `.dxf` openen, daarna `SAVEAS` → `.dwg`.

## Opbouw van de tekening

- Modelruimte in **meter**, oorsprong (0,0) = zuidwesthoek tent A (stramien 1/A).
- Layouts **01 Algemeen grondplan**, **02 Elektriciteitsplan**, **03 Noodplan**: elk één
  vergrendelde viewport (1:200) waarin de lagen van de andere plannen bevroren zijn
  (VP Freeze). In plan 02 en 03 staan stands en ondergrond grijs (VP-kleuroverride).
- Symbolen zijn blokken (STOPCONTACT_230V, VERDEELBORD, NOODUITGANG, BLUSSER, ...).

## Lagen

| Groep | Lagen |
|---|---|
| `BASIS-` | TENT, TENT-KOPPELING (tussengang), TENT-PALEN, STRAMIEN, STRAMIEN-TEKST, OMGEVING, OMGEVING-TEKST |
| `ALG-` | STANDS, STANDS-ARCERING, STANDNUMMERS, ONTHAAL, ZONES, LOGISTIEK, CATERING, SANITAIR, ZONES-TEKST, MAATVOERING |
| `ELEK-` | HOOFDVOEDING, VOEDINGSKABELS, VERDEELBORDEN, KABELS-STANDS, STOPCONTACTEN, CEE-400V, VERLICHTING, KABELS-VERLICHTING, KABELBRUGGEN, TEKST |
| `NOOD-` | UITGANGEN, VLUCHTWEGEN, NOODVERLICHTING, BLUSMIDDELEN, EHBO, VERZAMELPLAATS, HULPDIENSTEN, HOOFDSCHAKELAAR, TEKST |
| `KADER-` | TITELBLOK, LEGENDE, VIEWPORT (niet plotten) |

Elke laag heeft een omschrijving (zichtbaar in de Layer Properties Manager).

## Aannames (aan te passen)

- Stands 2 × 3 m, nummers 1–73 (tent 1, ingangszijde) en 74–128 (tent 2), zoals vorig jaar.
- Zones zoals 25–26: inkom, vestiaire, CV-check, lanyards, goodies, recruiters zones, CV-screening,
  photobooth, bar, logistieke zone, 2 loading bays, toiletten en 4 heat-units buiten.
- Elektriciteit: HVB 125 A achteraan, hoofdkabel door de tussengang, 10 verdeelkasten 32 A
  (stands automatisch per kast gegroepeerd) + 63-1 algemeen, 1 stopcontact per stand, 36 LED-armaturen.
- Noodplan: ingang + uitgang (3 m) en 8 nooduitgangen (2,4 m) op de plaatsen van de deuren van vorig jaar;
  vluchtpijlen wijzen automatisch naar de dichtste uitgang. Verzamelplaats en brandkraan: te bevestigen met stad Gent.
- Staanders h.o.h. 5 m en de omgeving zijn indicatief.

Aanpassen: wijzig `data/stands_2526.json` (posities) of de lijsten `ZONES` / `UITGANGEN` in het script
en draai `python3 genereer_grondplannen.py`; voorbeeld-PDF's met `python3 maak_preview.py Careerday_grondplannen.dxf preview`.
