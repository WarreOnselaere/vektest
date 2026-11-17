"""
Bouwt de matchquiz uit quiz_template.html + de standposities van het grondplan.

  index.html      studentenquiz (start in studentmodus)
  bedrijven.html  bedrijfsformulier (start in bedrijfsmodus)
  artifact_preview.html  fragment voor een claude.ai-artifact (demo)

Beide pagina's bevatten alles; met #student / #bedrijf achter de link wissel je van modus.

Gebruik:  python3 bouw_quiz.py
"""
import json
from pathlib import Path

HIER = Path(__file__).resolve().parent
DATA = HIER.parent / "careerday" / "data" / "stands_2526.json"
KOP = ('<!doctype html>\n<html lang="nl">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')


def main():
    stands = json.loads(DATA.read_text())
    # tent A = tent 1 (y 22-42), tent B = tent 2 (y 0-20)
    compact = [[s["nr"], round(s["x"], 2), round(s["y"], 2), s["w"], s["h"]] for s in stands]
    tpl = (HIER / "quiz_template.html").read_text()
    tpl = tpl.replace("/*__STANDEN__*/[]", json.dumps(compact, separators=(",", ":")))
    for naam, modus in (("index.html", "student"), ("bedrijven.html", "bedrijf")):
        html = tpl.replace('/*__MODUS__*/"student"', json.dumps(modus))
        if modus == "bedrijf":
            html = html.replace("<title>Career Day Matchquiz</title>", "<title>Bedrijfsprofiel Career Day</title>", 1)
        (HIER / naam).write_text(KOP + html + "\n</html>\n")
    (HIER / "artifact_preview.html").write_text(tpl)
    print("matchquiz gebouwd:", len(compact), "standen")


if __name__ == "__main__":
    main()
