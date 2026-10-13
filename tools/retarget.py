# Retargets MediaPipe pose landmarks (from tools/extract_poses.py) onto the Quaternius rig.
# Loaded in Blender after rig.py, into the same namespace: exec(open(".../retarget.py").read(), ns)
# A pose dict may carry "lm": {name: Vector} (Blender world, hip-centred); apply_pose then drives the rig from it.
import math, json
from mathutils import Vector, Matrix

LMI = dict(nose=0, ear_l=7, ear_r=8, sh_l=11, sh_r=12, el_l=13, el_r=14, wr_l=15, wr_r=16, pk_l=17, pk_r=18,
           ix_l=19, ix_r=20, th_l=21, th_r=22, hip_l=23, hip_r=24, kn_l=25, kn_r=26, an_l=27, an_r=28,
           he_l=29, he_r=30, to_l=31, to_r=32)
SUPPORT = {"he": 1.0, "to": 1.0, "kn": 0.8, "wr": 0.7, "el": 0.6, "hip": 0.5, "sh": 0.4}

def _rot(pitch, roll, yaw=0.0):
    return (Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(roll), 3, 'X')
            @ Matrix.Rotation(math.radians(pitch), 3, 'Y'))

def landmarks(raw, mirror=False, level=True, yaw_to=None, sym=False, multi=False):
    """MediaPipe world landmarks -> Blender world (Z up), hip-centred, levelled by support contacts and yawed so the
    body's left points +Y (or, when the hips are stacked vertically, the trunk points +X). Returns (dict, R) where R maps
    the original camera frame to this frame (for camera-matched QA renders)."""
    P0 = {k: Vector((raw[i][0], raw[i][2], -raw[i][1])) for k, i in LMI.items()}   # MP x right, y down, z away -> X, Y(depth), Z up
    vis = {k: raw[i][3] for k, i in LMI.items()}
    R = Matrix.Identity(3)
    feet = ("he_l", "he_r", "to_l", "to_r")
    lowest = sorted(P0, key=lambda k: P0[k].z)[:4]
    if level and sum(k in feet for k in lowest) >= 3:
        best = None
        for p10 in range(-12, 13, 1):
            for r10 in range(-8, 9, 2):
                Rt = _rot(p10, r10); zs = [(Rt @ P0[k]).z for k in feet]
                sc = (max(zs) - min(zs)) + 0.001 * (abs(p10) + abs(r10))
                if best is None or sc < best[0]: best = (sc, Rt)
        R = best[1]
    # lying / plank / quadruped bodies rest on several contacts: tilt so the lowest four support landmarks share one floor plane
    sh_c = (P0["sh_l"] + P0["sh_r"]) / 2; hp_c = (P0["hip_l"] + P0["hip_r"]) / 2; tr = sh_c - hp_c
    if level and multi and abs(tr.z) < 0.6 * tr.length:
        cand = [k for k in P0 if k[:2] in ("sh", "he", "to", "el", "wr", "kn") or k[:3] == "hip"]
        best = None
        for p10 in range(-25, 26, 2):
            for r10 in range(-24, 25, 3):
                Rt = _rot(p10, r10); zs = sorted((Rt @ P0[k]).z for k in cand)
                sc = (zs[3] - zs[0]) + 0.0015 * (abs(p10) + abs(r10))
                if best is None or sc < best[0]: best = (sc, Rt)
        R = best[1]
    P = {k: R @ v for k, v in P0.items()}
    # yaw: body's left -> +Y
    left = (P["hip_l"] - P["hip_r"]); left.z = 0
    if left.length > 0.06:
        yaw = math.atan2(left.x, left.y)               # rotate so left aligns with +Y
    else:
        tr = (P["sh_l"] + P["sh_r"]) / 2 - (P["hip_l"] + P["hip_r"]) / 2; tr.z = 0
        yaw = math.atan2(tr.y, tr.x) * -1 if tr.length > 1e-3 else 0.0
        yaw = -math.atan2(-tr.y, tr.x) if tr.length > 1e-3 else 0.0
    Ry = Matrix.Rotation(yaw if left.length > 0.06 else -math.atan2(tr.y, tr.x), 3, 'Z')
    if yaw_to is not None: Ry = Matrix.Rotation(math.radians(yaw_to), 3, 'Z') @ Ry
    P = {k: Ry @ v for k, v in P.items()}
    R = Ry @ R
    if mirror:
        P = {(k[:-2] + ("_r" if k.endswith("_l") else "_l") if k[-2:] in ("_l", "_r") else k): Vector((v.x, -v.y, v.z)) for k, v in P.items()}
        vis = {(k[:-2] + ("_r" if k.endswith("_l") else "_l") if k[-2:] in ("_l", "_r") else k): v for k, v in vis.items()}
        R = Matrix(((1, 0, 0), (0, -1, 0), (0, 0, 1))) @ R
    c = (P["hip_l"] + P["hip_r"]) / 2
    P = {k: v - c for k, v in P.items()}
    if sym: P = symmetrize(P, vis)
    P = shoulders_level(P)
    P["_vis"] = vis
    return P, R

