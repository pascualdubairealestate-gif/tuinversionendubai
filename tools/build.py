"""Genera /blog, sus artículos y las páginas legales a partir de la plantilla de index.html.
Uso: python3 tools/build.py   (desde la raíz del repo)"""
import json, re, sys, html as H

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://tuinversionendubai.com"
V = "20261113a"
DATE = "2026-10-28"
DATE_TXT = "28 de octubre de 2026"

src = open(f"{ROOT}/index.html").read()

def grab(start, end):
    i = src.index(start)
    return src[i:src.index(end, i) + len(end)]

def absolutize(s):
    s = re.sub(r'(?<!<use )href="#(?!")', 'href="/#', s)
    return s.replace('src="assets/', 'src="/assets/')

nav = absolutize(grab('<header class="nav" data-nav>', '</header>'))
footer = absolutize(grab('<footer class="footer">', '</footer>'))
tail = grab('  <!-- WhatsApp flotante -->', '<!-- Modal: dossier de proyecto -->').replace('  <!-- Modal: dossier de proyecto -->', '')
sprite = grab('  <!-- Iconos -->', '</svg>\n')
toast = '  <div class="toast" data-toast role="status" aria-live="polite"></div>\n'
favicon = re.search(r'<link rel="icon"[^>]*>', src).group(0)

PERSON_ID = SITE + "/sobre-pascual-vidal/#pascual"
ORG_ID = SITE + "/#organizacion"
WEB_ID = SITE + "/#web"
AUTHOR = {"@type": "Person", "@id": PERSON_ID, "name": "Pascual Vidal", "url": SITE + "/sobre-pascual-vidal/",
          "jobTitle": "Consultor de inversión inmobiliaria en Dubái", "image": SITE + "/assets/img/pascual-retrato.webp",
          "sameAs": ["https://www.instagram.com/pascual.dubairealestate/", "https://www.youtube.com/@pascual.dubairealestate"],
          "telephone": "+971507963006",
          "affiliation": {"@type": "RealEstateAgent", "name": "Dubana Real Estate", "address": {"@type": "PostalAddress", "addressLocality": "Dubái", "addressCountry": "AE"}}}
PUBLISHER = {"@type": "Organization", "@id": ORG_ID, "name": "Tu inversión en Dubái", "url": SITE + "/",
             "logo": {"@type": "ImageObject", "url": SITE + "/assets/img/logo-pv-512.png", "width": 512, "height": 512}, "telephone": "+971507963006"}
WA_LINK = "https://wa.me/message/QI3A7Q5BXFTCA1"
TODAY = "2026-11-15"

from PIL import Image as _Img
import os as _os


def dims(src):
    """Ancho y alto reales de una imagen local (para evitar saltos de maquetación)."""
    w, h = _Img.open(ROOT + src).size
    return f'width="{w}" height="{h}"'


def og_jpg(image):
    """Versión JPG 1200x630 de la imagen para redes (generada por tools/seo_assets.py)."""
    name = _os.path.basename(image).rsplit(".", 1)[0]
    j = f"/assets/img/og/{name}.jpg"
    return j if _os.path.exists(ROOT + j) else "/assets/img/og/pascual-vidal.jpg"



def page(path, title, desc, body, ld, og_image="/assets/img/og/pascual-vidal.jpg", og_type="article", body_attrs="", og_alt="Pascual Vidal, consultor inmobiliario español en Dubái"):
    url = SITE + path
    return f"""<!doctype html>
<html lang="es" class="no-js">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{H.escape(title)}</title>
  <meta name="description" content="{H.escape(desc)}" />
  <link rel="canonical" href="{url}" />
  <link rel="alternate" hreflang="es" href="{url}" />
  <link rel="alternate" hreflang="x-default" href="{url}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:locale" content="es_ES" />
  <meta property="og:site_name" content="Tu inversión en Dubái" />
  <meta property="og:url" content="{url}" />
  <meta property="og:title" content="{H.escape(title)}" />
  <meta property="og:description" content="{H.escape(desc)}" />
  <meta property="og:image" content="{SITE}{og_image}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="{H.escape(og_alt)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="author" content="Pascual Vidal" />
  <meta name="theme-color" content="#ffffff" />
  {favicon}
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500;1,600&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/styles.css?v={V}" />
  <script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
  </script>
</head>
<body class="blog-page"{body_attrs}>

  {nav}

  <main class="blog">
{body}
  </main>

  {footer}

{tail}{toast}
{sprite}
  <script defer src="/main.js?v={V}"></script>
</body>
</html>
"""


ARTICLES = []


def article(slug, title, h1, desc, lead, image, alt, sections, faqs, related, date=DATE, date_txt=DATE_TXT, wa_msg=None):
    summary = SUMMARIES.get(slug, [])
    ARTICLES.append(dict(slug=slug, title=title, h1=h1, desc=desc, lead=lead, image=image, alt=alt, date=date, date_txt=date_txt, summary=summary,
                         faqs=faqs, sections=[t for _, t, _ in sections]))
    tldr = ('\n      <div class="tldr" id="resumen"><b>En resumen</b><ul>' + "".join(f"<li>{x}</li>" for x in summary) + "</ul></div>") if summary else ""
    toc = "".join(f'<li><a href="#{sid}">{H.escape(t)}</a></li>' for sid, t, _ in sections)
    secs = "".join(f'\n      <h2 id="{sid}">{H.escape(t)}</h2>\n{c}' for sid, t, c in sections)
    faq_html = "".join(
        f'<details class="faq-item"><summary><span>{H.escape(q)}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><p>{a}</p></details>'
        for q, a in faqs)
    rel = "".join(f'<a class="related-card" href="/blog/{s}/"><small>Artículo</small><b>{H.escape(t)}</b><span>Leer →</span></a>' for s, t in related)
    path = f"/blog/{slug}/"
    wa_text = H.escape(wa_msg or ("Hola Pascual, he leído tu artículo «" + re.sub("<[^>]+>", "", h1) + "» y quiero consultarte mi caso."))
    body = f"""    <article class="article">
      <header class="article-head container">
        <nav class="crumbs" aria-label="Migas de pan"><a href="/">Inicio</a><span>/</span><a href="/blog/">Blog</a></nav>
        <p class="eyebrow"><span class="dot"></span>Guía para inversores · Actualizado el {date_txt}</p>
        <h1>{h1}</h1>
        <p class="article-lead">{lead}</p>
        <div class="article-author"><img src="/assets/img/pascual-retrato.webp" alt="Pascual Vidal" width="48" height="48" loading="lazy" /><span><a href="/sobre-pascual-vidal/" rel="author"><b>Pascual Vidal</b></a><small>Consultor inmobiliario en Dubái · RERA #97799 · <time datetime="{date}">{date_txt}</time></small></span></div>
      </header>
      <figure class="article-cover container"><img src="{image}" alt="{H.escape(alt)}" {dims(image)} loading="eager" fetchpriority="high" /></figure>
      <div class="article-layout container">
        <aside class="toc"><b>En este artículo</b><ol>{toc}</ol></aside>
        <div class="prose">{tldr}{secs}
      <h2 id="preguntas">Preguntas frecuentes</h2>
      <div class="article-faq">{faq_html}</div>
      <div class="article-cta">
        <div>
          <p class="eyebrow"><span class="dot"></span>Consultoría gratuita</p>
          <h3>¿Hacemos los números de tu caso?</h3>
          <p>En 20 minutos vemos tu presupuesto, tu objetivo y qué zonas encajan contigo. Sin compromiso.</p>
        </div>
        <div class="article-cta-actions">
          <a class="btn btn-wa" data-wa data-wa-msg="{wa_text}" href="{WA_LINK}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-wa"/></svg><span>Escríbeme por WhatsApp</span></a>
          <button class="btn btn-dark" type="button" data-open-guide>Descargar la guía gratis</button>
        </div>
      </div>
      <p class="disclaimer">Información general orientativa, no asesoramiento fiscal ni legal. Las tasas y normas cambian: confirma siempre las cifras vigentes antes de comprar.</p>
        </div>
      </div>
      <section class="related container"><h2>Sigue leyendo</h2><div class="related-grid">{rel}</div></section>
    </article>"""
    ld = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "@id": SITE + path + "#articulo", "headline": re.sub("<[^>]+>", "", h1), "description": desc,
         "abstract": " ".join(re.sub("<[^>]+>", "", x) for x in summary) or desc,
         "image": [SITE + og_jpg(image), SITE + image], "datePublished": date, "dateModified": date, "inLanguage": "es", "author": AUTHOR,
         "publisher": PUBLISHER, "mainEntityOfPage": {"@type": "WebPage", "@id": SITE + path}, "isPartOf": {"@id": WEB_ID},
         "articleSection": "Guías para inversores", "about": [{"@type": "Place", "name": "Dubái"}, {"@type": "Thing", "name": "Inversión inmobiliaria"}],
         "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".article-lead", ".tldr"]}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": title, "item": SITE + path}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in faqs]},
    ]
    return path, page(path, title + " · Pascual Vidal", desc, body, ld, og_image=og_jpg(image), og_alt=alt)


def p(*paras):
    return "".join(f"      <p>{x}</p>\n" for x in paras)


def ul(*items):
    return "      <ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>\n"


