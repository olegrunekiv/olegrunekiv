"""Turn a light-on-black image into ink cut-outs: white and black, alpha = brightness."""
import sys
from PIL import Image, ImageOps
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("L")
bbox = im.point(lambda v: 255 if v > 24 else 0).getbbox()
print("bbox", bbox)
# square crop around the fish centre with some breathing room
cx, cy = (bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2
half = max(bbox[2]-bbox[0], bbox[3]-bbox[1])/2 + 24
box = tuple(int(round(v)) for v in (cx-half, cy-half, cx+half, cy+half))
print("crop", box)
crop = im.crop(box).resize((520, 520), Image.LANCZOS)
# luminance -> alpha, with a soft black point so the jpeg noise in the background disappears
alpha = crop.point(lambda v: 0 if v < 10 else min(255, int((v-10)*255/235)))
for name, rgb in (("white", 255), ("black", 0)):
    ink = Image.new("LA", crop.size, rgb)
    ink.putalpha(alpha)
    ink.save(f"{out}/koi-{name}.png", optimize=True)