LIMBS = {"arm": ("el", "wr", "ix", "pk", "th"), "leg": ("kn", "an", "he", "to")}

def shoulders_level(P):
    """Monocular depth often tilts the shoulder line of side-on lying / plank poses by 20-40 deg. Real bodies keep the
    shoulder line roughly parallel to the hip line: rotate the upper body (shoulders, arms, head) about the trunk axis
    so its left-right line matches the hips'."""
    hip_c = (P["hip_l"] + P["hip_r"]) / 2; sh_c = (P["sh_l"] + P["sh_r"]) / 2
    ax = sh_c - hip_c
    if ax.length < 1e-3: return P
    ax.normalize()
    hl = P["hip_l"] - P["hip_r"]; sl = P["sh_l"] - P["sh_r"]
    hl = hl - ax * hl.dot(ax); sl = sl - ax * sl.dot(ax)
    if hl.length < 1e-3 or sl.length < 1e-3: return P
    hl.normalize(); sl.normalize()
    ang = math.atan2(ax.dot(sl.cross(hl)), sl.dot(hl))
    if abs(math.degrees(ang)) < 12: return P
    Rm = Matrix.Rotation(ang * 0.85, 3, ax)
    upper = [k for k in P if k[:2] in ("sh", "el", "wr", "ix", "pk", "th", "ea", "no")]
    out = dict(P)
    for k in upper: out[k] = sh_c + Rm @ (P[k] - sh_c)
    return out

def swap_limbs(L):
    """Opposite gait/alternation phase: each limb takes the other side's shape, reflected across the body's own
    sagittal plane (hip+shoulder line normal), attached at its own shoulder/hip. Trunk and head are kept."""
    up = ((L["sh_l"] + L["sh_r"]) / 2 - (L["hip_l"] + L["hip_r"]) / 2).normalized()
    left = (L["hip_l"] - L["hip_r"]) + (L["sh_l"] - L["sh_r"]); left = (left - up * left.dot(up)).normalized()
    refl = lambda v: v - left * (2 * v.dot(left))
    out = dict(L)
    for limb, keys in LIMBS.items():
        root = "sh_" if limb == "arm" else "hip_"
        for a, b in (("l", "r"), ("r", "l")):
            for k in keys:
                out[f"{k}_{a}"] = L[root + a] + refl(L[f"{k}_{b}"] - L[root + b])
    return out
def symmetrize(P, vis, lo=0.5, hi=0.6):
    """Occluded limb (low MediaPipe visibility) on a two-sided exercise: copy the visible limb, mirrored across the body's
    sagittal plane (hip-centred, body left = +Y)."""
    P = dict(P)
    for limb, keys in LIMBS.items():
        va = {s: sum(vis[f"{k}_{s}"] for k in keys) / len(keys) for s in "lr"}
        for bad, good in (("l", "r"), ("r", "l")):
            if va[bad] < lo and va[good] > hi and va[good] - va[bad] > 0.25:
                base_g = P[("sh_" if limb == "arm" else "hip_") + good]; base_b = P[("sh_" if limb == "arm" else "hip_") + bad]
                for k in keys:
                    v = P[f"{k}_{good}"] - base_g
                    P[f"{k}_{bad}"] = base_b + Vector((v.x, -v.y, v.z))
    return P

def mid(L, a, b): return (L[a] + L[b]) / 2

def frame(f, l):
    """Right-handed frame matrix from a forward and (approximate) left vector: columns f, l, u."""
    f = f.normalized(); l = (l - f * l.dot(f)).normalized(); u = f.cross(l)
    return Matrix((f, l, u)).transposed()

def rotate_world(name, Rw):
    Rarm = arm.matrix_world.to_3x3()
    _apply(arm.pose.bones[name], (Rarm.inverted() @ Rw @ Rarm).to_4x4())


