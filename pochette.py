from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random, os

T = 1000
img = Image.new("RGB", (T, T), (8, 6, 14))
px = img.load()
for y in range(T):
    for x in range(T):
        dx, dy = (x - T*0.5) / T, (y - T*0.66) / T
        r = math.hypot(dx, dy)
        halo = max(0.0, 1 - r * 2.0) ** 2
        bas = 12 + 14 * (y / T)
        px[x, y] = (int(bas + 160 * halo), int(bas * 0.7 + 34 * halo), int(bas * 1.5 + 215 * halo))

# rayures glitch
rnd = random.Random(7)
d0 = ImageDraw.Draw(img)
for i in range(60):
    y = rnd.randrange(T)
    h = rnd.choice([1, 1, 2, 3, 5])
    dec = rnd.randrange(-24, 24)
    img.paste(img.crop((0, y, T, y + h)).transform((T, h), Image.AFFINE, (1, 0, dec, 0, 1, 0)), (0, y))
    if rnd.random() < 0.45:
        d0.rectangle([0, y, rnd.randrange(50, 330), y + h - 1], fill=(255, 40, 220))

# onde 808 en bas, discrete
pts = []
for x in range(T):
    t = x / T
    v = math.sin(t * 9) * math.exp(-((t * 2.4) % 1) * 2.6) * 0.5 + math.sin(t * 41) * 0.10
    pts.append((x, int(T * 0.855 + v * 52)))
ImageDraw.Draw(img).line(pts, fill=(0, 240, 225), width=5)
for x in range(0, T, 2):
    h = abs(math.sin(x / 9)) * 20
    d0.line([(x, T * 0.855), (x, T * 0.855 - h)], fill=(255, 60, 220))

CHEMIN = "/home/furax/workspace/fritax-linux/assets-src/montserrat.ttf"
if not os.path.exists(CHEMIN):
    trouves = [p for p in __import__("glob").glob("/home/furax/workspace/**/*.ttf", recursive=True)]
    CHEMIN = trouves[0] if trouves else None
print("police :", CHEMIN)

def police(taille):
    if CHEMIN:
        try:
            return ImageFont.truetype(CHEMIN, taille)
        except Exception:
            pass
    return ImageFont.load_default()

def largeur(txt, f):
    b = f.getbbox(txt)
    return b[2] - b[0]

def ajuster(txt, taille_max, cible=880):
    """choisit la plus grande taille qui tient dans la largeur visee"""
    t = taille_max
    while t > 20 and largeur(txt, police(t)) > cible:
        t -= 4
    return police(t)

def texte_graisse(dc, pos, txt, f, couleur, graisse=3):
    """vraie graisse : contour epais de la meme couleur que le remplissage"""
    dc.text(pos, txt, font=f, fill=couleur, anchor="mm",
            stroke_width=graisse, stroke_fill=couleur)

f_mont = ajuster("MONTAGEM", 150, 700)
f_frit = ajuster("FRITAX", 300, 860)
f_ritm = ajuster("RITMADA", 130, 760)
f_bas = police(34)

calque = Image.new("RGBA", (T, T), (0, 0, 0, 0))
dc = ImageDraw.Draw(calque)
texte_graisse(dc, (T//2, 170), "MONTAGEM", f_mont, (255, 255, 255, 255), 5)
texte_graisse(dc, (T//2, 350), "FRITAX", f_frit, (232, 36, 255, 255), 9)
texte_graisse(dc, (T//2, 505), "R I T M A D A", f_ritm, (0, 245, 232, 255), 4)
dc.text((T//2, 930), "132 BPM  ·  BRAZILIAN PHONK  ·  FURAXDEV", font=f_bas,
        fill=(238, 230, 255, 235), anchor="mm")

img = Image.alpha_composite(img.convert("RGBA"), calque.filter(ImageFilter.GaussianBlur(26)))
img = Image.alpha_composite(img, calque).convert("RGB")
img.save("/tmp/pochette_phonk.png")
print("pochette :", img.size,
      "| largeurs :", largeur("MONTAGEM", f_mont), largeur("FRITAX", f_frit), largeur("R I T M A D A", f_ritm))
