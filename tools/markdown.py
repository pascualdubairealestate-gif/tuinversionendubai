"""Genera una versión Markdown (index.md) junto a cada index.html público.
Los agentes de IA la reciben al pedir la página con «Accept: text/markdown» (ver .htaccess)
o directamente en /ruta/index.md. Gasta muchos menos tokens que el HTML.
Uso: python3 tools/markdown.py [raíz]   (build.py lo llama al final)"""
import os, re, sys
from bs4 import BeautifulSoup
from markdownify import markdownify

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://tuinversionendubai.com"
SKIP = {".git", "crm", "tools", "assets", "mcp", ".well-known", "404"}
DROP = "script, style, noscript, svg, form, button, iframe, video, img, picture, .modal, .toast, .wa-float, .crumbs, [hidden], [aria-hidden='true']"

FOOTER = f"""
---

**Contacto:** Pascual Vidal · Tu inversión en Dubái (agente en Dubana Real Estate, RERA #97799)
Teléfono y WhatsApp: +971 50 796 3006 · {SITE}/contacto/
Instagram: https://www.instagram.com/pascual.dubairealestate/ · YouTube: https://www.youtube.com/@pascual.dubairealestate
Más contexto para IA: {SITE}/llms.txt
"""


def to_md(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    main = soup.find("main") or soup.body
    for el in main.select(DROP):
        el.decompose()
    for a in main.find_all("a", href=True):  # enlaces absolutos: el Markdown se lee fuera de la web
        h = a["href"]
        if h.startswith("/"):
            a["href"] = SITE + h
        elif h.startswith("#"):
            a["href"] = url + h
    body = markdownify(str(main), heading_style="ATX", bullets="-")
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    head = f"---\ntitle: {title}\nurl: {url}\nlang: es\n"
    if desc and desc.get("content"):
        head += f"description: {desc['content']}\n"
    head += "---\n\n"
    return head + body + "\n" + FOOTER


count = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    top = rel.split(os.sep)[0]
    if top in SKIP:
        dirnames[:] = []
        continue
    if "index.html" not in filenames:
        continue
    path = "/" if rel == "." else "/" + rel.replace(os.sep, "/") + "/"
    html = open(os.path.join(dirpath, "index.html"), encoding="utf-8").read()
    open(os.path.join(dirpath, "index.md"), "w", encoding="utf-8").write(to_md(html, SITE + path))
    count += 1
print(f"markdown: {count} páginas")
