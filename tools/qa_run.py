# Blender: (re)load the demo pipeline and queue a QA preview pass over every catalogue template (or ONLY=[names]).
# Results: <SP>/qa_results.json (audit + joint error per key), previews: <SP>/blender/cprev/<name>_NNN.png
import bpy, json, os, glob, traceback
SP = r"C:/Users/MATTGR~1/AppData/Local/Temp/claude/C--Git-Source-Code-WorkoutApp/acfa5728-297b-45e3-8295-fca078799ec9/scratchpad"
TOOLS = r"C:/Git Source Code/WorkoutApp/tools/"
dn = bpy.app.driver_namespace
old = dn.get("qa_tick")
if old and bpy.app.timers.is_registered(old): bpy.app.timers.unregister(old)
for o in [o for o in bpy.data.objects if o.name.startswith("DR_p_")]: bpy.data.objects.remove(o, do_unlink=True)
ns = {}
for f in ("rig.py", "exercises.py", "retarget.py", "machines.py"):
    exec(open(TOOLS + f, encoding="utf8").read(), ns)
ns["load_poses"](SP + "/poses.json"); ns["load_poses"](SP + "/poses2.json")
exec(open(TOOLS + "catalog.py", encoding="utf8").read(), ns)
ns["set_character"](dn.get("sex", "m"))
ns["setup_ik"](); ns["calibrate_hands"](); ns["calibrate_bends"](); ns["calibrate_head"]()
OUT = SP + "/blender/cprev"; RES = SP + "/qa_results.json"; os.makedirs(OUT, exist_ok=True)
ONLY = dn.get("qa_only")
if not ONLY and os.path.exists(RES): os.remove(RES)
sc = bpy.data.scenes["DeskResetDemos"]; sc.render.resolution_x, sc.render.resolution_y = 300, 200; sc.eevee.taa_render_samples = 8

def qa_one(spec):
    n = spec["name"]; r = {}
    try:
        r.update(ns["audit"](spec, samples=3))
        errs = []
        for P in spec["keys"]:
            if "_ref" in P and not any(k.startswith("fk_") for k in P) and not spec.get("stance"):
                ns["place"](P, P.get("anchor", spec.get("anchor", {})), None)
                errs.append(ns["joint_error"](P["_R"], P["_ref"])[0])
        r["joint_err"] = errs
        for f in glob.glob(f"{OUT}/{n}_[0-9][0-9][0-9].png"): os.remove(f)
        ns["render_anim"](spec, OUT, preview=True)
    except Exception:
        r["error"] = traceback.format_exc()[-500:]
    res = json.load(open(RES)) if os.path.exists(RES) else {}
    res[n] = r; json.dump(res, open(RES, "w"), indent=0)

ns["qa_one"] = qa_one
dn["cat"] = ns
dn["qa_queue"] = [s for s in ns["CAT"] if not ONLY or s["name"] in ONLY]
def tick():
    q = dn["qa_queue"]
    if not q: return None
    dn["cat"]["qa_one"](q.pop(0)); return 0.02
dn["qa_tick"] = tick
bpy.app.timers.register(tick, first_interval=0.2)
