/**
 * Career Day – standkeuze premium partners
 * Google Apps Script web-app die inzendingen van de partnersite in deze Google Sheet zet.
 *
 * Installatie (eenmalig, ±5 min):
 *  1. Maak een nieuwe Google Sheet, bv. "Standkeuze premium partners".
 *  2. Extensies > Apps Script. Vervang alle code door dit bestand en sla op.
 *  3. Implementeren > Nieuwe implementatie > type "Web-app".
 *       Uitvoeren als: Ikzelf     Toegang: Iedereen
 *  4. Kopieer de web-app-URL (eindigt op /exec) en plak ze in partnersite/site_template.html
 *     bij CONFIG.ENDPOINT. Draai daarna `python3 bouw_site.py`.
 */
const TABBLAD = 'Inzendingen';
const KOPPEN = ['Tijdstip', 'Editie', 'Bedrijf', 'Contactpersoon', 'E-mail', 'Telefoon',
                'Keuze 1', 'Keuze 2', 'Keuze 3', 'Opmerkingen'];

function blad_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(TABBLAD);
  if (!sh) {
    sh = ss.insertSheet(TABBLAD);
    sh.appendRow(KOPPEN);
    sh.getRange(1, 1, 1, KOPPEN.length).setFontWeight('bold').setBackground('#D7E7D1');
    sh.setFrozenRows(1);
  }
  return sh;
}

function schoon_(v, max) {
  v = String(v == null ? '' : v).trim().slice(0, max || 500);
  // voorkom dat tekst als formule wordt uitgevoerd in de sheet
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.website) return antwoord_({ ok: false });          // spam-val
  if (!p.bedrijf || !p.email || !p.keuze1) return antwoord_({ ok: false, fout: 'onvolledig' });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    blad_().appendRow([
      new Date(), schoon_(p.editie, 40), schoon_(p.bedrijf, 120), schoon_(p.contact, 120),
      schoon_(p.email, 160), schoon_(p.tel, 40),
      Number(p.keuze1) || '', Number(p.keuze2) || '', Number(p.keuze3) || '',
      schoon_(p.opmerkingen, 1000)
    ]);
  } finally {
    lock.releaseLock();
  }
  return antwoord_({ ok: true });
}

function doGet() {
  return antwoord_({ ok: true, info: 'Career Day standkeuze – gebruik POST' });
}

function antwoord_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Optioneel: maakt een tabblad "Overzicht" met per stand hoeveel partners hem als 1e/2e/3e keuze gaven
 * (laatste inzending per bedrijf telt). Uitvoeren via het menu Uitvoeren > maakOverzicht.
 */
function maakOverzicht() {
  const rijen = blad_().getDataRange().getValues().slice(1);
  const laatste = {};
  rijen.forEach(r => { laatste[String(r[2]).toLowerCase()] = r; });
  const tel = {};
  Object.values(laatste).forEach(r => {
    [6, 7, 8].forEach((k, i) => {
      const nr = r[k]; if (!nr) return;
      tel[nr] = tel[nr] || { k: [[], [], []] };
      tel[nr].k[i].push(r[2]);
    });
  });
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName('Overzicht') || ss.insertSheet('Overzicht');
  sh.clear();
  const uit = [['Stand', '# als 1e keuze', '# als 2e keuze', '# als 3e keuze', '1e keuze van', '2e keuze van', '3e keuze van']];
  Object.keys(tel).map(Number).sort((a, b) => a - b).forEach(nr => {
    const k = tel[nr].k;
    uit.push([nr, k[0].length, k[1].length, k[2].length, k[0].join(', '), k[1].join(', '), k[2].join(', ')]);
  });
  sh.getRange(1, 1, uit.length, uit[0].length).setValues(uit);
  sh.getRange(1, 1, 1, uit[0].length).setFontWeight('bold').setBackground('#D7E7D1');
  sh.setFrozenRows(1);
}
