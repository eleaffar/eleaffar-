# ContiChiari

Sito di calcolatori gratuiti e guide per freelance e partite IVA in Italia, con vendita di prodotti digitali.

**Come guadagna:** i calcolatori gratuiti (tasse forfettario, prestazione occasionale, tariffa oraria) portano traffico da Google, e le pagine rimandano al prodotto a pagamento *Gestionale Forfettario* (file Excel/Google Sheets a 9,99 €), che viene consegnato in automatico dalla piattaforma di pagamento.

## Struttura

| Percorso | Contenuto |
|---|---|
| `content/` | Testo di ogni pagina (frammenti HTML con metadati in testa) |
| `site/` | Sito generato, pubblicato su GitHub Pages |
| `site/assets/` | CSS, calcolatori (`calc.js`) e link di pagamento (`config.js`) |
| `build.py` | Genera `site/` da `content/` (menu, SEO, sitemap, elenco guide) |
| `prodotti/genera_gestionale.py` | Genera il file Excel del prodotto (non va pubblicato) |

Per aggiungere una guida: crea `content/nome-guida.html` con i metadati `title`, `description` e `blog: AAAA-MM-GG`, poi lancia `python3 build.py`.

## Da fare (una volta sola, circa 20 minuti)

1. **Pubblica il sito:** unisci questo branch in `master`, poi vai su GitHub, in *Settings → Pages → Source*, e scegli **GitHub Actions**. Il sito sarà su `https://eleaffar.github.io/eleaffar-/`.
2. **Apri il negozio su [Lemon Squeezy](https://www.lemonsqueezy.com):** crea l'account, crea il prodotto "Gestionale Forfettario" a 9 € e carica il file Excel. Genera il file con `pip install openpyxl && python3 prodotti/genera_gestionale.py`.
3. **Collega il pagamento:** copia il *checkout link* del prodotto in `site/assets/config.js` (`gestionaleForfettario: "https://..."`).
4. **Fatti trovare su Google:** registra il sito su [Google Search Console](https://search.google.com/search-console) e invia `sitemap.xml`.
5. **Fisco:** chiedi a un commercialista come dichiarare queste entrate. Se le vendite diventano regolari, può servire la partita IVA.

## Automazione

Una Routine settimanale di Claude può aggiungere una nuova guida o un nuovo strumento e aprire una pull request. Tu la leggi e la unisci: il sito si aggiorna da solo.
