"""Genera /blog, sus artículos y las páginas legales a partir de la plantilla de index.html.
Uso: python3 tools/build.py   (desde la raíz del repo)"""
import json, re, sys, html as H

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://tuinversionendubai.com"
V = "20261031c"
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

AUTHOR = {"@type": "Person", "name": "Pascual Vidal", "url": SITE + "/#sobre-mi"}


def page(path, title, desc, body, ld, og_image="/assets/img/pascual-dubai.webp", og_type="article", body_attrs=""):
    url = SITE + path
    return f"""<!doctype html>
<html lang="es" class="no-js">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{H.escape(title)}</title>
  <meta name="description" content="{H.escape(desc)}" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:locale" content="es_ES" />
  <meta property="og:site_name" content="Tu inversión en Dubái" />
  <meta property="og:url" content="{url}" />
  <meta property="og:title" content="{H.escape(title)}" />
  <meta property="og:description" content="{H.escape(desc)}" />
  <meta property="og:image" content="{SITE}{og_image}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="theme-color" content="#ffffff" />
  {favicon}
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


def article(slug, title, h1, desc, lead, image, alt, sections, faqs, related):
    ARTICLES.append(dict(slug=slug, title=title, h1=h1, desc=desc, lead=lead, image=image, alt=alt))
    toc = "".join(f'<li><a href="#{sid}">{H.escape(t)}</a></li>' for sid, t, _ in sections)
    secs = "".join(f'\n      <h2 id="{sid}">{H.escape(t)}</h2>\n{c}' for sid, t, c in sections)
    faq_html = "".join(
        f'<details class="faq-item"><summary><span>{H.escape(q)}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><p>{a}</p></details>'
        for q, a in faqs)
    rel = "".join(f'<a class="related-card" href="/blog/{s}/"><small>Artículo</small><b>{H.escape(t)}</b><span>Leer →</span></a>' for s, t in related)
    path = f"/blog/{slug}/"
    body = f"""    <article class="article">
      <header class="article-head container">
        <nav class="crumbs" aria-label="Migas de pan"><a href="/">Inicio</a><span>/</span><a href="/blog/">Blog</a></nav>
        <p class="eyebrow"><span class="dot"></span>Guía para inversores · Actualizado el {DATE_TXT}</p>
        <h1>{h1}</h1>
        <p class="article-lead">{lead}</p>
        <div class="article-author"><img src="/assets/img/pascual-retrato.webp" alt="Pascual Vidal" width="48" height="48" loading="lazy" /><span><b>Pascual Vidal</b><small>Consultor inmobiliario en Dubái · RERA #97799</small></span></div>
      </header>
      <figure class="article-cover container"><img src="{image}" alt="{H.escape(alt)}" loading="eager" /></figure>
      <div class="article-layout container">
        <aside class="toc"><b>En este artículo</b><ol>{toc}</ol></aside>
        <div class="prose">{secs}
      <h2 id="preguntas">Preguntas frecuentes</h2>
      <div class="article-faq">{faq_html}</div>
      <div class="article-cta">
        <div>
          <p class="eyebrow"><span class="dot"></span>Consultoría gratuita</p>
          <h3>¿Hacemos los números de tu caso?</h3>
          <p>En 20 minutos vemos tu presupuesto, tu objetivo y qué zonas encajan contigo. Sin compromiso.</p>
        </div>
        <div class="article-cta-actions">
          <a class="btn btn-wa" data-wa data-wa-msg="Hola Pascual, he leído tu artículo «{H.escape(h1)}» y quiero consultarte mi caso." href="#" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-wa"/></svg><span>Escríbeme por WhatsApp</span></a>
          <button class="btn btn-dark" type="button" data-open-guide>Descargar la guía gratis</button>
        </div>
      </div>
      <p class="disclaimer">Información general orientativa, no asesoramiento fiscal ni legal. Las tasas y normas cambian: confirma siempre las cifras vigentes antes de comprar.</p>
        </div>
      </div>
      <section class="related container"><h2>Sigue leyendo</h2><div class="related-grid">{rel}</div></section>
    </article>"""
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": h1.replace("<em>", "").replace("</em>", ""), "description": desc,
         "image": SITE + image, "datePublished": DATE, "dateModified": DATE, "inLanguage": "es", "author": AUTHOR,
         "publisher": {"@type": "Organization", "name": "Tu inversión en Dubái", "url": SITE + "/"}, "mainEntityOfPage": SITE + path},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": title, "item": SITE + path}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in faqs]},
    ]
    return path, page(path, title + " · Pascual Vidal", desc, body, ld, og_image=image)


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

# ---------------------------------------------------------------- índice
cards = "".join(
    f'<a class="post-card" href="/blog/{a["slug"]}/"><span class="post-img"><img src="{a["image"]}" alt="{H.escape(a["alt"])}" loading="lazy" /></span>'
    f'<span class="post-body"><small>Guía · {DATE_TXT}</small><b>{H.escape(a["title"])}</b><span>{H.escape(a["desc"])}</span><i>Leer artículo →</i></span></a>'
    for a in ARTICLES)
idx_body = f"""    <section class="blog-index container">
      <nav class="crumbs" aria-label="Migas de pan"><a href="/">Inicio</a><span>/</span><span>Blog</span></nav>
      <p class="eyebrow"><span class="dot"></span>Blog</p>
      <h1>Invertir en Dubái, <em>explicado claro</em></h1>
      <p class="article-lead">Costes reales, impuestos, Golden Visa, zonas y alquiler. Lo que te contaría en una consultoría, por escrito y en español.</p>
      <div class="post-grid">{cards}</div>
    </section>"""
idx_ld = {"@context": "https://schema.org", "@type": "Blog", "name": "Blog · Tu inversión en Dubái", "url": SITE + "/blog/", "inLanguage": "es",
          "blogPost": [{"@type": "BlogPosting", "headline": a["title"], "url": f'{SITE}/blog/{a["slug"]}/'} for a in ARTICLES]}
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
    return path, doc.replace('<meta name="theme-color"', '<meta name="robots" content="noindex, follow" />\n  <meta name="theme-color"', 1)


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
pages["_consultoria"] = ("/consultoria/", lp_doc.replace('<meta name="theme-color"', '<meta name="robots" content="noindex, follow" />\n  <meta name="theme-color"', 1))

import os
for key, (path, doc) in pages.items():
    d = ROOT + path
    os.makedirs(d, exist_ok=True)
    open(d + "index.html", "w").write(doc)
    print("ok", path)

urls = ["/"] + [p for k, (p, _) in pages.items() if k in ("_index",) or not k.startswith("_")]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
    f"  <url><loc>{SITE}{u}</loc><lastmod>{DATE}</lastmod></url>\n" for u in urls) + "</urlset>\n"
open(ROOT + "/sitemap.xml", "w").write(sm)
