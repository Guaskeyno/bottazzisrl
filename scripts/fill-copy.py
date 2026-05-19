#!/usr/bin/env python3
"""
Populate products.json `description` and `bullets` fields using tone-of-voice
templates per subcategory. Deterministic per slug — re-running gives stable output.
Only overwrites entries where `description` is empty (so manual edits are preserved).
"""
import json, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'products.json'

# Per-subcategory description variants (3 each).
# Voice: Davide, owner. Use "tu", short sentences, no invented specs.
DESCS = {
    'elmetti': [
        "Elmetto da cantiere. Lo proviamo insieme — una regolazione precisa fa la differenza per chi lo porta otto ore. In scorta sui modelli più richiesti.",
        "Protezione per la testa, semplice e affidabile. Pensato per chi sta fuori — sole, pioggia, polvere. Passa a provarlo in bottega.",
        "Elmetto da lavoro per il cantiere. Te lo facciamo provare prima dell'ordine, una taglia non vale l'altra. Ne teniamo qualche pezzo in scaffale.",
    ],
    'berretti': [
        "Per la testa, le orecchie, il collo — protezione semplice per chi sta fuori d'inverno. Si infila in un secondo, sta sotto l'elmetto. Lo trovi in negozio.",
        "Copricapo da lavoro per le giornate fredde. Si lava in lavatrice, non rovina. Te ne mostriamo qualcuno quando passi.",
        "Berretto pensato per chi lavora fuori col freddo. Comodo da portare per ore, senza dare fastidio sotto il casco. Ne teniamo qualche pezzo in scaffale.",
    ],
    'occhiali': [
        "Occhiali da lavoro per officina e cantiere. Te li facciamo provare prima dell'ordine — la calzata fa la differenza. In scorta sui modelli più richiesti.",
        "Protezione per gli occhi nei lavori con scintille, polveri o schegge. Comodi anche con la mascherina. Passa a provarli quando vuoi.",
        "Occhiali pensati per chi sta in officina o in cantiere tutti i giorni. Calzata da provare in bottega — non tutte le facce sono uguali. Ne teniamo qualche modello in scaffale.",
    ],
    'udito': [
        "Protezione per l'udito da portare in officina, in cantiere, vicino ai generatori. Comoda anche per turni lunghi. Te la facciamo provare prima dell'ordine.",
        "Cuffia antirumore per chi lavora con macchine pesanti. Si abbina al casco, non scomoda. Ne teniamo qualche pezzo in scaffale.",
        "Protezione per l'udito di tutti i giorni. Si regola sulla testa, non stringe. Passa a provarla quando vuoi.",
    ],
    'respirazione': [
        "Protezione per le vie respiratorie nei lavori con polveri o vapori. Te la facciamo provare prima dell'ordine — la tenuta sul viso conta. In scorta tutto l'anno.",
        "Per chi lavora a contatto con polveri, fumi o vapori. Comoda anche per turni lunghi. Ricambi disponibili in negozio.",
        "Maschera per le vie respiratorie nei lavori sporchi. Te la mostriamo prima dell'ordine, e i ricambi li teniamo a magazzino.",
    ],
    'anticaduta': [
        "Sistema anticaduta per chi lavora in quota — tetti, ponteggi, pali. La proviamo insieme prima di consegnarla, una taglia non vale l'altra. Ne teniamo qualche pezzo in scaffale.",
        "Dispositivo per il lavoro in altezza. Pensato per chi sale tutti i giorni. In bottega lo provi prima di prenderlo.",
        "Per il lavoro in quota di tutti i giorni. Te lo facciamo provare prima dell'ordine — la regolazione sul corpo fa la differenza. Disponibile in più taglie.",
    ],
    'alta-visibilita': [
        "Capo ad alta visibilità per chi lavora in strada, in cantiere, ai magazzini. Si lava in lavatrice senza problemi. Disponibile in più taglie a magazzino.",
        "Per farsi vedere — di giorno e con i fari. Comodo, taglio che lascia muoversi. Te lo facciamo provare prima dell'ordine.",
        "Indumento ad alta visibilità per chi sta in mezzo al traffico o ai mezzi pesanti. Pensato per giornate intere. Ne teniamo qualche pezzo in scorta tutto l'anno.",
    ],
    'pantaloni': [
        "Pantalone da lavoro pensato per chi si muove tutto il giorno. Te lo facciamo provare prima dell'ordine — sulle taglie non si scherza. Ne teniamo le più richieste in scaffale.",
        "Per il lavoro in cantiere, in officina, in magazzino. Regge i lavaggi industriali. Te ne mostriamo qualcuno quando passi.",
        "Pantalone da lavoro robusto e comodo. Taglio che lascia piegare e salire. Disponibile in più taglie a magazzino.",
    ],
    'multi-protezione': [
        "Tuta integrale per lavori sporchi — verniciatura, bonifiche, ambienti polverosi. Si indossa sopra l'abbigliamento da lavoro. In scorta sui modelli più richiesti.",
        "Coverall per chi entra in ambienti dove serve coprirsi del tutto. Pensata per turni continui. Te la facciamo vedere quando passi.",
        "Tuta da indossare sopra il vestiario, per i lavori dove la pulizia non è un'opzione. Disponibile in più taglie. Te la mostriamo prima dell'ordine.",
    ],
    'rischio-chimico': [
        "Guanto per il contatto con prodotti chimici, vernici e solventi. Te lo facciamo provare prima di ordinare le casse. Disponibile in più taglie.",
        "Protezione per le mani che lavorano con acidi, oli o sostanze aggressive. Lo provi in bottega prima dell'ordine. In scaffale sui modelli più richiesti.",
        "Guanto pensato per chi maneggia liquidi non amichevoli. Calzata da provare prima dell'ordine. Ne teniamo qualche modello a magazzino.",
    ],
    'rischio-meccanico': [
        "Guanto da lavoro contro tagli, abrasioni e urti. Lo proviamo insieme prima di ordinarli a casse. In scorta sui modelli più richiesti.",
        "Per chi maneggia lamiere, profili, vetri. Te lo facciamo provare prima dell'ordine. Disponibile in più taglie a magazzino.",
        "Guanto per il lavoro di tutti i giorni. Pensato per chi sa cosa significa una mano scoperta tra le lame. Passa a provarlo.",
    ],
    'rischio-termico': [
        "Per le mani esposte al calore — saldatura, forni, lavorazioni a caldo. Te lo facciamo provare prima dell'ordine. Disponibile in più taglie.",
        "Protezione per chi lavora con superfici calde, scintille, fiamma. Lo provi in bottega prima dell'ordine. Ne teniamo qualche modello a magazzino.",
        "Guanto pensato per saldatura e lavorazioni a caldo. Te lo facciamo provare prima dell'ordine. In scorta sui misti più richiesti.",
    ],
    'scarpe': [
        "Scarpa antinfortunistica per chi sta in piedi tutto il giorno. Te le facciamo provare — una mezza misura cambia tutto. Tre taglie sempre a magazzino sui modelli più richiesti.",
        "Calzatura da lavoro pensata per turni lunghi. Da provare in bottega prima dell'ordine. Ne teniamo qualche modello in scaffale.",
        "Scarpa da cantiere comoda fin dal primo giorno. Te la facciamo provare quando passi. Disponibile in più misure.",
    ],
    'stivali': [
        "Stivale da lavoro per chi sta in mezzo all'acqua, al fango, alle lavorazioni umide. Lo proviamo insieme prima dell'ordine. In scorta sui modelli più richiesti.",
        "Calzatura alta per cantieri bagnati o ambienti che sporcano. Disponibile in più taglie. Te lo facciamo vedere quando passi.",
        "Stivale pensato per chi lavora con liquidi, terreno smosso, ambienti scivolosi. Comodo da portare tutto il giorno. In bottega lo provi prima di ordinare.",
    ],
    'sanitario': [
        "Capo per il settore sanitario. Tessuto che regge i lavaggi a caldo, taglio comodo per il turno. Te lo facciamo provare prima dell'ordine.",
        "Abbigliamento per chi lavora in studio medico, in ambulatorio, in casa di cura. Disponibile in più taglie a magazzino.",
        "Per il personale sanitario. Comodo per ore, lavabile a caldo. Passa a provarlo quando vuoi.",
    ],
    'alberghiero': [
        "Capo per il settore alberghiero e della ristorazione. Tessuto che regge i lavaggi industriali. Disponibile in più taglie a magazzino.",
        "Abbigliamento per chi lavora in cucina, in sala, in reception. Pensato per giornate intere. Te lo facciamo provare prima dell'ordine.",
        "Per chi indossa la divisa otto ore al giorno. Comodo, lavabile, pensato per il mestiere. Passa a provarlo quando vuoi.",
    ],
    'busto': [
        "Capo da lavoro per officina, cantiere, magazzino. Tessuto che regge i lavaggi, taglio comodo. Disponibile in più taglie a magazzino.",
        "Abbigliamento da lavoro pensato per durare. Te lo facciamo provare prima dell'ordine. Ne teniamo qualche pezzo in scaffale tutto l'anno.",
        "Per chi indossa la divisa otto ore al giorno. Comodo, lavabile, pensato per il mestiere. Passa a provarlo quando vuoi.",
    ],
}