def bone_axis_world(name, local):
    pb = arm.pose.bones[name]
    return (arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ Vector(local)).normalized()

def palm_normal(L, s):
    n = (L["ix_" + s] - L["wr_" + s]).cross(L["pk_" + s] - L["wr_" + s])
    return (-n if s == "l" else n).normalized() if n.length > 1e-6 else None

def apply_landmarks(L, P):
    """Drive the rig from landmarks L (directions only; lengths come from the rig)."""
    ik_off(); reset()
    hip_c, sh_c = mid(L, "hip_l", "hip_r"), mid(L, "sh_l", "sh_r")
    trunk = (sh_c - hip_c).normalized()
    hipl = L["hip_l"] - L["hip_r"]
    # pelvis: up = trunk, left = hip line
    rest = frame(Vector((1, 0, 0)), Vector((0, 1, 0)))                       # rest: forward +X, left +Y, up +Z
    fwd = hipl.cross(trunk)                                                   # left x up = forward
    tgt = frame(fwd, hipl)
    rotate_world("pelvis", tgt @ rest.transposed())
    # spine: optional curvature (P["curve"] deg: + flexion / rounding), shoulder-line twist on the upper spine
    curve = P.get("curve", 0.0)
    side_ax = hipl.normalized()
    for b, k in (("spine_01", -0.5), ("spine_02", 0.0), ("spine_03", 0.5)):
        aim(b, (Matrix.Rotation(math.radians(curve * k), 3, side_ax) @ trunk))
    shl = L["sh_l"] - L["sh_r"]
    cur = jw("upperarm_l") - jw("upperarm_r")
    a_ = trunk
    cur = cur - a_ * cur.dot(a_); w_ = shl - a_ * shl.dot(a_)
    if cur.length > 1e-4 and w_.length > 1e-4:
        ang = math.degrees(math.atan2(a_.dot(cur.normalized().cross(w_.normalized())), cur.normalized().dot(w_.normalized())))
        tilt("spine_02", tuple(a_), ang * 0.5); tilt("spine_03", tuple(a_), ang * 0.5)
    # clavicles follow the landmark shoulder line (half weight: real collarbones move less than the joint marker)
    for s, sg in (("l", 1), ("r", -1)):
        cdir = bone_dir("clavicle_" + s)
        want = (L["sh_" + s] - sh_c).normalized()
        aim("clavicle_" + s, (cdir + want).normalized())
    # head: frame from ears and nose
    ear_c = mid(L, "ear_l", "ear_r")
    neck_dir = (ear_c - sh_c).normalized()
    aim("neck_01", (neck_dir + trunk).normalized())
    hl = L["ear_l"] - L["ear_r"]; hf = L["nose"] - ear_c
    hu = hf.normalized().cross(hl.normalized()) if hl.length > 1e-4 else neck_dir
    aim("Head", (neck_dir * 0.5 + hu.normalized() * 0.5).normalized())
    if hl.length > 1e-4:
        cur = jw("Head", True) - jw("Head"); ax = cur.normalized()
        f_now = bone_axis_world("Head", (0, 0, 1)); f_want = hf - ax * hf.dot(ax)
        # pick the head's local axis that faced forward at rest
        f_now = HEAD_FWD_AXIS and bone_axis_world("Head", HEAD_FWD_AXIS)
        f_now = f_now - ax * f_now.dot(ax)
        if f_now.length > 1e-4 and f_want.length > 1e-4:
            f_now.normalize(); f_want.normalize()
            tilt("Head", tuple(ax), math.degrees(math.atan2(ax.dot(f_now.cross(f_want)), f_now.dot(f_want))))
    # limbs
    for s in "lr":
        sg = SIDE[s]
        up_d = (L["el_" + s] - L["sh_" + s]).normalized(); fo_d = (L["wr_" + s] - L["el_" + s]).normalized()
        aim("upperarm_" + s, up_d)
        bend = fo_d - up_d * fo_d.dot(up_d)
        if bend.length > 0.12: roll_to("upperarm_" + s, bend)
        aim("lowerarm_" + s, fo_d)
        mode = P.get("hand" + s.upper(), P.get("hands", "relaxed")); HAND_MODE[s] = mode
        hand_pt = (L["ix_" + s] + L["pk_" + s]) / 2
        hdir = (hand_pt - L["wr_" + s]).normalized() if mode == "flat" else fo_d
        if mode == "flat" and fo_d.z < -0.3:                 # palm on the floor / a bench: fingers lie flat on the surface
            hdir = Vector((hdir.x, hdir.y, 0.0))
            if hdir.length < 0.2: hdir = Vector((fo_d.x, fo_d.y, 0.0))
            hdir = hdir.normalized() if hdir.length > 1e-4 else Vector((1, 0, 0))
        kw = P.get("palm" + s.upper(), P.get("palm"))
        want = palm_target(kw, s, sg, mode, P.get("S3", 180), fo_d, hdir) if kw else palm_normal(L, s)
        set_palm(s, fo_d, hdir, want)
        aim("hand_" + s, hdir)
        curl(s, CURL[mode], mode)
        th_d = (L["kn_" + s] - L["hip_" + s]).normalized(); sh_d = (L["an_" + s] - L["kn_" + s]).normalized()
        aim("thigh_" + s, th_d)
        kb = sh_d - th_d * sh_d.dot(th_d)
        sole = (L["to_" + s] - L["he_" + s])
        if kb.length > 0.12: roll_to("thigh_" + s, kb)
        elif sole.length > 1e-4: roll_to("thigh_" + s, -sole.normalized())
        aim("calf_" + s, sh_d)
        if sole.length > 1e-4:
            so = sole.normalized()
            dors = (L["an_" + s] - L["he_" + s]); dors = (dors - so * dors.dot(so)).normalized()
            aim("foot_" + s, (so * math.cos(math.radians(26)) - dors * math.sin(math.radians(26))).normalized())
            aim("ball_" + s, so)

