# Packs rendered frames + skin masks into one WebP sprite sheet per template and character:
#   top half = frames (4 columns), bottom half = matching skin masks (white = skin). The app tints skin with them.
# Usage: python tools/make_sprites.py <frames root> <sex m|f> <out demos dir> [name ...]
# Frames: <root>/<name>/<name>_NNN.png, masks: <root>/<name>/mask_NNN.png. Writes tools/sprite_meta.json.
import glob, json, os, sys
from PIL import Image

root, sex, out = sys.argv[1], sys.argv[2], sys.argv[3]
names = sys.argv[4:] or sorted(os.listdir(root))
HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = json.load(open(os.path.join(HERE, "catalog_timing.json")))
META_P = os.path.join(HERE, "sprite_meta.json")
meta = json.load(open(META_P)) if os.path.exists(META_P) else {}
W, H, COLS = 480, 320, 4
os.makedirs(f"{out}/{sex}", exist_ok=True)
sizes = {}
for n in names:
    fs = sorted(glob.glob(f"{root}/{n}/{n}_[0-9][0-9][0-9].png"))
    ms = sorted(glob.glob(f"{root}/{n}/mask_[0-9][0-9][0-9].png"))
    assert fs and len(fs) == len(ms), (n, len(fs), len(ms))
    rows = -(-len(fs) // COLS)
    sh = Image.new("RGB", (W * COLS, H * rows * 2), "black")
    for i, (f, m) in enumerate(zip(fs, ms)):
        x, y = (i % COLS) * W, (i // COLS) * H
        sh.paste(Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
        sh.paste(Image.open(m).convert("L").resize((W, H), Image.LANCZOS).convert("RGB"), (x, y + H * rows))
    p = f"{out}/{sex}/{n}.webp"
    sh.save(p, "WEBP", quality=84, method=6)
    sizes[n] = os.path.getsize(p) // 1024
    t = TIMING.get(n, {"steps": 6, "cyclic": False})
    meta[n] = [len(fs), t["steps"], int(t["cyclic"])]
json.dump(meta, open(META_P, "w"), separators=(",", ":"), sort_keys=True)
print(json.dumps({"sex": sex, "sprites": len(sizes), "kb_total": sum(sizes.values()), "kb_max": max(sizes.values(), default=0)}))
