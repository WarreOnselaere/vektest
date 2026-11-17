# Careerday – grondplannen (AutoCAD)

Twee tenten van **20 m × 90 m**, lange zijden tegen elkaar (samen 40 m × 90 m, 3.600 m²).

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
| `BASIS-` | TENT, TENT-KOPPELING, TENT-PALEN, STRAMIEN, STRAMIEN-TEKST, OMGEVING, OMGEVING-TEKST |
| `ALG-` | STANDS, STANDS-ARCERING, STANDNUMMERS, ONTHAAL, CATERING, MEUBILAIR, SANITAIR, ZONES-TEKST, MAATVOERING |
| `ELEK-` | HOOFDVOEDING, VOEDINGSKABELS, VERDEELBORDEN, KABELS-STANDS, STOPCONTACTEN, CEE-400V, VERLICHTING, KABELS-VERLICHTING, KABELBRUGGEN, TEKST |
| `NOOD-` | UITGANGEN, VLUCHTWEGEN, NOODVERLICHTING, BLUSMIDDELEN, EHBO, VERZAMELPLAATS, HULPDIENSTEN, HOOFDSCHAKELAAR, TEKST |
| `KADER-` | TITELBLOK, LEGENDE, VIEWPORT (niet plotten) |

Elke laag heeft een omschrijving (zichtbaar in de Layer Properties Manager).

## Aannames (aan te passen)

- 160 stands van 3 × 3 m (A01–A80, B01–B80), gangen 4 m, dwarsgang 4 m in het midden.
- Onthaal + vestiaire + EHBO aan de westkop, bar/netwerkzone aan de oostkop, sanitaire unit buiten (west).
- Aggregaat 250 kVA + hoofdverdeelbord buiten aan de oostkop; 4 subverdeelborden; 1 stopcontact 16 A per stand;
  36 LED-armaturen op 4 kringen. Vermogensbalans is indicatief.
- 2 hoofdingangen (4,00 m) + 8 nooduitgangen (2,40 m); verzamelplaats aan de noordzijde.
- Staanders h.o.h. 5 m, terrein, noordrichting en hydrant zijn indicatief.
