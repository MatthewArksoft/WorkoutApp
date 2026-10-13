# Blender: per-frame animation audit over every catalogue template (no rendering). Runs the exact render loop
# (rig.simulate) and flags anatomically broken or clipping frames. Needs the namespace built by qa_run.py (dn["cat"]).
# Results: <SP>/qa_anim.json  {template: {check: [[frame, value], ...]}}
import bpy, json, math, os, traceback
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

SP = r"C:/Users/MATTGR~1/AppData/Local/Temp/claude/C--Git-Source-Code-WorkoutApp/acfa5728-297b-45e3-8295-fca078799ec9/scratchpad"
OUT = SP + "/qa_anim.json"
dn = bpy.app.driver_namespace
ns = dn["cat"]
sc = bpy.data.scenes["DeskResetDemos"]; vl = sc.view_layers[0]

def rel(parent, child):
    """Child bone rotation relative to its parent, in the child's rest frame (3x3)."""
    arm = ns["arm"]; pb, cb = arm.pose.bones[parent], arm.pose.bones[child]
    rest = arm.data.bones[parent].matrix_local.inverted() @ arm.data.bones[child].matrix_local
    return (rest.inverted() @ (pb.matrix.inverted() @ cb.matrix)).to_3x3()

def swing_twist(m):
    """(swing rotation vector in the bone frame, twist degrees about the bone axis Y)."""
    q = m.to_quaternion()
    tw = Quaternion((q.w, 0, q.y, 0)); tw = tw.normalized() if tw.magnitude > 1e-6 else Quaternion()
    sw = q @ tw.inverted()
    ax, an = sw.to_axis_angle()
    if an > math.pi: an, ax = 2 * math.pi - an, -ax
    ta = tw.to_axis_angle(); t = ta[1] if ta[1] <= math.pi else ta[1] - 2 * math.pi
    return Vector(ax) * an, math.degrees(t) * (1 if ta[0].y >= 0 else -1)

HINGE = {}   # (parent, child) -> unit flexion axis in the child frame
def calibrate():
    P = ns["P"]
    ns["apply_pose"](P(T=180, armL=[0, 6, 90, 6], armR=[0, 6, 90, 6], legL=[60, 4, -30, 4], legR=[60, 4, -30, 4]))
    for s in "lr":
        for pair in (("thigh_" + s, "calf_" + s), ("upperarm_" + s, "lowerarm_" + s)):
            v, _ = swing_twist(rel(*pair)); HINGE[pair] = v.normalized()

# capsules (from joint, to joint, radius, start fraction): thighs / upper arms start mid-segment so the hip and
# shoulder attachments themselves never count as clipping
CAPS = {"torso": ("pelvis", "chest", 0.11, 0.0), "head": ("neck", "head", 0.10, 0.3)}
for s in "lr":
    CAPS.update({"uarm_" + s: ("shoulder_" + s, "elbow_" + s, 0.045, 0.45), "farm_" + s: ("elbow_" + s, "hand_" + s, 0.035, 0.0),
                 "thigh_" + s: ("hip_" + s, "knee_" + s, 0.06, 0.5), "shin_" + s: ("knee_" + s, "ankle_" + s, 0.045, 0.0)})
PAIRS = [(a, b) for a in ("farm_l", "farm_r", "uarm_l", "uarm_r") for b in ("torso", "head")] + \
        [("farm_l", "farm_r"), ("thigh_l", "thigh_r"), ("shin_l", "shin_r"), ("shin_l", "thigh_r"), ("shin_r", "thigh_l"),
         ("farm_l", "thigh_l"), ("farm_r", "thigh_r"), ("farm_l", "thigh_r"), ("farm_r", "thigh_l"),
         ("shin_l", "torso"), ("shin_r", "torso"), ("thigh_l", "torso"), ("thigh_r", "torso")]

def seg_dist(p1, q1, p2, q2):
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1.dot(d1), d2.dot(d2), d2.dot(r)
    c, b = d1.dot(r), d1.dot(d2); den = a * e - b * b
    s = min(max((b * f - c * e) / den, 0), 1) if den > 1e-9 else 0.0
    t = (b * s + f) / e if e > 1e-9 else 0.0
    if t < 0: t, s = 0.0, min(max(-c / a, 0), 1)
    elif t > 1: t, s = 1.0, min(max((b - c) / a, 0), 1)
    return ((p1 + d1 * s) - (p2 + d2 * t)).length