HEAD_FWD_AXIS = None

def calibrate_head():
    """Which local axis of the Head bone points forward (+X) at rest."""
    global HEAD_FWD_AXIS
    reset()
    best = None
    for ax in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
        v = bone_axis_world("Head", ax).x
        if best is None or v > best[1]: best = (ax, v)
    HEAD_FWD_AXIS = best[0]
    return HEAD_FWD_AXIS

_apply_pose_fk = apply_pose
def apply_pose(P):
    if "lm" in P: apply_landmarks(P["lm"], P)
    else: _apply_pose_fk(P)

_lerp_pose_fk = lerp_pose
def lerp_pose(A, B, t):
    out = _lerp_pose_fk({k: v for k, v in A.items() if k != "lm"}, {k: v for k, v in B.items() if k != "lm"}, t)
    if "lm" in A and "lm" in B:
        out["lm"] = {k: A["lm"][k].lerp(B["lm"][k], t) for k in A["lm"] if isinstance(A["lm"][k], Vector)}
    elif "lm" in A: out["lm"] = A["lm"]
    return out

POSES = {}
def load_poses(path):
    POSES.update(json.load(open(path)))
    return len(POSES)

def LM(ref, idx, mirror=False, **kw):
    """Key pose from a reference photo: LM("Pushups", 0). Extra kw (hands, palm, curve, anchor...) pass through."""
    post = kw.pop("mirror_post", False)
    L, R = landmarks(POSES[f"{ref}_{idx}"]["world"], mirror=False if post else mirror, sym=kw.pop("sym", False))
    if post: L = swap_limbs(L)
    kw["_post"] = post
    kw = dict(kw); kw.update(lm=L, T=180, _R=R, _ref=f"{ref}_{idx}", _mirror=mirror)
    kw.setdefault("armL", [0, 0, 0, 0]); kw.setdefault("armR", [0, 0, 0, 0]); kw.setdefault("legL", [0, 0, 0, 0]); kw.setdefault("legR", [0, 0, 0, 0])
    return kw

# ---------- QA: camera matched to the photo, 2D joint error ----------
QA_JOINTS = {"sh_l": ("upperarm_l", 0), "sh_r": ("upperarm_r", 0), "el_l": ("lowerarm_l", 0), "el_r": ("lowerarm_r", 0),
             "wr_l": ("hand_l", 0), "wr_r": ("hand_r", 0), "hip_l": ("thigh_l", 0), "hip_r": ("thigh_r", 0),
             "kn_l": ("calf_l", 0), "kn_r": ("calf_r", 0), "an_l": ("foot_l", 0), "an_r": ("foot_r", 0)}

