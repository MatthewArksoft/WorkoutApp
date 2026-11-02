# Blender headless: renders exercise demo templates for one character, synchronously (no UI/timers/MCP needed).
# Usage: blender.exe -b <DeskResetDemos.blend> --python tools/render_headless.py -- <sex m|f> <outdir> [--preview|--audit] [name ...]
#   --audit: no rendering; runs tools/qa_anim.py (per-frame anatomy/clipping audit) and writes <outdir>/qa_anim.json
#   DR_SP env var: scratchpad with poses.json/poses2.json (default: the pipeline's working scratchpad).
#   DR_TOOLS env var: tools/ dir to load (default: this script's own directory, i.e. wherever it's invoked from).
# Namespace loaded exactly like qa_run.py (rig/exercises/retarget/machines/catalog). Writes <outdir>/<name>/
# <name>_NNN.png + mask_NNN.png (skin AOV) + fig_NNN.png (figure AOV, make_sprites.py turns it into alpha).
# A catalogue template with still=True (hold()) renders exactly 1 frame at full quality. Keeps going on errors.
import bpy, os, sys, time, traceback

SP = os.environ.get("DR_SP", r"C:/Users/MATTGR~1/AppData/Local/Temp/claude/C--Git-Source-Code-WorkoutApp/acfa5728-297b-45e3-8295-fca078799ec9/scratchpad")
TOOLS = os.environ.get("DR_TOOLS", os.path.dirname(os.path.abspath(__file__)))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
preview, audit = "--preview" in argv, "--audit" in argv
argv = [a for a in argv if a not in ("--preview", "--audit")]
sex = argv[0] if argv else "m"
OUT = argv[1] if len(argv) > 1 else SP + "/demo"
only = argv[2:]

exec(open(TOOLS + "/setup_scene.py", encoding="utf8").read())   # idempotent: adds the 'fig' AOV + compositor slot if missing
ns = {}
for f in ("rig.py", "exercises.py", "retarget.py", "machines.py"):
    exec(open(TOOLS + "/" + f, encoding="utf8").read(), ns)
ns["load_poses"](SP + "/poses.json"); ns["load_poses"](SP + "/poses2.json")
exec(open(TOOLS + "/catalog.py", encoding="utf8").read(), ns)
ns["set_character"](sex)
ns["setup_ik"](); ns["calibrate_hands"](); ns["calibrate_bends"](); ns["calibrate_head"]()

if audit:
    dn = bpy.app.driver_namespace; dn["cat"] = ns; dn["anim_only"] = only; dn["anim_out"] = OUT + "/qa_anim.json"
    os.makedirs(OUT, exist_ok=True); exec(open(TOOLS + "/qa_anim.py", encoding="utf8").read(), {"__name__": "qa_anim"})
    print("audit ->", dn["anim_out"]); sys.exit(0)
sc = bpy.data.scenes["DeskResetDemos"]
sc.render.resolution_x, sc.render.resolution_y = (300, 200) if preview else (480, 320)
sc.eevee.taa_render_samples = 8 if preview else 24
if not preview: sc.eevee.shadow_ray_count = 3   # clean soft shadows (final_render.py quality)

todo = [s for s in ns["CAT"] if not only or s["name"] in only]
print(f"rendering {len(todo)} template(s) for '{sex}' -> {OUT}")
for spec in todo:
    name, t0 = spec["name"], time.time()
    try:
        still = spec.get("still", False)
        files = ns["render_anim"](spec, f"{OUT}/{name}", preview=still, limit=1 if still else None)
        dt = time.time() - t0
        print(f"{name}: {dt:.2f}s, {len(files)} frame(s){' [still]' if still else ''} ({dt/len(files):.2f}s/frame)")
    except Exception:
        print(f"{name}: ERROR\n{traceback.format_exc()[-800:]}")
print("done")