def table(head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'      <div class="table-scroll"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>\n'


def note(x):
    return f'      <p class="callout">{x}</p>\n'


pages = {}

# Resumen al inicio de cada artículo: respuestas directas y citables (lectores con prisa, Google y buscadores con IA).
SUMMARIES = {
    "cuanto-cuesta-comprar-piso-dubai": [
        "En Dubái hay estudios y apartamentos de 1 dormitorio por debajo de <strong>200.000 €</strong> en zonas en crecimiento; en obra nueva reservas con un <strong>10–20 %</strong> y pagas el resto por fases.",
        "El gasto principal es el <strong>4 % del Dubai Land Department</strong>, que se paga una sola vez.",
        "Calcula unos gastos totales del <strong>6–8 %</strong> en segunda mano y del <strong>4–5 %</strong> en obra nueva, donde normalmente no hay comisión de agencia.",
        "Cada año pagarás sobre todo la <strong>cuota de comunidad</strong> (<em>service charge</em>); en Emiratos no hay IBI.",
    ],
    "impuestos-invertir-dubai-espanol": [
        "En Emiratos, un particular no paga impuesto sobre la renta, ni sobre plusvalías, ni IBI: solo el <strong>4 % del DLD</strong> al comprar.",
        "Si eres residente fiscal en España, declaras el piso en el <strong>IRPF</strong> (alquiler, imputación de rentas o ganancia al vender).",
        "Con más de <strong>50.000 €</strong> en inmuebles en el extranjero debes presentar el <strong>modelo 720</strong>; según tu caso, también cuenta para Patrimonio.",
        "Existe un convenio de doble imposición España–Emiratos; la Golden Visa por sí sola no cambia tu residencia fiscal.",
    ],
    "golden-visa-dubai-inversion-inmobiliaria": [
        "La Golden Visa es una residencia de <strong>10 años</strong>, renovable, que no te obliga a vivir en Emiratos.",
        "Por inversión inmobiliaria necesitas un mínimo de <strong>2 millones de AED</strong> (unos 500.000 €) en una o varias propiedades; vale la obra nueva y, con condiciones, la compra con hipoteca.",
        "Puedes incluir a tu cónyuge, a tus hijos y, en muchos casos, a tus padres.",
        "Si no llegas al mínimo, existe un visado de inversor de 2 años con un umbral más bajo.",
    ],
    "invertir-en-dubai-desde-mexico": [
        "Un dírham ronda los <strong>5 pesos</strong>: un apartamento de 1 dormitorio de 1.000.000 AED son unos <strong>5 millones MXN</strong>.",
        "El dinero se envía por transferencia internacional (mejor en dólares) a la cuenta <em>escrow</em> del proyecto, justificando su origen.",
        "Como residente fiscal en México, declaras las rentas y la ganancia al vender; en Emiratos no pagas impuesto sobre la renta.",
        "Todo el proceso se puede hacer a distancia, sin viajar a Dubái.",
    ],
    "invertir-en-dubai-desde-colombia": [
        "Un dírham ronda los <strong>1.100 pesos colombianos</strong>: un apartamento de 1 habitación de 1.000.000 AED son unos <strong>1.100 millones COP</strong>.",
        "La inversión se canaliza por el mercado cambiario a través de tu banco, con la declaración de cambio que corresponda.",
        "Como residente fiscal en Colombia declaras rentas, ganancia ocasional y, si superas el límite de la DIAN, activos en el exterior.",
        "Comprar en Dubái te da patrimonio ligado al dólar y se puede hacer sin viajar.",
    ],
    "invertir-en-dubai-desde-miami": [
        "El dírham está fijado al dólar (<strong>1 USD = 3,6725 AED</strong>): compras, cobras y vendes sin riesgo de cambio.",
        "Un apartamento de 1 dormitorio de 1.000.000 AED cuesta unos <strong>272.000 USD</strong>; la Golden Visa empieza en unos 545.000 USD.",
        "Emiratos no grava al particular, pero el IRS sí: rentas y ganancias se declaran en EE. UU. (y FBAR si tienes cuentas allí por encima de 10.000 USD).",
        "Se paga por <em>wire transfer</em> en dólares y la compra se hace en remoto.",
    ],
    "invertir-en-dubai-desde-espana": [
        "Un dírham ronda los <strong>0,24 €</strong>: un estudio en zona en crecimiento cuesta unos <strong>155.000 €</strong> y un apartamento de 1 dormitorio, unos 240.000 €.",
        "En obra nueva reservas con un <strong>10–20 %</strong>; los bancos españoles no suelen financiar, pero algunos bancos de Emiratos dan hipoteca a no residentes (50–60 %).",
        "En Emiratos no hay IBI ni impuesto sobre la renta para particulares; en España declaras IRPF, modelo 720 si superas 50.000 € y, según tu caso, Patrimonio.",
        "Se puede comprar todo desde España, sin viajar.",
    ],
}

# ---------------------------------------------------------------- 1
pages["cuanto-cuesta-comprar-piso-dubai"] = article(
    "cuanto-cuesta-comprar-piso-dubai",
    "Cuánto cuesta comprar un piso en Dubái: todos los gastos",
    "Cuánto cuesta comprar un piso en Dubái: <em>todos los gastos</em>",
    "Precio de entrada, 4 % del Dubai Land Department, comisiones, hipoteca y gastos anuales. Lo que de verdad pagas al comprar un piso en Dubái, explicado por un consultor español.",
    "El precio del anuncio no es lo que pagas. Aquí tienes, uno por uno, los gastos de comprar un piso en Dubái —sobre plano y de segunda mano— y lo que te costará mantenerlo cada año.",
    "/assets/img/proyecto-dubai-islands.webp", "Vista de Dubai Islands, una de las zonas de obra nueva de Dubái",
    [
        ("precio", "Cuánto dinero necesitas para empezar",
         p("Dubái tiene un rango de precios muy amplio. Hay estudios y apartamentos de un dormitorio en zonas en crecimiento por debajo de 200.000 €, y apartamentos y villas en zonas prime que superan con facilidad el millón.",
           "La buena noticia es que, si compras <strong>sobre plano</strong>, no necesitas todo el dinero al principio. Lo habitual es reservar con un <strong>10–20 %</strong> y pagar el resto por fases durante la obra; algunos promotores incluso aplazan una parte a después de la entrega (<em>post-handover</em>).")),
        ("gastos-compra", "Gastos de compra, uno por uno",
         p("Estos son los gastos que se suman al precio. Las cifras son orientativas: confírmalas siempre en el momento de comprar.") +
         table(["Gasto", "Cuánto", "Quién lo paga"], [
             ["Registro en el Dubai Land Department (DLD)", "4 % del precio", "Comprador (a veces el promotor lo descuenta en promociones)"],
             ["Tasas administrativas del registro", "Unos cientos de euros", "Comprador"],
             ["Oficina de registro (<em>trustee</em>)", "Aprox. 2.000–4.000 AED + IVA, según el precio", "Comprador, en segunda mano"],
             ["Comisión de la agencia", "Normalmente 2 % + 5 % de IVA", "Comprador en segunda mano; en obra nueva suele pagarla el promotor"],
             ["Certificado de no deuda del promotor (NOC)", "Entre 500 y 5.000 AED", "Vendedor, en segunda mano"],
             ["Registro de hipoteca (si financias)", "0,25 % del préstamo + tasas", "Comprador"],
             ["Tasación y comisión del banco", "Tasación de unos 2.500–3.500 AED y hasta un 1 % de apertura", "Comprador"],
         ]) +
         note("<strong>Regla rápida:</strong> calcula entre un <strong>6 % y un 8 %</strong> sobre el precio en segunda mano, y alrededor de un <strong>4–5 %</strong> en obra nueva, donde normalmente no hay comisión de agencia.")),
        ("ejemplo", "Ejemplo con números: piso de 300.000 €",
         p("Supongamos un apartamento de segunda mano de 300.000 € pagado al contado:") +
         table(["Concepto", "Importe aproximado"], [
             ["Precio", "300.000 €"], ["DLD (4 %)", "12.000 €"], ["Comisión agencia (2 % + IVA)", "6.300 €"],
             ["Trustee y tasas de registro", "≈ 1.500 €"], ["<strong>Total</strong>", "<strong>≈ 319.800 €</strong>"],
         ]) +
         p("Si fuera <strong>obra nueva</strong> al mismo precio, desaparecería normalmente la comisión de agencia y el total rondaría los <strong>313.000 €</strong>, repartidos en el plan de pagos.")),
        ("gastos-anuales", "Gastos anuales: lo que cuesta mantenerlo",
         p("Una vez es tuyo, estos son los gastos recurrentes:") +
         ul("<strong>Cuota de comunidad (<em>service charge</em>):</strong> se paga por pie cuadrado al año y depende mucho del edificio. Es el gasto fijo más importante: pregúntalo siempre antes de comprar.",
            "<strong>Electricidad y agua (DEWA):</strong> si alquilas a largo plazo, las paga el inquilino.",
            "<strong>Seguro del hogar:</strong> económico, normalmente unos pocos cientos de euros al año.",
            "<strong>Gestión del alquiler:</strong> entre un 5 % y un 8 % del alquiler anual en larga estancia, y bastante más en alquiler vacacional, donde la gestión incluye reservas, limpieza y mantenimiento.",
            "<strong>Licencia de alquiler vacacional:</strong> solo si alquilas por noches, con su renovación anual.") +
         note("En Emiratos <strong>no hay IBI</strong> ni impuesto anual sobre la propiedad como en España.")),
        ("errores", "Errores que encarecen la compra",
         ul("Comparar precios sin mirar la <strong>cuota de comunidad</strong>: dos pisos al mismo precio pueden tener gastos anuales muy distintos.",
            "No reservar dinero para el <strong>amueblado</strong> si vas a alquilar: un piso amueblado se alquila antes y más caro.",
            "Elegir promotor solo por el precio: en obra nueva, la <strong>solvencia y el historial de entregas</strong> del promotor valen más que un pequeño descuento.",
            "Olvidar el <strong>tipo de cambio</strong>: el dírham está ligado al dólar, así que la evolución euro-dólar afecta a lo que pagas y a lo que cobras.")),
    ],
    [
        ("¿Se puede comprar en Dubái sin hipoteca?", "Sí, y es lo más habitual entre inversores extranjeros, sobre todo en obra nueva con plan de pagos."),
        ("¿Los bancos de Dubái dan hipoteca a no residentes?", "Sí, algunos bancos financian a no residentes, normalmente hasta el 50–60 % del valor y con más requisitos que a un residente."),
        ("¿Qué es el 4 % del DLD?", "Es la tasa de registro del Dubai Land Department, el registro oficial de la propiedad. Es el principal gasto de compra y se paga una sola vez."),
    ],
    [("impuestos-invertir-dubai-espanol", "Impuestos al invertir en Dubái siendo español"), ("golden-visa-dubai-inversion-inmobiliaria", "Golden Visa de Dubái por inversión inmobiliaria")],
)

# ---------------------------------------------------------------- 2
pages["impuestos-invertir-dubai-espanol"] = article(
    "impuestos-invertir-dubai-espanol",
    "Impuestos al invertir en Dubái siendo español",
    "Impuestos al invertir en Dubái <em>siendo español</em>",
    "Qué impuestos pagas en Emiratos y qué tienes que declarar en España si compras un piso en Dubái: alquiler, venta, IRPF, modelo 720 y convenio de doble imposición.",
    "«En Dubái no se pagan impuestos» es verdad solo a medias. Emiratos apenas grava la propiedad, pero si eres residente fiscal en España, Hacienda sí quiere saber de tu piso. Te explico qué pagas en cada país.",
    "/assets/img/pascual-consultoria.webp", "Pascual Vidal en una consultoría con inversores",
    [
        ("emiratos", "Qué pagas en Emiratos",
         ul("<strong>Al comprar:</strong> el 4 % del Dubai Land Department y las tasas de registro. Es un pago único.",
            "<strong>Por tener la propiedad:</strong> no hay IBI ni impuesto anual sobre la vivienda.",
            "<strong>Por alquilarla:</strong> no hay impuesto sobre la renta para personas físicas. Existe una tasa municipal sobre el alquiler, pero la paga el inquilino con su factura de luz y agua.",
            "<strong>Al venderla:</strong> no hay impuesto sobre la plusvalía para particulares.") +
         note("Ojo si compras a través de una <strong>empresa</strong>: desde 2023 Emiratos tiene un impuesto de sociedades del 9 % sobre beneficios a partir de cierto umbral. Para un particular que compra a su nombre, en general no aplica.")),
        ("espana", "Qué tienes que declarar en España",
         p("Si eres <strong>residente fiscal en España</strong> (vives más de 183 días al año en España o allí está tu centro de intereses), tributas por tu renta mundial. Eso incluye tu piso de Dubái:") +
         ul("<strong>Rentas del alquiler:</strong> se declaran en el IRPF como rendimientos del capital inmobiliario, restando los gastos deducibles.",
            "<strong>Si no lo alquilas:</strong> puede aplicarse la imputación de rentas inmobiliarias, como con cualquier segunda vivienda.",
            "<strong>Al venderlo:</strong> la ganancia patrimonial va a la base del ahorro del IRPF, con tipos que hoy van aproximadamente del 19 % al 30 %.",
            "<strong>Modelo 720:</strong> si tus inmuebles en el extranjero superan los 50.000 €, tienes que informar de ellos. Las multas desproporcionadas se anularon en 2022, pero la obligación de presentarlo sigue.",
            "<strong>Patrimonio:</strong> según tu comunidad autónoma y tu patrimonio total, el piso cuenta para el impuesto sobre el patrimonio o el de grandes fortunas.")),
        ("convenio", "El convenio de doble imposición España–Emiratos",
         p("España y Emiratos firmaron un convenio para evitar la doble imposición. Su función es que no pagues dos veces por la misma renta. Como Emiratos apenas grava al particular, en la práctica lo relevante para un residente en España es lo que pagas aquí.",
           "La forma exacta de aplicarlo depende de tu caso. Es justo el punto donde conviene un <strong>asesor fiscal</strong> con experiencia en inversiones en el extranjero.")),
        ("residencia", "¿Y si me voy a vivir a Dubái?",
         p("Si trasladas tu residencia fiscal a Emiratos, dejas de tributar en España por tu renta mundial. No basta con tener la Golden Visa: Hacienda mira dónde vives realmente, dónde está tu familia y dónde están tus intereses económicos.",
           "Además, cambiar de residencia tiene sus propias reglas y su papeleo. Si es tu plan, prepáralo con tiempo y con un asesor.")),
        ("consejos", "Mis consejos prácticos",
         ul("Guarda todos los justificantes: contrato, pagos al promotor, recibos del DLD y facturas de gastos. Te servirán para la declaración y para calcular la plusvalía al vender.",
            "Lleva el alquiler por una cuenta separada: facilita mucho el IRPF.",
            "Antes de comprar, decide si lo haces a tu nombre, a medias con tu pareja o con una empresa. Cambia la fiscalidad.",
            "Habla con tu asesor fiscal <strong>antes</strong> de firmar, no en mayo cuando toca la renta.")),
    ],
    [
        ("¿Pago impuestos en Dubái por alquilar mi piso?", "Como particular, en general no: Emiratos no tiene impuesto sobre la renta para personas físicas. Si eres residente en España, sí lo declaras en tu IRPF."),
        ("¿Tengo que presentar el modelo 720 por un piso en Dubái?", "Sí, si tus inmuebles en el extranjero superan en total los 50.000 € y eres residente fiscal en España."),
        ("¿Hay impuesto por vender un piso en Dubái?", "En Emiratos no, para un particular. En España, si eres residente, la ganancia tributa en la base del ahorro del IRPF."),
    ],
    [("cuanto-cuesta-comprar-piso-dubai", "Cuánto cuesta comprar un piso en Dubái"), ("golden-visa-dubai-inversion-inmobiliaria", "Golden Visa de Dubái por inversión inmobiliaria")],
)

# ---------------------------------------------------------------- 3
pages["golden-visa-dubai-inversion-inmobiliaria"] = article(
    "golden-visa-dubai-inversion-inmobiliaria",
    "Golden Visa de Dubái por inversión inmobiliaria: requisitos",
    "Golden Visa de Dubái por inversión inmobiliaria: <em>requisitos</em>",
    "Requisitos para conseguir la Golden Visa de 10 años en Dubái comprando una propiedad: inversión mínima de 2 millones de AED, obra nueva, hipoteca, familia y pasos del trámite.",
    "La Golden Visa te da 10 años de residencia en Emiratos, renovables, para ti y tu familia. Y se puede conseguir comprando una propiedad. Te explico los requisitos, qué propiedades valen y cómo es el proceso.",
    "/assets/img/pascual-dubai.webp", "Pascual Vidal en Dubái",
    [
        ("que-es", "Qué es la Golden Visa",
         p("Es un visado de residencia de <strong>10 años</strong>, renovable, que no depende de un empleador. Te permite vivir, trabajar o emprender en Emiratos, abrir cuentas bancarias con facilidad y patrocinar a tu familia.",
           "A diferencia de otros visados, <strong>no te obliga a vivir en Emiratos</strong>: no se cancela por pasar largas temporadas fuera.")),
        ("requisitos", "Requisitos por inversión inmobiliaria",
         ul("<strong>Inversión mínima de 2 millones de AED</strong> (unos 500.000 €, según el cambio) en una o varias propiedades.",
            "Vale también la <strong>obra nueva</strong> de promotores aprobados, siempre que la inversión cumpla el mínimo.",
            "Puedes comprar <strong>con hipoteca</strong>, con condiciones: el banco tiene que emitir la documentación necesaria y cuenta lo que realmente tienes pagado.",
            "Si compras a medias, por ejemplo con tu pareja, hay reglas sobre cómo se reparte el mínimo entre los propietarios.",
            "Pasaporte en vigor, seguro médico, revisión médica y registro biométrico para el Emirates ID.") +
         note("Si tu inversión no llega a 2 millones de AED, existe un <strong>visado de inversor de 2 años</strong> con un mínimo más bajo. Es una opción intermedia que mucha gente no conoce.")),
        ("familia", "Tu familia también",
         p("Con la Golden Visa puedes patrocinar a tu <strong>cónyuge</strong>, a tus <strong>hijos</strong> y, en muchos casos, a tus <strong>padres</strong>, con la misma duración de visado. Es uno de los motivos por los que tantas familias españolas la eligen.")),
        ("pasos", "Pasos del trámite",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "Elegir una propiedad que cumpla los requisitos. Revisamos contigo el valor y el promotor.",
             "Comprar y registrar la propiedad en el Dubai Land Department (escritura u Oqood en obra nueva).",
             "Solicitar la Golden Visa por los canales oficiales con la documentación de la propiedad.",
             "Hacer la revisión médica y el registro biométrico en Dubái.",
             "Recibir el visado y el Emirates ID. Después, añadir a la familia.",
         ]) + "</ol>\n" +
         p("Los plazos y costes del trámite cambian con frecuencia. Te los confirmo actualizados en el momento de comprar.")),
        ("merece-la-pena", "¿Merece la pena?",
         p("Si tu plan es invertir alrededor de medio millón de euros, la Golden Visa es un <strong>extra muy valioso</strong>: residencia a largo plazo, facilidad bancaria y la opción de mudarte cuando quieras, sin obligación de hacerlo.",
           "Ahora bien, compra la propiedad por su rentabilidad y su potencial, no solo por el visado. La Golden Visa es la guinda, no el pastel.")),
    ],
    [
        ("¿Cuánto hay que invertir para la Golden Visa en Dubái?", "Un mínimo de 2 millones de AED en propiedad, que equivale aproximadamente a medio millón de euros según el tipo de cambio."),
        ("¿Vale una propiedad sobre plano para la Golden Visa?", "Sí, en muchos casos, si es de un promotor aprobado y la inversión alcanza el mínimo exigido."),
        ("¿Tengo que vivir en Dubái para mantener la Golden Visa?", "No. A diferencia de otros visados, la Golden Visa no se cancela por pasar largas temporadas fuera de Emiratos."),
    ],
    [("cuanto-cuesta-comprar-piso-dubai", "Cuánto cuesta comprar un piso en Dubái"), ("impuestos-invertir-dubai-espanol", "Impuestos al invertir en Dubái siendo español")],
)

