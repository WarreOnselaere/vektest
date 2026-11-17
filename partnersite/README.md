# Standkeuze premium partners – Career Day

Website waar premium partners hun 3 favoriete standplaatsen (1e, 2e, 3e keuze) aanduiden op het
grondplan en versturen. Inzendingen komen in een Google Sheet.

| Bestand | Wat |
|---|---|
| `index.html` | De website (één bestand, geen server nodig) |
| `site_template.html` | Bron; pas hier tekst en `CONFIG` aan |
| `bouw_site.py` | Bouwt `index.html` uit de template + standposities (`../careerday/data/stands_2526.json`) |
| `apps-script/Code.gs` | Ontvanger: zet elke inzending als rij in een Google Sheet |

## Live zetten (± 10 minuten)

1. **Google Sheet + script**: maak een Google Sheet → *Extensies → Apps Script* → plak `apps-script/Code.gs`
   → *Implementeren → Nieuwe implementatie → Web-app* (uitvoeren als: ikzelf, toegang: iedereen) → kopieer de URL.
2. **Instellen**: open `site_template.html`, zet bovenaan in `CONFIG`:
   `ENDPOINT` = die URL, eventueel `DEADLINE` en `NIET_BESCHIKBAAR` (standen die al vastliggen).
   Draai `python3 bouw_site.py`.
3. **Hosten**: zet `index.html` online, bv. GitHub Pages (repo → Settings → Pages) of door de map te slepen
   op app.netlify.com/drop. Stuur de link naar je premium partners.

Zonder `ENDPOINT` staat de site in demomodus: er wordt niets verstuurd en de partner krijgt een
samenvatting om te kopiëren.

In de Sheet: menu *Uitvoeren → maakOverzicht* maakt een tabblad met per stand wie hem als 1e/2e/3e
keuze opgaf (laatste inzending per bedrijf telt) – handig om conflicten te zien.
