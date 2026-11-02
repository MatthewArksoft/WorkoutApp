# Packs rendered frames into one transparent sprite per template and character:
#   top half = frames (<=4 columns), bottom half = matching skin masks (white = skin, opaque). The app tints skin
#   with them and draws the sheet straight onto its own --surface-2 background.
#   Alpha keeps the soft floor shadow (figure cut out of the white render via the 'fig' AOV; unshadowed floor/world
#   -> fully transparent, shadow -> translucent black, figure -> opaque). A template with exactly 1 rendered frame
#   (a catalogue `still=True` hold()) is packed the same way and saved as a lossless PNG instead of an animated WebP.
# Usage: python tools/make_sprites.py <frames root> <sex m|f> <out demos dir> [name ...]
# Frames: <root>/<name>/<name>_NNN.png, masks: <root>/<name>/mask_NNN.png, figure AOV: <root>/<name>/fig_NNN.png.
import glob, json, os, sys
import numpy as np
from PIL import Image

root, sex, out = sys.argv[1], sys.argv[2], sys.argv[3]
names = sys.argv[4:] or sorted(os.listdir(root))
HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = json.load(open(os.path.join(HERE, "catalog_timing.json")))
META_P = os.path.join(HERE, "sprite_meta.json")
meta = json.load(open(META_P)) if os.path.exists(META_P) else {}
W, H, COLS = 480, 320, 4
WHITE = 0.999    # measured floor/world luminance with no shadow (EEVEE Standard view transform, final_render.py settings)
EPS = 1e-4
os.makedirs(f"{out}/{sex}", exist_ok=True)
sizes = {}

def cutout(frame_png, fig_png):
    """RGBA frame: figure (+ equipment) opaque, soft floor shadow kept as alpha over black, rest transparent.
    a = fig AOV (1 on figure, 0 on floor/world); B = background estimate; s = shadow alpha from how much darker
    than a bare-white floor B is; unpremultiply so the figure's own colour has no background bleed at its edge."""
    P = np.asarray(Image.open(frame_png).convert("RGB"), dtype=np.float32) / 255
    a = np.asarray(Image.open(fig_png).convert("L"), dtype=np.float32) / 255
    a3 = a[..., None]
    B = np.minimum(1.0, P / np.clip(1 - a3, EPS, 1))
    lum = B[..., 0] * 0.2126 + B[..., 1] * 0.7152 + B[..., 2] * 0.0722
    s = np.clip(1 - lum / WHITE, 0, 1)
    alpha = a + (1 - a) * s
    color = np.clip((P - (1 - a3) * B) / np.clip(alpha, EPS, None)[..., None], 0, 1)
    rgba = np.concatenate([color, alpha[..., None]], axis=-1)
    return Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").resize((W, H), Image.LANCZOS)

for n in names:
    fs = sorted(glob.glob(f"{root}/{n}/{n}_[0-9][0-9][0-9].png"))
    ms = sorted(glob.glob(f"{root}/{n}/mask_[0-9][0-9][0-9].png"))
    gs = sorted(glob.glob(f"{root}/{n}/fig_[0-9][0-9][0-9].png"))
    assert fs and len(fs) == len(ms) == len(gs), (n, len(fs), len(ms), len(gs))
    still = len(fs) == 1
    cols = min(COLS, len(fs)); rows = -(-len(fs) // cols)
    sh = Image.new("RGBA", (W * cols, H * rows * 2), (0, 0, 0, 0))
    for i, (f, m, g) in enumerate(zip(fs, ms, gs)):
        x, y = (i % cols) * W, (i // cols) * H
        sh.paste(cutout(f, g), (x, y))
        sh.paste(Image.open(m).convert("L").resize((W, H), Image.LANCZOS).convert("RGBA"), (x, y + H * rows))
    if still:
        p = f"{out}/{sex}/{n}.png"; sh.save(p, "PNG", optimize=True)
        meta[n] = [1, 1, 0]
    else:
        p = f"{out}/{sex}/{n}.webp"; sh.save(p, "WEBP", quality=80, method=6, alpha_quality=70)
        t = TIMING.get(n, {"steps": 6, "cyclic": False})
        meta[n] = [len(fs), t["steps"], int(t["cyclic"])]
    sizes[n] = os.path.getsize(p) // 1024

json.dump(meta, open(META_P, "w"), separators=(",", ":"), sort_keys=True)
print(json.dumps({"sex": sex, "sprites": len(sizes), "kb_total": sum(sizes.values()), "kb_max": max(sizes.values(), default=0)}))
