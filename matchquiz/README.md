# Matchquiz – Career Day

Studenten doen een korte quiz (12 vragen, ± 2 minuten) en krijgen hun **top 5 bedrijven** met standnummer
en een route op het grondplan. Bedrijven vullen vooraf **dezelfde vragen** in over hun bedrijf.
Alles komt samen in één Google Sheet.

| Bestand | Wat |
|---|---|
| `index.html` | Studentenquiz (deze link deel je met studenten, bv. via QR-code aan de ingang) |
| `bedrijven.html` | Bedrijfsformulier (deze link mail je naar de deelnemende bedrijven) |
| `quiz_template.html` | Bron van beide pagina's; pas hier `CONFIG`, vragen en teksten aan |
| `bouw_quiz.py` | Bouwt `index.html` en `bedrijven.html` (+ standposities uit `../careerday/data/stands_2526.json`) |
| `apps-script/Code.gs` | Google Sheet-koppeling: bewaart bedrijfsprofielen, levert ze aan de quiz, logt anonieme resultaten |

## De vragen (zelfde voor student en bedrijf)

1. Wat zoek je / wat bieden jullie aan (stage, starterjob, traineeship, studentenjob, thesis)
2. Studierichting
3. Domeinen (finance, audit, consulting, marketing, supply chain, data, HR, tax & legal, ondernemen)
4. Bedrijfsgrootte
5. Locatie
6–11. Zes "dit of dat"-schalen over de werksfeer (structuur ↔ vrijheid, team ↔ zelfstandig, tempo ↔ balans,
   internationaal ↔ lokaal, mensen ↔ analytisch, kantoor ↔ thuiswerk)
12. Twee belangrijkste waarden (leren, impact, verloning, sfeer, doorgroeien, internationaal)

**Matchscore (0–100 %)**: aanbod 26 · domein 26 · werksfeer 18 · studierichting 10 · waarden 8 · locatie 7 · grootte 5.
De gewichten staan in `GEWICHT` in `quiz_template.html`. Elke match toont de 3 belangrijkste redenen
("Biedt een stage aan", "Werft in Consulting & strategie", …).

## Live zetten (± 10 minuten)

1. **Google Sheet + script**: nieuwe Google Sheet → *Extensies → Apps Script* → plak `apps-script/Code.gs`
   → *Implementeren → Nieuwe implementatie → Web-app* (uitvoeren als: ikzelf, toegang: iedereen) → kopieer de URL.
2. **Instellen**: in `quiz_template.html` bij `CONFIG` de `ENDPOINT` invullen (en eventueel `EDITIE`,
   `CODE_VRAGEN`). Draai `python3 bouw_quiz.py`.
3. **Hosten**: zet `index.html` en `bedrijven.html` online (GitHub Pages of app.netlify.com/drop).
   Mail `…/bedrijven.html` naar de bedrijven, deel `…/index.html` met studenten.

Zonder `ENDPOINT` draait alles in **demomodus** met verzonnen voorbeeldbedrijven; het bedrijfsformulier
geeft dan een samenvatting om te kopiëren.

## In de Sheet

- Tabblad **Bedrijven**: één rij per bedrijf. Opnieuw versturen met dezelfde naam = bijwerken.
  Kolom *Stand* mag je zelf invullen/aanpassen; *Zichtbaar* op FALSE verbergt een bedrijf in de quiz.
  E-mail en contactpersoon worden nooit naar de quiz gestuurd.
- Tabblad **Studenten**: anoniem (geen naam/e-mail) welke matches elke student kreeg.
  Uitzetten met `LOG_STUDENTEN: false`.
- *Uitvoeren → maakStatistiek*: per bedrijf hoe vaak het in een top 5 stond – leuk om achteraf aan partners te tonen.
- Optioneel toegangscode voor bedrijven: `BEDRIJFSCODE` in `Code.gs` + `CODE_VRAGEN: true`.
