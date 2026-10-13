# Blender: full-quality render of every catalogue template for one character (dn["sex"] = "m" | "f"), 480x320,
# EEVEE 24 samples / 3 shadow rays, frames + skin masks: <SP>/blender/full_<sex>/<name>/<name>_NNN.png + mask_NNN.png.
# Queued on a timer so the MCP connection never times out. dn["final_resume"] = True keeps finished templates
# (a template counts as finished when every frame has its mask) - use it after a crash.
# Needs the namespace from qa_run.py / test_render.py for the same character (dn["cat"]).
import bpy, os, glob, time, traceback, shutil
SP = r"C:/Users/MATTGR~1/AppData/Local/Temp/claude/C--Git-Source-Code-WorkoutApp/acfa5728-297b-45e3-8295-fca078799ec9/scratchpad"
dn = bpy.app.driver_namespace
ns = dn["cat"]
base = SP + "/blender/full_" + dn.get("sex", "m")
if os.path.isdir(base) and not dn.get("final_resume"): shutil.rmtree(base)
os.makedirs(base, exist_ok=True)
sc = bpy.data.scenes["DeskResetDemos"]; sc.render.resolution_x, sc.render.resolution_y = 480, 320
sc.eevee.taa_render_samples = 24; sc.eevee.shadow_ray_count = 3     # clean soft shadows

def finished(n):
    fs = glob.glob(f"{base}/{n}/{n}_[0-9][0-9][0-9].png")
    return fs and len(fs) == len(glob.glob(f"{base}/{n}/mask_[0-9][0-9][0-9].png"))
dn["final_queue"] = [s for s in ns["CAT"] if not finished(s["name"])]
dn["final_log"] = {"started": time.time(), "done": [], "errs": {}}
def tick():
    q = dn["final_queue"]
    if not q:
        dn["final_log"]["finished"] = time.time(); return None
    spec = q.pop(0); out = base + "/" + spec["name"]
    shutil.rmtree(out, ignore_errors=True)
    try:
        dn["cat"]["render_anim"](spec, out); dn["final_log"]["done"].append(spec["name"])
    except Exception:
        dn["final_log"]["errs"][spec["name"]] = traceback.format_exc()[-400:]
    return 0.02
old = dn.get("final_tick")
if old and bpy.app.timers.is_registered(old): bpy.app.timers.unregister(old)
dn["final_tick"] = tick
bpy.app.timers.register(tick, first_interval=0.2)
