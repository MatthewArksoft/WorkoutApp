# Blender script: poses the Quaternius Universal Base Character (CC0) and renders exercise demo frames.
# Loaded inside Blender via MCP:  exec(open(r".../tools/rig.py").read(), ns)
# Works only in scene "DeskResetDemos" (character collection DR_character, props prefixed DR_p_).
import bpy, math, os
from mathutils import Vector, Matrix

sc = bpy.data.scenes["DeskResetDemos"]
vl = sc.view_layers[0]
arm = bpy.data.objects["Armature"]
body = bpy.data.objects["SuperHero_Male"]
bpy.data.objects["Eyebrows"].hide_render = True   # not skinned to the rig
CHARS = {"m": ("Armature", "SuperHero_Male", "DR_character"), "f": ("Armature_F", "SuperHero_Female", "DR_character_f")}

def set_character(sex):
    """Point every posing / render function at the male or female character (same rig) and hide the other."""
    global arm, body
    for k, (_, _, col) in CHARS.items():
        c = bpy.data.collections.get(col)
        if c: c.hide_render = c.hide_viewport = k != sex
    arm, body = bpy.data.objects[CHARS[sex][0]], bpy.data.objects[CHARS[sex][1]]

# ---------- directions ----------
def d(p, l=0.0, side=0):
    """Pitch p: 0 = straight down, 90 = forward (+X), 180 = up, 270/-90 = back. l = degrees out to `side` (+Y left / -Y right)."""
    p, l = math.radians(p), math.radians(l)
    return Vector((math.sin(p) * math.cos(l), side * math.sin(l), -math.cos(p) * math.cos(l)))

SIDE = {"l": 1, "r": -1}
FOOT_FLAT = 64          # foot pitch with the sole flat on the floor (rest geometry: 26 deg ankle->ball slope)
FINGERS = ["index", "middle", "ring", "pinky"]
HAND_MODE = {"l": "relaxed", "r": "relaxed"}
CURL = {"relaxed": (18, 22, 12, 10), "grip": (72, 88, 62, 38), "flat": (0, 0, 0, 0)}   # knuckle, mid, tip, thumb (deg)   # character faces +X; its left is +Y (away from camera)

# ---------- posing ----------
def reset():
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    vl.update()

def _apply(pb, R):
    M = pb.matrix.copy(); h = M.translation.copy()
    pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    pb.scale = (1, 1, 1)   # matrix decomposition drifts scale; keep bones rigid
    vl.update()

def _rinv():
    return arm.matrix_world.to_3x3().inverted()

