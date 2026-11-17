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
| `Careerday_04_groene_loper.dxf` | Ondergrond + groene loper met maten per deel |
| `materiaallijst_elektriciteit.csv` | Paddenstoelen, kattekoppen, kabels per lengte, kabelbruggen + detail per kabel |
| `preview/*.pdf` / `*.png` | Voorbeeldplots van de 3 layouts |
| `genereer_grondplannen.py` | Script dat de DXF's genereert (`pip install ezdxf`) |

Openen in AutoCAD: gewoon de `.dxf` openen, daarna `SAVEAS` → `.dwg`.

## Opbouw van de tekening

- Modelruimte in **meter**, oorsprong (0,0) = zuidwesthoek tent A (stramien 1/A).
- Layouts **01 Algemeen grondplan**, **02 Elektriciteitsplan**, **03 Noodplan**, **04 Groene loper**: elk één
  vergrendelde viewport (1:200) waarin de lagen van de andere plannen bevroren zijn
  (VP Freeze). In plan 02 en 03 staan stands en ondergrond grijs (VP-kleuroverride).
- Symbolen zijn blokken (STOPCONTACT_230V, VERDEELBORD, NOODUITGANG, BLUSSER, ...).

## Lagen

| Groep | Lagen |
|---|---|
| `BASIS-` | TENT, TENT-KOPPELING (tussengang), TENT-PALEN, STRAMIEN, STRAMIEN-TEKST, OMGEVING, OMGEVING-TEKST |
| `ALG-` | STANDS, STANDS-ARCERING, STANDNUMMERS, ONTHAAL, ZONES, LOGISTIEK, CATERING, SANITAIR, ZONES-TEKST, MAATVOERING |
| `ELEK-` | HOOFDVOEDING, PADDENSTOELEN, KATTEKOPPEN, KABEL-05M (blauw), KABEL-10M (oranje), KABEL-15M (paars), KABEL-40M (rood), KABELBRUGGEN, VERLICHTING, TEKST |
| `LOPER-` | GROENE-LOPER, RAND, AS, MAATVOERING, TEKST |
| `NOOD-` | UITGANGEN, VLUCHTWEGEN, NOODVERLICHTING, BLUSMIDDELEN, EHBO, VERZAMELPLAATS, HULPDIENSTEN, HOOFDSCHAKELAAR, TEKST |
| `KADER-` | TITELBLOK, LEGENDE, VIEWPORT (niet plotten) |

Elke laag heeft een omschrijving (zichtbaar in de Layer Properties Manager).

## Aannames (aan te passen)

- Stands 2 × 3 m, nummers 1–73 (tent 1, ingangszijde) en 74–128 (tent 2), zoals vorig jaar.
- Zones zoals 25–26: inkom, vestiaire, CV-check, lanyards, goodies, recruiters zones, CV-screening,
  photobooth, bar, logistieke zone, 2 loading bays, toiletten en 4 heat-units buiten.
- Groene loper: 2,00 m breed (zoals vorig jaar), ± 334 m lang, van de ingang van tent 1 slingerend langs alle
  standen, via de doorgang achteraan in de tussengang naar tent 2, einde bij de bar (`LOPER` in het script).
- Elektriciteit (`elek_routing.py`): kabels worden automatisch getrokken over een rooster van 0,5 m, **nooit over de
  groene loper**, bij voorkeur onder/achter de stands; waar een looppad gekruist wordt komt een kabelbrug.
  Paddenstoelen (32 A, max. 9 aansluitingen) zo gekozen dat elke stand met max. 15 m kabel bereikt wordt;
  paddenstoelen doorgelust in strengen van max. 3. Elke stand 1 kattekop (2 stopcontacten).
  Kabels krijgen de kleur van hun lengte: 5 m blauw, 10 m oranje, 15 m paars, 40 m rood.
  Hoofdborden: HVB-N (ELEK+W), HVB-Z en HVB-W (ELEK-doorsteken) en HVB-M in de tussengang (via hoofdkabel 125 A),
  posities van de pleinaansluitingen te bevestigen met stad Gent.
- Noodplan: ingang + uitgang (3 m) en 8 nooduitgangen (2,4 m) op de plaatsen van de deuren van vorig jaar;
  vluchtpijlen wijzen automatisch naar de dichtste uitgang. Verzamelplaats en brandkraan: te bevestigen met stad Gent.
- Staanders h.o.h. 5 m en de omgeving zijn indicatief.

Aanpassen: wijzig `data/stands_2526.json` (posities) of de lijsten `ZONES` / `UITGANGEN` in het script
en draai `python3 genereer_grondplannen.py`; voorbeeld-PDF's met `python3 maak_preview.py Careerday_grondplannen.dxf preview`.
