import sys
from PIL import Image
src, outbase = sys.argv[1], sys.argv[2]
# crop fractions: left, top, right, bottom (0..1) ; optional upscale
regions = []
args = sys.argv[3:]
for a in args:
    l,t,r,b = map(float, a.split(","))
    regions.append((l,t,r,b))
im = Image.open(src).convert("L")
W,H = im.size
for i,(l,t,r,b) in enumerate(regions):
    box = (int(l*W), int(t*H), int(r*W), int(b*H))
    crop = im.crop(box)
    # upscale 2x for legibility
    crop = crop.resize((crop.width*2, crop.height*2), Image.LANCZOS)
    out = f"{outbase}_{i}.png"
    crop.save(out)
    print("wrote", out, crop.size)