def aim(name, dw):
    pb = arm.pose.bones[name]
    cur = (pb.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
    _apply(pb, cur.rotation_difference((_rinv() @ dw).normalized()).to_matrix().to_4x4())

def tilt(name, axis_world, deg):
    _apply(arm.pose.bones[name], Matrix.Rotation(math.radians(deg), 4, (_rinv() @ Vector(axis_world)).normalized()))

def bone_dir(name):
    pb = arm.pose.bones[name]
    return (arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()

REST_BEND = {}   # bone -> local vector: direction the child segment bends toward (elbow: forward, knee: backward) at rest

def calibrate_bends():
    reset()
    Rarm = arm.matrix_world.to_3x3()
    for s in "lr":
        for bone, w in (("upperarm_" + s, Vector((1, 0, 0))), ("thigh_" + s, Vector((-1, 0, 0)))):
            M = Rarm @ arm.pose.bones[bone].matrix.to_3x3()
            REST_BEND[bone] = M.inverted() @ w
    return {k: [round(c, 2) for c in v] for k, v in REST_BEND.items()}

def roll_to(name, want, max_deg=None):
    """Roll a bone about its own axis so its rest bend direction points toward `want` (perpendicular part).
    max_deg: skip larger corrections (a requested hyperextension must not spin the limb around)."""
    ax = bone_dir(name)
    cur = arm.matrix_world.to_3x3() @ arm.pose.bones[name].matrix.to_3x3() @ REST_BEND[name]
    cur = cur - ax * cur.dot(ax); want = want - ax * want.dot(ax)
    if cur.length < 1e-4 or want.length < 1e-4: return
    cur.normalize(); want.normalize()
    deg = math.degrees(math.atan2(ax.dot(cur.cross(want)), cur.dot(want)))
    if max_deg is None or abs(deg) <= max_deg: tilt(name, tuple(ax), deg)

def hinge(upper, lower_dir, straight_hint=None):
    """Elbows and knees are hinges: roll the upper bone so the joint bends only toward the lower segment.
    Nearly straight limbs take the roll from straight_hint (e.g. knee faces where the toes point)."""
    ud = bone_dir(upper); bend = lower_dir - ud * lower_dir.dot(ud)
    lim = None if upper.startswith("upperarm") else 100     # the humerus rotates freely; a femur never spins round
    if bend.length > 0.12: roll_to(upper, bend, lim)
    elif straight_hint is not None: roll_to(upper, straight_hint, lim)

def bent(upper, lower_dir, deg=4.0):
    """A dead-straight elbow/knee gets a few degrees of natural flexion toward its hinge side, so contact IK
    always bends it the right way (a perfectly straight chain lets the solver flip it backwards)."""
    ud = bone_dir(upper)
    if lower_dir.angle(ud) >= math.radians(deg): return lower_dir
    b = arm.matrix_world.to_3x3() @ arm.pose.bones[upper].matrix.to_3x3() @ REST_BEND[upper]
    b = b - ud * b.dot(ud)
    if b.length < 1e-4: return lower_dir
    a = math.radians(deg); return (ud * math.cos(a) + b.normalized() * math.sin(a)).normalized()

def apply_pose(P):
    """T trunk pitch (180 upright, 90 prone head +X, 270 supine head -X). roll: trunk roll about its axis.
    S upper-spine pitch (S1/S2/S3 override individual spine bones), twist: upper-body rotation about trunk.
    N neck pitch, H head pitch. armL/armR [upper p,l, fore p,l]; legL/legR [thigh p,l, shin p,l, foot p?]. clavR/clavL lift deg."""
    ik_off(); reset()
    T = P["T"]; S = P.get("S", T)
    tilt("pelvis", (0, 1, 0), 180 - T)   # +Y rotation tips the body's up-axis toward +X
    if P.get("roll"): tilt("pelvis", tuple(d(T)), P["roll"])
    aim("spine_01", d(P.get("S1", (T + S) / 2))); aim("spine_02", d(P.get("S2", S))); aim("spine_03", d(P.get("S3", S)))
    if P.get("twist"): tilt("spine_02", tuple(d(P.get("S2", S))), P["twist"])
    H = P.get("H", P.get("S3", S))
    aim("neck_01", d(P.get("N", H))); aim("Head", d(H))
    for s in "lr":
        sg = SIDE[s]
        if P.get("clav" + s.upper()): tilt("clavicle_" + s, tuple(d(P.get("S3", S))), sg * P["clav" + s.upper()])
        a = P["arm" + s.upper()]
        # scapular elevation: shoulders rise as the arm goes overhead (0 at 70 deg from the trunk axis, ~20 deg fully overhead)
        up = d(P.get("S3", S)); ang = math.degrees(up.angle(d(a[0], a[1], sg)))
        elev = P.get("elev" + s.upper(), max(0.0, (70 - ang) / 70) * 20)
        if elev: tilt("clavicle_" + s, tuple(d(P.get("S3", S) - 90)), sg * elev)
        aim("upperarm_" + s, d(a[0], a[1], sg)); hinge("upperarm_" + s, d(a[2], a[3], sg)); aim("lowerarm_" + s, bent("upperarm_" + s, d(a[2], a[3], sg)))
        mode = P.get("hand" + s.upper(), P.get("hands", "relaxed")); HAND_MODE[s] = mode
        fdir = d(a[2], a[3], sg)
        hdir = d(P.get("handdir", 92), 12, sg) if mode == "flat" else fdir   # flat: fingers forward along the surface
        S3 = P.get("S3", S)
        set_palm(s, fdir, hdir, palm_target(P.get("palm" + s.upper(), P.get("palm")), s, sg, mode, S3, fdir, hdir))
        aim("hand_" + s, hdir)
        curl(s, CURL[mode], mode)
        g = P["leg" + s.upper()]
        # foot bone runs ankle -> ball, sloping 26 deg down when the sole is flat (pitch 64); planted shins are near vertical
        fp = g[4] if len(g) > 4 else (FOOT_FLAT if -50 <= g[2] <= 50 else g[2] + 90)
        fl = g[5] if len(g) > 5 else 0
        aim("thigh_" + s, d(g[0], g[1], sg)); hinge("thigh_" + s, d(g[2], g[3], sg), -d(90 if -15 <= fp <= 110 else fp, fl, sg))
        aim("calf_" + s, bent("thigh_" + s, d(g[2], g[3], sg)))
        aim("foot_" + s, d(fp, fl, sg))
        aim("ball_" + s, d(90 if -15 <= fp <= 110 else fp, fl, sg))   # toes lie flat when the foot points forward/down

# ---------- IK (planted hands/feet) ----------
# Each limb gets a 2-bone IK constraint (upper+lower) on its lower bone and a target at the wrist/ankle.
# FK sets the intent (bend plane, body position); IK only corrects contacts. Feet also track a toe target so they stay flat.
EFF = {"hand_l": "lowerarm_l", "hand_r": "lowerarm_r", "foot_l": "calf_l", "foot_r": "calf_r"}

def _empty(name):
    o = bpy.data.objects.get(name)
    if not o:
        o = bpy.data.objects.new(name, None); sc.collection.objects.link(o)
    return o

def setup_ik():
    for limb, bone in EFF.items():
        pb = arm.pose.bones[bone]
        ik = pb.constraints.get("DR_IK") or pb.constraints.new('IK'); ik.name = "DR_IK"
        ik.target = _empty("DR_t_" + limb); ik.pole_target = None
        ik.chain_count = 2; ik.use_tail = True; ik.use_stretch = False; ik.influence = 0.0
        if limb.startswith("foot"):
            f = arm.pose.bones["foot_" + limb[-1]]
            dt = f.constraints.get("DR_DT") or f.constraints.new('DAMPED_TRACK'); dt.name = "DR_DT"
            dt.target = _empty("DR_toe_" + limb); dt.track_axis = 'TRACK_Y'; dt.influence = 0.0

def ik_off():
    for limb, bone in EFF.items():
        c = arm.pose.bones[bone].constraints.get("DR_IK")
        if c: c.influence = 0.0
        if limb.startswith("foot"):
            c = arm.pose.bones["foot_" + limb[-1]].constraints.get("DR_DT")
            if c: c.influence = 0.0

def limb_state(limb, J, fwd):
    """Tip (wrist/ankle), pole and toe for a limb from the current FK pose."""
    s = limb[-1]
    root, mid = (J["shoulder_" + s], J["elbow_" + s]) if limb.startswith("hand") else (J["hip_" + s], J["knee_" + s])
    tip = jw(EFF[limb], True)
    bend = mid - (root + tip) / 2
    if bend.length < 0.02:   # nearly straight: knees point forward, elbows back
        bend = fwd.copy() if limb.startswith("foot") else -fwd
    return {"tip": tip.copy(), "pole": mid + bend.normalized() * 0.6, "toe": J["toe_" + s].copy() if limb.startswith("foot") else None,
            "seg": (tip - mid).normalized()}

def ik_on(limb, tip, pole, toe=None):
    _empty("DR_t_" + limb).location = tip; _empty("DR_pole_" + limb).location = pole
    arm.pose.bones[EFF[limb]].constraints["DR_IK"].influence = 1.0
    if toe is not None:
        _empty("DR_toe_" + limb).location = toe
        arm.pose.bones["foot_" + limb[-1]].constraints["DR_DT"].influence = 1.0

def _mid(limb):
    return jw("calf_" + limb[-1]) if limb.startswith("foot") else jw("lowerarm_" + limb[-1])

def calibrate_poles():
    """Pick each limb's pole_angle so IK reproduces the FK elbow/knee (the right value is rig-specific)."""
    bent = {"T": 160, "armL": [-40, 20, 80, 10], "armR": [-40, 20, 80, 10], "legL": [70, 8, -30, 6], "legR": [70, 8, -30, 6]}
    out = {}
    for limb in EFF:
        apply_pose(bent); arm.location = (0, 0, 0); vl.update()
        st = limb_state(limb, joints(), d(70)); mid0 = _mid(limb).copy()
        ik = arm.pose.bones[EFF[limb]].constraints["DR_IK"]
        best = None
        for a in list(range(-180, 180, 10)):
            ik.pole_angle = math.radians(a); ik_on(limb, st["tip"], st["pole"]); vl.update()
            e = (_mid(limb) - mid0).length
            if best is None or e < best[1]: best = (a, e)
        for a in [best[0] + k for k in range(-9, 10)]:
            ik.pole_angle = math.radians(a); vl.update()
            e = (_mid(limb) - mid0).length
            if e < best[1]: best = (a, e)
        ik.pole_angle = math.radians(best[0]); ik.influence = 0.0
        out[limb] = (best[0], round(best[1] * 100, 2))
    ik_off(); vl.update()
    return out

def body_frame(J):
    up = (J["neck"] - J["pelvis"]).normalized()
    left = (J["shoulder_l"] - J["shoulder_r"]).normalized()
    fwd = left.cross(up).normalized()
    return fwd, left, up

def reach_targets(R, J):
    """R = {limb: (joint, (forward, left, up) metres in the body frame)} or (joint, (x, y, z), "world") for world offsets"""
    out = {}
    if R:
        fwd, left, up = body_frame(J)
        for limb, spec_ in R.items():
            jn, (a, b, c) = spec_[0], spec_[1]
            out[limb] = J[jn] + (Vector((a, b, c)) if len(spec_) > 2 and spec_[2] == "world" else fwd * a + left * b + up * c)
    return out

def reach_lerp(spec, keys, i, t, J):
    ra = keys[i].get("reach", spec.get("reach")); rb = keys[(i + 1) % len(keys)].get("reach", spec.get("reach"))
    A, B = reach_targets(ra, J), reach_targets(rb, J)
    return {l: A[l].lerp(B.get(l, A[l]), t) for l in A}

def drive(spec, keys, states, i, t, ctx):
    """Driven contacts: spec["slide"] = {limb: z} keeps a hand/foot on a line at height z (ab wheel);
    spec["track"](ctx) -> {limb: (tip, toe)} for scripted paths (pedals, moving handles)."""
    out = {}
    for l, z in (spec.get("slide") or {}).items():
        tip = states[i][l]["tip"].lerp(states[(i + 1) % len(keys)][l]["tip"], t); tip.z = z
        out[l] = (tip, None)
    if spec.get("rear_foot_z") is not None:                       # rear foot up on a bench (RFESS / couch bridges)
        back = min(("foot_l", "foot_r"), key=lambda l: states[0][l]["tip"].x)
        tip = states[0][back]["tip"].copy(); tip.z = spec["rear_foot_z"]; tip.x += spec.get("rear_foot_dx", 0.0); out[back] = (tip, None)
    if spec.get("feet_z") is not None:                            # both feet up on a raised surface
        for l in ("foot_l", "foot_r"):
            tip = states[0][l]["tip"].copy(); dz = spec["feet_z"] - tip.z; tip.z = spec["feet_z"]
            out[l] = (tip, states[0][l]["toe"] + Vector((0, 0, dz)))
    if spec.get("track"): out.update(spec["track"](ctx))
    return out

_LIMB_IDX = {}
def limb_low(l):
    """Lowest mesh point (world z) of a hand (incl. fingers) or foot (incl. toes)."""
    key = (body.name, l)
    if key not in _LIMB_IDX:
        names = {g.index: g.name for g in body.vertex_groups}; sd = "_" + l[-1]
        pre = ("foot", "ball") if l.startswith("foot") else ("hand", "thumb", "index", "middle", "ring", "pinky")
        _LIMB_IDX[key] = [v.index for v in body.data.vertices if v.groups and
                          names[max(v.groups, key=lambda g: g.weight).group].startswith(pre) and names[max(v.groups, key=lambda g: g.weight).group].endswith(sd)]
    co = body_coords()
    return float(co[_LIMB_IDX[key], 2].min())

def support_z():
    """Top of whatever the body rests on at floor level: the exercise mat if one is out, else the floor."""
    return 0.012 if any(n.startswith("DR_p_mat") for n in USED) else 0.0

def _plant(spec, keys, locs):
    fwd = d(keys[0]["T"] - 90) if keys[0]["T"] != 180 else Vector((1, 0, 0))
    states, lows = [], []
    for i, P in enumerate(keys):
        apply_pose(P); arm.location = locs[i]; vl.update()
        Jk = joints(); states.append({l: limb_state(l, Jk, fwd) for l in EFF})
        lows.append({l: limb_low(l) for l in EFF})
    def contact(l):
        tips = [st[l]["tip"] for st in states]
        still = max((t - tips[0]).length for t in tips) < 0.07
        zs = [t.z for t in tips]
        xy = max((t - tips[0]).xy.length for t in tips)
        on_floor = l.startswith("foot") and xy < 0.3 and ((max(zs) < 0.15 and max(zs) - min(zs) < 0.05) or      # sole down
                                                         max(lw[l] for lw in lows) - support_z() < 0.12)     # toes down (push-up, plank)
        flat_hand = l.startswith("hand") and all(k.get("hand" + l[-1].upper(), k.get("hands")) == "flat" for k in keys) \
            and max(zs) < 0.35 and max((t - tips[0]).xy.length for t in tips) < 0.3
        return still or on_floor or flat_hand
    driven = set(spec.get("reach", {})) | set(spec.get("slide", {})) | set(spec.get("driven", []))
    if spec.get("feet_z") is not None: driven |= {"foot_l", "foot_r"}
    for k in keys: driven |= set(k.get("reach", {}))
    plant = set(spec.get("plant", [l for l in EFF if contact(l)])) - set(spec.get("free", [])) - driven
    # pin at the first key's contact point (that is where anchors/props were placed)
    pins, fz = {}, support_z()
    for l in plant:
        tip = states[0][l]["tip"].copy(); toe = states[0][l]["toe"].copy() if l.startswith("foot") else None
        flat = l.startswith("foot") or keys[0].get("hand" + l[-1].upper(), keys[0].get("hands")) == "flat"
        gap = lows[0][l] - fz
        if flat and -0.04 < gap < (0.12 if l.startswith("foot") else 0.25):   # sole / palm resting on the floor: touch it exactly
            if toe is not None and states[0][l]["seg"].z > -0.6 and tip.z - toe.z > 0.07:   # shin far from vertical, foot pointing down: on the toes
                toe.z -= gap            # on the toes (plank, push-up): tip the foot, never pull a straight leg into a bend
            else:
                tip.z -= gap
                if toe is not None: toe.z -= gap
        pins[l] = (tip, toe)
    return states, pins

def capture():
    """The pose a key resolved to (whatever drove it: angles, landmarks, IK-free): every bone's local transform."""
    return {"_hand": dict(HAND_MODE), **{pb.name: (pb.matrix_basis.to_quaternion(), pb.matrix_basis.to_translation()) for pb in arm.pose.bones}}

def blend(A, B, t):
    """In-between pose: shortest-arc slerp of each bone's local rotation between two captured keys.
    Continuous by construction - no parameter can snap half-way between keys."""
    ik_off()
    for pb in arm.pose.bones:
        qa, la = A[pb.name]; qb, lb = B[pb.name]
        if qa.dot(qb) < 0: qb = -qb
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = qa.slerp(qb, t); pb.location = la.lerp(lb, t); pb.scale = (1, 1, 1)
    HAND_MODE.update(A["_hand"] if t < 0.5 else B["_hand"])
    vl.update()

def curl(s, c, mode=None):
    """Finger flexion about each finger bone's local X (toward the palm). Thumb: calibrated pose per mode (calibrate_thumbs)."""
    k, m, t, th = c
    for f in FINGERS:
        for i, ang in ((1, k), (2, m), (3, t)):
            pb = arm.pose.bones[f"{f}_0{i}_{s}"]
            pb.rotation_mode = 'XYZ'; pb.rotation_euler = (math.radians(ang) * CURL_SIGN[s], 0, 0)
    tp = THUMB.get((s, mode), (0, 0, 0, 0))
    for i, k_ in ((1, None), (2, 1.0), (3, 0.6)):
        pb = arm.pose.bones[f"thumb_0{i}_{s}"]; pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (math.radians(tp[0]), 0, math.radians(tp[1])) if i == 1 else (math.radians(tp[2] * k_), 0, math.radians(tp[3] * k_))
    vl.update()

CURL_SIGN = {"l": 1, "r": 1}   # set by calibrate_curl()

def calibrate_curl():
    """Pick the rotation sign that moves fingertips toward the palm (palm normal = hand bone local +X in this rig)."""
    out = {}
    for s in "lr":
        reset(); vl.update()
        tip0 = jw(f"middle_03_{s}", True); palm = palm_world(s)
        best = None
        for sign in (1, -1):
            CURL_SIGN[s] = sign; curl(s, (60, 60, 40, 0))
            dz = (jw(f"middle_03_{s}", True) - tip0).dot(palm)
            if best is None or dz > best[1]: best = (sign, dz)
        CURL_SIGN[s] = best[0]; out[s] = best
        curl(s, (0, 0, 0, 0))
    return out

THUMB = {}                      # (side, mode) -> (thumb_01 x, z, thumb_02 x, z) degrees, from calibrate_thumbs()
PALM_AXIS = {"l": 1, "r": 1}    # sign of the hand bone's local X that points out of the palm (calibrate_hands)

def palm_world(s):
    return (arm.matrix_world.to_3x3() @ arm.pose.bones["hand_" + s].matrix.to_3x3() @ Vector((PALM_AXIS[s], 0, 0))).normalized()

def palm_target(kw, s, sg, mode, S3, fdir, hdir):
    """World direction the palm should face. Body-relative keywords; flat hands default palm-down, others palm toward the midline.
    Falls back when the wanted direction is (nearly) along the forearm, where it can't be reached by rolling."""
    up_b, fwd_b = d(S3), d(S3 - 90)
    lat = up_b.cross(fwd_b).normalized() * sg          # out to this arm's side
    words = {"in": -lat, "out": lat, "forward": fwd_b, "back": -fwd_b, "head": up_b, "feet": -up_b,
             "down": Vector((0, 0, -1)), "up": Vector((0, 0, 1))}
    R = fdir.rotation_difference(hdir).inverted()
    for w in [kw or ("down" if mode == "flat" else "in"), "down", "back", "forward"]:
        v = R @ words[w]; v = v - fdir * v.dot(fdir)
        if v.length > 0.35: return words[w]
    return None

def set_palm(s, fdir, hdir, want):
    """Roll the forearm about its own axis (pronation/supination) so that after the wrist bends from fdir to hdir the palm faces `want`."""
    if want is None: return
    pre = fdir.rotation_difference(hdir).inverted() @ want
    pre = pre - fdir * pre.dot(fdir)
    cur = palm_world(s); cur = cur - fdir * cur.dot(fdir)
    if pre.length < 1e-3 or cur.length < 1e-3: return
    pre.normalize(); cur.normalize()
    tilt("lowerarm_" + s, tuple(fdir), math.degrees(math.atan2(fdir.dot(cur.cross(pre)), cur.dot(pre))))

def calibrate_hands():
    """Palm axis (T-pose palms face down), finger curl sign, thumb pose per hand mode."""
    for s in "lr":
        reset()
        x = arm.matrix_world.to_3x3() @ arm.pose.bones["hand_" + s].matrix.to_3x3() @ Vector((1, 0, 0))
        PALM_AXIS[s] = 1 if x.z < 0 else -1
    return {"palm_axis": dict(PALM_AXIS), "curl": calibrate_curl(), "thumb": calibrate_thumbs()}

def calibrate_thumbs():
    """Coordinate descent on the thumb so its tip lands where a real thumb rests for each hand mode."""
    res = {}
    for s in "lr":
        for mode in ("grip", "relaxed", "flat"):
            reset(); THUMB[(s, mode)] = (0, 0, 0, 0); curl(s, CURL[mode], mode)
            f = (jw("middle_01_" + s) - jw("hand_" + s)).normalized(); n = palm_world(s)
            u = (jw("index_01_" + s) - jw("pinky_01_" + s)).normalized()       # toward the thumb side
            i1 = jw("index_01_" + s)
            if mode == "grip":       # tip across the curled index/middle middle phalanges
                tgt = (jw("index_02_" + s) + jw("index_02_" + s, True) + jw("middle_02_" + s) + jw("middle_02_" + s, True)) / 4 + f * 0.014
            elif mode == "relaxed":  # loosely in front of the index finger
                tgt = i1 + u * 0.018 + n * 0.035 + f * 0.012
            else:                    # flat: spread in the palm plane beside the index
                tgt = i1 + u * 0.05 - f * 0.012 + n * 0.004
            prm = [0.0, 0.0, 0.0, 0.0]
            def err():
                THUMB[(s, mode)] = tuple(prm); curl(s, CURL[mode], mode)
                return (jw("thumb_03_" + s, True) - tgt).length
            best = err()
            for step in (20, 10, 5, 2):
                improved = True
                while improved:
                    improved = False
                    for i in range(4):
                        for dv in (step, -step):
                            prm[i] += dv
                            if abs(prm[i]) <= 90:
                                e = err()
                                if e < best - 1e-5:
                                    best = e; improved = True; break
                            prm[i] -= dv
                        if improved: break
            THUMB[(s, mode)] = tuple(prm); curl(s, CURL[mode], mode)
            res[f"{s}_{mode}"] = ([round(v) for v in prm], round(best * 100, 2))
    reset()
    return res

def lerp_pose(A, B, t):
    out = {}
    for k in set(A) | set(B):
        a, b = A.get(k, B.get(k)), B.get(k, A.get(k))
        if isinstance(a, (list, tuple)):
            n = max(len(a), len(b))
            pad = lambda v: list(v) + [[v[2] + 90, 0][j - 4] for j in range(len(v), n)]   # foot pitch, foot lateral
            out[k] = [x + (y - x) * t for x, y in zip(pad(a), pad(b))]
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            out[k] = a + (b - a) * t
        else:
            out[k] = a if t < 0.5 else b
    return out

# ---------- measurements ----------
def body_coords():
    """All deformed body vertices, world space (numpy N x 3)."""
    import numpy as np
    ev = body.evaluated_get(vl.depsgraph); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co); ev.to_mesh_clear()
    M = np.array(ev.matrix_world, dtype=np.float32)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]