def photo_camera(R, pts, margin=1.15):
    """Ortho camera looking the way the photo's camera did (R from landmarks())."""
    v = (R @ Vector((0, 1, 0))).normalized(); u = (R @ Vector((0, 0, 1))).normalized()
    right = v.cross(u).normalized(); up = right.cross(v).normalized()
    xs = [p.dot(right) for p in pts]; ys = [p.dot(up) for p in pts]
    c = right * (min(xs) + max(xs)) / 2 + up * (min(ys) + max(ys)) / 2
    cam.location = c - v * 12
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = Matrix((right, up, -v)).transposed().to_quaternion()
    aspect = sc.render.resolution_x / sc.render.resolution_y
    cam.data.ortho_scale = max(max(xs) - min(xs), (max(ys) - min(ys)) * aspect) * margin
    return right, up

def joint_error(R, ref_key):
    """Mean 2D joint error (% of torso length) between the posed rig, seen from the photo camera, and the photo landmarks."""
    rec = POSES[ref_key]; w, h = rec["w"], rec["h"]
    v = (R @ Vector((0, 1, 0))).normalized(); u = (R @ Vector((0, 0, 1))).normalized()
    right = v.cross(u).normalized(); up = right.cross(v).normalized()
    A, B = [], []
    for k, (bone, tail) in QA_JOINTS.items():
        p = jw(bone, bool(tail)); A.append((p.dot(right), p.dot(up)))
        q = rec["img"][LMI[k]]; B.append((q[0] * w, -q[1] * h))
    n = len(A)
    ax = sum(a[0] for a in A) / n; ay = sum(a[1] for a in A) / n; bx = sum(b[0] for b in B) / n; by = sum(b[1] for b in B) / n
    num = sum((a[0] - ax) * (b[0] - bx) + (a[1] - ay) * (b[1] - by) for a, b in zip(A, B))
    den = sum((a[0] - ax) ** 2 + (a[1] - ay) ** 2 for a in A)
    s = num / den if den else 1
    err = [math.hypot(s * (a[0] - ax) + bx - b[0], s * (a[1] - ay) + by - b[1]) for a, b in zip(A, B)]
    tor = math.hypot((B[0][0] + B[1][0]) / 2 - (B[6][0] + B[7][0]) / 2, (B[0][1] + B[1][1]) / 2 - (B[6][1] + B[7][1]) / 2)
    return round(100 * sum(err) / n / tor, 1), {k: round(100 * e / tor) for k, e in zip(QA_JOINTS, err)}

# ---------- hybrid keys: photo pose + hand-set limbs (fk_armL/fk_armR/fk_legL/fk_legR, fk_N/fk_H) ----------
_apply_landmarks_base = apply_landmarks
def apply_landmarks(L, P):
    _apply_landmarks_base(L, P)
    S3 = P.get("S3", 180)
    for s in "lr":
        sg = SIDE[s]
        a = P.get("fk_arm" + s.upper())
        if a:
            aim("upperarm_" + s, d(a[0], a[1], sg)); hinge("upperarm_" + s, d(a[2], a[3], sg)); aim("lowerarm_" + s, bent("upperarm_" + s, d(a[2], a[3], sg)))
            mode = P.get("hand" + s.upper(), P.get("hands", "relaxed")); fdir = d(a[2], a[3], sg)
            hdir = d(P.get("handdir", 92), 12, sg) if mode == "flat" else fdir
            set_palm(s, fdir, hdir, palm_target(P.get("palm" + s.upper(), P.get("palm")), s, sg, mode, S3, fdir, hdir))
            aim("hand_" + s, hdir); curl(s, CURL[mode], mode)
        g = P.get("fk_leg" + s.upper())
        if g:
            fp = g[4] if len(g) > 4 else (FOOT_FLAT if -50 <= g[2] <= 50 else g[2] + 90)
            aim("thigh_" + s, d(g[0], g[1], sg)); hinge("thigh_" + s, d(g[2], g[3], sg), -d(90 if -15 <= fp <= 110 else fp, 0, sg))
            aim("calf_" + s, bent("thigh_" + s, d(g[2], g[3], sg)))
            aim("foot_" + s, d(fp, 0, sg)); aim("ball_" + s, d(90 if -15 <= fp <= 110 else fp, 0, sg))
    stance = P.get("stance")
    for s in "lr":
        sg = SIDE[s]
        if stance == "stand" and not P.get("fk_leg" + s.upper()):
            aim("thigh_" + s, d(2, 6, sg)); hinge("thigh_" + s, d(-2, 5, sg), -d(90, 0, sg)); aim("calf_" + s, d(-2, 5, sg))
        if stance == "seated" and not P.get("fk_leg" + s.upper()):
            aim("thigh_" + s, d(90, 8, sg)); hinge("thigh_" + s, d(4, 6, sg)); aim("calf_" + s, d(4, 6, sg))
        flatten_foot(L, s, sg, force=stance in ("stand", "seated"))
    if P.get("fk_N") is not None: aim("neck_01", d(P["fk_N"]))
    if P.get("fk_H") is not None: aim("Head", d(P["fk_H"]))