# ---------------------------------------------------------------- países (noviembre 2026)
D2, D2_TXT = "2026-11-13", "13 de noviembre de 2026"
FX_NOTE = "Cifras aproximadas: el dírham (AED) va ligado al dólar (1 USD = 3,6725 AED), así que lo que cambia es tu moneda frente al dólar. Revisa el tipo de cambio del día."

pages["mexico"] = article(
    "invertir-en-dubai-desde-mexico",
    "Invertir en Dubái desde México: guía práctica",
    "Invertir en Dubái <em>desde México</em>",
    "Cómo comprar un piso en Dubái siendo mexicano: precios en pesos, cómo enviar el dinero, qué declarar ante el SAT y cómo hacerlo todo sin viajar.",
    "Cada vez más mexicanos compran en Dubái para cobrar rentas en una moneda ligada al dólar. Te explico cuánto cuesta en pesos, cómo se envía el dinero, qué declaras en México y cómo se compra a distancia.",
    "/assets/img/blog-mexico-emiratos.webp", "Bandera de México junto a la bandera de Emiratos Árabes Unidos",
    [
        ("por-que", "Por qué Dubái atrae a inversores mexicanos",
         ul("<strong>Rentas en una moneda estable:</strong> el dírham va ligado al dólar, así que tus ingresos no dependen del peso.",
            "<strong>Compra 100 % a tu nombre:</strong> los extranjeros pueden comprar en plena propiedad (<em>freehold</em>) en las zonas habilitadas, con registro oficial en el Dubai Land Department.",
            "<strong>Obra nueva con planes de pago:</strong> reservas con un 10–20 % y pagas el resto por fases.",
            "<strong>Seguridad jurídica:</strong> en obra nueva tus pagos van a una cuenta <em>escrow</em> supervisada por el gobierno.")),
        ("precios", "Cuánto cuesta en pesos",
         p(FX_NOTE + " Con un dólar entre 18 y 20 pesos, un dírham ronda los <strong>5 pesos</strong>.") +
         table(["Propiedad (ejemplo)", "En dírhams", "En pesos (aprox.)"], [
             ["Estudio en zona en crecimiento", "650.000 AED", "≈ 3,3 millones MXN"],
             ["Apartamento de 1 dormitorio", "1.000.000 AED", "≈ 5 millones MXN"],
             ["Apartamento de 2 dormitorios", "1.800.000 AED", "≈ 9 millones MXN"],
             ["Mínimo para la Golden Visa", "2.000.000 AED", "≈ 10 millones MXN"],
         ]) +
         p("Súmale alrededor de un 4–5 % de gastos de compra en obra nueva. Te lo detallo en <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">cuánto cuesta comprar un piso en Dubái</a>.")),
        ("dinero", "Cómo enviar el dinero desde México",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "<strong>Transferencia internacional (SWIFT)</strong> desde tu banco en México a la cuenta <em>escrow</em> del proyecto o a la del promotor. Pregunta la comisión fija y, sobre todo, el tipo de cambio que te aplican: ahí está el coste real.",
             "<strong>Plataformas como Wise o Revolut:</strong> suelen dar mejor tipo de cambio. Comprueba el límite por envío y que el destinatario acepta pagos desde ellas.",
             "<strong>Envía en dólares si puedes:</strong> como el dírham está ligado al dólar, convertir pesos a dólares y enviar dólares suele ser lo más sencillo.",
             "<strong>Justifica el origen de los fondos:</strong> el promotor y el banco te pedirán documentos que demuestren de dónde sale el dinero, por las normas contra el blanqueo. Tenlos listos.",
         ]) + "</ol>\n"),
        ("impuestos", "Impuestos en México",
         p("Si eres <strong>residente fiscal en México</strong>, tributas por tus ingresos de cualquier país, también por tu piso en Dubái:") +
         ul("<strong>Rentas del alquiler:</strong> se declaran en México en tu declaración anual.",
            "<strong>Al vender:</strong> la ganancia se declara en México como enajenación de inmuebles.",
            "<strong>En Emiratos:</strong> como particular no pagas impuesto sobre la renta ni sobre plusvalías, solo el 4 % del registro al comprar.",
            "<strong>Si compras con una empresa en Emiratos:</strong> ojo con el régimen de REFIPRE (regímenes fiscales preferentes) y sus declaraciones informativas.") +
         p("México y Emiratos firmaron un convenio para evitar la doble imposición. Cómo se aplica depende de tu caso: consúltalo con tu contador <strong>antes</strong> de comprar.")),
        ("distancia", "Comprar sin viajar",
         p("Todo el proceso se puede hacer en remoto: elección de la propiedad, reserva, firma electrónica del contrato y pagos. Yo vivo en Dubái todo el año y me ocupo de lo que requiere estar presente, incluida la entrega de llaves. Si quieres venir a verlo, consulta los requisitos de entrada vigentes para tu pasaporte.")),
        ("golden-visa", "Golden Visa para mexicanos",
         p("Con una inversión de 2 millones de AED (unos 10 millones de pesos) puedes pedir la residencia de 10 años para ti y tu familia, sin obligación de vivir en Emiratos. Todos los requisitos, en la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">guía de la Golden Visa</a>.")),
    ],
    [
        ("¿Un mexicano puede comprar una propiedad en Dubái?", "Sí. Los extranjeros pueden comprar en plena propiedad en las zonas habilitadas, sin necesidad de residir en Emiratos ni de tener visado."),
        ("¿Tengo que declarar al SAT un piso en Dubái?", "Si eres residente fiscal en México, sí debes declarar las rentas y, al vender, la ganancia. Consulta con tu contador cómo hacerlo en tu caso."),
        ("¿Cuál es la forma más barata de mandar dinero de México a Dubái?", "Depende del importe. Compara la comisión y, sobre todo, el tipo de cambio de tu banco con plataformas como Wise o Revolut; enviar en dólares suele simplificarlo."),
    ],
    [("invertir-en-dubai-desde-colombia", "Invertir en Dubái desde Colombia"), ("invertir-en-dubai-desde-espana", "Invertir en Dubái desde España")],
    date=D2, date_txt=D2_TXT, wa_msg="Hola Pascual, te escribo desde México. Quiero información para invertir en Dubái.",
)

pages["colombia"] = article(
    "invertir-en-dubai-desde-colombia",
    "Invertir en Dubái desde Colombia: guía práctica",
    "Invertir en Dubái <em>desde Colombia</em>",
    "Cómo comprar un piso en Dubái siendo colombiano: precios en pesos colombianos, cómo enviar el dinero por el mercado cambiario, qué declarar ante la DIAN y cómo comprar a distancia.",
    "Para un inversor colombiano, Dubái es una forma de tener patrimonio en una moneda ligada al dólar, con rentas de alquiler y sin impuesto sobre la renta en Emiratos. Te explico precios, envío del dinero e impuestos en Colombia.",
    "/assets/img/blog-colombia-emiratos.webp", "Bandera de Colombia junto a la bandera de Emiratos Árabes Unidos",
    [
        ("por-que", "Por qué Dubái atrae a inversores colombianos",
         ul("<strong>Patrimonio en dólares:</strong> el dírham va ligado al dólar y protege tu inversión de la devaluación del peso.",
            "<strong>Rentas de alquiler:</strong> demanda alta de alquiler anual y vacacional.",
            "<strong>Planes de pago en obra nueva:</strong> reservas con un 10–20 % y pagas el resto durante la construcción.",
            "<strong>Compra segura y registrada:</strong> cada compra queda inscrita en el Dubai Land Department.")),
        ("precios", "Cuánto cuesta en pesos colombianos",
         p(FX_NOTE + " Con un dólar entre 3.900 y 4.300 pesos, un dírham ronda los <strong>1.100 pesos</strong>.") +
         table(["Propiedad (ejemplo)", "En dírhams", "En pesos colombianos (aprox.)"], [
             ["Estudio en zona en crecimiento", "650.000 AED", "≈ 715 millones COP"],
             ["Apartamento de 1 habitación", "1.000.000 AED", "≈ 1.100 millones COP"],
             ["Apartamento de 2 habitaciones", "1.800.000 AED", "≈ 2.000 millones COP"],
             ["Mínimo para la Golden Visa", "2.000.000 AED", "≈ 2.200 millones COP"],
         ]) +
         p("En obra nueva no pagas todo de golpe: con la entrada del 10–20 % empiezas, y el resto va por plazos. Gastos de compra: <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">aquí, uno por uno</a>.")),
        ("dinero", "Cómo enviar el dinero desde Colombia",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "<strong>Por el mercado cambiario:</strong> una inversión en el exterior se canaliza a través de tu banco (intermediario del mercado cambiario) con la declaración de cambio que corresponda. Tu banco te indica el formulario.",
             "<strong>Transferencia en dólares</strong> a la cuenta <em>escrow</em> del proyecto o del promotor. Pregunta la comisión y el tipo de cambio que te aplican.",
             "<strong>Documenta el origen de los fondos:</strong> en Dubái te lo pedirán por las normas contra el blanqueo, y en Colombia te conviene tenerlo todo en orden.",
             "<strong>Guarda cada comprobante:</strong> los necesitarás para la declaración de renta y la de activos en el exterior.",
         ]) + "</ol>\n"),
        ("impuestos", "Impuestos en Colombia",
         p("Si eres <strong>residente fiscal en Colombia</strong>, declaras tus rentas y tu patrimonio de cualquier país:") +
         ul("<strong>Declaración de renta:</strong> incluye las rentas del alquiler en Dubái y, al vender, la ganancia ocasional.",
            "<strong>Declaración de activos en el exterior:</strong> si tus activos fuera superan el límite que fija la DIAN cada año, tienes que presentarla.",
            "<strong>Impuesto al patrimonio:</strong> si tu patrimonio total supera el umbral, el piso cuenta.",
            "<strong>En Emiratos:</strong> como particular no pagas impuesto sobre la renta ni sobre plusvalías; solo el 4 % del registro al comprar.") +
         p("Colombia y Emiratos firmaron un convenio para evitar la doble imposición. Habla con tu contador <strong>antes</strong> de comprar para hacerlo bien desde el principio.")),
        ("distancia", "Comprar sin viajar",
         p("La reserva, el contrato y los pagos se hacen a distancia. Yo estoy en Dubái todo el año y me encargo de lo presencial: revisión de la vivienda, entrega de llaves, amueblado y alquiler. Si quieres venir, consulta antes los requisitos de entrada vigentes para tu pasaporte.")),
        ("golden-visa", "Golden Visa para colombianos",
         p("Invirtiendo 2 millones de AED en propiedad puedes solicitar la residencia de 10 años para ti y tu familia. Requisitos y pasos en la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">guía de la Golden Visa</a>.")),
    ],
    [
        ("¿Un colombiano puede comprar vivienda en Dubái?", "Sí. Los extranjeros pueden comprar en plena propiedad en las zonas habilitadas, sin residir en Emiratos."),
        ("¿Tengo que declarar en Colombia un piso en Dubái?", "Si eres residente fiscal en Colombia, sí: en la declaración de renta y, si superas el límite, en la de activos en el exterior. Confírmalo con tu contador."),
        ("¿Cómo envío el dinero desde Colombia?", "A través de tu banco, como operación del mercado cambiario con su declaración de cambio, normalmente en dólares a la cuenta escrow del proyecto."),
    ],
    [("invertir-en-dubai-desde-mexico", "Invertir en Dubái desde México"), ("invertir-en-dubai-desde-miami", "Invertir en Dubái desde Miami")],
    date=D2, date_txt=D2_TXT, wa_msg="Hola Pascual, te escribo desde Colombia. Quiero información para invertir en Dubái.",
)

pages["miami"] = article(
    "invertir-en-dubai-desde-miami",
    "Invertir en Dubái desde Miami y EE. UU.: guía para hispanos",
    "Invertir en Dubái <em>desde Miami</em>",
    "Guía para hispanos en Miami y Estados Unidos que quieren comprar en Dubái: sin riesgo de cambio con el dólar, cómo pagar, qué declarar al IRS y cómo comprar a distancia.",
    "Si vives en Miami o en cualquier parte de EE. UU., Dubái tiene una ventaja que pocos destinos ofrecen: el dírham va ligado al dólar. Te explico cómo se paga, qué declaras al IRS y por qué tantos inversores latinos de Florida lo están mirando.",
    "/assets/img/blog-eeuu-emiratos.webp", "Bandera de Estados Unidos junto a la bandera de Emiratos Árabes Unidos",
    [
        ("por-que", "Por qué Dubái encaja con un inversor de Miami",
         ul("<strong>Sin riesgo de cambio:</strong> 1 USD = 3,6725 AED, fijo desde hace décadas. Compras, cobras y vendes prácticamente en dólares.",
            "<strong>Sin impuesto sobre la renta en Emiratos</strong> para particulares, ni impuesto anual sobre la propiedad.",
            "<strong>Diversificación:</strong> un mercado con dinámica distinta a la de Florida, con fuerte demanda de alquiler.",
            "<strong>Compra a distancia</strong> y gestión completa desde Dubái, en español.")),
        ("precios", "Cuánto cuesta en dólares",
         table(["Propiedad (ejemplo)", "En dírhams", "En dólares"], [
             ["Estudio en zona en crecimiento", "650.000 AED", "≈ 177.000 USD"],
             ["Apartamento de 1 dormitorio", "1.000.000 AED", "≈ 272.000 USD"],
             ["Apartamento de 2 dormitorios", "1.800.000 AED", "≈ 490.000 USD"],
             ["Mínimo para la Golden Visa", "2.000.000 AED", "≈ 545.000 USD"],
         ]) +
         p("Como el cambio es fijo, estos importes apenas varían. Suma alrededor de un 4–5 % de gastos de compra en obra nueva: <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">el desglose completo</a>.")),
        ("pagos", "Cómo se paga desde EE. UU.",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "<strong>Wire transfer en dólares</strong> desde tu banco en EE. UU. a la cuenta <em>escrow</em> del proyecto o a la del promotor. Sin conversión de moneda que te haga perder.",
             "<strong>Planes de pago del promotor:</strong> los bancos de EE. UU. no suelen financiar propiedades en el extranjero, así que la obra nueva con pagos por fases es lo más habitual.",
             "<strong>Origen de los fondos:</strong> ten a mano extractos y documentos que lo justifiquen; te los pedirán.",
         ]) + "</ol>\n"),
        ("impuestos", "Impuestos en EE. UU.",
         p("Si eres ciudadano, residente permanente (green card) o residente fiscal en EE. UU., el IRS grava tus ingresos de cualquier país:") +
         ul("<strong>Rentas del alquiler:</strong> se declaran en tu declaración federal, con sus gastos y la amortización que corresponda a una propiedad en el extranjero.",
            "<strong>Al vender:</strong> la ganancia tributa en EE. UU.",
            "<strong>Cuentas en Emiratos:</strong> si abres una cuenta bancaria allí y el saldo total de tus cuentas en el extranjero supera 10.000 USD, tienes que presentar el FBAR. Según tus activos, también puede aplicar el formulario 8938.",
            "<strong>Florida</strong> no tiene impuesto estatal sobre la renta.",
            "<strong>Sin convenio de doble imposición</strong> entre EE. UU. y Emiratos; como Emiratos no grava al particular, en la práctica tributas en EE. UU.") +
         p("Revísalo con tu CPA o asesor fiscal <strong>antes</strong> de comprar, sobre todo si vas a comprar a través de una LLC.")),
        ("distancia", "Comprar sin viajar",
         p("Reserva, contrato, pagos y registro se hacen en remoto. Yo estoy en Dubái todo el año y me ocupo de la entrega, la revisión de desperfectos, el amueblado y el alquiler. Hay vuelos directos desde Miami a Dubái si quieres venir a verlo.")),
        ("golden-visa", "Golden Visa",
         p("Con 2 millones de AED (unos 545.000 USD) en propiedad puedes pedir la residencia de 10 años para ti y tu familia, compatible con seguir viviendo en Miami. Requisitos en la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">guía de la Golden Visa</a>.")),
    ],
    [
        ("¿Hay riesgo de cambio al invertir en Dubái desde EE. UU.?", "Muy poco: el dírham está ligado al dólar a 3,6725 AED por dólar desde hace décadas."),
        ("¿Tengo que declarar al IRS un piso en Dubái?", "Sí, si eres ciudadano o residente fiscal en EE. UU.: las rentas y la ganancia al vender. Si tienes cuentas en Emiratos, revisa también el FBAR."),
        ("¿Puedo financiar la compra con un banco de EE. UU.?", "Normalmente no para una propiedad en el extranjero. Lo habitual es usar el plan de pagos del promotor en obra nueva."),
    ],
    [("invertir-en-dubai-desde-mexico", "Invertir en Dubái desde México"), ("impuestos-invertir-dubai-espanol", "Impuestos al invertir en Dubái siendo español")],
    date=D2, date_txt=D2_TXT, wa_msg="Hola Pascual, te escribo desde Miami / EE. UU. Quiero información para invertir en Dubái.",
)

pages["espana"] = article(
    "invertir-en-dubai-desde-espana",
    "Invertir en Dubái desde España: guía práctica",
    "Invertir en Dubái <em>desde España</em>",
    "Cómo comprar un piso en Dubái siendo español: precios en euros, cómo enviar el dinero desde tu banco, financiación, qué declarar a Hacienda y cómo comprar sin viajar.",
    "España es de donde más me escriben para invertir en Dubái. Te explico cuánto cuesta en euros, cómo mandar el dinero, si puedes financiarlo, qué declaras a Hacienda y cómo se compra a 6.000 kilómetros sin perder el control.",
    "/assets/img/blog-espana-emiratos.webp", "Bandera de España junto a la bandera de Emiratos Árabes Unidos",
    [
        ("por-que", "Por qué Dubái atrae a inversores españoles",
         ul("<strong>Rentas de alquiler</strong> con una demanda que sigue creciendo, tanto anual como vacacional.",
            "<strong>Sin IBI ni impuesto sobre la renta</strong> en Emiratos para particulares.",
            "<strong>Planes de pago en obra nueva:</strong> reservas con un 10–20 % y pagas el resto durante la construcción.",
            "<strong>Diversificar fuera del euro:</strong> el dírham va ligado al dólar.",
            "<strong>Compra segura:</strong> registro oficial en el Dubai Land Department y cuentas <em>escrow</em> en obra nueva.")),
        ("precios", "Cuánto cuesta en euros",
         p(FX_NOTE + " Con un euro entre 1,05 y 1,15 dólares, un dírham ronda los <strong>0,24 €</strong>.") +
         table(["Propiedad (ejemplo)", "En dírhams", "En euros (aprox.)"], [
             ["Estudio en zona en crecimiento", "650.000 AED", "≈ 155.000 €"],
             ["Apartamento de 1 dormitorio", "1.000.000 AED", "≈ 240.000 €"],
             ["Apartamento de 2 dormitorios", "1.800.000 AED", "≈ 430.000 €"],
             ["Mínimo para la Golden Visa", "2.000.000 AED", "≈ 480.000 €"],
         ]) +
         p("A eso súmale los gastos de compra, que te detallo uno por uno en <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">cuánto cuesta comprar un piso en Dubái</a>.")),
        ("dinero", "Cómo enviar el dinero desde España",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "<strong>Transferencia internacional (SWIFT)</strong> desde tu banco a la cuenta <em>escrow</em> del proyecto o a la del promotor. Fíjate en la comisión y, sobre todo, en el tipo de cambio euro–dírham que te aplican.",
             "<strong>Wise o Revolut</strong> suelen dar mejor cambio en importes medianos. Comprueba los límites por envío y que el destinatario acepta el pago.",
             "<strong>Justifica el origen de los fondos:</strong> nómina, venta de un inmueble, ahorros… Te lo pedirán en Dubái y tu banco español también puede preguntarlo.",
             "<strong>Guarda todos los justificantes:</strong> los necesitarás para la renta, el modelo 720 y para calcular la ganancia cuando vendas.",
         ]) + "</ol>\n"),
        ("financiacion", "¿Puedo financiarlo?",
         p("Los bancos españoles no suelen financiar una vivienda en el extranjero. Las opciones reales son el <strong>plan de pagos del promotor</strong> en obra nueva o una <strong>hipoteca de un banco de Emiratos</strong>: algunos financian a no residentes, normalmente hasta el 50–60 % del valor y con más requisitos que a un residente.")),
        ("impuestos", "Qué declaras a Hacienda",
         p("Si sigues siendo residente fiscal en España, el piso de Dubái cuenta en tu IRPF, en el modelo 720 si superas los 50.000 € en el extranjero y, según tu caso, en Patrimonio. Lo tienes explicado paso a paso en <a href=\"/blog/impuestos-invertir-dubai-espanol/\">impuestos al invertir en Dubái siendo español</a>.")),
        ("distancia", "Comprar sin viajar",
         p("Todo se puede hacer desde España: elección, reserva, firma electrónica y pagos. Yo vivo en Dubái todo el año y me encargo de lo presencial: revisión de la vivienda, entrega de llaves, amueblado y alquiler. Hay vuelos directos desde Madrid y Barcelona, y la diferencia horaria es de solo 2–3 horas. Los españoles no necesitan visado previo para entrar en Emiratos como turistas.")),
        ("golden-visa", "Golden Visa para españoles",
         p("Con 2 millones de AED (unos 480.000 €) en propiedad puedes pedir la residencia de 10 años para ti y tu familia, sin obligación de vivir allí. Requisitos y pasos en la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">guía de la Golden Visa</a>.")),
    ],
    [
        ("¿Un español puede comprar un piso en Dubái?", "Sí. Los extranjeros pueden comprar en plena propiedad (freehold) en las zonas habilitadas, sin residir en Emiratos ni tener visado."),
        ("¿Cuánto dinero necesito para empezar?", "En obra nueva puedes empezar con la entrada del 10–20 % del precio. Un estudio en zona en crecimiento ronda los 155.000 €, así que la entrada parte de unos 15.000–30.000 € más gastos."),
        ("¿Un banco español me da hipoteca para Dubái?", "Normalmente no. Lo habitual es el plan de pagos del promotor o una hipoteca de un banco de Emiratos, que financia a no residentes hasta el 50–60 %."),
    ],
    [("impuestos-invertir-dubai-espanol", "Impuestos al invertir en Dubái siendo español"), ("invertir-en-dubai-desde-mexico", "Invertir en Dubái desde México")],
    date=D2, date_txt=D2_TXT, wa_msg="Hola Pascual, te escribo desde España. Quiero información para invertir en Dubái.",
)


# ---------------------------------------------------------------- tanda 3 (15 nov 2026): rentabilidad, sobre plano, zonas, RAK, Argentina
D3, D3_TXT = "2026-11-15", "15 de noviembre de 2026"

SUMMARIES.update({
    "rentabilidad-alquiler-dubai": [
        "La rentabilidad <strong>bruta</strong> media del alquiler residencial en Dubái ronda el <strong>6,5–7 %</strong>; los apartamentos rinden más que las villas.",
        "Las cifras de «hasta un 20 %» no son la media del mercado: suelen sumar revalorización de obra nueva o contar solo ingresos brutos de alquiler vacacional.",
        "La rentabilidad <strong>neta</strong> realista, tras comunidad, gestión y meses vacíos, suele quedar entre <strong>1 y 2,5 puntos</strong> por debajo de la bruta.",
        "Los estudios y apartamentos de 1 dormitorio en zonas de precio medio son los que mejor rentabilidad dan en porcentaje.",
    ],
    "comprar-sobre-plano-dubai": [
        "Comprar sobre plano (<em>off-plan</em>) es comprar una vivienda en construcción: reservas con un <strong>10–20 %</strong> y pagas el resto por fases.",
        "Tus pagos van a una <strong>cuenta escrow</strong> del proyecto, regulada por ley, y la compra se registra en el Dubai Land Department (Oqood).",
        "El 4 % del DLD se paga al principio; en obra nueva normalmente no pagas comisión de agencia.",
        "Los riesgos reales son el retraso en la entrega, un promotor débil y tener que vender antes de terminar de pagar: se reducen eligiendo bien promotor, proyecto y plan de pagos.",
    ],
    "mejores-zonas-invertir-dubai": [
        "No hay una «mejor zona»: depende de si buscas <strong>rentabilidad por alquiler</strong>, <strong>revalorización</strong> o un piso para uso propio.",
        "Para rentabilidad, zonas de precio medio como <strong>JVC</strong> o Dubai Sports City superan el 8 % bruto; las zonas prime como Downtown rondan el 5 %.",
        "Business Bay y Dubai Marina equilibran alquiler, liquidez y demanda internacional.",
        "Dubai South / Expo City y Dubai Islands son apuestas de crecimiento a medio plazo ligadas a grandes infraestructuras.",
    ],
    "invertir-ras-al-khaimah-al-marjan": [
        "Ras Al Khaimah está a unos <strong>50 minutos</strong> del aeropuerto de Dubái y permite a extranjeros comprar en plena propiedad en zonas como <strong>Al Marjan Island</strong>.",
        "El gran motor es <strong>Wynn Al Marjan Island</strong>, el primer resort integrado con casino de Emiratos, con apertura prevista en <strong>septiembre de 2027</strong>.",
        "Los precios de entrada son más bajos que en las zonas prime de Dubái, con planes de pago en obra nueva.",
        "Es una inversión más especulativa que Dubái: depende de que el turismo crezca como se espera; conviene elegir bien promotor y ubicación.",
    ],
    "invertir-en-dubai-desde-argentina": [
        "Un argentino puede comprar en plena propiedad en Dubái sin residir allí, y todo el proceso se puede hacer a distancia.",
        "El dírham va ligado al dólar: tu inversión y tus rentas quedan en una moneda dura.",
        "Si eres residente fiscal en Argentina, declaras las rentas en <strong>Ganancias</strong> y el inmueble en <strong>Bienes Personales</strong>.",
        "Las normas cambiarias argentinas cambian a menudo: confirma con tu banco cómo comprar y transferir dólares al exterior antes de reservar.",
    ],
})

pages["rentabilidad"] = article(
    "rentabilidad-alquiler-dubai",
    "Rentabilidad del alquiler en Dubái en 2026: cifras reales",
    "Rentabilidad del alquiler en Dubái: <em>cifras reales</em>",
    "Cuánto rinde de verdad un piso en Dubái: rentabilidad bruta y neta por tipo de vivienda y zona, alquiler anual frente a vacacional y por qué desconfiar del «hasta 20 %».",
    "Seguro que has visto anuncios de «rentabilidades de hasta el 20 %» en Dubái. Te explico qué cifras da hoy el mercado, cómo pasar de rentabilidad bruta a neta y qué tipo de propiedad rinde más.",
    "/assets/img/video-airbnb.webp", "Apartamento amueblado en Dubái preparado para alquiler vacacional",
    [
        ("media", "Cuánto rinde un piso en Dubái hoy",
         p("Según datos de Property Monitor publicados por Engel &amp; Völkers, en noviembre de 2026 la rentabilidad bruta media del residencial en Dubái era del <strong>6,66 %</strong>: <strong>6,96 %</strong> en apartamentos, 5,20 % en adosados y 4,67 % en villas. Es muy superior a la de ciudades como Madrid, Londres o Nueva York, donde lo normal es moverse entre el 2 % y el 4 %.") +
         table(["Tipo de propiedad", "Rentabilidad bruta media (nov. 2026)"], [
             ["Apartamentos", "≈ 7,0 %"],
             ["Adosados (townhouses)", "≈ 5,2 %"],
             ["Villas", "≈ 4,7 %"],
             ["Media residencial", "≈ 6,7 %"],
         ]) +
         p("Los apartamentos rinden más porque su precio de compra es más bajo en proporción al alquiler que cobran. Los estudios y los de 1 dormitorio suelen dar los mejores porcentajes.")),
        ("veinte", "¿Y lo del «hasta un 20 %»?",
         p("Esa cifra no es la rentabilidad del alquiler. Cuando ves un 15–20 % suele ser una de estas tres cosas:") +
         ul("<strong>Revalorización de obra nueva:</strong> lo que ha subido el precio entre que reservaste y la entrega. Es real en un mercado alcista, pero no está garantizado y no es un ingreso anual.",
            "<strong>Rentabilidad sobre lo pagado, no sobre el precio:</strong> si solo has pagado el 20 % y el piso se revaloriza un 4 %, sobre tu dinero eso es un 20 %. El riesgo crece en la misma proporción.",
            "<strong>Ingresos brutos de alquiler vacacional</strong> en temporada alta, sin restar gestión, limpieza, suministros ni las semanas vacías.") +
         note("Mi regla: si alguien te promete una rentabilidad, pídele que te la desglose en <strong>alquiler neto</strong> y <strong>revalorización estimada</strong> por separado. Si no puede, no es una cifra, es publicidad.")),
        ("neta", "De rentabilidad bruta a neta",
         p("La rentabilidad bruta es el alquiler anual dividido entre el precio. Para saber lo que de verdad te queda hay que restar:") +
         ul("<strong>Cuota de comunidad</strong> (<em>service charge</em>): se paga por pie cuadrado y varía mucho de un edificio a otro.",
            "<strong>Gestión:</strong> en alquiler anual, una comisión moderada; en vacacional, la empresa gestora se queda un porcentaje de los ingresos.",
            "<strong>Meses vacíos</strong> entre inquilinos o semanas sin reservas.",
            "<strong>Mantenimiento</strong> y, en vacacional, limpieza, suministros, internet y la licencia de <em>holiday home</em>.",
            "<strong>Los gastos de compra</strong> (sobre todo el 4 % del DLD) si quieres calcular la rentabilidad sobre lo que de verdad has invertido.") +
         p("En la práctica, la neta suele quedar entre 1 y 2,5 puntos por debajo de la bruta. Un apartamento con un 7 % bruto puede dejarte un 5 % neto, que sigue siendo muy buena cifra en un activo en moneda ligada al dólar. Te explico todos los gastos en <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">cuánto cuesta comprar un piso en Dubái</a>.")),
        ("anual-vacacional", "Alquiler anual o vacacional",
         table(["", "Alquiler anual", "Alquiler vacacional"], [
             ["Ingresos", "Estables, normalmente cobrados en 1 a 4 cheques al año", "Más altos en bruto, variables según temporada"],
             ["Gastos", "Bajos", "Gestión, limpieza, suministros y amueblado"],
             ["Trabajo", "Mínimo", "Alto, salvo que lo delegues en una gestora"],
             ["Requisitos", "Contrato registrado en Ejari", "Licencia de holiday home del Departamento de Turismo"],
         ]) +
         p("El vacacional suele rendir más en zonas turísticas (Marina, Downtown, Palm, Business Bay), pero solo si el piso está bien amueblado y bien gestionado. En zonas residenciales el anual suele ganar en neto y en tranquilidad.")),
        ("que-rinde", "Qué propiedad rinde más",
         ul("<strong>Tamaño:</strong> estudios y 1 dormitorio, mejor porcentaje; 2–3 dormitorios, inquilinos más estables (familias).",
            "<strong>Zona:</strong> las zonas de precio medio dan más rentabilidad; las prime, más liquidez y revalorización. Lo comparo zona por zona en <a href=\"/blog/mejores-zonas-invertir-dubai/\">las mejores zonas para invertir en Dubái</a>.",
            "<strong>Edificio:</strong> una comunidad cara se come la rentabilidad. Pregunta siempre la cuota por pie cuadrado antes de comprar.",
            "<strong>Obra nueva o segunda mano:</strong> la segunda mano alquila desde el primer día; la obra nueva da mejor precio de entrada y plan de pagos, pero no rinde hasta la entrega.")),
    ],
    [
        ("¿Qué rentabilidad da un piso en Dubái?", "La rentabilidad bruta media del residencial ronda el 6,5–7 % (en torno al 7 % en apartamentos y algo menos del 5 % en villas). La neta suele quedar entre 1 y 2,5 puntos por debajo."),
        ("¿Es real una rentabilidad del 20 % en Dubái?", "No como rentabilidad del alquiler. Esas cifras suelen mezclar la revalorización de la obra nueva, calcular sobre lo pagado y no sobre el precio, o contar ingresos brutos de alquiler vacacional."),
        ("¿Se pagan impuestos por el alquiler en Dubái?", "En Emiratos, un particular no paga impuesto sobre la renta por el alquiler. Si eres residente fiscal en otro país, normalmente tendrás que declararlo allí."),
        ("¿Qué rinde más, alquiler anual o vacacional?", "El vacacional suele dar más ingresos brutos en zonas turísticas, pero con más gastos y gestión. En zonas residenciales, el anual suele ganar en neto."),
    ],
    [("mejores-zonas-invertir-dubai", "Las mejores zonas para invertir en Dubái"), ("cuanto-cuesta-comprar-piso-dubai", "Cuánto cuesta comprar un piso en Dubái")],
    date=D3, date_txt=D3_TXT, wa_msg="Hola Pascual, he leído tu artículo sobre la rentabilidad del alquiler en Dubái. ¿Me haces los números de una propiedad?",
)

pages["sobre-plano"] = article(
    "comprar-sobre-plano-dubai",
    "Comprar sobre plano en Dubái: cómo funciona y qué riesgos tiene",
    "Comprar sobre plano en Dubái: <em>guía completa</em>",
    "Cómo funciona comprar una propiedad sobre plano (off-plan) en Dubái: planes de pago, cuenta escrow, registro Oqood, gastos, riesgos reales y cómo elegir promotor.",
    "La mayoría de mis clientes compran sobre plano: entras con un 10–20 % y pagas el resto mientras se construye. Te explico cómo funciona paso a paso, qué te protege y en qué fijarte para no equivocarte de proyecto.",
    "/assets/img/proyecto-dubai-islands.webp", "Proyecto de obra nueva en Dubai Islands frente al mar",
    [
        ("que-es", "Qué es comprar sobre plano",
         p("Comprar sobre plano (<em>off-plan</em>) es comprar una vivienda que todavía se está construyendo, directamente al promotor. A cambio de esperar a la entrega consigues normalmente <strong>mejor precio de entrada</strong> que en un edificio terminado y un <strong>plan de pagos</strong> repartido en el tiempo, sin necesidad de hipoteca.")),
        ("pasos", "El proceso paso a paso",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "<strong>Selección:</strong> comparamos proyectos según tu presupuesto y objetivo (alquiler, revalorización, Golden Visa, uso propio).",
             "<strong>Reserva:</strong> se bloquea la unidad con un depósito y se firma el formulario de reserva.",
             "<strong>Contrato (SPA):</strong> el contrato de compraventa con el promotor, que fija precio, plan de pagos y fecha estimada de entrega. Se puede firmar en remoto.",
             "<strong>Registro Oqood:</strong> el promotor registra tu compra en el Dubai Land Department. Aquí se paga el 4 % del DLD.",
             "<strong>Pagos por fases</strong> durante la construcción, siempre a la cuenta <em>escrow</em> del proyecto.",
             "<strong>Entrega (handover):</strong> revisión de la vivienda, pago final y título de propiedad. A partir de aquí puedes alquilar o vender.",
         ]) + "</ol>\n"),
        ("planes", "Planes de pago habituales",
         table(["Plan", "Cómo funciona", "Para quién"], [
             ["Durante la obra (ej. 60/40)", "60 % durante la construcción y 40 % a la entrega", "Quien tiene liquidez o hipotecará al final"],
             ["Post-handover (ej. 50/50)", "Parte se paga después de la entrega, a veces en 2–5 años", "Quien quiere pagar con el propio alquiler"],
             ["Mensual o trimestral", "Cuotas pequeñas y constantes", "Quien prefiere repartir el esfuerzo"],
         ]) +
         p("Los porcentajes son ejemplos: cada promotor y proyecto tiene el suyo, y a veces se negocian.")),
        ("proteccion", "Qué te protege como comprador",
         ul("<strong>Cuenta escrow:</strong> tu dinero va a una cuenta del proyecto que el promotor solo puede usar para construir, según el avance de obra.",
            "<strong>Proyecto registrado en RERA</strong> y compra inscrita en el DLD: puedes comprobar promotor y proyecto en los canales oficiales del Dubai Land Department.",
            "<strong>Si un proyecto se cancela</strong>, la normativa prevé la devolución de lo depositado en la cuenta escrow.") +
         note("Antes de reservar, compruebo contigo que el proyecto está registrado, que el número de cuenta escrow coincide con el oficial y que nunca pagas a una cuenta personal ni de un intermediario.")),
        ("costes", "Gastos de comprar sobre plano",
         ul("<strong>4 % del Dubai Land Department</strong>, al registrar la compra.",
            "<strong>Tasa de registro Oqood y trámites</strong> del promotor (unos 1.000 € en total, según proyecto).",
            "<strong>Sin comisión de agencia</strong> en la mayoría de casos: la paga el promotor.",
            "<strong>A la entrega:</strong> conexión de suministros, amueblado si vas a alquilar y la primera cuota de comunidad.") +
         p("En total, calcula alrededor de un 4–5 % sobre el precio. Desglose completo en <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">cuánto cuesta comprar un piso en Dubái</a>.")),
        ("riesgos", "Riesgos reales y cómo reducirlos",
         ul("<strong>Retrasos en la entrega:</strong> son frecuentes. Elige promotores con historial de entregas y revisa qué dice el contrato sobre retrasos.",
            "<strong>Promotor pequeño o nuevo:</strong> no siempre es malo, pero exige revisar más (proyectos entregados, avance real de obra, solvencia).",
            "<strong>Vender antes de la entrega:</strong> muchos promotores solo permiten traspasar el contrato cuando has pagado un porcentaje mínimo, a menudo en torno al 30–40 %, y cobran una tasa.",
            "<strong>Comprar caro:</strong> en zonas con mucha oferta nueva, los alquileres pueden bajar en el momento de la entrega. Compara siempre con precios de segunda mano cercanos.",
            "<strong>Plan de pagos que no puedes cumplir:</strong> si dejas de pagar, puedes perder parte de lo aportado. Asegúrate de que el calendario encaja con tu liquidez.")),
        ("promotor", "Cómo elegir promotor y proyecto",
         p("Miro cuatro cosas: el <strong>historial de entregas</strong> del promotor, la <strong>ubicación</strong> (demanda de alquiler real hoy, no solo en el folleto), el <strong>precio por pie cuadrado</strong> frente a lo terminado en la zona y la <strong>cuota de comunidad</strong> prevista. Si buscas la residencia, revisa también los requisitos de la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">Golden Visa</a>, que se puede conseguir con obra nueva.")),
    ],
    [
        ("¿Es seguro comprar sobre plano en Dubái?", "Es un sistema regulado: el proyecto debe estar registrado, tus pagos van a una cuenta escrow y la compra se inscribe en el Dubai Land Department. El riesgo principal es el retraso o elegir un mal promotor, que se reduce revisando bien antes de reservar."),
        ("¿Cuánto necesito para comprar sobre plano?", "Normalmente una entrada del 10–20 % del precio más el 4 % del DLD y las tasas de registro. El resto se paga por fases."),
        ("¿Puedo vender antes de que entreguen el piso?", "Sí, traspasando el contrato, pero muchos promotores exigen haber pagado un porcentaje mínimo (a menudo en torno al 30–40 %) y cobran una tasa por el traspaso."),
        ("¿Puedo comprar sobre plano sin viajar?", "Sí. Reserva, contrato y pagos se hacen en remoto. Yo me encargo de lo presencial, incluida la revisión y la entrega de llaves."),
    ],
    [("rentabilidad-alquiler-dubai", "Rentabilidad del alquiler en Dubái"), ("golden-visa-dubai-inversion-inmobiliaria", "Golden Visa de Dubái por inversión")],
    date=D3, date_txt=D3_TXT, wa_msg="Hola Pascual, he leído tu guía sobre comprar sobre plano en Dubái y quiero ver proyectos.",
)

pages["zonas"] = article(
    "mejores-zonas-invertir-dubai",
    "Las mejores zonas para invertir en Dubái en 2026",
    "Las mejores zonas para invertir <em>en Dubái</em>",
    "Qué zonas de Dubái convienen según tu objetivo: rentabilidad por alquiler (JVC, Sports City), equilibrio (Business Bay, Marina), prime (Downtown) y crecimiento (Dubai South, Dubai Islands).",
    "La pregunta que más me hacen es «¿dónde compro?». La respuesta depende de lo que busques: renta mensual, revalorización o un piso para disfrutar. Te comparo las zonas que más recomiendo, con datos de rentabilidad.",
    "/assets/img/pascual-dubai.webp", "Pascual Vidal en Dubái con el skyline de la ciudad al fondo",
    [
        ("objetivo", "Primero, tu objetivo",
         ul("<strong>Rentabilidad por alquiler:</strong> zonas de precio medio, con mucha demanda de inquilinos y precio de entrada bajo.",
            "<strong>Revalorización:</strong> zonas nuevas ligadas a grandes infraestructuras, normalmente comprando sobre plano.",
            "<strong>Seguridad y liquidez:</strong> zonas consolidadas y conocidas internacionalmente, donde es más fácil revender.",
            "<strong>Golden Visa:</strong> llegar a 2 millones de AED con una o varias propiedades.")),
        ("tabla", "Comparativa de zonas",
         table(["Zona", "Perfil", "Rentabilidad bruta aprox. (apartamentos)"], [
             ["Jumeirah Village Circle (JVC)", "Rentabilidad, precio de entrada bajo", "≈ 8–9 %"],
             ["Dubai Sports City", "Rentabilidad", "≈ 8 %"],
             ["Business Bay", "Equilibrio: céntrica, muy demandada", "≈ 6,3 %"],
             ["Dubai Marina", "Turística, alquiler vacacional, liquidez", "≈ 5,9 %"],
             ["Dubai Creek Harbour", "Nueva zona prime (Emaar)", "≈ 5,4 %"],
             ["Downtown Dubai", "Prime, máxima liquidez", "≈ 5,3 %"],
         ]) +
         p("Rentabilidades brutas medias orientativas de 2026 (Property Monitor, vía Engel &amp; Völkers, y REIDIN). Varían según edificio, tamaño y precio de compra.")),
        ("rentabilidad", "Para rentabilidad: JVC y Dubai Sports City",
         p("Son zonas residenciales de precio medio con mucha demanda de profesionales que buscan alquiler asequible. Los estudios y apartamentos de 1 dormitorio dan los mejores porcentajes de la ciudad. La contrapartida: hay mucha oferta nueva, así que importa elegir bien el edificio y no pagar de más.")),
        ("equilibrio", "Equilibrio: Business Bay y Dubai Marina",
         p("<strong>Business Bay</strong>, junto a Downtown, combina demanda de ejecutivos, alquiler vacacional y buena reventa. <strong>Dubai Marina</strong> es la zona más turística junto al mar: ideal para alquiler vacacional bien gestionado y muy líquida, aunque el precio de entrada es más alto.")),
        ("prime", "Prime: Downtown y Dubai Creek Harbour",
         p("Junto al Burj Khalifa, <strong>Downtown</strong> es la dirección más reconocida de Dubái. Rinde menos en porcentaje, pero es de lo más fácil de revender y tiende a mantener valor. <strong>Dubai Creek Harbour</strong> es la gran apuesta de Emaar como «nuevo Downtown», con precios aún por debajo.")),
        ("crecimiento", "Crecimiento: Dubai South, Expo City y Dubai Islands",
         p("Son zonas para comprar sobre plano pensando en el medio plazo. <strong>Dubai South y Expo City</strong> crecen alrededor del aeropuerto Al Maktoum, que está previsto que sea el principal de Dubái. <strong>Dubai Islands</strong> es un frente marítimo nuevo con playas y hoteles. Hay más potencial de revalorización y también más incertidumbre. Cómo funciona comprar en construcción: <a href=\"/blog/comprar-sobre-plano-dubai/\">guía de compra sobre plano</a>.")),
        ("fuera", "¿Y fuera de Dubái?",
         p("Abu Dabi (Yas y Saadiyat) y Ras Al Khaimah ofrecen precios de entrada más bajos y sus propios motores de crecimiento. Te explico el caso de Al Marjan en <a href=\"/blog/invertir-ras-al-khaimah-al-marjan/\">invertir en Ras Al Khaimah</a>.")),
    ],
    [
        ("¿Cuál es la mejor zona para invertir en Dubái?", "Depende del objetivo. Para rentabilidad, zonas de precio medio como JVC o Dubai Sports City; para equilibrio, Business Bay o Dubai Marina; para liquidez, Downtown; para crecimiento, Dubai South o Dubai Islands."),
        ("¿Qué zona de Dubái da más rentabilidad por alquiler?", "Las zonas de precio medio, como JVC, Dubai Sports City o International City, superan el 8 % bruto en apartamentos, frente a cerca del 5 % en Downtown."),
        ("¿Dónde comprar para alquiler vacacional en Dubái?", "En zonas turísticas como Dubai Marina, Downtown, Business Bay o Palm Jumeirah, con una buena gestión y la licencia de holiday home."),
    ],
    [("rentabilidad-alquiler-dubai", "Rentabilidad del alquiler en Dubái"), ("comprar-sobre-plano-dubai", "Comprar sobre plano en Dubái")],
    date=D3, date_txt=D3_TXT, wa_msg="Hola Pascual, he leído tu artículo sobre las mejores zonas de Dubái. ¿Qué zona me recomiendas para mi caso?",
)

pages["rak"] = article(
    "invertir-ras-al-khaimah-al-marjan",
    "Invertir en Ras Al Khaimah y Al Marjan Island: guía 2026",
    "Invertir en Ras Al Khaimah <em>y Al Marjan Island</em>",
    "Por qué los inversores miran Ras Al Khaimah y Al Marjan Island: el resort Wynn (apertura en 2027), precios frente a Dubái, compra en plena propiedad, riesgos y Golden Visa.",
    "Ras Al Khaimah es el emirato del que más me preguntan después de Dubái, sobre todo por Al Marjan Island y el resort de Wynn. Te explico qué está pasando allí, cuánto cuesta y qué riesgos tiene.",
    "/assets/img/emirato-ras-al-khaimah-wynn.webp", "Al Marjan Island en Ras Al Khaimah con el resort Wynn en construcción",
    [
        ("donde", "Dónde está y por qué interesa",
         p("Ras Al Khaimah (RAK) es el emirato más al norte de Emiratos, a unos 50 minutos por carretera del aeropuerto internacional de Dubái. <strong>Al Marjan Island</strong> es un conjunto de islas artificiales frente a su costa, con playas, hoteles y residencias donde los extranjeros pueden comprar en plena propiedad (<em>freehold</em>), igual que en Al Hamra o Mina Al Arab.")),
        ("wynn", "El motor: Wynn Al Marjan Island",
         p("Wynn Resorts está construyendo en Al Marjan Island el primer resort integrado con casino de Emiratos, con más de 1.500 habitaciones, teatro, puerto deportivo y playa privada. En octubre de 2024 obtuvo la primera licencia de juego comercial del país. Tras un retraso por la situación regional, Wynn ha confirmado la <strong>apertura en septiembre de 2027</strong> y ha elevado el presupuesto a unos 5.700 millones de dólares.") +
         p("Para el inversor, eso significa más turismo internacional, más empleo y más demanda de alojamiento alrededor de la isla. Ras Al Khaimah tuvo su mejor primer semestre de visitantes en 2026, con más de 670.000.")),
        ("precios", "Precios frente a Dubái",
         p("El precio por metro cuadrado en Al Marjan sigue por debajo del de las zonas prime de Dubái frente al mar, como Dubai Marina o Palm Jumeirah. La mayoría de la oferta es <strong>obra nueva con planes de pago</strong>, con entradas del 10–20 % como en Dubái. Cada proyecto tiene sus cifras: te las preparo con la disponibilidad real del momento.")),
        ("riesgos", "Los riesgos, sin rodeos",
         ul("<strong>Es una apuesta por el futuro:</strong> gran parte del valor depende de que el turismo crezca como se espera tras la apertura del resort.",
            "<strong>Mucha oferta nueva</strong> que se entregará en pocos años: importa la ubicación dentro de la isla y la calidad del promotor.",
            "<strong>Mercado más pequeño y menos líquido</strong> que Dubái: revender puede llevar más tiempo.",
            "<strong>Fechas de entrega:</strong> como en cualquier obra nueva, revisa el historial del promotor y el contrato.") +
         note("Mi recomendación: RAK como complemento, no como primera y única inversión si tu presupuesto es ajustado. Si ya tienes algo en Dubái o buscas más potencial de revalorización asumiendo más riesgo, encaja muy bien.")),
        ("compra", "Cómo se compra",
         p("El proceso es muy parecido al de Dubái: reserva, contrato con el promotor, registro y pagos por fases, todo a distancia. Las tasas de registro no son las mismas que las del Dubai Land Department; te las detallo en cada proyecto. Cómo funciona la obra nueva: <a href=\"/blog/comprar-sobre-plano-dubai/\">guía para comprar sobre plano</a>.")),
        ("golden-visa", "Golden Visa",
         p("La Golden Visa por inversión inmobiliaria es un programa federal de Emiratos, así que una propiedad en Ras Al Khaimah que cumpla los requisitos también puede dar acceso a ella. Revisa los requisitos generales en la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">guía de la Golden Visa</a> y confirmamos los del emirato para tu caso.")),
    ],
    [
        ("¿Pueden los extranjeros comprar en Ras Al Khaimah?", "Sí, en plena propiedad en las zonas habilitadas, como Al Marjan Island, Al Hamra o Mina Al Arab."),
        ("¿Cuándo abre el resort Wynn de Al Marjan Island?", "Wynn ha confirmado su apertura para septiembre de 2027."),
        ("¿Es mejor invertir en Ras Al Khaimah o en Dubái?", "Dubái es un mercado más grande, consolidado y líquido. Ras Al Khaimah ofrece precios de entrada más bajos y más potencial de revalorización, con más riesgo. Para muchos inversores tiene sentido como complemento."),
    ],
    [("mejores-zonas-invertir-dubai", "Las mejores zonas para invertir en Dubái"), ("comprar-sobre-plano-dubai", "Comprar sobre plano en Dubái")],
    date=D3, date_txt=D3_TXT, wa_msg="Hola Pascual, he leído tu artículo sobre Ras Al Khaimah y Al Marjan. Quiero ver proyectos.",
)

pages["argentina"] = article(
    "invertir-en-dubai-desde-argentina",
    "Invertir en Dubái desde Argentina: guía práctica",
    "Invertir en Dubái <em>desde Argentina</em>",
    "Cómo comprar un piso en Dubái siendo argentino: precios en dólares, cómo transferir el dinero, qué declarar en Ganancias y Bienes Personales y cómo comprar a distancia.",
    "Para un argentino, Dubái es una forma de tener patrimonio y rentas en una moneda ligada al dólar, en un mercado con seguridad jurídica. Te explico precios, cómo se envía el dinero, qué declaras en Argentina y cómo se compra sin viajar.",
    "/assets/img/pascual-llamada.webp", "Pascual Vidal en una videollamada de consultoría con un inversor",
    [
        ("por-que", "Por qué Dubái atrae a inversores argentinos",
         ul("<strong>Patrimonio en moneda dura:</strong> el dírham está ligado al dólar a 3,6725 AED por dólar.",
            "<strong>Rentas de alquiler</strong> con rentabilidades brutas medias en torno al 6,5–7 %. Detalle en <a href=\"/blog/rentabilidad-alquiler-dubai/\">rentabilidad del alquiler en Dubái</a>.",
            "<strong>Seguridad jurídica:</strong> compra registrada en el Dubai Land Department y cuentas escrow en obra nueva.",
            "<strong>Planes de pago:</strong> en obra nueva entras con un 10–20 % y pagas el resto por fases, sin hipoteca.")),
        ("precios", "Cuánto cuesta en dólares",
         table(["Propiedad (ejemplo)", "En dírhams", "En dólares"], [
             ["Estudio en zona en crecimiento", "650.000 AED", "≈ 177.000 USD"],
             ["Apartamento de 1 dormitorio", "1.000.000 AED", "≈ 272.000 USD"],
             ["Apartamento de 2 dormitorios", "1.800.000 AED", "≈ 490.000 USD"],
             ["Mínimo para la Golden Visa", "2.000.000 AED", "≈ 545.000 USD"],
         ]) +
         p("Como el cambio con el dólar es fijo, estos importes apenas varían. Suma alrededor de un 4–5 % de gastos en obra nueva: <a href=\"/blog/cuanto-cuesta-comprar-piso-dubai/\">el desglose completo</a>.")),
        ("dinero", "Cómo enviar el dinero desde Argentina",
         "      <ol>" + "".join(f"<li>{x}</li>" for x in [
             "<strong>Confirma las reglas cambiarias vigentes:</strong> las normas para comprar dólares y transferirlos al exterior han cambiado mucho en los últimos años. Pregunta a tu banco o asesor qué aplica hoy a tu caso.",
             "<strong>Transferencia en dólares</strong> a la cuenta <em>escrow</em> del proyecto o del promotor, desde tu cuenta en Argentina o desde una cuenta tuya en el exterior.",
             "<strong>Justifica el origen de los fondos:</strong> en Dubái te pedirán documentos que lo demuestren, por las normas contra el blanqueo. Es más fácil si los fondos están declarados.",
             "<strong>Guarda todos los comprobantes</strong> para tus declaraciones en Argentina.",
         ]) + "</ol>\n"),
        ("impuestos", "Impuestos en Argentina",
         p("Si eres <strong>residente fiscal en Argentina</strong>, tributas por tu renta y tu patrimonio de cualquier país:") +
         ul("<strong>Impuesto a las Ganancias:</strong> declaras las rentas del alquiler en Dubái y, al vender, el resultado de la venta.",
            "<strong>Bienes Personales:</strong> el inmueble en el exterior forma parte de tu patrimonio a declarar.",
            "<strong>En Emiratos:</strong> como particular no pagas impuesto sobre la renta ni sobre plusvalías, solo el 4 % del registro al comprar.") +
         p("Las alícuotas, mínimos y regímenes cambian a menudo. Revísalo con tu contador <strong>antes</strong> de comprar.")),
        ("distancia", "Comprar sin viajar",
         p("Reserva, contrato y pagos se hacen a distancia con firma electrónica. Yo estoy en Dubái todo el año y me ocupo de lo presencial: revisión, entrega de llaves, amueblado y alquiler. Si quieres venir a verlo, consulta antes los requisitos de entrada vigentes para tu pasaporte.")),
        ("golden-visa", "Golden Visa para argentinos",
         p("Con 2 millones de AED (unos 545.000 USD) en propiedad puedes pedir la residencia de 10 años para ti y tu familia, sin obligación de vivir en Emiratos. Requisitos en la <a href=\"/blog/golden-visa-dubai-inversion-inmobiliaria/\">guía de la Golden Visa</a>.")),
    ],
    [
        ("¿Un argentino puede comprar una propiedad en Dubái?", "Sí. Los extranjeros pueden comprar en plena propiedad en las zonas habilitadas, sin residir en Emiratos ni tener visado."),
        ("¿Tengo que declarar en Argentina un piso en Dubái?", "Si eres residente fiscal en Argentina, sí: las rentas en Ganancias y el inmueble en Bienes Personales. Confírmalo con tu contador."),
        ("¿Cómo mando el dinero de Argentina a Dubái?", "Normalmente con una transferencia en dólares a la cuenta escrow del proyecto. Antes, confirma con tu banco las normas cambiarias vigentes para transferir al exterior."),
    ],
    [("invertir-en-dubai-desde-miami", "Invertir en Dubái desde Miami"), ("invertir-en-dubai-desde-colombia", "Invertir en Dubái desde Colombia")],
    date=D3, date_txt=D3_TXT, wa_msg="Hola Pascual, te escribo desde Argentina. Quiero información para invertir en Dubái.",
)


# ---------------------------------------------------------------- índice
ARTICLES.sort(key=lambda a: a["date"], reverse=True)
cards = "".join(
    f'<a class="post-card" href="/blog/{a["slug"]}/"><span class="post-img"><img src="{a["image"]}" alt="{H.escape(a["alt"])}" {dims(a["image"])} loading="lazy" /></span>'
    f'<span class="post-body"><small>Guía · {a["date_txt"]}</small><b>{H.escape(a["title"])}</b><span>{H.escape(a["desc"])}</span><i>Leer artículo →</i></span></a>'
    for a in ARTICLES)
idx_body = f"""    <section class="blog-index container">
      <nav class="crumbs" aria-label="Migas de pan"><a href="/">Inicio</a><span>/</span><span>Blog</span></nav>
      <p class="eyebrow"><span class="dot"></span>Blog</p>
      <h1>Invertir en Dubái, <em>explicado claro</em></h1>
      <p class="article-lead">Costes reales, impuestos, Golden Visa, zonas y alquiler. Lo que te contaría en una consultoría, por escrito y en español.</p>
      <div class="post-grid">{cards}</div>
    </section>"""
idx_ld = {"@context": "https://schema.org", "@type": "Blog", "@id": SITE + "/blog/#blog", "name": "Blog · Tu inversión en Dubái", "url": SITE + "/blog/", "inLanguage": "es",
          "author": {"@id": PERSON_ID}, "publisher": PUBLISHER, "isPartOf": {"@id": WEB_ID},
          "blogPost": [{"@type": "BlogPosting", "@id": f'{SITE}/blog/{a["slug"]}/#articulo', "headline": a["title"], "url": f'{SITE}/blog/{a["slug"]}/',
                        "datePublished": a["date"], "image": SITE + og_jpg(a["image"]), "author": {"@id": PERSON_ID}} for a in ARTICLES]}
pages["_index"] = ("/blog/", page("/blog/", "Blog sobre invertir en Dubái · Pascual Vidal",
                                  "Guías en español sobre invertir en Dubái: cuánto cuesta comprar, impuestos para españoles, Golden Visa, zonas y alquiler.",
                                  idx_body, idx_ld, og_type="website"))

# ---------------------------------------------------------------- páginas legales
# Rellena estos datos: aparecen en las tres páginas.
TITULAR = "Pascual Vidal"
NIF = "[NIF / n.º de pasaporte]"
DIRECCION = "[Dirección postal completa], Dubái, Emiratos Árabes Unidos"
EMAIL = "[email de contacto]"
LEGAL_DATE = DATE_TXT


def legal_page(slug, title, intro, sections):
    secs = "".join(f'\n      <h2 id="s{i}">{H.escape(t)}</h2>\n{c}' for i, (t, c) in enumerate(sections, 1))
    body = f"""    <article class="article legal">
      <header class="article-head container">
        <nav class="crumbs" aria-label="Migas de pan"><a href="/">Inicio</a><span>/</span><span>{H.escape(title)}</span></nav>
        <h1>{H.escape(title)}</h1>
        <p class="article-lead">{intro}</p>
        <p class="disclaimer">Última actualización: {LEGAL_DATE}</p>
      </header>
      <div class="article-layout container legal-layout">
        <div class="prose">{secs}
        </div>
      </div>
    </article>"""
    path = f"/{slug}/"
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": SITE + path, "inLanguage": "es"}
    doc = page(path, title + " · Tu inversión en Dubái", re.sub("<[^>]+>", "", intro), body, ld, og_type="website")
    return path, doc.replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />', '<meta name="robots" content="noindex, follow" />', 1)


pages["_aviso"] = legal_page("aviso-legal", "Aviso legal",
    "Información sobre el titular de este sitio web y las condiciones de uso, conforme a la Ley 34/2002 de servicios de la sociedad de la información (LSSI).", [
    ("Titular del sitio web",
     ul(f"<strong>Titular:</strong> {TITULAR}", f"<strong>NIF / documento:</strong> {NIF}", f"<strong>Domicilio:</strong> {DIRECCION}",
        f"<strong>Email:</strong> {EMAIL}", "<strong>Actividad:</strong> consultoría de inversión inmobiliaria en Dubái",
        "<strong>Registro profesional:</strong> agente registrado en RERA (Real Estate Regulatory Agency, Dubai Land Department) con el número 97799")),
    ("Objeto", p("Este sitio web informa sobre los servicios de consultoría inmobiliaria del titular y permite contactar con él. El acceso y el uso de la web implican la aceptación de este aviso legal.")),
    ("Uso del sitio web", p("Te comprometes a hacer un uso adecuado de los contenidos y a no emplearlos para actividades ilícitas o que puedan dañar al titular o a terceros.")),
    ("Contenidos e información", p("Los contenidos de esta web, incluidos los artículos del blog, tienen carácter informativo y general. No constituyen asesoramiento legal, fiscal ni financiero personalizado. Los precios, tasas, rentabilidades y normativas citados son orientativos y pueden cambiar: confírmalos siempre antes de tomar una decisión de inversión.",
                                    "Las imágenes de proyectos pueden ser recreaciones o material facilitado por los promotores y tienen carácter ilustrativo.")),
    ("Propiedad intelectual", p("Los textos, el diseño, el logotipo y las fotografías propias son del titular o se usan con permiso. Queda prohibida su reproducción sin autorización. Las marcas y nombres de terceros pertenecen a sus respectivos propietarios.")),
    ("Enlaces a terceros", p("La web contiene enlaces a sitios de terceros (WhatsApp, YouTube, Instagram, Google…). El titular no se responsabiliza de sus contenidos ni de sus políticas.")),
    ("Responsabilidad", p("El titular no garantiza la ausencia de errores en los contenidos ni la disponibilidad continua de la web, y no responde de los daños derivados de su uso, salvo en los casos previstos por la ley.")),
    ("Legislación aplicable", p("Este aviso legal se rige por la legislación española en lo que resulte aplicable a usuarios residentes en España, sin perjuicio de los derechos que te reconozca la normativa de consumidores.")),
])

pages["_privacidad"] = legal_page("privacidad", "Política de privacidad",
    "Cómo tratamos los datos personales que nos facilitas en esta web, conforme al Reglamento General de Protección de Datos (RGPD) y la Ley Orgánica 3/2018 (LOPDGDD).", [
    ("Responsable del tratamiento", ul(f"<strong>Responsable:</strong> {TITULAR}", f"<strong>NIF / documento:</strong> {NIF}", f"<strong>Domicilio:</strong> {DIRECCION}", f"<strong>Email:</strong> {EMAIL}")),
    ("Qué datos recogemos",
     p("Solo los que nos das en los formularios de la web:") +
     ul("<strong>Guía gratuita y noticias:</strong> tu email.",
        "<strong>Consultoría:</strong> nombre, email, teléfono, presupuesto orientativo, objetivo de inversión y el mensaje que quieras añadir.",
        "<strong>Dossier de proyecto:</strong> nombre, email, teléfono y el proyecto que te interesa.",
        "<strong>Datos técnicos:</strong> la página desde la que envías el formulario y, si llegas desde una campaña, su origen (por ejemplo, Instagram).") +
     p("Si nos escribes por WhatsApp o email, trataremos también los datos que incluyas en tus mensajes.")),
    ("Para qué los usamos",
     ul("Responder a tus consultas y preparar la consultoría que solicitas.", "Enviarte la guía y la información o el dossier que pides.",
        "Enviarte nuestras noticias semanales sobre el mercado inmobiliario de Dubái y Oriente Medio, si te suscribes.",
        "Hacer el seguimiento comercial de tu interés en invertir, mientras no te opongas.")),
    ("Base legal",
     ul("<strong>Tu consentimiento</strong>, al enviar el formulario o suscribirte. Puedes retirarlo cuando quieras.",
        "<strong>La aplicación de medidas precontractuales</strong> que tú solicitas, como la consultoría o el envío de un dossier.")),
    ("Cuánto tiempo los conservamos", p("Mientras mantengamos la relación o no pidas que los borremos. Si te das de baja de las noticias, dejaremos de enviártelas de inmediato. Después, los conservaremos bloqueados solo el tiempo necesario para atender posibles responsabilidades legales.")),
    ("Con quién los compartimos",
     p("No vendemos tus datos. Para prestar el servicio usamos proveedores que los tratan por cuenta nuestra:") +
     ul("<strong>Hostinger</strong> (alojamiento de la web y del sistema donde guardamos los contactos).",
        "<strong>Google</strong> (correo electrónico, calendario, tipografías de la web y, solo si aceptas las cookies de medición, Google Ads y Analytics).", "<strong>Meta / WhatsApp</strong>, si nos contactas por WhatsApp.",
        "<strong>YouTube</strong>, solo si reproduces un vídeo incrustado.") +
     p("Si decides invertir, y siempre con tu conocimiento, podremos compartir los datos necesarios con promotores, notarías, bancos o el Dubai Land Department para tramitar la operación.")),
    ("Transferencias internacionales", p("El responsable desarrolla su actividad en Dubái (Emiratos Árabes Unidos), país sin decisión de adecuación de la Comisión Europea, por lo que tus datos se consultan y gestionan desde allí. Al enviarnos tus datos para recibir nuestros servicios, consientes esta transferencia, que es necesaria para atender tu solicitud. Algunos proveedores (como Google o Meta) pueden tratar datos en Estados Unidos con las garantías que ofrecen sus propias políticas.")),
    ("Tus derechos", p(f"Puedes pedir el acceso, la rectificación, la supresión, la oposición, la limitación del tratamiento y la portabilidad de tus datos, y retirar tu consentimiento, escribiendo a {EMAIL}. Si consideras que no hemos atendido bien tu solicitud, puedes reclamar ante la Agencia Española de Protección de Datos (www.aepd.es).")),
    ("Seguridad", p("Aplicamos medidas razonables para proteger tus datos: conexión cifrada, acceso al sistema de contactos con contraseña y almacenamiento fuera de las carpetas públicas de la web.")),
])

pages["_cookies"] = legal_page("cookies", "Política de cookies",
    "Qué cookies y tecnologías similares usa esta web y cómo puedes gestionarlas.", [
    ("Qué son las cookies", p("Son pequeños archivos que una web guarda en tu navegador. Tecnologías parecidas, como el almacenamiento local del navegador, cumplen funciones similares.")),
    ("Qué usa esta web",
     p("<strong>Sin tu permiso, esta web no usa cookies publicitarias ni de analítica.</strong> Siempre guarda en tu navegador estos datos técnicos, necesarios para que funcione bien:") +
     '      <div class="table-scroll"><table><thead><tr><th>Nombre</th><th>Para qué</th><th>Duración</th></tr></thead><tbody>'
     '<tr><td>pv_guide_seen</td><td>No volver a mostrarte el aviso de la guía en la misma visita</td><td>Hasta cerrar el navegador</td></tr>'
     '<tr><td>pv_guide_done</td><td>Recordar que ya pediste la guía</td><td>Hasta que lo borres</td></tr>'
     '<tr><td>pv_utm</td><td>Recordar desde qué campaña llegaste, para atender bien tu consulta</td><td>Hasta cerrar el navegador</td></tr>'
     '<tr><td>pv_leads</td><td>Copia de seguridad de tus envíos por si falla la conexión</td><td>Hasta que lo borres</td></tr>'
     '<tr><td>pv_consent</td><td>Recordar si aceptaste o rechazaste las cookies de medición</td><td>Hasta que lo borres</td></tr>'
     '</tbody></table></div>\n' +
     p("Al ser estrictamente necesarios para el servicio que pides, no requieren tu consentimiento.")),
    ("Cookies de medición de Google (solo si aceptas)",
     p("Si aceptas en el aviso de cookies, activamos <strong>Google Ads</strong> (y, si está configurado, <strong>Google Analytics</strong>) para saber qué anuncios traen visitas y contactos, sin identificarte por tu nombre. Google puede instalar cookies como <em>_gcl_au</em>, <em>_ga</em> o <em>_ga_*</em>, con una duración de entre 90 días y 2 años.",
       "Si las rechazas, no se carga nada de Google en esta web. Puedes cambiar de opinión cuando quieras desde el enlace <strong>«Configurar cookies»</strong> del pie de página. Más información en la política de privacidad de Google (policies.google.com/privacy).")),
    ("Servicios de terceros",
     ul("<strong>Vídeos de YouTube:</strong> no se cargan hasta que pulsas reproducir, y usan el modo de privacidad mejorada de YouTube (youtube-nocookie.com). Al reproducirlos, YouTube puede guardar sus propias cookies.",
        "<strong>Tipografías de Google Fonts:</strong> se descargan de los servidores de Google, que recibe tu dirección IP, pero no instalan cookies.",
        "<strong>WhatsApp e Instagram:</strong> solo si pulsas sus enlaces, ya en sus propias webs.")),
    ("Cómo gestionarlas", p("Puedes borrar estos datos o bloquearlos desde la configuración de tu navegador (Chrome, Safari, Firefox, Edge…). Si los bloqueas, la web seguirá funcionando, aunque podrías ver el aviso de la guía más de una vez.")),
    ("Cambios", p("Si añadimos otras herramientas de analítica o publicidad, te pediremos permiso antes y actualizaremos esta página.")),
])

# ---------------------------------------------------------------- página de aterrizaje para anuncios
contact = absolutize(grab('    <section class="contact section section-light" id="contacto">', '</section>'))
home_faq = dict(re.findall(r'<summary><span>(.*?)</span>.*?</summary>\s*<p>(.*?)</p>', src, re.S))
lp_faqs = [(q, home_faq[q]) for q in ["¿Puedo comprar sin viajar a Dubái?", "¿Cuánto dinero necesito para invertir en Dubái?", "¿Qué pasa con mi propiedad cuando no estoy en Dubái?", "¿Qué impuestos pago al invertir en Dubái?"] if q in home_faq]
lp_faq_html = "".join(f'<details class="faq-item"><summary><span>{q}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><p>{a}</p></details>' for q, a in lp_faqs)
steps = [("Antes", "Elegimos bien", "Analizamos tu objetivo y tu presupuesto, comparamos zonas y promotores y hacemos los números reales de cada propiedad."),
         ("Durante", "Compras tranquilo", "Reserva, contratos, pagos y registro en el Dubai Land Department. Te represento en todo, aunque no viajes."),
         ("Después", "No te quedas solo", "Entrega de llaves, amueblado, alquiler vacacional o anual, mantenimiento, reventa y Golden Visa.")]
steps_html = "".join(f'<div class="lp-step"><span>0{i}</span><small class="eyebrow"><span class="dot"></span>{a}</small><h3>{b}</h3><p>{c}</p></div>' for i, (a, b, c) in enumerate(steps, 1))
lp_body = f"""    <section class="lp-hero container">
      <p class="eyebrow"><span class="dot"></span>Consultor inmobiliario español en Dubái · RERA #97799</p>
      <h1>Invierte en Dubái con alguien que <em>sigue contigo</em> después de comprar</h1>
      <p class="article-lead">Hay muchos comerciales y pocos consultores. Te ayudo a elegir la propiedad adecuada con números reales y me ocupo de todo lo que viene después: alquiler, mantenimiento, reventa y Golden Visa. En español.</p>
      <div class="lp-trust"><img src="/assets/img/dubai-land-department.webp" alt="Dubai Land Department" width="140" height="34" /><span><b>+90</b> operaciones gestionadas</span><span><b>12 meses</b> al año viviendo en Dubái</span><span><b>0 %</b> impuesto sobre la renta personal en EAU</span></div>
    </section>
{contact}
    <section class="lp-block container"><h2>Cómo trabajo contigo</h2><div class="lp-steps">{steps_html}</div></section>
    <section class="lp-block container"><h2>Preguntas frecuentes</h2><div class="article-faq">{lp_faq_html}</div></section>"""
lp_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "Consultoría gratuita para invertir en Dubái", "url": SITE + "/consultoria/", "inLanguage": "es"}
lp_doc = page("/consultoria/", "Consultoría gratuita para invertir en Dubái · Pascual Vidal",
              "Reserva una llamada gratuita de 20 minutos con un consultor inmobiliario español en Dubái. Te acompaño antes, durante y después de la compra.",
              lp_body, lp_ld, og_type="website", body_attrs=" data-no-guide-popup")
pages["_consultoria"] = ("/consultoria/", lp_doc.replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />', '<meta name="robots" content="noindex, follow" />', 1))


# ---------------------------------------------------------------- página de autor (E-E-A-T: quién está detrás de los contenidos)
ABOUT_FACTS = [
    ("Quién soy", p(
        "Soy <strong>Pascual Vidal</strong>, consultor inmobiliario español afincado en Dubái. Llevo tres años en el mercado inmobiliario de Emiratos y vivo aquí los 12 meses del año.",
        "Estoy registrado como agente en <strong>RERA</strong> (Real Estate Regulatory Agency, el regulador del Dubai Land Department) con el número <strong>97799</strong>. He gestionado más de <strong>90 operaciones</strong> en Dubái.")),
    ("A quién ayudo", p(
        "A inversores hispanohablantes —de España, México, Colombia, Argentina, Chile, Perú y Estados Unidos— que quieren comprar una propiedad en Dubái, Abu Dabi o Ras Al Khaimah, sobre todo de obra nueva, y que no quieren quedarse solos una vez firmada la compra.")),
    ("Cómo trabajo", ul(
        "<strong>Consultor, no comercial:</strong> antes de recomendarte una propiedad analizamos tu objetivo y tu presupuesto y hacemos los números reales.",
        "<strong>Compra en remoto:</strong> reserva, contratos, pagos y registro en el Dubai Land Department sin que tengas que viajar.",
        "<strong>Después de comprar:</strong> entrega de llaves, amueblado a medida, alquiler vacacional o anual, mantenimiento, reventa y Golden Visa.")),
    ("Dónde puedes verme", p(
        'Explico el mercado de Dubái en mi canal de <a href="https://www.youtube.com/@pascual.dubairealestate" rel="me noopener" target="_blank">YouTube</a> y en <a href="https://www.instagram.com/pascual.dubairealestate/" rel="me noopener" target="_blank">Instagram</a>, y por escrito en el <a href="/blog/">blog</a>.')),
]
about_secs = "".join(f'\n      <h2 id="a{i}">{H.escape(t)}</h2>\n{c}' for i, (t, c) in enumerate(ABOUT_FACTS, 1))
about_posts = "".join(f'<li><a href="/blog/{a["slug"]}/">{H.escape(a["title"])}</a></li>' for a in ARTICLES)
about_body = f"""    <article class="article">
      <header class="article-head container">
        <nav class="crumbs" aria-label="Migas de pan"><a href="/">Inicio</a><span>/</span><span>Pascual Vidal</span></nav>
        <p class="eyebrow"><span class="dot"></span>Consultor inmobiliario en Dubái · RERA #97799</p>
        <h1>Pascual Vidal, <em>consultor inmobiliario</em> español en Dubái</h1>
        <p class="article-lead">Ayudo a hispanohablantes a invertir en propiedades en Dubái y Emiratos, y sigo a su lado después de la compra.</p>
      </header>
      <figure class="article-cover container"><img src="/assets/img/pascual-dubai.webp" alt="Pascual Vidal en Dubái" {dims("/assets/img/pascual-dubai.webp")} loading="eager" fetchpriority="high" style="aspect-ratio:16/9;object-position:center 30%" /></figure>
      <div class="article-layout container">
        <aside class="toc"><b>En esta página</b><ol>{"".join(f'<li><a href="#a{i}">{H.escape(t)}</a></li>' for i, (t, _) in enumerate(ABOUT_FACTS, 1))}</ol></aside>
        <div class="prose">{about_secs}
      <h2 id="articulos">Mis guías</h2>
      <ul>{about_posts}</ul>
      <div class="article-cta">
        <div>
          <p class="eyebrow"><span class="dot"></span>Consultoría gratuita</p>
          <h3>¿Hablamos de tu inversión?</h3>
          <p>En 20 minutos vemos tu presupuesto, tu objetivo y qué zonas encajan contigo. Sin compromiso.</p>
        </div>
        <div class="article-cta-actions">
          <a class="btn btn-wa" data-wa data-wa-msg="Hola Pascual, he leído quién eres en tu web y quiero hablar de mi inversión en Dubái." href="{WA_LINK}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-wa"/></svg><span>Escríbeme por WhatsApp</span></a>
          <a class="btn btn-dark" href="/#contacto">Reservar llamada</a>
        </div>
      </div>
        </div>
      </div>
    </article>"""
about_ld = {"@context": "https://schema.org", "@type": "ProfilePage", "@id": SITE + "/sobre-pascual-vidal/", "url": SITE + "/sobre-pascual-vidal/",
            "name": "Pascual Vidal, consultor inmobiliario español en Dubái", "inLanguage": "es", "isPartOf": {"@id": WEB_ID}, "dateModified": TODAY,
            "mainEntity": dict(AUTHOR, **{
                "description": "Consultor inmobiliario español en Dubái, registrado en RERA con el n.º 97799. Asesora a inversores hispanohablantes en la compra, alquiler y reventa de propiedades en Emiratos.",
                "nationality": {"@type": "Country", "name": "España"}, "knowsLanguage": ["es", "en"], "homeLocation": {"@type": "City", "name": "Dubái"},
                "worksFor": {"@id": ORG_ID},
                "hasCredential": {"@type": "EducationalOccupationalCredential", "credentialCategory": "Licencia profesional",
                                  "name": "Agente inmobiliario registrado en RERA n.º 97799",
                                  "recognizedBy": {"@type": "GovernmentOrganization", "name": "Dubai Land Department (RERA)", "url": "https://dubailand.gov.ae/"}},
                "knowsAbout": ["Inversión inmobiliaria en Dubái", "Obra nueva sobre plano", "Golden Visa de Emiratos", "Alquiler vacacional en Dubái",
                               "Fiscalidad de inversores españoles y latinoamericanos en Dubái"]})}
pages["_autor"] = ("/sobre-pascual-vidal/", page("/sobre-pascual-vidal/", "Pascual Vidal, consultor inmobiliario español en Dubái (RERA #97799)",
    "Quién es Pascual Vidal: consultor inmobiliario español en Dubái registrado en RERA (n.º 97799), con más de 90 operaciones. Inversión, postventa, alquiler y Golden Visa.",
    about_body, about_ld, og_type="profile"))

# ---------------------------------------------------------------- 404
nf_body = """    <section class="notfound container">
      <p class="eyebrow"><span class="dot"></span>Error 404</p>
      <h1>Esta página <em>no existe</em></h1>
      <p class="article-lead">Puede que el enlace esté mal o que la hayamos movido. Esto es lo más leído:</p>
      <div class="post-links">""" + "".join(f'<a class="btn btn-dark btn-sm" href="/blog/{a["slug"]}/">{H.escape(a["title"])}</a>' for a in ARTICLES[:4]) + """</div>
      <p><a class="btn btn-primary" href="/">Volver al inicio</a></p>
    </section>"""
nf = page("/404/", "Página no encontrada · Tu inversión en Dubái", "La página que buscas no existe.", nf_body,
          {"@context": "https://schema.org", "@type": "WebPage", "name": "Página no encontrada"}, og_type="website")
nf = nf.replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />', '<meta name="robots" content="noindex, follow" />')
nf = re.sub(r'\s*<link rel="(canonical|alternate)"[^>]*>', "", nf)
open(ROOT + "/404.html", "w").write(nf)

# ---------------------------------------------------------------- llms.txt (resumen para buscadores con IA: ChatGPT, Perplexity, Gemini, Claude…)
def _txt(x):
    return H.unescape(re.sub("<[^>]+>", "", x))

llms = ["# Tu inversión en Dubái · Pascual Vidal", "",
        "> Consultoría de inversión inmobiliaria en Dubái para hispanohablantes, dirigida por Pascual Vidal, consultor español registrado en RERA "
        "(Dubai Land Department) con el n.º 97799, que vive en Dubái y ha gestionado más de 90 operaciones. Ayuda a comprar propiedades —sobre todo de "
        "obra nueva— en Dubái, Abu Dabi y Ras Al Khaimah, y se ocupa de la postventa: entrega, amueblado, alquiler vacacional y anual, reventa y Golden Visa.", "",
        "Datos clave:",
        "- Idiomas: español e inglés. Clientes de España, México, Colombia, Argentina, Chile, Perú y Estados Unidos.",
        "- La compra se puede hacer entera en remoto; primera consultoría gratuita de 20 minutos.",
        "- Agencia: opera con Dubana Real Estate (Dubái).",
        "- Contacto: teléfono y WhatsApp +971 50 796 3006 · WhatsApp " + WA_LINK + " · formulario en " + SITE + "/#contacto",
        "- YouTube: https://www.youtube.com/@pascual.dubairealestate · Instagram: https://www.instagram.com/pascual.dubairealestate/", "",
        "## Páginas principales", "",
        f"- [Inicio]({SITE}/): servicios, proyectos destacados y preguntas frecuentes sobre invertir en Dubái.",
        f"- [Quién es Pascual Vidal]({SITE}/sobre-pascual-vidal/): trayectoria, licencia RERA y forma de trabajar.",
        f"- [Consultoría gratuita]({SITE}/consultoria/): reserva de llamada.", "",
        "## Guías (blog)", ""]
for a in ARTICLES:
    llms.append(f"- [{a['title']}]({SITE}/blog/{a['slug']}/): {a['desc']}")
llms += ["", "## Preguntas frecuentes", ""]
for q, a in home_faq.items():
    llms.append(f"- **{_txt(q)}** {_txt(a)}")
llms += ["", "## Resúmenes de las guías", ""]
for a in ARTICLES:
    if a["summary"]:
        llms.append(f"### {a['title']}")
        llms.append(f"Fuente: {SITE}/blog/{a['slug']}/ (actualizado {a['date']})")
        llms += [f"- {_txt(x)}" for x in a["summary"]]
        llms.append("")
llms.append("Información orientativa, no asesoramiento fiscal ni legal. Cifras y normas sujetas a cambios.")
open(ROOT + "/llms.txt", "w").write("\n".join(llms) + "\n")

import os
for key, (path, doc) in pages.items():
    d = ROOT + path
    os.makedirs(d, exist_ok=True)
    open(d + "index.html", "w").write(doc)
    print("ok", path)

LASTMOD = {"/": TODAY, "/blog/": max(a["date"] for a in ARTICLES), "/sobre-pascual-vidal/": TODAY, "/guia/": TODAY, "/al-marjan-island/": TODAY}
LASTMOD.update({f'/blog/{a["slug"]}/': a["date"] for a in ARTICLES})
urls = ["/", "/guia/", "/al-marjan-island/", "/sobre-pascual-vidal/", "/blog/"] + [f'/blog/{a["slug"]}/' for a in ARTICLES]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
    f"  <url><loc>{SITE}{u}</loc><lastmod>{LASTMOD[u]}</lastmod></url>\n" for u in urls) + "</urlset>\n"
open(ROOT + "/sitemap.xml", "w").write(sm)