def body_bbox():
    ev = body.evaluated_get(vl.depsgraph)
    me = ev.to_mesh(); mw = ev.matrix_world; vs = me.vertices
    pts = [mw @ vs[i].co for i in range(0, len(vs), 6)]
    ev.to_mesh_clear()
    return pts

def jw(bone, tail=False):
    pb = arm.pose.bones[bone]
    return arm.matrix_world @ (pb.tail if tail else pb.head)

def joints():
    J = {}
    for s in "lr":
        if HAND_MODE.get(s) == "grip":   # inside the fist: just palm-side of the knuckles
            palm = palm_world(s).normalized()
            J["hand_" + s] = jw("middle_01_" + s) + palm * 0.03 + (jw("hand_" + s) - jw("middle_01_" + s)) * 0.15
        else:
            J["hand_" + s] = (jw("hand_" + s) + jw("middle_01_" + s)) / 2
        J["gax_" + s] = (jw("pinky_01_" + s) - jw("index_01_" + s)).normalized()
        J["elbow_" + s] = jw("lowerarm_" + s); J["shoulder_" + s] = jw("upperarm_" + s)
        J["knee_" + s] = jw("calf_" + s); J["ankle_" + s] = jw("foot_" + s); J["toe_" + s] = jw("ball_" + s)
        J["hip_" + s] = jw("thigh_" + s)
    J["pelvis"] = jw("pelvis"); J["chest"] = jw("spine_03", True); J["neck"] = jw("neck_01"); J["head"] = jw("Head", True)
    J["hands"] = (J["hand_l"] + J["hand_r"]) / 2; J["hips"] = (J["hip_l"] + J["hip_r"]) / 2
    J["shoulders"] = (J["shoulder_l"] + J["shoulder_r"]) / 2
    return J