_lerp_hybrid = lerp_pose
def lerp_pose(A, B, t):
    out = _lerp_hybrid(A, B, t)
    for k in set(A) | set(B):
        if k.startswith("fk_"):
            a, b = A.get(k), B.get(k)
            if isinstance(a, list) and isinstance(b, list): out[k] = [x + (y - x) * t for x, y in zip(a, b)]
            elif isinstance(a, (int, float)) and isinstance(b, (int, float)): out[k] = a + (b - a) * t
            else: out[k] = a if t < 0.5 else b
    return out

def flatten_foot(L, s, sg, force=False):
    """Feet in floor contact sit flat: when the shin is near vertical (or forced), the sole is levelled, keeping its heading."""
    shin = bone_dir("calf_" + s)
    if not force and shin.angle(Vector((0, 0, -1))) > math.radians(38): return
    head = L["to_" + s] - L["he_" + s]; head.z = 0
    if head.length < 0.05:
        f = (L["hip_l"] - L["hip_r"]).cross(Vector((0, 0, 1))); f.z = 0      # left x up = forward
        head = f if f.length > 1e-3 else Vector((1, 0, 0))
    head.normalize()
    out = Vector((0, sg, 0)); head = (head + out * 0.12).normalized()          # natural slight toe-out
    aim("foot_" + s, (head * math.cos(math.radians(26)) - Vector((0, 0, 1)) * math.sin(math.radians(26))).normalized())
    aim("ball_" + s, head)

# ---------- mesh-based anchors: rest the torso on a bench / the seat on a chair ----------
def region_low(kind):
    """Lowest mesh point of a body region: 'torso' (pelvis..neck) or 'seat' (around the hips/upper thighs)."""
    J = joints(); a, b = J["pelvis"], J["neck"]
    ab = b - a; L2 = ab.length_squared
    lo = 9.0
    for p in body_bbox():
        t = (p - a).dot(ab) / L2
        if kind == "torso" and 0.05 <= t <= 0.95 and (p - (a + ab * t)).length < 0.3: lo = min(lo, p.z)
        if kind == "seat" and -0.35 <= t <= 0.15 and (p - (a + ab * max(t, 0))).length < 0.35: lo = min(lo, p.z)
    return lo

SUPPORT_GROUPS = {"feet": ("ankle_l", "ankle_r"), "knees": ("knee_l", "knee_r"), "hands": ("hand_l", "hand_r"), "hips": ("hip_l", "hip_r")}

def support_group(J, anchor):
    """Which body part carries the weight: seated/bench -> hips; otherwise the lowest of feet/knees/hands/hips."""
    az = anchor.get("z") if anchor else None
    if isinstance(az, tuple) and az[0] in ("torso", "seat", "pelvis"): return "hips"
    return min(SUPPORT_GROUPS, key=lambda g: min(J[j].z for j in SUPPORT_GROUPS[g]) + (0.04 if g == "hips" else 0.0))

_place_base = place
def place(P, anchor, J0=None):
    anchor = anchor or {}
    az = anchor.get("z")
    if isinstance(az, tuple) and az[0] in ("torso", "seat"):
        _place_base(P, {**anchor, "z": "ground"}, J0)
        arm.location.z += az[1] - region_low(az[0]); vl.update()
    else:
        _place_base(P, anchor, J0)
    # keep the supporting body part fixed in x/y across key poses (feet stay put while the body moves over them)
    if J0 is not None and "x" not in anchor and not anchor.get("free_xy"):
        g = PLACE_GROUP.get("g") or support_group(J0, anchor)
        J = joints(); a, b = SUPPORT_GROUPS[g]
        if abs(J[a].z - J[b].z) > 0.05:          # one of the pair is lifted (reach, tap, single-leg): anchor on the one still down
            a = b = min((a, b), key=lambda j: J[j].z)
        cur, ref = (J[a] + J[b]) / 2, (J0[a] + J0[b]) / 2
        arm.location.x += ref.x - cur.x; arm.location.y += ref.y - cur.y; vl.update()
    return arm.location.copy()

PLACE_GROUP = {}
