"""Genera il sito statico in site/ a partire dai frammenti in content/.

Ogni file in content/ inizia con commenti di metadati:
  <!-- title: Titolo della pagina -->
  <!-- description: Descrizione per Google (max ~155 caratteri) -->
  <!-- blog: 2026-09-29 -->   (facoltativo: la pagina finisce nell'elenco del blog)
  <!-- script: calc -->       (facoltativo: carica assets/calc.js)

Uso: python3 build.py
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
CONTENT = ROOT / "content"
SITE = ROOT / "site"
BASE_URL = "https://eleaffar.github.io/eleaffar-/"
BRAND = "ContiChiari"

NAV = [
    ("index.html", "Home"),
    ("strumenti.html", "Strumenti"),
    ("prodotti.html", "Prodotti"),
    ("blog.html", "Guide"),
]

TEMPLATE = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>€</text></svg>">
</head>
<body>
<header><div class="wrap">
<a class="logo" href="index.html">Conti<span>Chiari</span></a>
<nav>{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>© {brand} · Strumenti e guide per freelance e partite IVA in Italia.</p>
<p>I calcoli sono stime indicative e non sostituiscono il parere di un commercialista. · <a href="privacy.html">Privacy e note legali</a></p>
</div></footer>
<script src="assets/config.js"></script>
{scripts}
</body>
</html>
"""


def parse(path):
    text = path.read_text(encoding="utf-8")
    meta = dict(re.findall(r"<!--\s*(\w+):\s*(.*?)\s*-->", text.split("\n\n", 1)[0]))
    body = re.sub(r"^(\s*<!--\s*\w+:.*?-->\s*\n)+", "", text)
    return meta, body


def blog_index(posts):
    items = "\n".join(
        f'<div class="card"><h3><a href="{p}">{html.escape(m["title"])}</a></h3>'
        f'<p>{html.escape(m["description"])}</p></div>'
        for p, m in posts
    )
    return f'<div class="grid">{items}</div>'


def main():
    pages = {p.stem + ".html": parse(p) for p in sorted(CONTENT.glob("*.html"))}
    posts = sorted(
        ((name, m) for name, (m, _) in pages.items() if "blog" in m),
        key=lambda x: x[1]["blog"],
        reverse=True,
    )
    for name, (meta, body) in pages.items():
        body = body.replace("{{BLOG_INDEX}}", blog_index(posts))
        nav = "".join(f'<a href="{href}">{label}</a>' for href, label in NAV)
        scripts = '<script src="assets/calc.js"></script>' if meta.get("script") == "calc" else ""
        out = TEMPLATE.format(
            title=html.escape(meta["title"]),
            description=html.escape(meta["description"]),
            canonical=BASE_URL + ("" if name == "index.html" else name),
            nav=nav,
            body=body.strip(),
            brand=BRAND,
            scripts=scripts,
        )
        (SITE / name).write_text(out, encoding="utf-8")

    urls = "\n".join(
        f"  <url><loc>{BASE_URL}{'' if n == 'index.html' else n}</loc></url>" for n in pages
    )
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8",
    )
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
    (SITE / ".nojekyll").write_text("")
    print(f"Generate {len(pages)} pagine in {SITE}")


if __name__ == "__main__":
    main()