def place(P, anchor, J0=None):
    """Pose and position the armature. anchor: {'z': (joint, value)|'ground', 'x': (joint, value|None)}; None value = match J0."""
    apply_pose(P)
    arm.location = (0, 0, 0); vl.update()
    J = joints()
    loc = Vector((0, 0, 0))
    az = anchor.get("z", "ground")
    if az == "ground":
        loc.z = -min(p.z for p in body_bbox())
    elif az[1] is None and J0 is not None:      # same height as in the first key (e.g. the foot that stays on a box)
        loc.z = J0[az[0]].z - J[az[0]].z
    else:
        loc.z = az[1] - J[az[0]].z
    ax = anchor.get("x")
    if ax:
        tx = ax[1] if ax[1] is not None else (J0[ax[0]].x if J0 else J[ax[0]].x)
        loc.x = tx - J[ax[0]].x
    arm.location = loc; vl.update()
    return loc

# ---------- props ----------
COLORS = {"metal": (0.13, 0.15, 0.19, 1), "pad": (0.22, 0.25, 0.31, 1), "wood": (0.78, 0.70, 0.58, 1),
          "wall": (0.88, 0.89, 0.91, 1), "cable": (0.08, 0.09, 0.11, 1), "band": (0.98, 0.45, 0.09, 1),
          "towel": (0.93, 0.93, 0.95, 1), "ball": (0.25, 0.55, 0.95, 1), "mat": (0.35, 0.62, 0.70, 1), "plate": (0.10, 0.11, 0.13, 1),
          "frame": (0.30, 0.33, 0.38, 1), "chrome": (0.80, 0.82, 0.85, 1), "uphol": (0.06, 0.065, 0.075, 1), "accent": (0.95, 0.42, 0.08, 1),
          "rubber": (0.04, 0.04, 0.045, 1), "foam": (0.14, 0.15, 0.17, 1), "steel": (0.55, 0.58, 0.62, 1),
          "pack": (0.05, 0.09, 0.19, 1), "bag": (0.72, 0.58, 0.40, 1)}