body = bpy.data.objects[ns["body"].name] if "body" in ns else bpy.data.objects["SuperHero_Male"]
_names = {g.index: g.name for g in body.vertex_groups}
_dom = [(_names[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else "") for v in body.data.vertices]
EXTREMITY = np.array([d.startswith(("hand_", "thumb", "index", "middle", "ring", "pinky", "foot_", "ball_")) for d in _dom])
SAMPLE = np.arange(0, len(_dom), 3)
POLYS = [f.vertices[:] for f in body.data.polygons]
LIMB_V = {l: np.array([d.startswith(pre) for d in _dom]) for l, pre in
          (("hand_l", ("hand_l", "thumb_0", "index_0", "middle_0", "ring_0", "pinky_0")), ("hand_r", ("hand_r",)),
           ("foot_l", ("foot_l", "ball_l")), ("foot_r", ("foot_r", "ball_r")))}
for _l in ("hand_l", "hand_r"):   # finger groups end in _l / _r
    LIMB_V[_l] = np.array([d == "hand_" + _l[-1] or (d.startswith(("thumb", "index", "middle", "ring", "pinky")) and d.endswith("_" + _l[-1])) for d in _dom])
DOM = np.array(_dom)

def body_points():
    ev = body.evaluated_get(vl.depsgraph); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co); ev.to_mesh_clear()
    M = np.array(ev.matrix_world)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    return co

def prop_clips(co):
    """Deepest body penetration (m) into any prop, ignoring hands/feet (they grip and stand on things) and the mat."""
    worst = (0.0, "")
    pts = co[SAMPLE][~EXTREMITY[SAMPLE]]
    for o in bpy.data.objects:
        if o.name not in ns["USED"] or o.hide_render or o.type != 'MESH' or "mat" in o.name.lower(): continue
        bb = np.array([o.matrix_world @ Vector(c) for c in o.bound_box])
        m = np.all((pts > bb.min(0) + 0.01) & (pts < bb.max(0) - 0.01), axis=1)
        if not m.any(): continue
        if not len(o.data.polygons): continue
        mw = o.matrix_world
        tree = BVHTree.FromPolygons([mw @ v.co for v in o.data.vertices], [f.vertices[:] for f in o.data.polygons])
        for p in pts[m][:400]:
            pw = Vector(p.tolist()); loc, n, _, _ = tree.find_nearest(pw)
            if loc is None: continue
            dep = -(pw - loc).dot(n)
            if dep > worst[0]: worst = (dep, o.name.replace("DR_p_", ""))
    return worst

