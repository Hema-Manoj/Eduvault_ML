from PIL import Image
import imagehash

# Use the SAME certificate image you test with
img = Image.open("output_images/unstop_sample.png").convert("RGB")

w, h = img.size

# ⚠️ MUST MATCH phash.py EXACTLY
logo_region = img.crop((
    int(w * 0.02),
    int(h * 0.02),
    int(w * 0.25),
    int(h * 0.18)
))

print("Unstop logo pHash:")
print(imagehash.phash(logo_region))
