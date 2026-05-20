#!/usr/bin/env python3
"""
One-shot fixes for products.json:
  - Correct filterSlug for items the heuristic mis-categorized
  - Override description/bullets for items where the templated copy
    doesn't match the specific product (cooling caps, filter cartridges,
    welder hood, chainsaw kit, helmet accessories, etc.)

Re-runnable: keyed by sku, so re-running just re-applies the same overrides.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'products.json'

# ── Move products to the correct filterSlug ───────────────────
# Also update category macro + subcategory label to match.
MACRO = {
    'elmetti': ('Capo', 'Elmetti'),
    'berretti': ('Capo', 'Berretti'),
    'occhiali': ('Capo', 'Occhiali'),
    'udito': ('Capo', 'Udito'),
    'respirazione': ('Capo', 'Respirazione'),
    'anticaduta': ('Corpo', 'Anticaduta'),
    'busto': ('Corpo', 'Busto'),
    'alta-visibilita': ('Corpo', 'Alta visibilità'),
    'multi-protezione': ('Corpo', 'Multi-protezione'),
    'pantaloni': ('Corpo', 'Pantaloni'),
    'rischio-chimico': ('Mani', 'Rischio chimico'),
    'rischio-meccanico': ('Mani', 'Rischio meccanico'),
    'rischio-termico': ('Mani', 'Rischio termico'),
    'scarpe': ('Piedi', 'Scarpe'),
    'stivali': ('Piedi', 'Stivali'),
    'sanitario': ('Sanitario', 'Sanitario'),
    'alberghiero': ('Alberghiero', 'Alberghiero'),
}

# sku -> new filterSlug
RECATEGORIZE = {
    '0ELMACBE00':           'berretti',         # Berretto sottocasco winter
    '0ELMAC0CC':            'occhiali',         # Occhiale FUEGO per elmetto (was elmetti)
    '0POCPC0VISBALBI':      'occhiali',         # Visiera c/caschetto balbi 2 (was elmetti)
    '0GTIKV011MA00':        'rischio-termico',  # Guanti aramidico 28cm (was meccanico)
    '0GTIGO001202':         'rischio-chimico',  # Guanti lattice VE920 (was meccanico)
    '0ABPCUTI01':           'berretti',         # Cuffia saldatore — head, not glove
}

# sku -> description override (where the templated subcategory copy is wrong
# for this specific product). Voice: Davide, "tu", no inventions beyond what
# the product name/standard nomenclature implies.
DESC_OVERRIDES = {
    # Cooling/refrigerated head gear — opposite of "winter cold"
    '0ABLRE6594BE00':
        "Berretto refrigerante per chi lavora al caldo — bagni l'inserto, lo strizzi, ti raffredda la testa per qualche ora. Lo teniamo a magazzino per l'estate.",
    '0ABLRE6521ELFR':
        "Frontalino refrigerante da mettere dentro l'elmetto nelle giornate calde. Si bagna, si strizza, ti tiene fresca la fronte. Ricambio veloce, lo trovi in negozio.",
    # Helmet accessories — not full helmets
    '0ELMPESOTT002':
        "Sottogola di ricambio per elmetto Granite — tiene il casco al posto giusto anche piegandosi. Cambio veloce, senza attrezzi. In scaffale insieme agli elmetti.",
    '0POCPC0VISBALBI':
        "Visiera con caschetto in un solo pezzo — protezione per faccia e testa nei lavori con schegge o spruzzi. Te la facciamo provare prima dell'ordine.",
    '0ELMAC0CC':
        "Occhiale che si aggancia all'elmetto FUEGO — protezione per gli occhi senza dover indossare due cose separate. Lo provi in negozio.",
    # Replacement visor lenses
    '0POCPC0VISCV12':
        "Visiera APET da 250 micron, ricambio per gli occhiali CV12. Lente trasparente, sostituzione veloce. La teniamo a magazzino sui modelli più richiesti.",
    '0POCPC0VISCV16':
        "Visiera APET Foam Top & Shield da 300 micron, per il modello CV16. Ricambio veloce, lente trasparente. La trovi in negozio.",
    # Filter cartridges (not masks) — letters per EN 14387 standard
    '0RESFIDPI230A1':
        "Filtro A1 di ricambio — codice 43405100. Per vapori organici, da abbinare alla semimaschera. Lo teniamo a magazzino tutto l'anno.",
    '0RESFIDPI200A1P1COMB':
        "Filtro combinato A1P1 — codice 43403215. Per vapori organici più polveri. Ricambio veloce, in scorta in negozio.",
    '0RESFIDPI230COMB':
        "Filtro combinato A1P1 — codice 43405127. Per vapori organici più polveri, formato 230. Lo teniamo a magazzino.",
    '0RESFIDPIAIRLINE':
        "Filtro per linea aria (airline) — codice 43442033. Ricambio specifico per il sistema, da cambiare a scadenza. In scorta in negozio.",
    '0RESFIDPI230B1':
        "Filtro B1 — codice 43405101. Per gas inorganici. Lo teniamo a magazzino sui modelli più richiesti.",
    '0RESFIDPI230E1':
        "Filtro E1 — codice 43405102. Per gas acidi come l'anidride solforosa. Ricambio in scorta in negozio.",
    '0RESFIDPI230K1':
        "Filtro K1 — codice 43405103. Per l'ammoniaca. Lo teniamo a magazzino tutto l'anno.",
    # Earplugs — templated copy is for over-ear cuffie
    '0PUDARC00':
        "Tappi auricolari con archetto delta — pronti al collo quando entri ed esci dagli ambienti rumorosi. Lo provi in negozio, comodi anche per turni lunghi.",
    '0PUDDELTA006':
        "Tappi auricolari delta, box da 6 paia — protezione semplice per chi lavora con macchine rumorose. Confezioni più grandi a magazzino.",
    '0PUDDELTA00':
        "Tappi auricolari delta, confezione da 200 paia — per le squadre che lavorano vicino a macchine rumorose tutti i giorni. In scorta tutto l'anno.",
    # Welder hood (after move from rischio-termico to berretti)
    '0ABPCUTI01':
        "Cuffia in tessuto ignifugo per il saldatore — copre testa, collo e nuca dalle scintille. Te la facciamo provare in negozio. In scaffale tutto l'anno.",
    # Chainsaw kit
    '0ABLBOGTCE0001':
        "Guanto antitaglio pensato per chi lavora con la motosega. Calzata generosa per il movimento, da provare in bottega prima dell'ordine. In scorta sui modelli più richiesti.",
    '0ABLBOGACE000':
        "Gambale antitaglio per chi lavora con la motosega — si indossa sopra lo stivale, copre la gamba dalle scintille e dai tagli. Te lo facciamo provare prima dell'ordine.",
    '0ABLBOSTICE000':
        "Stivale da boscaiolo per chi taglia legna e lavora nel bosco — comodo per turni lunghi, suola pensata per il terreno smosso. In scorta sui modelli più richiesti.",
    # Glove translations where templated 'lamiere, profili, vetri' fits poorly
    '0GTIKV011MA00':  # aramidico (after move to termico)
        "Guanto in tessuto aramidico da 28 cm — pensato per chi tocca superfici calde o lavora vicino a scintille. Te lo facciamo provare prima dell'ordine. Disponibile in più taglie.",
    '0GTIGO001202':   # lattice (after move to chimico)
        "Guanto in lattice VE920 Venisette — calzata morbida, presa salda da bagnato. Lo teniamo a magazzino sui modelli più richiesti.",
    # Driver glove (pelle bovino) — leather, more "vestire le mani" than antitaglio
    '0GTIFB009OR00':
        "Guanto driver in pelle di bovino bordato — calzata morbida che si fa al lavoro. Te lo facciamo provare prima dell'ordine, in scorta sui modelli più richiesti.",
    # Zoccolo da lavoro
    '0SCARLZOMO00':
        "Zoccolo antinfortunistico — pensato per chi sta in piedi tutto il giorno e si toglie le scarpe spesso. Lo provi in negozio, una mezza misura cambia tutto.",
}

# Bullet overrides for items where category bullets don't fit
BULLET_OVERRIDES = {
    '0ABLRE6594BE00': [
        "Bagni l'inserto, lo strizzi, ti raffredda la testa",
        "Pensato per le giornate calde",
        "In scaffale d'estate",
    ],
    '0ABLRE6521ELFR': [
        "Si mette dentro l'elmetto in un attimo",
        "Tiene fresca la fronte per qualche ora",
        "Ricambio veloce, lo trovi in negozio",
    ],
    '0ELMPESOTT002': [
        "Tiene il casco fermo anche piegandosi",
        "Cambio senza attrezzi",
        "Ricambio specifico per l'elmetto Granite",
    ],
    '0ELMAC0CC': [
        "Si aggancia direttamente all'elmetto FUEGO",
        "Una sola cosa da indossare invece di due",
        "Calzata da provare insieme",
    ],
    '0POCPC0VISBALBI': [
        "Protegge faccia e testa in un pezzo solo",
        "Per lavori con schegge o spruzzi",
        "Te la facciamo provare prima dell'ordine",
    ],
    '0POCPC0VISCV12': [
        "Lente trasparente in APET da 250 micron",
        "Ricambio specifico per gli occhiali CV12",
        "Sostituzione veloce",
    ],
    '0POCPC0VISCV16': [
        "Lente APET Foam Top & Shield da 300 micron",
        "Ricambio specifico per il modello CV16",
        "La trovi in negozio",
    ],
    '0RESFIDPI230A1': [
        "Classe A1 — per vapori organici",
        "Codice 43405100",
        "Da abbinare alla semimaschera",
    ],
    '0RESFIDPI200A1P1COMB': [
        "Combinato A1P1 — vapori organici più polveri",
        "Codice 43403215",
        "Ricambio in scorta in negozio",
    ],
    '0RESFIDPI230COMB': [
        "Combinato A1P1 formato 230",
        "Codice 43405127",
        "In scorta a magazzino",
    ],
    '0RESFIDPIAIRLINE': [
        "Filtro per sistema airline",
        "Codice 43442033",
        "Cambio a scadenza, in scorta in negozio",
    ],
    '0RESFIDPI230B1': [
        "Classe B1 — per gas inorganici",
        "Codice 43405101",
        "In scorta sui modelli più richiesti",
    ],
    '0RESFIDPI230E1': [
        "Classe E1 — per gas acidi (es. anidride solforosa)",
        "Codice 43405102",
        "Ricambio in scorta in negozio",
    ],
    '0RESFIDPI230K1': [
        "Classe K1 — per l'ammoniaca",
        "Codice 43405103",
        "Lo teniamo a magazzino tutto l'anno",
    ],
    '0PUDARC00': [
        "Con archetto, pronti al collo quando servono",
        "Per chi entra ed esce da ambienti rumorosi",
        "Comodi anche per turni lunghi",
    ],
    '0PUDDELTA006': [
        "Box da 6 paia",
        "Per chi lavora con macchine rumorose",
        "Confezioni più grandi a magazzino",
    ],
    '0PUDDELTA00': [
        "Confezione da 200 paia",
        "Per le squadre che lavorano in officina",
        "In scorta tutto l'anno",
    ],
    '0ABPCUTI01': [
        "Tessuto ignifugo per il saldatore",
        "Copre testa, collo e nuca dalle scintille",
        "Te la facciamo provare in negozio",
    ],
    '0ABLBOGTCE0001': [
        "Pensato per chi lavora con la motosega",
        "Calzata generosa per il movimento",
        "Da provare in bottega prima dell'ordine",
    ],
    '0ABLBOGACE000': [
        "Si indossa sopra lo stivale",
        "Copre la gamba dalle scintille e dai tagli",
        "Pensato per il lavoro con la motosega",
    ],
    '0ABLBOSTICE000': [
        "Pensato per il lavoro nel bosco",
        "Suola per il terreno smosso",
        "Comodo per turni lunghi",
    ],
    '0GTIKV011MA00': [
        "Tessuto aramidico da 28 cm",
        "Per superfici calde o vicino alle scintille",
        "Disponibile in più taglie",
    ],
    '0GTIGO001202': [
        "Lattice — calzata morbida",
        "Presa salda anche da bagnato",
        "In scorta sui modelli più richiesti",
    ],
    '0GTIFB009OR00': [
        "Pelle di bovino, bordato",
        "Calzata morbida che si fa al lavoro",
        "Te lo facciamo provare prima dell'ordine",
    ],
    '0SCARLZOMO00': [
        "Per chi sta in piedi tutto il giorno",
        "Comodo da togliere e rimettere",
        "Una mezza misura cambia tutto — provalo in bottega",
    ],
}


def main():
    products = json.loads(DATA.read_text(encoding='utf-8'))
    by_sku = {p['sku'].strip(): p for p in products}

    # Sanity: warn if any sku in overrides isn't present
    all_skus = set(by_sku.keys())
    for tag, mapping in (('RECATEGORIZE', RECATEGORIZE),
                        ('DESC_OVERRIDES', DESC_OVERRIDES),
                        ('BULLET_OVERRIDES', BULLET_OVERRIDES)):
        for sku in mapping:
            if sku not in all_skus:
                print(f'  WARN: {tag} key {sku!r} not found in products.json')

    # Apply re-categorizations; clear desc/bullets so they get re-templated
    # (unless explicitly overridden below).
    for sku, new_slug in RECATEGORIZE.items():
        p = by_sku.get(sku)
        if not p:
            continue
        if p['filterSlug'] != new_slug:
            p['filterSlug'] = new_slug
            macro, sub = MACRO[new_slug]
            p['category'] = macro
            p['subcategory'] = sub
            # Clear templated copy so fill-copy.py re-picks from new pool
            if sku not in DESC_OVERRIDES:
                p['description'] = ''
            if sku not in BULLET_OVERRIDES:
                p['bullets'] = []

    # Apply bespoke description overrides
    for sku, desc in DESC_OVERRIDES.items():
        p = by_sku.get(sku)
        if p:
            p['description'] = desc

    # Apply bullet overrides
    for sku, bullets in BULLET_OVERRIDES.items():
        p = by_sku.get(sku)
        if p:
            p['bullets'] = bullets

    # Re-sort by macro/sub/name for stable diffs
    ORDER = ['Capo', 'Corpo', 'Mani', 'Piedi', 'Sanitario', 'Alberghiero']
    products.sort(
        key=lambda p: (ORDER.index(p['category']), p['subcategory'], p['name'].lower())
    )

    DATA.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'Applied {len(RECATEGORIZE)} re-categorizations, '
          f'{len(DESC_OVERRIDES)} desc overrides, '
          f'{len(BULLET_OVERRIDES)} bullet overrides.')


if __name__ == '__main__':
    main()