def cable_through(co_tree):
    """Cables / bands / ropes passing through the body (beyond 10 cm from either end)."""
    worst = (0.0, "")
    btree, bmw = co_tree; binv = bmw.inverted(); bnm = binv.transposed().to_3x3()
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.name not in ns["USED"] or o.hide_render or not any(k in n for k in ("cab", "rope", "band", "strap")): continue
        z = (o.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized(); L = o.dimensions.z
        if L < 0.25: continue
        a = o.matrix_world.translation - z * L / 2
        for k in range(1, 20):
            d = L * k / 20
            if d < 0.1 or L - d < 0.1: continue
            p = a + z * d; loc, nrm, _, _ = btree.find_nearest(binv @ p)
            if loc is None: continue
            dep = -(p - bmw @ loc).dot((bnm @ nrm).normalized())
            if dep > worst[0]: worst = (dep, o.name.replace("DR_p_", ""))
    return worst

POP_J = ("hand_l", "hand_r", "elbow_l", "elbow_r", "knee_l", "knee_r", "ankle_l", "ankle_r", "head", "pelvis")
def audit_template(spec):
    F = {}
    def flag(k, i, v):
        F.setdefault(k, []).append([i, round(v, 3) if isinstance(v, float) else v])
    prevJ, prevT, steps = None, {}, {}
    for i in ns["simulate"](spec):
        J = ns["joints"]()
        # hinge joints: flexion must be about the hinge axis, never reversed
        for s in "lr":
            for pair, nm, lim in ((("thigh_" + s, "calf_" + s), "knee", 12), (("upperarm_" + s, "lowerarm_" + s), "elbow", 15)):
                v, tw = swing_twist(rel(*pair)); h = HINGE[pair]; fl = math.degrees(v.dot(h)); off = math.degrees((v - h * v.dot(h)).length)
                if fl < -lim: flag(nm + "_reversed_" + s, i, fl)
                if off > 35 and math.degrees(v.length) > 20: flag(nm + "_sideways_" + s, i, off)
                if nm == "elbow":
                    if abs(tw) > 110: flag("forearm_twist_" + s, i, tw)
                    if s in prevT and abs(tw - prevT[s]) > 70: flag("forearm_flip_" + s, i, tw - prevT[s])
                    prevT[s] = tw
            v, tw = swing_twist(rel("lowerarm_" + s, "hand_" + s))
            if math.degrees(v.length) > 95: flag("wrist_extreme_" + s, i, math.degrees(v.length))
            if abs(tw) > 70: flag("wrist_twist_" + s, i, tw)
            v, tw = swing_twist(rel("pelvis", "thigh_" + s))
            if abs(tw) > 65: flag("thigh_twist_" + s, i, tw)
            v, tw = swing_twist(rel("clavicle_" + s, "upperarm_" + s))
            if abs(tw) > 120: flag("upperarm_twist_" + s, i, tw)
        for a, b, lim in (("neck_01", "Head", 55), ("spine_03", "neck_01", 55), ("spine_01", "spine_02", 45), ("spine_02", "spine_03", 45)):
            v, tw = swing_twist(rel(a, b))
            if math.degrees(v.length) > lim: flag("bend_" + b, i, math.degrees(v.length))
            if abs(tw) > 50: flag("twist_" + b, i, tw)
        # limb-vs-limb / limb-vs-torso interpenetration (capsules)
        for a, b in PAIRS:
            A, B = CAPS[a], CAPS[b]
            a0, b0 = J[A[0]].lerp(J[A[1]], A[3]), J[B[0]].lerp(J[B[1]], B[3])
            dep = A[2] + B[2] - seg_dist(a0, J[A[1]], b0, J[B[1]])
            if dep > 0.04: flag("clip_" + a + "_" + b, i, dep)
        if prevJ:
            for j in POP_J: steps.setdefault(j, []).append((J[j] - prevJ[j]).length)
        prevJ = J
        co = body_points()
        floor = 0.012 if any(o.name.startswith("DR_p_mat") and o.name in ns["USED"] for o in bpy.data.objects) else 0.0
        k = int(np.argmin(co[:, 2]))
        if co[k, 2] < floor - 0.02: flag("below_floor", i, f"{DOM[k]} {floor - co[k, 2]:.3f}")
        for l, m in LIMB_V.items():      # a hand/foot hovering just above the floor reads as a missed contact
            z = float(co[m, 2].min()) - floor
            if 0.025 < z < 0.10: flag("hover_" + l, i, z)
        dep, who = prop_clips(co)
        if dep > 0.03: flag("into_prop", i, f"{who} {dep:.2f}")
        bt = (BVHTree.FromPolygons(co.tolist(), POLYS), Matrix.Identity(4))
        dep, who = cable_through(bt)
        if dep > 0.02: flag("cable_through_body", i, f"{who} {dep:.2f}")
    # popping: a joint's frame-to-frame step spiking well above both neighbouring steps
    for j, st in steps.items():
        n = len(st)
        for k in range(n):
            nb = max(st[(k - 1) % n], st[(k + 1) % n])
            if st[k] > 0.08 and st[k] > 2.2 * nb: flag("pop_" + j, k + 1, st[k])
    F["frames"] = i + 1
    return F

calibrate()
ONLY = dn.get("anim_only")
if not ONLY and os.path.exists(OUT): os.remove(OUT)
dn["anim_queue"] = [s for s in ns["CAT"] if not ONLY or s["name"] in ONLY]
def tick():
    q = dn["anim_queue"]
    if not q: return None
    spec = q.pop(0)
    try: r = audit_template(spec)
    except Exception: r = {"error": traceback.format_exc()[-600:]}
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    res[spec["name"]] = r; json.dump(res, open(OUT, "w"))
    return 0.02
old = dn.get("anim_tick")
if old and bpy.app.timers.is_registered(old): bpy.app.timers.unregister(old)
dn["anim_tick"] = tick
bpy.app.timers.register(tick, first_interval=0.2)
