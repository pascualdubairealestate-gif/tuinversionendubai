"""Genera los recursos SEO estáticos: imágenes Open Graph en JPG (1200x630), favicons PNG y logo.
Uso: python3 tools/seo_assets.py   (desde la raíz del repo). Solo hace falta volver a ejecutarlo si cambian las imágenes."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = "."
IMG = f"{ROOT}/assets/img"
OG = f"{IMG}/og"
os.makedirs(OG, exist_ok=True)

NAVY = (7, 13, 24)
SAND = (217, 199, 167)
WHITE = (255, 255, 255)
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def cover(src, w, h):
    im = Image.open(src).convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


# Imagen principal de la web: panel con texto + foto de Pascual
og = Image.new("RGB", (1200, 630), NAVY)
photo = cover(f"{IMG}/pascual-dubai.webp", 480, 630)
og.paste(photo, (720, 0))
d = ImageDraw.Draw(og)
d.rectangle((0, 0, 8, 630), fill=SAND)
d.text((70, 120), "CONSULTOR INMOBILIARIO ESPAÑOL · RERA #97799", font=ImageFont.truetype(SANS_B, 20), fill=SAND)
title = ImageFont.truetype(SERIF, 68)
d.text((70, 180), "Tu inversión", font=title, fill=WHITE)
d.text((70, 262), "en Dubái", font=title, fill=WHITE)
d.text((70, 380), "con Pascual Vidal", font=ImageFont.truetype(SANS, 34), fill=SAND)
d.text((70, 500), "tuinversionendubai.com", font=ImageFont.truetype(SANS, 24), fill=(200, 205, 215))
og.save(f"{OG}/pascual-vidal.jpg", quality=86, optimize=True, progressive=True)

# Portadas del blog y proyectos en JPG (WhatsApp, LinkedIn y algunos lectores no muestran WebP)
for name in os.listdir(IMG):
    if name.endswith(".webp") and (name.startswith("blog-") or name.startswith("proyecto-")):
        cover(f"{IMG}/{name}", 1200, 630).save(f"{OG}/{name[:-5]}.jpg", quality=84, optimize=True, progressive=True)

# Logo y favicons «PV»
def mark(size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((0, 0, size - 1, size - 1), radius=round(size * 0.22), fill=NAVY)
    f = ImageFont.truetype(SERIF, round(size * 0.44))
    dd.text((size / 2, size / 2), "PV", font=f, fill=SAND, anchor="mm")
    return im


mark(512).save(f"{IMG}/logo-pv-512.png", optimize=True)
mark(32).save(f"{ROOT}/favicon-32.png", optimize=True)
apple = Image.new("RGB", (180, 180), NAVY)
apple.paste(mark(180), (0, 0), mark(180))
apple.save(f"{ROOT}/apple-touch-icon.png", optimize=True)
mark(192).save(f"{IMG}/icon-192.png", optimize=True)
mark(48).save(f"{ROOT}/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("ok")