METAL = {"metal", "plate", "cable", "frame", "chrome", "steel"}
ROUGH = {"chrome": 0.18, "steel": 0.3, "frame": 0.38, "metal": 0.35, "plate": 0.42, "uphol": 0.55, "rubber": 0.85}

def _mat(key):
    name = "DR_m_" + key
    m = bpy.data.materials.get(name)
    if not m:
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = COLORS[key]
        b.inputs["Roughness"].default_value = ROUGH.get(key, 0.55)
        b.inputs["Metallic"].default_value = 0.85 if key in ("chrome", "steel") else (0.4 if key in METAL else 0.0)
    return m

LIB = {}   # kind -> template mesh (lathe / tube shapes, real-world metres)

def _lathe(key, profile, seg=40):
    """Closed (r, z) profile revolved about Z."""
    if key in LIB: return LIB[key]
    import bmesh
    bm = bmesh.new(); rings = []
    poles = {j: bm.verts.new((0.0, 0.0, z)) for j, (r, z) in enumerate(profile) if r < 1e-6}   # on-axis points are shared
    for i in range(seg):
        a = 2 * math.pi * i / seg; ca, sa = math.cos(a), math.sin(a)
        rings.append([poles[j] if j in poles else bm.verts.new((r * ca, r * sa, z)) for j, (r, z) in enumerate(profile)])
    n = len(profile)
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(n):
            k = (j + 1) % n
            vs = []
            for v in (A[j], B[j], B[k], A[k]):
                if v not in vs: vs.append(v)
            if len(vs) >= 3: bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("DR_lib_" + key); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    LIB[key] = me; return me

