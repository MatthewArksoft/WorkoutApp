# Points the app at the rendered demo sprites (demos/m|f/<template>.webp animated, or .png still): writes the DEMO
# name map and the DM sprite metadata into index.html, removes unreferenced demo files, updates the credit.
# Usage (repo root): python tools/apply_demos.py tools/catalog_map.json
import hashlib, json, os, re, sys

m = json.load(open(sys.argv[1], encoding="utf8"))
_app = re.sub(r"const DEMO = \{.*?\};\nconst DM = \{.*?\};", "", open("index.html", encoding="utf8").read(), count=1, flags=re.S)
m = {k: v for k, v in m.items() if json.dumps(k, ensure_ascii=False) in _app}   # only exercises the app actually lists (home program)
meta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite_meta.json")))
used = set(m.values())
ext = lambda t: "png" if meta.get(t, [0])[0] == 1 else "webp"   # DM[t][0] == 1 frame -> still PNG, else animated WebP
missing = sorted(f"demos/{s}/{t}.{ext(t)}" for t in used for s in "mf" if not os.path.exists(f"demos/{s}/{t}.{ext(t)}"))
assert not missing, f"missing sprites: {missing[:10]}"
assert used <= set(meta), sorted(used - set(meta))

def sprite_hash(t):   # first 8 hex chars of sha1 over both sexes' sprite bytes: changes whenever either is re-rendered
    h = hashlib.sha1()
    for s in "mf": h.update(open(f"demos/{s}/{t}.{ext(t)}", "rb").read())
    return h.hexdigest()[:8]

html = open("index.html", encoding="utf8").read()
new = ("const DEMO = " + json.dumps(m, ensure_ascii=False, separators=(",", ":")) + ";\n"
       "const DM = " + json.dumps({t: meta[t] + [sprite_hash(t)] for t in sorted(used)}, separators=(",", ":")) + "; // template -> [frames, frames per key, cyclic, sprite hash]")
html, n = re.subn(r"const DEMO = \{.*?\};(\nconst DM = \{.*?\};[^\n]*)?", lambda _: new, html, count=1, flags=re.S)
assert n == 1
html = re.sub(r'<p class="note">Exercise (photos|animations)[^\n]*</p>',
              '<p class="note">Exercise animations: Quaternius Universal Base Characters (CC0), posed from '
              '<a href="https://github.com/yuhonas/free-exercise-db" target="_blank" rel="noopener">free-exercise-db</a> reference photos (public domain).</p>',
              html, count=1)
open("index.html", "w", encoding="utf8").write(html)

removed = 0
for d, _, fs in os.walk("demos"):
    for f in fs:
        p = os.path.join(d, f).replace("\\", "/")
        stem, _, suf = f.rpartition(".")
        keep = p.split("/")[-2] in ("m", "f") and stem in used and suf == ext(stem)   # also drops a template's old .webp once it became a still .png
        if not keep: os.remove(p); removed += 1
print(json.dumps({"names": len(m), "templates": len(used), "removed_files": removed}))