# Per-subcategory bullet pool. Each product gets 3 picks (deterministic by slug).
# Voice: short, use-case oriented, no invented specs.
BULLETS = {
    'elmetti': [
        "Per chi sta in cantiere tutti i giorni",
        "Comodo da portare per ore",
        "Lo provi in negozio prima dell'ordine",
        "Pensato per il lavoro fuori al sole e alla pioggia",
        "Ne teniamo qualche pezzo in scaffale",
        "Regolazione da provare insieme",
    ],
    'berretti': [
        "Per le giornate fredde in cantiere",
        "Si infila sotto l'elmetto senza ingombro",
        "Comodo da portare per ore",
        "Lascia il viso libero",
        "Ne teniamo qualche pezzo in scaffale",
        "Lo provi quando passi in bottega",
    ],
    'occhiali': [
        "Per il lavoro in officina e cantiere",
        "Da provare prima di prenderne più paia",
        "Comodi anche con la mascherina",
        "Ne teniamo i modelli più richiesti in scaffale",
        "Pensati per chi lavora con scintille o schegge",
        "Calzata da provare insieme",
    ],
    'udito': [
        "Per chi lavora vicino a macchine rumorose",
        "Si abbinano al casco senza scomporsi",
        "Comodi anche per turni lunghi",
        "Da provare prima di ordinarli in più paia",
        "In scorta sui modelli più richiesti",
        "Pensati per officina, cantiere, generatori",
    ],
    'respirazione': [
        "Per chi lavora con polveri o vapori",
        "Da provare prima di ordinare le confezioni",
        "Ricambi disponibili in negozio",
        "Si abbina a occhiali e visiera",
        "Comoda anche per turni lunghi",
        "In scorta tutto l'anno",
    ],
    'anticaduta': [
        "Per chi lavora in quota tutti i giorni",
        "La proviamo insieme prima di consegnarla",
        "Pensata per tetti, ponteggi e pali",
        "Disponibile in più taglie da provare in bottega",
        "Ne teniamo qualche pezzo in scaffale",
        "Regolazione precisa sul corpo",
    ],
    'alta-visibilita': [
        "Per chi lavora in strada o nel traffico",
        "Visibile di giorno e con i fari",
        "Si lava in lavatrice senza problemi",
        "Comodo per giornate intere",
        "Disponibile in più taglie a magazzino",
        "Lo provi in negozio prima dell'ordine",
    ],
    'pantaloni': [
        "Per chi si muove tutto il giorno",
        "Disponibile in più taglie a magazzino",
        "Da provare prima di ordinarli per la squadra",
        "Regge i lavaggi industriali",
        "Comodo per cantiere, officina, magazzino",
        "Te lo facciamo provare quando passi",
    ],
    'multi-protezione': [
        "Per ambienti polverosi o sporchi",
        "Si indossa sopra l'abbigliamento da lavoro",
        "Pensata per turni continui",
        "Disponibile in più taglie",
        "Te la facciamo vedere prima dell'ordine",
        "In scorta sui modelli più richiesti",
    ],
    'rischio-chimico': [
        "Per chi maneggia liquidi aggressivi",
        "Lo provi in bottega prima di ordinare le casse",
        "Disponibile in più taglie a magazzino",
        "Pensato per uso quotidiano",
        "Ne teniamo i modelli più richiesti in scaffale",
        "Calzata da provare insieme",
    ],
    'rischio-meccanico': [
        "Per chi maneggia lamiere, profili, vetri",
        "Te lo facciamo provare prima dell'ordine",
        "Disponibile in più taglie a magazzino",
        "Pensato per il lavoro di tutti i giorni",
        "In scorta sui modelli più richiesti",
        "Comodo anche per ore continue",
    ],
    'rischio-termico': [
        "Per saldatura e lavorazioni a caldo",
        "Pensato per il contatto con superfici calde",
        "Lo provi prima di prenderne più paia",
        "Disponibile in più taglie a magazzino",
        "Te lo facciamo provare quando passi",
        "In scorta sui misti più richiesti",
    ],
    'scarpe': [
        "Per chi sta in piedi tutto il giorno",
        "Tre taglie sempre a magazzino sui più richiesti",
        "Una mezza misura cambia tutto — provala in bottega",
        "Comoda fin dal primo giorno",
        "Pensata per turni lunghi",
        "Ne teniamo i modelli più richiesti in scaffale",
    ],
    'stivali': [
        "Per ambienti bagnati, fango, lavorazioni umide",
        "Da provare prima di ordinarne più paia",
        "Comodo da portare tutto il giorno",
        "In scorta nelle taglie più richieste",
        "Te lo facciamo vedere quando passi",
        "Pensato per acqua, fango, terreno smosso",
    ],
    'sanitario': [
        "Per chi lavora in studio medico o ambulatorio",
        "Tessuto che regge i lavaggi a caldo",
        "Disponibile in più taglie a magazzino",
        "Comodo per turni continui",
        "Te lo facciamo provare prima dell'ordine",
        "Ne teniamo qualche pezzo in scaffale",
    ],
    'alberghiero': [
        "Per cucina, sala o reception",
        "Tessuto che regge i lavaggi industriali",
        "Disponibile in più taglie a magazzino",
        "Comodo per turni lunghi",
        "Te lo facciamo provare prima dell'ordine",
        "Ne teniamo qualche pezzo in scaffale",
    ],
    'busto': [
        "Per chi indossa la divisa otto ore al giorno",
        "Disponibile in più taglie a magazzino",
        "Te lo facciamo provare prima dell'ordine",
        "Regge i lavaggi industriali",
        "Taglio che lascia muoversi",
        "Comodo per giornate intere",
    ],
}


def stable_hash(s: str) -> int:
    return int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)


def pick_description(slug: str, cat: str) -> str:
    pool = DESCS.get(cat) or DESCS['busto']
    return pool[stable_hash(slug + ':desc') % len(pool)]


def pick_bullets(slug: str, cat: str, n: int = 3) -> list:
    pool = BULLETS.get(cat) or BULLETS['busto']
    start = stable_hash(slug + ':bullets') % len(pool)
    rotated = pool[start:] + pool[:start]
    return rotated[:n]


def main():
    products = json.loads(DATA.read_text(encoding='utf-8'))
    overwrite_all = '--force' in sys.argv

    filled_desc = filled_bul = skipped = 0
    for p in products:
        cat = p.get('filterSlug', 'busto')
        if overwrite_all or not (p.get('description') or '').strip():
            p['description'] = pick_description(p['slug'], cat)
            filled_desc += 1
        else:
            skipped += 1
        if overwrite_all or not p.get('bullets'):
            p['bullets'] = pick_bullets(p['slug'], cat)
            filled_bul += 1

    DATA.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'descriptions filled: {filled_desc} (skipped {skipped} with existing)')
    print(f'bullet sets filled:  {filled_bul}')


if __name__ == '__main__':
    main()