def _tube(key, path, r, sides=14):
    """Tube of radius r swept along a polyline path (list of Vectors)."""
    if key in LIB: return LIB[key]
    import bmesh
    bm = bmesh.new(); rings = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        u = t.cross(Vector((0, 1, 0)))
        if u.length < 1e-3: u = t.cross(Vector((1, 0, 0)))
        u.normalize(); w = t.cross(u)
        rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / sides) + w * math.sin(2 * math.pi * k / sides)) * r) for k in range(sides)])
    for i in range(len(rings) - 1):
        for k in range(sides):
            bm.faces.new([rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % sides], rings[i][(k + 1) % sides]])
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("DR_lib_" + key); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    LIB[key] = me; return me

def lib_shapes():
    # 20 kg Olympic iron plate (r 225 mm, 45 mm): raised rim, recessed web, raised hub, 52 mm bore
    _lathe("plate", [(0.026, -0.0225), (0.062, -0.0225), (0.064, -0.016), (0.196, -0.011), (0.204, -0.0225), (0.222, -0.0225),
                     (0.225, -0.019), (0.225, 0.019), (0.222, 0.0225), (0.204, 0.0225), (0.196, 0.011), (0.064, 0.016), (0.062, 0.0225), (0.026, 0.0225)])
    # pro-style round rubber dumbbell head (r 62 mm, 85 mm long) with chamfered faces
    _lathe("dbhead", [(0.0, -0.0425), (0.050, -0.0425), (0.060, -0.036), (0.062, -0.028), (0.062, 0.028), (0.060, 0.036), (0.050, 0.0425), (0.0, 0.0425)])
    # kettlebell bell (16 kg proportions): flat base, round belly, tapered shoulders
    _lathe("kbbody", [(0.0, -0.105), (0.066, -0.105), (0.088, -0.092), (0.104, -0.060), (0.110, -0.015), (0.104, 0.035), (0.088, 0.072),
                      (0.060, 0.096), (0.028, 0.106), (0.0, 0.108)])
    # kettlebell handle: horns rise from the shoulders and arch over the top (grip at local origin)
    pts = []
    for i in range(25):
        t = i / 24; a = math.pi * t
        x = 0.072 * math.cos(a); z = -0.105 + 0.105 * (math.sin(a) ** 0.55)
        pts.append(Vector((x, 0, z)))
    _tube("kbhandle", pts, 0.0165)

def _prop(name, kind, color):
    full = "DR_p_" + name
    o = bpy.data.objects.get(full)
    if o and o.get("kind") != kind:          # same name built as a different shape by another template: rebuild
        bpy.data.objects.remove(o, do_unlink=True); o = None
    if not o:
        import bmesh
        if kind in LIB or kind in ("plate", "dbhead", "kbbody", "kbhandle"):
            lib_shapes(); me = LIB[kind].copy(); me.name = full
        else:
            me = bpy.data.meshes.new(full); bm = bmesh.new()
            if kind == "box": bmesh.ops.create_cube(bm, size=2.0)
            elif kind == "cyl": bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=2)
            else: bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1)
            bm.to_mesh(me); bm.free()
            for p in me.polygons: p.use_smooth = kind != "box"
        o = bpy.data.objects.new(full, me)
        if kind == "box":                                  # rounded edges read as real upholstery / tube steel
            bv = o.modifiers.new("bevel", 'BEVEL'); bv.width = 0.012; bv.segments = 3; bv.limit_method = 'ANGLE'
            bv.harden_normals = False; o.modifiers.new("ws", 'WEIGHTED_NORMAL')
        col = bpy.data.collections.get("DR_props") or bpy.data.collections.new("DR_props")
        if col.name not in sc.collection.children: sc.collection.children.link(col)
        col.objects.link(o); o["kind"] = kind
    o.data.materials.clear(); o.data.materials.append(_mat(color))
    o.hide_render = False
    o.rotation_mode = 'QUATERNION'
    USED.add(full)
    return o

USED = set()

def hide_props():
    for o in bpy.data.objects:
        if o.name.startswith("DR_p_"): o.hide_render = True
    USED.clear()

def box(name, center, size, color="pad", pitch=0.0, yaw=0.0):
    """size = full (x, y, z); pitch rotates about Y (deg, + tips the +X end down), yaw about Z."""
    o = _prop(name, "box", color)
    o.location = Vector(center); o.scale = (1, 1, 1)
    h = Vector(size) / 2                                 # geometry in metres so the bevel stays uniform
    for v in o.data.vertices: v.co = Vector((math.copysign(h.x, v.co.x), math.copysign(h.y, v.co.y), math.copysign(h.z, v.co.z)))
    o.data.update()
    bv = o.modifiers.get("bevel")
    if bv: bv.width = min(0.014, min(size) * 0.22)
    o.rotation_quaternion = (Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, 'Y')).to_quaternion()
    return o

def rod(name, a, b, r, color="metal"):
    o = _prop(name, "cyl", color)
    a, b = Vector(a), Vector(b); v = b - a
    o.location = (a + b) / 2; o.scale = (r, r, max(v.length / 2, 1e-4))
    o.rotation_quaternion = v.normalized().to_track_quat('Z', 'Y') if v.length > 1e-6 else (1, 0, 0, 0)
    return o

def ball(name, c, r, color="metal"):
    o = _prop(name, "sph", color); o.location = Vector(c); o.scale = (r, r, r); return o

def _orient(o, c, axis, scale=1.0, up=None):
    """Place a lathe/tube prop: local Z along `axis`; optional local X hint `up`."""
    ax = Vector(axis).normalized()
    o.location = Vector(c); o.scale = (scale, scale, scale)
    if up is None: o.rotation_quaternion = ax.to_track_quat('Z', 'Y')
    else:
        x = (Vector(up) - ax * Vector(up).dot(ax)).normalized(); y = ax.cross(x)
        o.rotation_quaternion = Matrix((x, y, ax)).transposed().to_quaternion()
    return o

def plate(name, c, axis, r=0.225, thick=None):
    """Olympic iron plate centred at c, bore along axis; r scales the 20 kg plate, thick stretches its width."""
    o = _orient(_prop(name, "plate", "plate"), c, axis, r / 0.225)
    if thick: o.scale.z = thick / 0.045
    rod(name + "_hub", Vector(c) - Vector(axis).normalized() * 0.026 * (thick or 0.045) / 0.045,
        Vector(c) + Vector(axis).normalized() * 0.026 * (thick or 0.045) / 0.045, 0.06 * r / 0.225, "steel")
    return o

def plate_between(name, a, b, r, color="plate"):
    """Drop-in for a plate drawn as rod(a, b, r): real plate geometry spanning a..b."""
    a, b = Vector(a), Vector(b)
    return plate(name, (a + b) / 2, b - a, r, max((b - a).length, 0.015))

