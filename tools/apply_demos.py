# Points the app at the rendered demo sprites (demos/m|f/<template>.webp): writes the DEMO name map and the DM
# sprite metadata into index.html, removes unreferenced demo files, updates the credit.
# Usage (repo root): python tools/apply_demos.py tools/catalog_map.json
import json, os, re, sys

m = json.load(open(sys.argv[1], encoding="utf8"))
meta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite_meta.json")))
used = set(m.values())
missing = sorted(f"demos/{s}/{t}.webp" for t in used for s in "mf" if not os.path.exists(f"demos/{s}/{t}.webp"))
assert not missing, f"missing sprites: {missing[:10]}"
assert used <= set(meta), sorted(used - set(meta))

html = open("index.html", encoding="utf8").read()
new = ("const DEMO = " + json.dumps(m, ensure_ascii=False, separators=(",", ":")) + ";\n"
       "const DM = " + json.dumps({t: meta[t] for t in sorted(used)}, separators=(",", ":")) + "; // template -> [frames, frames per key, cyclic]")
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
        keep = f.endswith(".webp") and p.split("/")[-2] in ("m", "f") and f[:-5] in used
        if not keep: os.remove(p); removed += 1
print(json.dumps({"names": len(m), "templates": len(used), "removed_files": removed}))
