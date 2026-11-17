/**
 * Career Day – matchquiz
 * Google Apps Script web-app die
 *   - bedrijfsprofielen opslaat (tabblad "Bedrijven", één rij per bedrijf; opnieuw versturen = bijwerken)
 *   - de zichtbare profielen teruggeeft aan de studentenquiz (GET ?actie=bedrijven)
 *   - anoniem bijhoudt welke matches studenten kregen (tabblad "Studenten")
 *
 * Installatie (eenmalig, ±5 min):
 *  1. Maak een nieuwe Google Sheet, bv. "Matchquiz Career Day".
 *  2. Extensies > Apps Script. Vervang alle code door dit bestand en sla op.
 *  3. Implementeren > Nieuwe implementatie > type "Web-app".
 *       Uitvoeren als: Ikzelf     Toegang: Iedereen
 *  4. Kopieer de web-app-URL (eindigt op /exec) en plak ze in matchquiz/quiz_template.html
 *     bij CONFIG.ENDPOINT. Draai daarna `python3 bouw_quiz.py`.
 *  Wijzig je later deze code: Implementeren > Implementaties beheren > bewerken > Nieuwe versie.
 *
 * Een bedrijf verbergen: zet in kolom "Zichtbaar" op FALSE.
 * Standnummer aanvullen of corrigeren: pas kolom "Stand" aan; de quiz neemt het meteen over.
 */
const BEDRIJFSCODE = '';   // invullen (en CONFIG.CODE_VRAGEN = true) om enkel bedrijven met de code toe te laten

const TAB_B = 'Bedrijven';
const KOP_B = ['Laatst bijgewerkt', 'Editie', 'Bedrijf', 'Contactpersoon', 'E-mail', 'Stand', 'Website', 'Pitch', 'Profiel (JSON)', 'Zichtbaar'];
const TAB_S = 'Studenten';
const KOP_S = ['Tijdstip', 'Editie', 'Studierichting', 'Zoekt', 'Domeinen', 'Top-matches', 'Alle antwoorden (JSON)'];

function blad_(naam, koppen) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(naam);
  if (!sh) {
    sh = ss.insertSheet(naam);
    sh.appendRow(koppen);
    sh.getRange(1, 1, 1, koppen.length).setFontWeight('bold').setBackground('#D7E7D1');
    sh.setFrozenRows(1);
  }
  return sh;
}

function schoon_(v, max) {
  v = String(v == null ? '' : v).trim().slice(0, max || 500);
  return /^[=+\-@]/.test(v) ? "'" + v : v;   // geen formules in de sheet
}

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.website2) return antwoord_({ ok: false });            // spam-val
  if (p.actie === 'student') return student_(p);
  if (p.actie === 'bedrijf') return bedrijf_(p);
  return antwoord_({ ok: false, fout: 'onbekende actie' });
}

function bedrijf_(p) {
  if (BEDRIJFSCODE && String(p.code || '').trim() !== BEDRIJFSCODE) return antwoord_({ ok: false, fout: 'code' });
  if (!p.bedrijf || !p.email || !p.profiel) return antwoord_({ ok: false, fout: 'onvolledig' });
  let profiel;
  try { profiel = JSON.parse(p.profiel); } catch (x) { return antwoord_({ ok: false, fout: 'profiel' }); }
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sh = blad_(TAB_B, KOP_B);
    const rij = [new Date(), schoon_(p.editie, 40), schoon_(p.bedrijf, 80), schoon_(p.contact, 80), schoon_(p.email, 120),
      Number(p.stand) || '', schoon_(p.website, 200), schoon_(p.pitch, 160), JSON.stringify(profiel).slice(0, 4000)];
    const namen = sh.getLastRow() > 1 ? sh.getRange(2, 3, sh.getLastRow() - 1, 1).getValues().map(r => String(r[0]).trim().toLowerCase()) : [];
    const i = namen.indexOf(String(p.bedrijf).trim().toLowerCase());
    if (i >= 0) {
      const bestaand = sh.getRange(i + 2, 1, 1, KOP_B.length).getValues()[0];
      if (!rij[5] && bestaand[5]) rij[5] = bestaand[5];          // standnummer van de organisatie niet wissen
      rij.push(bestaand[9] === '' ? true : bestaand[9]);          // "Zichtbaar" behouden
      sh.getRange(i + 2, 1, 1, KOP_B.length).setValues([rij]);
    } else {
      rij.push(true);
      sh.appendRow(rij);
    }
  } finally {
    lock.releaseLock();
  }
  return antwoord_({ ok: true });
}

function student_(p) {
  let a = {};
  try { a = JSON.parse(p.antwoorden || '{}'); } catch (x) {}
  blad_(TAB_S, KOP_S).appendRow([new Date(), schoon_(p.editie, 40), schoon_(a.richting, 20), schoon_([].concat(a.zoek || []).join(', '), 100),
    schoon_([].concat(a.domein || []).join(', '), 100), schoon_(p.top, 600), JSON.stringify(a).slice(0, 2000)]);
  return antwoord_({ ok: true });
}

function doGet(e) {
  const actie = e && e.parameter && e.parameter.actie;
  if (actie !== 'bedrijven') return antwoord_({ ok: true, info: 'Career Day matchquiz – gebruik ?actie=bedrijven' });
  const sh = blad_(TAB_B, KOP_B);
  const rijen = sh.getLastRow() > 1 ? sh.getRange(2, 1, sh.getLastRow() - 1, KOP_B.length).getValues() : [];
  const bedrijven = [];
  rijen.forEach(r => {
    if (r[9] === false || String(r[9]).toUpperCase() === 'FALSE' || !r[2]) return;
    let profiel = null;
    try { profiel = JSON.parse(r[8]); } catch (x) { return; }
    // enkel publieke velden: geen contactpersoon of e-mail
    bedrijven.push({ naam: String(r[2]).replace(/^'/, ''), stand: Number(r[5]) || null, website: String(r[6]), pitch: String(r[7]).replace(/^'/, ''), p: profiel });
  });
  return antwoord_({ ok: true, bedrijven: bedrijven });
}

function antwoord_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Optioneel: tabblad "Statistiek" met per bedrijf hoe vaak het in de top van een student stond.
 * Handig om na de Career Day aan partners te tonen. Uitvoeren via Uitvoeren > maakStatistiek.
 */
function maakStatistiek() {
  const rijen = blad_(TAB_S, KOP_S).getDataRange().getValues().slice(1);
  const tel = {};
  rijen.forEach(r => String(r[5]).split(' | ').forEach((m, i) => {
    const naam = m.replace(/\s*\(\d+%\)\s*$/, '').trim(); if (!naam) return;
    tel[naam] = tel[naam] || [0, 0];
    tel[naam][0]++; if (i === 0) tel[naam][1]++;
  }));
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName('Statistiek') || ss.insertSheet('Statistiek');
  sh.clear();
  const uit = [['Bedrijf', '# keer in top 5', '# keer beste match']].concat(
    Object.keys(tel).sort((a, b) => tel[b][0] - tel[a][0]).map(n => [n, tel[n][0], tel[n][1]]));
  uit.push(['Totaal studenten', rijen.length, '']);
  sh.getRange(1, 1, uit.length, 3).setValues(uit);
  sh.getRange(1, 1, 1, 3).setFontWeight('bold').setBackground('#D7E7D1');
  sh.setFrozenRows(1);
}