def dumbbell(name, c, axis=(0, 1, 0), length=0.32):
    """Pro-style dumbbell: knurled chrome handle, collars, round rubber heads with chrome end caps."""
    c = Vector(c); u = Vector(axis).normalized(); k = length / 0.32
    rod(name + "_bar", c - u * 0.075 * k, c + u * 0.075 * k, 0.0155, "chrome")
    rod(name + "_knurl", c - u * 0.048 * k, c + u * 0.048 * k, 0.0163, "steel")
    for s_, sg in (("1", -1), ("2", 1)):
        rod(name + "_col" + s_, c + u * sg * 0.068 * k, c + u * sg * 0.078 * k, 0.027, "chrome")
        _orient(_prop(name + "_h" + s_, "dbhead", "rubber"), c + u * sg * 0.1205 * k, u, k)
        rod(name + "_cap" + s_, c + u * sg * 0.161 * k, c + u * sg * 0.1645 * k, 0.034 * k, "chrome")

def barbell(name, c, axis=(0, 1, 0), length=1.6):
    """Olympic barbell: chrome shaft with knurled grips, sleeves, collars, a 20 kg + 10 kg plate per side."""
    c = Vector(c); u = Vector(axis).normalized(); h = length / 2
    rod(name + "_bar", c - u * (h - 0.30), c + u * (h - 0.30), 0.014, "chrome")
    for s_, sg in (("1", -1), ("2", 1)):
        rod(name + "_knurl" + s_, c + u * sg * 0.09, c + u * sg * 0.40, 0.0146, "steel")
        rod(name + "_sleeve" + s_, c + u * sg * (h - 0.30), c + u * sg * h, 0.025, "chrome")
        rod(name + "_ring" + s_, c + u * sg * (h - 0.31), c + u * sg * (h - 0.29), 0.032, "steel")
        plate(name + "_pA" + s_, c + u * sg * (h - 0.255), u)
        plate(name + "_pB" + s_, c + u * sg * (h - 0.200), u, 0.165, 0.035)
        rod(name + "_clip" + s_, c + u * sg * (h - 0.175), c + u * sg * (h - 0.155), 0.036, "accent")

def kettlebell(name, c, up=(0, 0, 1), side=None):
    """Cast-iron kettlebell hanging from the grip point c (handle top). `up` points from bell to grip."""
    c = Vector(c); up = Vector(up).normalized()
    side = Vector(side) if side is not None else up.cross(Vector((1, 0, 0)))
    if side.length < 1e-3: side = Vector((0, 1, 0))
    side = (side - up * side.dot(up)).normalized()
    # handle: local X across the window, local Z up; built in an XZ arch -> map local X->side, Z->up
    o = _prop(name + "_h", "kbhandle", "plate")
    o.location = c; o.scale = (1, 1, 1)
    o.rotation_quaternion = Matrix((side, up.cross(side), up)).transposed().to_quaternion()
    _orient(_prop(name + "_b", "kbbody", "plate"), c - up * 0.21, up)

def bench(name, x0, x1, top, width=0.30, color="pad", pitch=0.0):
    box(name + "_pad", ((x0 + x1) / 2, 0, top - 0.04), (abs(x1 - x0), width, 0.08), color, pitch)
    if pitch == 0:
        box(name + "_leg", ((x0 + x1) / 2, 0, (top - 0.08) / 2), (abs(x1 - x0) * 0.8, width * 0.5, top - 0.08), "metal")

def column(name, x, y, h=2.3):
    box(name, (x, y, h / 2), (0.12, 0.12, h), "metal")

# ---------- camera ----------
cam = bpy.data.objects["DR_cam"]

def set_camera(points, az=-70, el=10, margin=1.14):
    a, e = math.radians(az), math.radians(el)
    fwd = -Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
    right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
    xs = [p.dot(right) for p in points]; ys = [p.dot(up) for p in points]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    aspect = sc.render.resolution_x / sc.render.resolution_y
    center = right * cx + up * cy
    # shift along the view axis so the centre is in front of the camera
    cam.location = center - fwd * 12
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = fwd.to_track_quat('-Z', 'Y')
    cam.data.ortho_scale = max(w, h * aspect) * margin

def prop_points():
    pts = []
    for o in bpy.data.objects:
        if o.name in USED and not o.hide_render:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return pts

# ---------- animation ----------
def render_anim(spec, outdir, preview=False):
    """spec: name, keys [pose], anchor, props(J, J0, i), steps, cam {az, el, margin}, focus [joint names] (zoom)."""
    os.makedirs(outdir, exist_ok=True); files = []
    ng = sc.compositing_node_group; fo = ng.nodes.get("DR_mask") if ng else None   # skin mask (tools/setup_scene.mask_pass)
    for n in simulate(spec, preview):
        path = f"{outdir}/{spec['name']}_{n:03d}.png"
        sc.render.filepath = path
        if fo: fo.directory = outdir + "/_m"; fo.file_name = "m"; sc.frame_current = n + 1
        bpy.ops.render.render(write_still=True, scene=sc.name)
        if fo:
            out = [f for f in os.listdir(outdir + "/_m") if f.endswith(".png")]
            os.replace(max((os.path.join(outdir, "_m", f) for f in out), key=os.path.getmtime), f"{outdir}/mask_{n:03d}.png")
        files.append(path)
    if fo and os.path.isdir(outdir + "/_m") and not os.listdir(outdir + "/_m"): os.rmdir(outdir + "/_m")
    return files

def simulate(spec, preview=False):
    """Poses, contacts, props and camera for every frame of the animation; yields the frame number once each is ready."""
    keys = loop_keys(spec); anchor = spec.get("anchor", {})
    props = spec.get("props"); steps = spec.get("steps", 6)
    # 1) place key poses, collect framing points
    hide_props()
    locs, Js, pts, caps = [], [], [], []
    J0 = None
    for i, P in enumerate(keys):
        loc = place(P, P.get("anchor", anchor), J0); loc = settle()
        caps.append(capture())
        J = joints()
        if J0 is None: J0 = J
        locs.append(loc.copy()); Js.append(J)
        if props: props(J, J0)
        if spec.get("focus"):
            pts += [J[j] for j in spec["focus"]]
        else:
            bb = body_bbox()   # frame the body; equipment counts only near it (tall towers get cropped)
            lo = Vector((min(p.x for p in bb) - 0.45, min(p.y for p in bb) - 0.45, 0.0))
            hi = Vector((max(p.x for p in bb) + 0.45, max(p.y for p in bb) + 0.45, max(p.z for p in bb) + 0.3))
            pts += bb + [Vector((min(max(p.x, lo.x), hi.x), min(max(p.y, lo.y), hi.y), min(max(p.z, lo.z), hi.z))) for p in prop_points()]
    # contacts: a hand/foot that barely moves across the key poses is planted (IK-pinned at its mean position)
    states, PLANT = _plant(spec, keys, locs)
    c = spec.get("cam", {})
    set_camera(pts, c.get("az", -70), c.get("el", 10), c.get("margin", 1.1 if spec.get("focus") is None else 1.6))
    # 2) pose each frame
    seq = range(len(keys)) if not preview else range(len(keys))
    n = 0
    for i in seq:
        A, B = keys[i], keys[(i + 1) % len(keys)]
        la, lb = locs[i], locs[(i + 1) % len(keys)]
        rng = [0] if preview else range(steps)
        for k in rng:
            t = k / steps
            ctx = {"phase": (i + t) / len(keys), "i": i, "t": t, "n": len(keys), "J0": J0, "states": states}
            if not spec.get("linear"): t = t * t * (3 - 2 * t)
            blend(caps[i], caps[(i + 1) % len(keys)], t)
            arm.location = la.lerp(lb, t); vl.update()
            if not PLANT:      # planted hands/feet already hold the body on the floor; re-grounding would fight them
                frame_ground(keys, i, lambda P: P.get("anchor", anchor), arm.location.copy())
            for l, (tip, toe) in PLANT.items():                # posed exactly on its pin already: leave it (pole-less IK drifts)
                if (jw(EFF[l], True) - tip).length > 0.01:
                    ik_on(l, tip, states[i][l]["pole"].lerp(states[(i + 1) % len(keys)][l]["pole"], t), toe)
            drv = drive(spec, keys, states, i, t, ctx)
            for l, (tip, toe) in drv.items():
                ik_on(l, tip, tip, toe)
            vl.update()
            held = set(PLANT) | set(drv)
            for l, tgt in reach_lerp(spec, keys, i, t, joints()).items():
                ik_on(l, tgt, tgt); held.add(l)
            vl.update()
            for _ in range(3):                                   # nothing sinks through the floor between key poses
                lo = trunk_low()
                if lo > -0.008: break
                arm.location.z -= lo; vl.update()
            fz = support_z()
            for l in ("foot_l", "foot_r"):                       # a swinging foot never scuffs through the floor
                if l in held: continue
                s_ = l[-1]; th, sh = bone_dir("thigh_" + s_), bone_dir("calf_" + s_)
                if th.angle(sh) < math.radians(25): continue   # straight leg: IK could hyperextend it; leave FK
                dip = limb_low(l) - fz
                if dip < -0.006:
                    tip = jw(EFF[l], True) + Vector((0, 0, -dip)); ik_on(l, tip, tip); vl.update()
            if props: props(joints(), J0, ctx)
            yield n; n += 1
    ik_off()

def settle():
    """Lift a placed key pose out of the floor (same rule as the per-frame guard), so contacts are pinned where the
    body will really be - otherwise the guard lifts the body later and the pinned feet bend the knees."""
    for _ in range(3):
        lo = trunk_low()
        if lo > -0.008: break
        arm.location.z -= lo; vl.update()
    return arm.location.copy()

def trunk_low():
    """Lowest mesh point of everything but the hands and feet (fingers and toes included; those are kept on
    surfaces by contact IK and the per-limb floor guard, never by lifting the whole body)."""
    import numpy as np
    key = ("trunk", body.name)
    if key not in _LIMB_IDX:
        for l in EFF: limb_low(l)                                   # builds the per-limb vertex lists
        m = np.ones(len(body.data.vertices), bool)
        for l in EFF: m[_LIMB_IDX[(body.name, l)]] = False
        _LIMB_IDX[key] = m
    return float(body_coords()[_LIMB_IDX[key], 2].min())

def loop_keys(spec):
    base = {k: spec[k] for k in ("hands", "handL", "handR", "handdir", "palm", "palmL", "palmR", "stance") if k in spec}
    k = [{**base, **key} for key in spec["keys"]]
    return k + k[-2:0:-1] if spec.get("pingpong") else k

def frame_ground(keys, i, anchor_of, loc):
    """Re-ground every interpolated frame when both neighbouring keys are floor-grounded (stops the body dipping into the floor)."""
    a, b = anchor_of(keys[i]), anchor_of(keys[(i + 1) % len(keys)])
    if a.get("z", "ground") == "ground" and b.get("z", "ground") == "ground":
        loc.z = arm.location.z - float(body_coords()[:, 2].min())
        arm.location = loc; vl.update()

def audit(spec, samples=4):
    """Sliding of planted contacts and floor penetration over interpolated frames (no rendering)."""
    keys = loop_keys(spec); anchor = spec.get("anchor", {})
    locs, J0, caps = [], None, []
    for P in keys:
        place(P, P.get("anchor", anchor), J0); locs.append(settle()); caps.append(capture()); J0 = J0 or joints()
    states, PLANT = _plant(spec, keys, locs)
    slide = {l: 0.0 for l in PLANT}; fk_slide = 0.0; lowest = 9.0
    for i in range(len(keys)):
        for k in range(samples):
            t = k / samples; t = t * t * (3 - 2 * t)
            blend(caps[i], caps[(i + 1) % len(keys)], t); arm.location = locs[i].lerp(locs[(i + 1) % len(keys)], t); vl.update()
            if not PLANT: frame_ground(keys, i, lambda P: P.get("anchor", anchor), arm.location.copy())
            for l, (tip, toe) in PLANT.items(): fk_slide = max(fk_slide, (jw(EFF[l], True) - tip).length)
            for l, (tip, toe) in PLANT.items(): ik_on(l, tip, states[i][l]["pole"].lerp(states[(i + 1) % len(keys)][l]["pole"], t), toe)
            vl.update()
            for _ in range(3):
                lo_ = trunk_low()
                if lo_ > -0.008: break
                arm.location.z -= lo_; vl.update()
            for l, (tip, toe) in PLANT.items(): slide[l] = max(slide[l], (jw(EFF[l], True) - tip).length)
            lowest = min(lowest, min(p.z for p in body_bbox()))
    ik_off()
    return {"planted": sorted(PLANT), "fk_slide_cm": round(fk_slide * 100, 1), "ik_slide_cm": round(max(slide.values(), default=0) * 100, 1), "lowest_cm": round(lowest * 100, 1)}
