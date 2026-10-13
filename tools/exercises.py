# Exercise animation specs for tools/rig.py. Each spec: name, keys (poses), anchor, props(J, J0), cam, focus.
# Angles: pitch 0 = down, 90 = forward (+X), 180 = up, -90 = back. Arms/legs [upper p, l, lower p, l, (foot p)].
from mathutils import Vector as V

def P(T=180, armL=(4, 7, 4, 6), armR=(4, 7, 4, 6), legL=(0, 4, 0, 4), legR=(0, 4, 0, 4), **kw):
    kw.update(T=T, armL=list(armL), armR=list(armR), legL=list(legL), legR=list(legR)); return kw

def both(a): return dict(armL=a, armR=a)
def legs(g): return dict(legL=g, legR=g)

STAND = P()
SEAT = 0.45                      # bench/seat top height
PLANK_T, SIDE_T = 95, 103.5        # forearm plank / side plank trunk pitch: elbows and toes both on the floor
SIT = dict(legL=[90, 6, 0, 6], legR=[90, 6, 0, 6])
ON_SEAT = {"z": ("pelvis", SEAT + 0.08)}
FEET = {"x": ("ankle_r", None)}  # keep the near foot planted

def seat_props(back=False, h=SEAT):
    def f(J, J0, *a):
        x = J0["pelvis"].x
        box("seat", (x - 0.05, 0, h - 0.04), (0.42, 0.36, 0.08), "pad")
        box("seat_leg", (x - 0.05, 0, (h - 0.08) / 2), (0.08, 0.08, h - 0.08), "metal")
        if back: box("seat_back", (x - 0.28, 0, h + 0.33), (0.07, 0.36, 0.62), "pad")
    return f

def with_db(base=None, which="lr", axis=None):
    def f(J, J0, *a):
        if base: base(J, J0)
        for s in which: dumbbell("db_" + s, J["hand_" + s], J["gax_" + s])   # handle runs across the knuckles
    return f

def with_bar(base=None, axis=None, length=1.6):
    def f(J, J0, *a):
        if base: base(J, J0)
        barbell("bb", J["hands"], (J["hand_l"] - J["hand_r"]).normalized(), length)
    return f

def with_cable(anchor_fn, base=None, from_="hands", handle=True):
    def f(J, J0, *a):
        if base: base(J, J0)
        A = anchor_fn(J0)
        column("col", A.x + 0.08, A.y, max(2.3, A.z + 0.2))
        rod("cable", A, J[from_], 0.006, "cable")
        if handle and from_ == "hands": rod("handle", J["hand_l"], J["hand_r"], 0.014)
    return f

def with_band(base=None, a="hand_l", b="hand_r", color="band"):
    def f(J, J0, *x):
        if base: base(J, J0)
        rod("band", J[a], J[b], 0.012 if color == "band" else 0.02, color)
    return f

def combine(*fs):
    def f(J, J0, *a):
        for g in fs: g(J, J0)
    return f

def wall_behind(offset=0.16, joint="shoulders"):
    return lambda J, J0, *a: box("wall", (J0[joint].x - offset - 0.05, 0, 1.2), (0.1, 2.2, 2.4), "wall")

def incline_pad(J, J0, *a, T=132):
    n = d(T - 90)                      # chest-facing direction
    c = (J0["chest"] + J0["pelvis"]) / 2 + n * 0.13
    box("incline", c, (0.9, 0.34, 0.06), "pad", pitch=-(T - 90))
    box("incline_leg", (c.x - 0.1, 0, c.z / 2), (0.08, 0.08, c.z), "metal")

SPECS = []
def A(name, keys, **kw):
    kw.update(name=name, keys=keys); SPECS.append(kw)

# ---------------- PULLING ----------------
A("seated-cable-row", [
    P(T=168, **SIT, **both([90, 8, 90, 6])),
    P(T=184, **SIT, **both([-40, 14, 88, 6]))],
  anchor=ON_SEAT, props=with_cable(lambda J0: V((J0["hands"].x + 1.0, 0, J0["hands"].z)), seat_props()))

A("chest-supported-row", [
    P(T=132, H=150, legL=[-18, 6, -10, 6], legR=[-18, 6, -10, 6], **both([0, 8, 0, 4])),
    P(T=132, H=150, legL=[-18, 6, -10, 6], legR=[-18, 6, -10, 6], **both([-72, 16, 0, 6]))],
  anchor=FEET, props=with_db(incline_pad))

A("one-arm-row", [
    P(T=96, H=110, armL=[0, 4, 0, 4], armR=[0, 10, 0, 6], legL=[0, 6, -90, 6, -80], legR=[-8, 14, 0, 8]),
    P(T=96, H=110, armL=[0, 4, 0, 4], armR=[-78, 10, 0, 6], legL=[0, 6, -90, 6, -80], legR=[-8, 14, 0, 8])],
  anchor={"x": ("ankle_r", None)},
  props=with_db(lambda J, J0: bench("bench", J0["ankle_l"].x - 0.12, J0["hand_l"].x + 0.15, J0["knee_l"].z - 0.04), "r"))

A("door-towel-row", [
    P(T=214, H=208, legL=[34, 4, 34, 4], legR=[34, 4, 34, 4], **both([118, 6, 118, 4])),
    P(T=190, H=186, legL=[10, 4, 10, 4], legR=[10, 4, 10, 4], **both([-28, 18, 98, 6]))],
  anchor={"x": ("ankle_r", None)},
  props=lambda J, J0, *a: (box("door", (J0["hands"].x + 0.12, 0, 1.05), (0.05, 0.9, 2.1), "wood"),
                           rod("towel", J0["hands"] + V((0.1, 0, 0)), J["hands"], 0.02, "towel")), cam=dict(az=-108))

A("prone-towel-pulldown", [
    P(T=90, H=110, legL=[-90, 4, -90, 4, -80], legR=[-90, 4, -90, 4, -80], **both([104, 22, 104, 22])),
    P(T=90, H=110, legL=[-90, 4, -90, 4, -80], legR=[-90, 4, -90, 4, -80], **both([-100, 62, 104, 26]))],
  props=with_band(color="towel"), cam=dict(el=16))

A("lat-pulldown", [
    P(**SIT, **both([174, 34, 174, 16])),
    P(T=186, **SIT, **both([10, 56, 168, 14]))],
  anchor=ON_SEAT, props=lambda J, J0, *a: (seat_props()(J, J0), column("col", J0["pelvis"].x + 0.85, 0, 2.45),
      rod("beam", V((J0["pelvis"].x + 0.85, 0, 2.4)), V((J0["hands"].x, 0, 2.4)), 0.035),
      rod("cable", V((J0["hands"].x, 0, 2.4)), J["hands"], 0.006, "cable"),
      rod("lat_bar", J["hand_l"] + V((0, 0.14, 0)), J["hand_r"] - V((0, 0.14, 0)), 0.015)))

A("pull-up", [
    P(H=180, legL=[0, 4, -40, 4], legR=[0, 4, -40, 4], **both([176, 30, 176, 14])),
    P(H=186, legL=[5, 4, -45, 4], legR=[5, 4, -45, 4], **both([10, 58, 170, 14]))],
  anchor={"z": ("hand_r", 2.18), "x": ("hand_r", None)},
  props=lambda J, J0, *a: (rod("pullbar", V((J0["hands"].x, 0.55, 2.18)), V((J0["hands"].x, -0.55, 2.18)), 0.018),
                           rod("brk_l", V((J0["hands"].x, 0.55, 2.18)), V((J0["hands"].x - 0.5, 0.55, 2.18)), 0.02),
                           rod("brk_r", V((J0["hands"].x, -0.55, 2.18)), V((J0["hands"].x - 0.5, -0.55, 2.18)), 0.02),
                           box("wall", (J0["hands"].x - 0.55, 0, 1.3), (0.1, 2.2, 2.6), "wall")))

A("pullover", [
    P(T=270, H=270, **SIT, **both([248, 12, 252, 6])),
    P(T=270, H=270, **SIT, **both([180, 12, 176, 6]))],
  anchor={"z": ("pelvis", SEAT + 0.12)},
  props=lambda J, J0, *a: (bench("bench", J0["head"].x - 0.05, J0["pelvis"].x + 0.15, SEAT),
                           dumbbell("db", J["hands"], (0, 0, 1), 0.28)))

A("straight-arm-pulldown", [
    P(T=166, H=172, **both([150, 10, 150, 6])),
    P(T=166, H=172, **both([12, 10, 12, 6]))],
  anchor=FEET, props=with_cable(lambda J0: V((J0["hands"].x + 0.9, 0, 2.15))))

A("face-pull", [
    P(H=180, **both([95, 10, 95, 6])),
    P(H=182, **both([92, 78, 176, 14]))],
  anchor=FEET, props=lambda J, J0, *a: (column("col", J0["hands"].x + 1.05, 0, 2.3),
                                          rod("rope_l", V((J0["hands"].x + 1.0, 0, J0["hands"].z)), J["hand_l"], 0.012, "cable"),
                                          rod("rope_r", V((J0["hands"].x + 1.0, 0, J0["hands"].z)), J["hand_r"], 0.012, "cable")),
  cam=dict(az=-55))

A("rear-delt-fly", [P(**both([90, 6, 90, 6])), P(**both([90, 86, 90, 86]))], anchor=FEET, cam=dict(az=-40))
A("band-pull-apart", [P(**both([90, 8, 90, 8])), P(**both([90, 82, 90, 82]))], anchor=FEET, props=with_band(), cam=dict(az=-40))

A("incline-rear-delt-raise", [
    P(T=132, H=150, legL=[-18, 6, -10, 6], legR=[-18, 6, -10, 6], **both([0, 8, 0, 8])),
    P(T=132, H=150, legL=[-18, 6, -10, 6], legR=[-18, 6, -10, 6], **both([20, 82, 20, 82]))],
  anchor=FEET, props=with_db(incline_pad, axis=(1, 0, 0)),
  cam=dict(az=-45))

A("external-rotation", [P(**both([2, 10, 90, 6])), P(**both([2, 12, 90, 70]))], anchor=FEET, props=with_band(), cam=dict(az=-30, el=25))

A("scap-squeeze", [P(**both([4, 12, 90, 8])), P(**both([-32, 22, 88, 14]))], anchor=FEET, cam=dict(az=-40, el=15))

A("y-raise", [P(T=170, **both([8, 12, 8, 12])), P(T=170, **both([158, 34, 160, 34]))], anchor=FEET, cam=dict(az=-35))

A("incline-y-raise", [
    P(T=132, H=150, legL=[-18, 6, -10, 6], legR=[-18, 6, -10, 6], **both([0, 10, 0, 10])),
    P(T=132, H=150, legL=[-18, 6, -10, 6], legR=[-18, 6, -10, 6], **both([128, 32, 128, 32]))],
  anchor=FEET, props=with_db(incline_pad, axis=(1, 0, 0)),
  cam=dict(az=-50))

PRONE = dict(T=90, H=100, legL=[-90, 5, -90, 5, -80], legR=[-90, 5, -90, 5, -80])
A("prone-ytw", [
    P(**PRONE, **both([90, 34, 90, 34])), P(**PRONE, **both([106, 34, 106, 34])),
    P(**PRONE, **both([92, 84, 92, 84])), P(**PRONE, **both([118, 76, 118, 76]))],
  props=lambda J, J0, *a: box("mat", (J0["pelvis"].x, 0, 0.005), (2.0, 0.7, 0.01), "mat"), cam=dict(az=-50, el=24))

A("swimmers", [
    P(**PRONE, **both([102, 16, 102, 16])), P(**PRONE, **both([102, 84, 102, 84])),
    P(**PRONE, **both([-102, 84, -102, 84])), P(**PRONE, **both([-102, 16, -102, 16]))],
  props=lambda J, J0, *a: box("mat", (J0["pelvis"].x, 0, 0.005), (2.0, 0.7, 0.01), "mat"), cam=dict(az=-50, el=24), pingpong=True)

# ---------------- NECK / POSTURE ----------------
A("chin-tuck", [P(N=156, H=186), P(N=190, H=174)], anchor=FEET,
  focus=["pelvis", "head", "shoulder_l", "shoulder_r", "hand_r"], cam=dict(az=-88, el=12, margin=1.25))
A("chin-tuck-supine", [P(T=270, N=270, H=270, **legs([135, 8, -48, 8]), **both([90, 14, 90, 14])), P(T=270, N=244, H=228, **legs([135, 8, -48, 8]), **both([90, 14, 90, 14]))],
  focus=["pelvis", "head", "shoulders", "hand_r"], cam=dict(az=-80, el=14, margin=1.3),
  props=lambda J, J0, *a: box("mat", (J0["pelvis"].x - 0.2, 0, 0.005), (2.0, 0.7, 0.01), "mat"))
A("wall-slide", [P(**both([180, 88, 180, 4])), P(**both([180, 34, 180, 22]))], anchor=FEET,
  props=wall_behind(0.18), cam=dict(az=-22, el=14))

# ---------------- PRESSING ----------------
A("push-up", [
    P(T=113, H=124, **both([0, 10, 0, 6]), **legs([-67, 5, -67, 5, 10])),
    P(T=97, H=106, **both([-128, 38, 10, 10]), **legs([-83, 5, -83, 5, 0]))],
  anchor={"x": ("hand_r", None)}, cam=dict(az=-62))

A("incline-push-up", [
    P(T=128, H=135, **both([0, 10, 0, 6]), **legs([-52, 5, -52, 5, 25])),
    P(T=114, H=120, **both([-120, 38, 12, 10]), **legs([-66, 5, -66, 5, 20]))],
  anchor={"x": ("ankle_r", None)},
  props=lambda J, J0, *a: bench("bench", J0["hands"].x - 0.25, J0["hands"].x + 0.25, J0["hands"].z - 0.03))

SUP_BENCH = dict(T=270, H=270, legL=[90, 16, 0, 10], legR=[90, 16, 0, 10])
A("bench-press", [P(**SUP_BENCH, **both([0, 58, 180, 6])), P(**SUP_BENCH, **both([180, 10, 180, 6]))],
  anchor={"z": ("pelvis", SEAT + 0.12)},
  props=with_db(lambda J, J0: bench("bench", J0["head"].x - 0.1, J0["pelvis"].x + 0.2, SEAT)), cam=dict(az=-60, el=12))
A("incline-press", [P(T=240, H=240, legL=[90, 16, 0, 10], legR=[90, 16, 0, 10], **both([-30, 56, 150, 6])),
                    P(T=240, H=240, legL=[90, 16, 0, 10], legR=[90, 16, 0, 10], **both([150, 10, 150, 6]))],
  anchor={"z": ("pelvis", SEAT + 0.1)},
  props=with_db(lambda J, J0: (box("inc_back", (J0["pelvis"] + J0["chest"]) / 2 + d(240 + 90) * 0.13, (0.75, 0.32, 0.07), "pad", pitch=30),
                               box("seat", (J0["pelvis"].x + 0.05, 0, SEAT - 0.04), (0.4, 0.32, 0.08), "pad"))), cam=dict(az=-60, el=12))
A("floor-press", [P(T=270, H=270, legL=[135, 8, -48, 8], legR=[135, 8, -48, 8], **both([90, 80, 180, 6])),
                  P(T=270, H=270, legL=[135, 8, -48, 8], legR=[135, 8, -48, 8], **both([180, 10, 180, 6]))],
  props=with_db(lambda J, J0: box("mat", (J0["pelvis"].x, 0, 0.005), (2.0, 0.7, 0.01), "mat")), cam=dict(az=-60, el=14))
A("seated-chest-press", [P(**SIT, **both([-80, 42, 90, 6])), P(**SIT, **both([90, 12, 90, 6]))],
  anchor=ON_SEAT, props=seat_props(back=True))
A("cable-chest-press", [
    P(legL=[16, 4, 0, 4], legR=[-14, 4, -8, 4], **both([-80, 42, 90, 6])),
    P(legL=[16, 4, 0, 4], legR=[-14, 4, -8, 4], **both([90, 12, 90, 6]))],
  anchor=FEET, props=lambda J, J0, *a: (column("col", J0["shoulders"].x - 0.7, 0, 2.3), rod("cable_l", V((J0["shoulders"].x - 0.65, 0.5, J0["hands"].z)), J["hand_l"], 0.006, "cable"),
                                         rod("cable_r", V((J0["shoulders"].x - 0.65, -0.5, J0["hands"].z)), J["hand_r"], 0.006, "cable")))
A("shoulder-press", [P(**SIT, **both([180, 86, 180, 6])), P(**SIT, **both([180, 14, 180, 8]))],
  anchor=ON_SEAT, props=with_db(seat_props(back=True)), cam=dict(az=-35))
HALF_KNEEL = dict(legL=[90, 8, 0, 8], legR=[0, 8, -90, 8, -80])
A("angled-press", [P(**HALF_KNEEL, armL=[4, 8, 4, 6], armR=[18, 22, 162, 6]),
                   P(**HALF_KNEEL, armL=[4, 8, 4, 6], armR=[140, 12, 140, 6])],
  props=lambda J, J0, *a: rod("landmine", V((J0["pelvis"].x - 1.2, 0, 0.03)), J["hand_r"], 0.022))
A("serratus-punch", [P(T=270, H=270, legL=[135, 8, -48, 8], legR=[135, 8, -48, 8], armL=[90, 10, 90, 10], armR=[180, 4, 180, 4]),
                     P(T=270, H=270, legL=[135, 8, -48, 8], legR=[135, 8, -48, 8], armL=[90, 10, 90, 10], armR=[180, 4, 180, 4], clavR=38)],
  props=with_db(lambda J, J0: box("mat", (J0["pelvis"].x, 0, 0.005), (2.0, 0.7, 0.01), "mat"), "r", (0, 1, 0)),
  focus=["head", "pelvis", "hand_r", "knee_r", "ankle_r", "shoulder_r"], cam=dict(az=-80, el=14, margin=1.3))

# ---------------- HIPS / GLUTES ----------------
BRIDGE_DOWN = dict(T=270, H=270, legL=[153, 8, 29, 8], legR=[153, 8, 29, 8], **both([81, 14, 81, 14]))   # feet ~40 cm from hips, knees up
BRIDGE_UP = dict(T=303, H=276, legL=[110, 8, -2, 8], legR=[110, 8, -2, 8], **both([81, 14, 81, 14]))
mat_under = lambda J, J0, *a: box("mat", (J0["pelvis"].x, 0, 0.005), (2.0, 0.7, 0.01), "mat")
A("glute-bridge", [P(**BRIDGE_DOWN), P(**BRIDGE_UP)], anchor={"x": ("ankle_r", None)}, props=mat_under, cam=dict(az=-62, el=12), free=["hand_l", "hand_r"])
A("single-leg-bridge", [P(**dict(BRIDGE_DOWN, legR=[150, 8, 150, 8])), P(**dict(BRIDGE_UP, legR=[128, 8, 128, 8]))],
  anchor={"x": ("ankle_l", None)}, props=mat_under, cam=dict(az=-62, el=12), free=["hand_l", "hand_r"])
A("hip-thrust", [
    P(T=238, H=255, legL=[128, 10, -14, 10], legR=[128, 10, -14, 10], **both([90, 30, 90, 30])),
    P(T=272, H=292, legL=[92, 10, 0, 10], legR=[92, 10, 0, 10], **both([90, 30, 90, 30]))],
  anchor={"x": ("ankle_r", None)},
  props=lambda J, J0, *a: (bench("bench", J0["chest"].x - 0.55, J0["chest"].x + 0.05, 0.42),
                           barbell("bb", (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, 0, 0.12)))))

HINGE_UP = dict(H=180, **both([2, 8, 2, 6]), legL=[0, 6, 2, 6], legR=[0, 6, 2, 6])
HINGE_DN = dict(T=104, H=116, **both([0, 8, 0, 6]), legL=[14, 6, -4, 6], legR=[14, 6, -4, 6])
A("rdl-dumbbell", [P(**HINGE_UP), P(**HINGE_DN)], anchor=FEET, props=with_db())
A("rdl-barbell", [P(**HINGE_UP), P(**HINGE_DN)], anchor=FEET, props=with_bar())
A("pull-through", [P(**{**HINGE_UP, **both([12, 2, 12, 2])}), P(**{**HINGE_DN, **both([-24, 2, -24, 2]), "legL": [14, 12, -4, 10], "legR": [14, 12, -4, 10]})],
  anchor=FEET, props=with_cable(lambda J0: V((J0["pelvis"].x - 1.1, 0, 0.25))))
A("deadlift", [P(**{**HINGE_UP, **both([8, -6, 8, -6])}), P(T=128, H=140, **both([0, -4, 0, -4]), legL=[62, 14, -22, 10], legR=[62, 14, -22, 10])],
  anchor=FEET, props=lambda J, J0, *a: kettlebell("kb", J["hands"]))
A("trap-bar-deadlift", [P(**{**HINGE_UP, **both([0, 14, 0, 10])}), P(T=128, H=140, **both([0, 14, 0, 10]), legL=[62, 8, -22, 8], legR=[62, 8, -22, 8])],
  anchor=FEET, props=with_bar(length=1.4))
A("single-leg-rdl", [
    P(H=180, armL=[2, 8, 2, 6], armR=[2, 8, 2, 6], legL=[0, 4, 2, 4], legR=[-14, 4, -20, 4]),
    P(T=98, H=108, armL=[0, 8, 0, 6], armR=[0, 8, 0, 6], legL=[10, 4, -3, 4], legR=[-82, 4, -82, 4, -10])],
  anchor={"x": ("ankle_l", None)}, props=lambda J, J0, *a: kettlebell("kb", J["hand_r"]))
A("back-extension", [
    P(T=36, H=40, **both([0, 10, 0, 10]), legL=[-45, 6, -45, 6], legR=[-45, 6, -45, 6]),
    P(T=135, H=140, **both([-10, 30, 160, 30]), legL=[-45, 6, -45, 6], legR=[-45, 6, -45, 6])],
  anchor={"z": ("ankle_r", 0.55), "x": ("ankle_r", None)},
  props=lambda J, J0, *a: (box("pad", J0["hips"] + V((0.10, 0, -0.08)), (0.10, 0.42, 0.26), "pad", pitch=-45),
                           rod("frame", J0["hips"] + V((0.08, 0, -0.22)), J0["ankle_r"] + V((0.0, 0, -0.10)), 0.03),
                           rod("upright", J0["hips"] + V((0.08, 0, -0.22)), V((J0["hips"].x + 0.08, 0, 0)), 0.03),
                           box("foot", J0["ankle_r"] + V((0.03, 0, -0.07)), (0.22, 0.42, 0.05), "pad", pitch=-45)), cam=dict(az=-80))
A("hip-hinge", [P(**HINGE_UP), P(**dict(HINGE_DN, **both([2, 8, 2, 6])))], anchor=FEET, props=wall_behind(0.45, "pelvis"))
A("kb-swing", [P(T=112, H=120, **both([-22, 4, -22, 4]), legL=[40, 10, -16, 8], legR=[40, 10, -16, 8]),
               P(H=180, **both([92, 4, 92, 4]))], anchor=FEET, props=lambda J, J0, *a: kettlebell("kb", J["hands"]))

# ---------------- SQUAT / LUNGE / STEP ----------------
GOBLET = both([-5, 10, 140, -25])
A("goblet-squat", [P(**GOBLET), P(T=150, H=168, **GOBLET, legL=[82, 14, -24, 8], legR=[82, 14, -24, 8])],
  anchor=FEET, props=lambda J, J0, *a: dumbbell("db", J["hands"] + V((0.04, 0, -0.06)), (0, 0, 1), 0.28))
A("box-squat", [P(**GOBLET), P(T=150, H=168, **GOBLET, legL=[82, 14, -24, 8], legR=[82, 14, -24, 8])],
  anchor=FEET, props=lambda J, J0, *a: (dumbbell("db", J["hands"] + V((0.04, 0, -0.06)), (0, 0, 1), 0.28),
                                         box("box", (J0["ankle_r"].x - 0.42, 0, 0.22), (0.4, 0.45, 0.44), "wood")))
A("bodyweight-squat", [P(), P(T=150, H=168, **both([90, 10, 90, 8]), legL=[82, 14, -24, 8], legR=[82, 14, -24, 8])], anchor=FEET)
A("wall-sit", [P(**both([4, 10, 80, 10]), legL=[90, 10, 0, 8], legR=[90, 10, 0, 8]),
               P(**both([4, 10, 78, 10]), legL=[86, 10, -2, 8], legR=[86, 10, -2, 8])],
  anchor=FEET, props=wall_behind(0.16))
A("leg-press", [
    P(T=232, H=225, **both([20, 18, 60, 10]), legL=[140, 12, 34, 10], legR=[140, 12, 34, 10]),
    P(T=232, H=225, **both([20, 18, 60, 10]), legL=[118, 10, 116, 8], legR=[118, 10, 116, 8])],
  anchor={"z": ("pelvis", 0.52), "x": ("pelvis", 0)},
  props=lambda J, J0, *a: (box("back", (J0["pelvis"] + J0["chest"]) / 2 + d(232 + 90) * 0.14, (0.75, 0.42, 0.07), "pad", pitch=38),
                           box("seat", (J0["pelvis"].x + 0.02, 0, 0.42), (0.42, 0.42, 0.08), "pad"),
                           box("plate", (J["ankle_l"] + J["ankle_r"]) / 2 + V((0.07, 0, 0.02)), (0.05, 0.6, 0.55), "metal", pitch=-26)))
A("leg-extension", [P(armL=[4, 20, 30, 20], armR=[4, 20, 30, 20], legL=[90, 6, -6, 6], legR=[90, 6, -6, 6]),
                    P(armL=[4, 20, 30, 20], armR=[4, 20, 30, 20], legL=[90, 6, 78, 6], legR=[90, 6, 78, 6])],
  anchor=ON_SEAT, props=combine(seat_props(back=True), lambda J, J0, *a: rod("shin_pad", J["ankle_l"] + V((0.06, 0.12, 0.05)), J["ankle_r"] + V((0.06, -0.12, 0.05)), 0.05, "pad")))
SPLIT_UP = dict(legL=[14, 4, -2, 4], legR=[-22, 4, -14, 4, 40])
SPLIT_DN = dict(legL=[82, 4, -18, 4], legR=[-12, 4, -98, 4, 20])
A("split-squat", [P(**SPLIT_UP, **both([2, 8, 2, 6])), P(**SPLIT_DN, **both([0, 8, 0, 6]))], anchor={"x": ("ankle_l", None)}, props=with_db())
A("smith-split-squat", [P(**SPLIT_UP, **both([-40, 70, 170, 20])), P(**SPLIT_DN, **both([-40, 70, 170, 20]))], anchor={"x": ("ankle_l", None)},
  props=lambda J, J0, *a: barbell("bb", J["shoulders"] + V((-0.08, 0, 0.07)), length=1.5))
A("reverse-lunge", [P(**both([2, 8, 2, 6])), P(**SPLIT_DN, **both([0, 8, 0, 6]))], anchor={"x": ("ankle_l", None)}, props=with_db())
A("rfess", [P(legL=[10, 4, -2, 4], legR=[-30, 4, -110, 4, -100], **both([0, 8, 0, 6])),
            P(legL=[78, 4, -22, 4], legR=[-6, 4, -120, 4, -105], **both([0, 8, 0, 6]))],
  anchor={"x": ("ankle_l", None)}, props=with_db(lambda J, J0: bench("bench", J0["ankle_r"].x - 0.35, J0["ankle_r"].x + 0.15, J0["ankle_r"].z - 0.03)))
A("step-up", [P(**both([2, 8, 2, 6]), legL=[0, 4, 0, 4], legR=[78, 4, -14, 4]),
              P(**both([2, 8, 2, 6]), legL=[-10, 4, -70, 4, -40], legR=[0, 4, 0, 4], anchor={"z": ("ankle_r", 0.37), "x": ("ankle_r", None)})],
  anchor={"x": ("ankle_l", None)}, props=with_db(lambda J, J0: box("box", (J0["ankle_r"].x + 0.04, 0, 0.15), (0.45, 0.6, 0.30), "wood")))

# ---------------- ABDUCTION ----------------
A("hip-abduction", [P(armL=[24, 34, 30, 20], armR=[4, 8, 4, 6]), P(armL=[24, 34, 30, 20], armR=[4, 8, 4, 6], legR=[0, 34, 0, 34])],
  anchor={"x": ("ankle_l", None)}, props=lambda J, J0, *a: box("support", (J0["hand_l"].x, J0["hand_l"].y, J0["hand_l"].z / 2), (0.06, 0.06, J0["hand_l"].z), "metal"),
  cam=dict(az=-15, el=8))
A("seated-abduction", [P(**SIT, **both([4, 22, 60, 22])), P(**both([4, 22, 60, 22]), legL=[90, 34, -4, 34], legR=[90, 34, -4, 34])],
  anchor=ON_SEAT, props=seat_props(back=True), cam=dict(az=-15, el=30))
WALK_SQ = dict(T=165, H=176, **both([30, 14, 60, 14]))
A("lateral-walk", [P(**WALK_SQ, legL=[30, 8, -16, 8], legR=[30, 20, -16, 20]), P(**WALK_SQ, legL=[30, 20, -16, 20], legR=[30, 8, -16, 8])],
  props=with_band(a="knee_l", b="knee_r"), cam=dict(az=-12, el=8))
SIDE_LY = dict(T=90, roll=-90, H=90, armL=[90, 0, 90, 0], armR=[-90, 0, -90, 0])
A("side-lying-abduction", [P(**SIDE_LY, legL=[-90, 0, -90, 0], legR=[-90, 0, -90, 0]), P(**SIDE_LY, legL=[-90, 0, -90, 0], legR=[-118, 0, -118, 0])],
  props=mat_under, cam=dict(az=-80, el=18))

# ---------------- CORE ----------------
A("plank", [P(T=PLANK_T, H=PLANK_T + 8, **both([0, 4, 90, -10]), **legs([PLANK_T - 180, 4, PLANK_T - 180, 4, 10])), P(T=PLANK_T + 1, H=PLANK_T + 9, **both([0, 4, 90, -10]), **legs([PLANK_T - 179, 4, PLANK_T - 179, 4, 10]))], anchor={"z": ("elbow_r", 0.045)},
  props=mat_under, cam=dict(el=14))
A("plank-reach", [P(T=PLANK_T, H=PLANK_T + 8, **both([0, 4, 90, -10]), **legs([PLANK_T - 180, 4, PLANK_T - 180, 4, 10])),
                  P(T=PLANK_T, H=PLANK_T + 12, armL=[0, 4, 90, -10], armR=[92, 6, 92, 4], **legs([PLANK_T - 180, 4, PLANK_T - 180, 4, 10]))], anchor={"z": ("elbow_l", 0.045)},
  props=mat_under, cam=dict(el=14))
HIGH_PLANK = dict(T=109, H=120, **legs([-71, 10, -71, 10, 15]))
A("shoulder-taps", [P(**HIGH_PLANK, **both([0, 10, 0, 6])), P(**HIGH_PLANK, armL=[0, 10, 0, 6], armR=[40, -30, 150, -60])],
  anchor={"x": ("hand_l", None)}, props=mat_under, cam=dict(az=-50, el=14))
# hips lift slightly as the knee drives through (as people do), so the swinging knee clears the floor
MC_TUCK, MC_MID, MC_BACK = [70, 6, -78, 6, -20], [-25, 6, -100, 6, -40], [-71, 6, -71, 6, 15]
MC_UP = {**HIGH_PLANK, "T": 100, "H": 112}   # flatter trunk = hips higher (hands fixed)
A("mountain-climbers", [P(**{**HIGH_PLANK, **both([0, 10, 0, 6]), "legR": MC_TUCK, "legL": MC_BACK}),
                        P(**{**MC_UP, **both([0, 10, 0, 6]), "legR": MC_MID, "legL": MC_MID}),
                        P(**{**HIGH_PLANK, **both([0, 10, 0, 6]), "legL": MC_TUCK, "legR": MC_BACK}),
                        P(**{**MC_UP, **both([0, 10, 0, 6]), "legR": MC_MID, "legL": MC_MID})],
  anchor={"x": ("hand_r", None)}, plant=["hand_l", "hand_r"], props=mat_under, steps=3, cam=dict(el=14))
SUP = dict(T=270, H=270)
A("dead-bug", [P(**SUP, **both([180, 8, 180, 8]), **legs([180, 8, 90, 8])),
               P(**SUP, armL=[180, 8, 180, 8], armR=[256, 8, 256, 8], legL=[98, 8, 98, 8], legR=[180, 8, 90, 8]),
               P(**SUP, **both([180, 8, 180, 8]), **legs([180, 8, 90, 8])),
               P(**SUP, armL=[256, 8, 256, 8], armR=[180, 8, 180, 8], legL=[180, 8, 90, 8], legR=[98, 8, 98, 8])],
  props=mat_under, cam=dict(az=-62, el=14))
QUAD = dict(T=90, H=110, **both([0, 4, 0, 4]), **legs([0, 4, -90, 4, -80]))
A("bird-dog", [P(**QUAD), P(**dict(QUAD, armR=[92, 4, 92, 4], legL=[-90, 4, -90, 4, -80])),
               P(**QUAD), P(**dict(QUAD, armL=[92, 4, 92, 4], legR=[-90, 4, -90, 4, -80]))],
  props=mat_under, cam=dict(az=-62, el=12))
A("cat-cow", [P(**dict(QUAD, S1=114, S2=96, S3=70, H=30)), P(**dict(QUAD, S1=72, S2=86, S3=110, H=140))], props=mat_under, cam=dict(az=-80, el=8))
MCG = dict(T=270, legL=[90, 4, 90, 4], legR=[135, 8, -48, 8], **both([90, 14, 90, 14]))
A("mcgill-curl-up", [P(**MCG, S=270, H=270), P(**MCG, S=256, H=252)], props=mat_under,
  cam=dict(az=-75, el=10))
A("hollow-hold", [P(T=270, S=246, H=236, **both([128, 8, 128, 8]), **legs([150, 6, 96, 6])),
                  P(T=270, S=240, H=230, **both([124, 8, 124, 8]), **legs([146, 6, 92, 6]))], props=mat_under, cam=dict(az=-70, el=10))
SIDEP = dict(roll=-90, armL=[0, 0, 90, -90], armR=[-10, 0, 40, 0])   # left side down; bottom forearm points where the chest faces (-Y)
A("side-plank", [P(T=SIDE_T, H=SIDE_T, **SIDEP, legL=[SIDE_T - 180, 0, SIDE_T - 180, 0, 90, -90], legR=[SIDE_T - 180, 0, SIDE_T - 180, 0, 90, 90]), P(T=SIDE_T + 1.5, H=SIDE_T + 1.5, **SIDEP, legL=[SIDE_T - 178.5, 0, SIDE_T - 178.5, 0, 90, -90], legR=[SIDE_T - 178.5, 0, SIDE_T - 178.5, 0, 90, 90])],
  anchor={"z": ("elbow_l", 0.045), "x": ("ankle_l", None)}, props=mat_under, cam=dict(az=-88, el=10))
A("push-up-to-side-plank", [P(**HIGH_PLANK, **both([0, 10, 0, 6])), P(T=107, roll=-90, H=120, armL=[0, 0, 0, 0], armR=[180, 0, 180, 0], **legs([-67, 0, -67, 0, 10]))],
  anchor={"x": ("hand_l", None)}, props=mat_under, cam=dict(az=-70, el=14))
CRUNCH_LEGS = legs([135, 8, -48, 8])
A("crunch", [P(T=270, S=270, H=270, **CRUNCH_LEGS, **both([110, 12, 110, 12])), P(T=270, S=238, H=230, **CRUNCH_LEGS, **both([118, 12, 118, 12]))],
  props=mat_under, cam=dict(az=-70, el=10))
A("swiss-ball-crunch", [P(T=262, S=262, H=262, **legs([96, 16, 0, 10]), **both([130, 30, 120, 30])), P(T=262, S=232, H=226, **legs([96, 16, 0, 10]), **both([140, 30, 130, 30]))],
  anchor={"x": ("ankle_r", None)}, props=lambda J, J0, *a: ball("ball", J0["pelvis"] + V((-0.06, 0, -0.36)), 0.33, "ball"))
A("cable-crunch", [P(T=176, S=176, H=186, armL=[160, 14, 300, 30], armR=[160, 14, 300, 30], **legs([0, 8, -90, 8, -80])),
                   P(T=138, S=74, H=50, armL=[60, 14, 200, 30], armR=[60, 14, 200, 30], **legs([0, 8, -90, 8, -80]))],
  anchor={"x": ("knee_r", None)}, props=with_cable(lambda J0: V((J0["head"].x - 0.7, 0, 2.3)), mat_under, handle=False))
def crunch_machine(J, J0, *a):
    x0 = J0["pelvis"].x
    box("mc_base", (x0 - 0.05, 0, 0.03), (1.1, 0.6, 0.06), "metal")
    box("mc_seat", (x0 + 0.02, 0, SEAT - 0.04), (0.44, 0.40, 0.09), "pad")
    rod("mc_seat_post", V((x0 + 0.02, 0, 0.06)), V((x0 + 0.02, 0, SEAT - 0.09)), 0.045)
    box("mc_back", (x0 - 0.21, 0, SEAT + 0.30), (0.08, 0.38, 0.52), "pad", pitch=-10)
    column("mc_column", x0 - 0.42, 0, 1.75)
    fwd, left, up = body_frame(J)
    piv = V((x0 - 0.42, 0, 1.55))
    anchors = []
    for s_ in "lr":
        sh = J["shoulder_" + s_]
        an = sh - fwd * 0.12 + up * 0.20 + left * (0.06 if s_ == "l" else -0.06)   # strap anchor just behind/above the shoulder
        anchors.append(an)
        rod("mc_strap_" + s_, an, J["hand_" + s_], 0.018, "cable")
        rod("mc_handle_" + s_, J["hand_" + s_] + left * 0.04 * (1 if s_ == "l" else -1), J["hand_" + s_] - left * 0.04 * (1 if s_ == "l" else -1), 0.02, "pad")
    mid = (anchors[0] + anchors[1]) / 2
    rod("mc_yoke", anchors[0], anchors[1], 0.025)
    rod("mc_lever", mid, piv, 0.035)
    box("mc_stack", (x0 - 0.42, 0.45, 0.55), (0.22, 0.14, 0.9), "plate")
    rod("mc_cable", piv, V((x0 - 0.42, 0.45, 1.0)), 0.006, "cable")
    rod("mc_roller", J0["ankle_l"] + fwd * 0.07 + V((0, 0.08, 0.05)), J0["ankle_r"] + fwd * 0.07 + V((0, -0.08, 0.05)), 0.05, "pad")
EAR_L, EAR_R = ("head", (0.04, 0.12, -0.13)), ("head", (0.04, -0.12, -0.13))
A("machine-crunch", [P(**SIT, S=186, H=184, **both([110, 10, 205, 10])), P(**SIT, T=166, S=128, H=112, **both([95, 10, 190, 10]))],
  anchor=ON_SEAT, props=crunch_machine, reach={"hand_l": EAR_L, "hand_r": EAR_R}, cam=dict(az=-62, el=10))
A("reverse-crunch", [P(T=270, H=270, **both([81, 16, 81, 16]), **legs([178, 6, 96, 6])), P(T=280, H=270, **both([81, 16, 81, 16]), **legs([206, 6, 132, 6]))],
  props=mat_under, cam=dict(az=-70, el=10))
A("knee-raise", [P(**both([2, 22, 92, 6]), **legs([0, 4, 0, 4])), P(**both([2, 22, 92, 6]), **legs([96, 6, 4, 6]))],
  anchor={"z": ("pelvis", 1.15), "x": ("pelvis", 0)},
  props=lambda J, J0, *a: (box("backpad", (J0["pelvis"].x - 0.2, 0, 1.45), (0.08, 0.4, 0.8), "pad"),
                           box("rest_l", (J0["elbow_l"].x + 0.1, J0["elbow_l"].y, J0["elbow_l"].z - 0.07), (0.4, 0.12, 0.06), "pad"),
                           box("rest_r", (J0["elbow_r"].x + 0.1, J0["elbow_r"].y, J0["elbow_r"].z - 0.07), (0.4, 0.12, 0.06), "pad"),
                           column("post", J0["pelvis"].x - 0.28, 0, 2.1)))
A("leg-pull-in", [P(T=222, H=200, **both([-34, 12, -12, 12]), **legs([102, 4, 102, 4])), P(T=210, H=195, **both([-34, 12, -12, 12]), **legs([150, 4, 64, 4]))],
  props=mat_under, cam=dict(az=-70, el=10))
A("lying-leg-raise", [P(T=270, H=270, **both([262, 12, 262, 12]), **legs([105, 4, 82, 4])), P(T=270, H=270, **both([262, 12, 262, 12]), **legs([176, 4, 96, 4]))],
  props=mat_under, cam=dict(az=-70, el=10))
A("ab-rollout", [P(T=114, S=122, H=126, **both([4, 6, 4, 6]), **legs([18, 6, -90, 6, -95])), P(T=97, S=96, H=102, **both([62, 6, 62, 6]), **legs([-52, 6, -90, 6, -95]))],
  anchor={"x": ("knee_r", None)}, slide={"hand_l": 0.115, "hand_r": 0.115},
  props=lambda J, J0, *a: (box("mat", (J0["knee_r"].x + 0.3, 0, 0.005), (1.8, 0.7, 0.01), "mat"),
                           rod("wheel", V((J["hands"].x, 0.05, 0.1)), V((J["hands"].x, -0.05, 0.1)), 0.1, "plate"),
                           rod("wheel_hub", V((J["hands"].x, 0.06, 0.1)), V((J["hands"].x, -0.06, 0.1)), 0.03, "metal"),
                           rod("wheel_handle", V((J["hands"].x, J["hand_l"].y, 0.1)), V((J["hands"].x, J["hand_r"].y, 0.1)), 0.016, "metal")))
PALLOF_IN = {"hand_l": ("chest", (0.13, 0.025, -0.15)), "hand_r": ("chest", (0.13, -0.025, -0.15))}     # clasped at the sternum
PALLOF_OUT = {"hand_l": ("chest", (0.55, 0.025, -0.17)), "hand_r": ("chest", (0.55, -0.025, -0.17))}   # pressed straight out
CHOP_HIGH = {"hand_l": ("chest", (0.30, -0.30, 0.36)), "hand_r": ("chest", (0.30, -0.36, 0.30))}       # both hands together, high right
CHOP_LOW = {"hand_l": ("chest", (0.36, 0.40, -0.62)), "hand_r": ("chest", (0.34, 0.34, -0.66))}        # low left
WIDE = dict(legL=[0, 12, 0, 10], legR=[0, 12, 0, 10])
A("woodchop", [P(**WIDE, twist=-24, armL=[140, -38, 140, -38], armR=[140, 38, 140, 38], reach=CHOP_HIGH), P(**WIDE, twist=24, armL=[40, 38, 40, 38], armR=[40, -38, 40, -38], reach=CHOP_LOW)],
  props=with_cable(lambda J0: V((J0["pelvis"].x + 0.3, -1.1, 2.0)), from_="hands", handle=False), cam=dict(az=-40))
A("cable-lift", [P(**WIDE, twist=24, armL=[40, 38, 40, 38], armR=[40, -38, 40, -38], reach=CHOP_LOW), P(**WIDE, twist=-24, armL=[140, -38, 140, -38], armR=[140, 38, 140, 38], reach=CHOP_HIGH)],
  props=with_cable(lambda J0: V((J0["pelvis"].x + 0.3, 1.1, 0.3)), from_="hands", handle=False), cam=dict(az=-40))
A("pallof-press", [P(**WIDE, armL=[12, 20, 100, -55], armR=[12, 20, 100, -55], reach=PALLOF_IN), P(**WIDE, **both([88, 4, 88, -6]), reach=PALLOF_OUT)],
  props=lambda J, J0, *a: (column("col", J0["pelvis"].x, 1.2, 2.3), rod("cable", V((J0["pelvis"].x, 1.15, J0["hands"].z)), J["hands"], 0.006, "cable")), cam=dict(az=-18, el=8))
A("pallof-rotation", [P(**WIDE, **both([88, 4, 88, -6]), reach=PALLOF_OUT), P(**WIDE, twist=-30, armL=[88, -34, 88, -40], armR=[88, 40, 88, 34], reach=PALLOF_OUT)],
  props=lambda J, J0, *a: (column("col", J0["pelvis"].x, 1.2, 2.3), rod("cable", V((J0["pelvis"].x, 1.15, J0["hands"].z)), J["hands"], 0.006, "cable")), cam=dict(az=-18, el=8))
A("landmine-rainbow", [P(**WIDE, twist=-26, armL=[130, 32, 130, 32], armR=[130, -32, 130, -32]), P(**WIDE, twist=26, armL=[130, -32, 130, -32], armR=[130, 32, 130, 32])],
  props=lambda J, J0, *a: rod("landmine", V((J0["pelvis"].x + 1.4, 0, 0.03)), J["hands"], 0.022), cam=dict(az=-45))

# ---------------- STRETCH / MOBILITY ----------------
A("pec-stretch", [P(armL=[4, 8, 4, 6], armR=[90, 88, 180, 2]), P(T=172, armL=[4, 8, 4, 6], armR=[70, 96, 180, 2], legL=[18, 4, 0, 4])],
  anchor={"x": ("ankle_r", None)}, props=lambda J, J0, *a: box("frame", (J0["elbow_r"].x + 0.05, J0["elbow_r"].y - 0.05, 1.05), (0.12, 0.1, 2.1), "wood"),
  cam=dict(az=-140, el=10))
CHILD = dict(T=74, S=72, H=45, **legs([64, 5, -90, 4, -95]))
A("childs-pose", [P(**CHILD, **both([76, 8, 76, 8])), P(**CHILD, armL=[76, -14, 76, -14], armR=[76, 30, 76, 30])],
  props=mat_under, cam=dict(az=-60, el=16))
A("hamstring-stretch", [P(T=270, H=262, legL=[90, 4, 90, 4], legR=[152, 4, 152, 4], **both([150, 8, 150, 8])),
                        P(T=270, H=258, legL=[90, 4, 90, 4], legR=[172, 4, 172, 4], **both([165, 8, 168, 8]))],
  props=lambda J, J0, *a: (mat_under(J, J0), rod("towel", J["hands"], J["toe_r"], 0.018, "towel")), cam=dict(az=-70, el=10))
A("couch-stretch", [P(legL=[90, 6, 0, 6], legR=[-4, 6, 172, 4, 200], **both([4, 10, 90, 10])), P(T=184, legL=[84, 6, -6, 6], legR=[-14, 6, 168, 4, 200], **both([4, 10, 90, 10]))],
  anchor={"x": ("knee_r", None)}, props=lambda J, J0, *a: box("wall", (J0["knee_r"].x - 0.17, 0, 0.55), (0.1, 1.6, 1.1), "wall"))
A("hip-flexor-stretch", [P(**HALF_KNEEL, **both([4, 10, 90, 10])), P(legL=[85, 8, -45, 8], legR=[-30, 8, -90, 8, -80], **both([4, 10, 90, 10]))],
  anchor={"x": ("knee_r", None)}, props=mat_under)
A("figure-4", [P(T=270, H=270, legL=[135, 8, -48, 8], legR=[124, 44, 96, -54], **both([90, 14, 90, 14])),
               P(T=270, H=262, legL=[172, 8, 96, 8], legR=[150, 44, 112, -54], **both([150, 10, 150, -10]))],
  props=mat_under, cam=dict(az=-55, el=20))
A("t-spine-extension", [P(**SIT, **both([160, 40, 300, 40])), P(**SIT, S=212, S3=222, H=226, **both([178, 40, 280, 40]))],
  anchor=ON_SEAT, props=lambda J, J0, *a: (seat_props()(J, J0), box("chair_back", (J0["pelvis"].x - 0.25, 0, SEAT + 0.28), (0.05, 0.4, 0.52), "wood")))
# side-lying (left side down, chest toward -Y): "forward" for knees/arms is -Y, i.e. lateral -90 (left) / +90 (right)
OB = dict(T=90, roll=-90, H=90, legL=[90, -90, -90, 0, 0], legR=[90, 90, -90, 0, 0], armL=[90, -90, 90, -90])
A("open-book", [P(**OB, armR=[90, 90, 90, 90]), P(**OB, armR=[180, 0, 180, 0]), P(**OB, armR=[90, -88, 90, -88])],
  props=mat_under, cam=dict(az=-60, el=40), pingpong=True)
A("snow-angel", [P(T=270, H=270, **legs([135, 8, -48, 8]), **both([90, 24, 90, 24])), P(T=270, H=270, **legs([135, 8, -48, 8]), **both([90, 89, 90, 89])),
                 P(T=270, H=270, **legs([135, 8, -48, 8]), **both([270, 89, 270, 89])), P(T=270, H=270, **legs([135, 8, -48, 8]), **both([270, 24, 270, 24]))],
  props=mat_under, cam=dict(az=-50, el=42), pingpong=True)
A("hip-switch", [P(T=186, **both([-36, 18, -14, 18]), legL=[128, -14, 4, -30], legR=[128, 40, 4, 30]),
                 P(T=186, **both([-36, 18, -14, 18]), legL=[128, 40, 4, 30], legR=[128, -14, 4, -30])],
  props=mat_under, cam=dict(az=-20, el=24))

# ---------------- CARRY / CARDIO ----------------
WALK_A = dict(legL=[20, 4, -4, 4], legR=[-18, 4, -30, 4])
WALK_B = dict(legL=[-18, 4, -30, 4], legR=[20, 4, -4, 4])
A("farmer-carry", [P(**WALK_A, **both([0, 10, 0, 8])), P(**WALK_B, **both([0, 10, 0, 8]))], props=with_db(axis=(1, 0, 0)), steps=5)
A("suitcase-carry", [P(**WALK_A, armR=[0, 10, 0, 8], armL=[8, 8, 14, 6]), P(**WALK_B, armR=[0, 10, 0, 8], armL=[-8, 8, -2, 6])],
  props=with_db(which="r", axis=(1, 0, 0)), steps=5)
A("walk", [P(**WALK_A, armL=[-16, 6, 0, 6], armR=[16, 6, 30, 6]), P(**WALK_B, armL=[16, 6, 30, 6], armR=[-16, 6, 0, 6])], steps=5)
A("treadmill-walk", [P(**WALK_A, armL=[-16, 6, 0, 6], armR=[16, 6, 30, 6]), P(**WALK_B, armL=[16, 6, 30, 6], armR=[-16, 6, 0, 6])], steps=5,
  props=lambda J, J0, *a: (box("deck", (J0["pelvis"].x, 0, -0.03), (1.8, 0.75, 0.08), "metal", pitch=-6),
                           column("console_l", J0["pelvis"].x + 0.85, 0.35, 1.3), column("console_r", J0["pelvis"].x + 0.85, -0.35, 1.3),
                           box("console", (J0["pelvis"].x + 0.85, 0, 1.3), (0.2, 0.8, 0.12), "metal")))
A("ruck-walk", [P(**WALK_A, armL=[-16, 6, 0, 6], armR=[16, 6, 30, 6]), P(**WALK_B, armL=[16, 6, 30, 6], armR=[-16, 6, 0, 6])], steps=5,
  props=lambda J, J0, *a: box("pack", J["chest"] + V((-0.2, 0, -0.18)), (0.18, 0.34, 0.44), "pad"))
import math as _m
BIKE_C = V((0.24, 0, 0.36)); BIKE_R = 0.17; BIKE_FAN = V((0.80, 0, 0.52))
def _pedal(side, ph):
    a = 2 * _m.pi * ph + (0 if side == "l" else _m.pi)
    return BIKE_C + V((BIKE_R * _m.sin(a), 0.13 if side == "l" else -0.13, BIKE_R * _m.cos(a)))
def _bike_hand(side, ph):
    a = 2 * _m.pi * ph + (_m.pi if side == "l" else 0)          # arms opposite the same-side leg
    return V((0.56 + 0.07 * _m.sin(a), 0.25 if side == "l" else -0.25, 1.12))
def bike_track(ctx):
    ph = ctx["phase"]; out = {}
    for s_ in "lr":
        pd = _pedal(s_, ph)
        out["foot_" + s_] = (pd + V((-0.13, 0, 0.075)), pd + V((0.0, 0, 0.012)))   # ball of the foot on the pedal
        out["hand_" + s_] = (_bike_hand(s_, ph), None)
    return out
def bike_props(J, J0, ctx=None, *a):
    ph = ctx["phase"] if ctx else 0.0
    C, F = BIKE_C, BIKE_FAN
    rod("b_rear_foot", V((-0.48, -0.30, 0.04)), V((-0.48, 0.30, 0.04)), 0.035)
    rod("b_front_foot", V((0.98, -0.32, 0.04)), V((0.98, 0.32, 0.04)), 0.035)
    rod("b_beam", V((-0.48, 0, 0.05)), V((0.98, 0, 0.05)), 0.04)
    rod("b_seat_tube", V((-0.05, 0, 0.86)), V((0.14, 0, 0.30)), 0.04)
    rod("b_rear_strut", V((0.14, 0, 0.30)), V((-0.40, 0, 0.05)), 0.035)
    rod("b_down_tube", V((0.14, 0, 0.30)), V((0.62, 0, 0.30)), 0.04)
    rod("b_fan_post", V((0.62, 0, 0.30)), F, 0.04)
    rod("b_front_post", V((0.62, 0, 0.30)), V((0.90, 0, 0.05)), 0.04)
    box("b_saddle", (-0.03, 0, 0.885), (0.28, 0.20, 0.07), "pad")
    rod("b_fan", F + V((0, -0.09, 0)), F + V((0, 0.09, 0)), 0.32, "pad")
    rod("b_fan_rim", F + V((0, -0.095, 0)), F + V((0, 0.095, 0)), 0.30, "metal")
    rod("b_fan_hub", F + V((0, -0.11, 0)), F + V((0, 0.11, 0)), 0.06, "plate")
    rod("b_axle", C + V((0, -0.14, 0)), C + V((0, 0.14, 0)), 0.025, "plate")
    for s_ in "lr":
        pd = _pedal(s_, ph); y = 0.13 if s_ == "l" else -0.13
        rod("b_crank_" + s_, C + V((0, y, 0)), pd, 0.016, "plate")
        box("b_pedal_" + s_, pd + V((0, 0, -0.012)), (0.11, 0.09, 0.025), "plate")
        h = J["hand_" + s_]; piv = V((0.66, 0.20 if s_ == "l" else -0.20, 0.42))
        rod("b_lever_" + s_, piv, h + V((0, 0, -0.06)), 0.022)
        rod("b_grip_" + s_, h + V((0, 0, -0.07)), h + V((0, 0, 0.07)), 0.02, "pad")
    box("b_console", (0.74, 0, 1.02), (0.06, 0.20, 0.14), "plate")
    rod("b_console_post", V((0.78, 0, 0.84)), V((0.74, 0, 0.98)), 0.02)
BIKE_POSE = dict(T=162, H=170, **both([50, 14, 85, 6]), legL=[72, 6, -12, 6], legR=[72, 6, -12, 6])
A("bike", [P(**BIKE_POSE)] * 4, anchor={"z": ("pelvis", 0.965), "x": ("pelvis", 0.0)}, steps=6, linear=True,
  track=bike_track, driven=["foot_l", "foot_r", "hand_l", "hand_r"], props=bike_props, cam=dict(az=-70, el=10))
A("rower", [P(T=158, H=168, **both([84, 6, 88, 4]), **legs([138, 8, 16, 8, 90])), P(T=200, H=192, **both([-40, 16, 92, 6]), **legs([92, 6, 92, 6, 170]))],
  anchor={"z": ("pelvis", 0.38), "x": ("ankle_r", None)},
  props=lambda J, J0, *a: (box("rail", (J0["pelvis"].x + 0.3, 0, 0.2), (1.9, 0.12, 0.08), "metal"), box("row_seat", (J["pelvis"].x - 0.02, 0, 0.3), (0.3, 0.26, 0.06), "pad"),
                           box("flywheel", (J0["pelvis"].x + 1.15, 0, 0.4), (0.2, 0.3, 0.55), "metal"),
                           rod("chain", V((J0["pelvis"].x + 1.05, 0, 0.55)), J["hands"], 0.006, "cable"), rod("row_handle", J["hand_l"], J["hand_r"], 0.016)))
A("battle-ropes", [P(T=165, H=176, armL=[100, 10, 112, 6], armR=[44, 10, 70, 6], **legs([36, 12, -18, 10])),
                   P(T=165, H=176, armL=[44, 10, 70, 6], armR=[100, 10, 112, 6], **legs([36, 12, -18, 10]))], steps=4,
  props=lambda J, J0, *a: (rod("rope_l", J["hand_l"], V((J0["pelvis"].x + 2.2, 0.15, 0.08)), 0.02, "cable"), rod("rope_r", J["hand_r"], V((J0["pelvis"].x + 2.2, -0.15, 0.08)), 0.02, "cable")))


# ---------------- HANDS ----------------
# grip: fist around equipment; flat: palm down on floor/bench; relaxed: slight natural curl (default)
GRIP = """seated-cable-row chest-supported-row door-towel-row prone-towel-pulldown lat-pulldown pull-up pullover straight-arm-pulldown
face-pull band-pull-apart incline-rear-delt-raise external-rotation incline-y-raise bench-press incline-press floor-press seated-chest-press
cable-chest-press shoulder-press hip-thrust rdl-dumbbell rdl-barbell pull-through deadlift trap-bar-deadlift kb-swing goblet-squat box-squat
split-squat smith-split-squat reverse-lunge rfess step-up knee-raise ab-rollout woodchop cable-lift pallof-press pallof-rotation
landmine-rainbow farmer-carry bike rower battle-ropes hamstring-stretch leg-extension cable-crunch""".split()
FLAT = """push-up incline-push-up mountain-climbers push-up-to-side-plank bird-dog cat-cow childs-pose plank plank-reach side-plank
leg-pull-in hip-switch""".split()
SIDED = {"one-arm-row": {"handL": "flat", "handR": "grip"}, "angled-press": {"handR": "grip"}, "serratus-punch": {"handR": "grip"},
         "single-leg-rdl": {"handR": "grip"}, "suitcase-carry": {"handR": "grip"}, "hip-abduction": {"handL": "grip"},
         "shoulder-taps": {"handL": "flat", "handR": "flat"}}
for _s in SPECS:
    _s.setdefault("hands", "grip" if _s["name"] in GRIP else "flat" if _s["name"] in FLAT else "relaxed")
    for _k, _v in SIDED.get(_s["name"], {}).items(): _s.setdefault(_k, _v)

# palm direction (body-relative words, see rig.palm_target): overhand bars, pressing toward the feet, cupped goblet, etc.
PALM = {"rdl-barbell": "back", "deadlift": "back", "kb-swing": "back", "pull-up": "forward", "lat-pulldown": "forward",
        "straight-arm-pulldown": "back", "bench-press": "feet", "incline-press": "feet", "floor-press": "feet", "shoulder-press": "forward",
        "band-pull-apart": "down", "goblet-squat": "head", "box-squat": "head", "hip-thrust": "down", "ab-rollout": "back", "bike": "down",
        "rower": "down", "prone-towel-pulldown": "down", "pullover": "up", "wall-slide": "forward", "pec-stretch": "forward",
        "smith-split-squat": "forward", "trap-bar-deadlift": "in"}
for _s in SPECS:
    if _s["name"] in PALM: _s.setdefault("palm", PALM[_s["name"]])

# hands pinned to the body each frame (IK), offsets in the body frame (forward, left, up) metres
TEMPLE_L, TEMPLE_R = ("head", (0.03, 0.09, -0.11)), ("head", (0.03, -0.09, -0.11))
CROSS_L, CROSS_R = ("shoulder_r", (0.10, 0.04, -0.06)), ("shoulder_l", (0.10, -0.04, -0.06))
HIP_L, HIP_R = ("hip_l", (0.0, 0.10, 0.08)), ("hip_r", (0.0, -0.10, 0.08))
REACH = {"cable-crunch": {"hand_l": TEMPLE_L, "hand_r": TEMPLE_R}, "machine-crunch": {"hand_l": TEMPLE_L, "hand_r": TEMPLE_R},
         "crunch": {"hand_l": CROSS_L, "hand_r": CROSS_R}, "swiss-ball-crunch": {"hand_l": CROSS_L, "hand_r": CROSS_R},
         "lateral-walk": {"hand_l": HIP_L, "hand_r": HIP_R}, "hip-abduction": {"hand_r": HIP_R}, "side-plank": {"hand_r": HIP_R}}
for _s in SPECS:
    if _s["name"] in REACH: _s["reach"] = REACH[_s["name"]]
    if _s["name"] in ("plank", "plank-reach", "side-plank"): _s["free"] = ["hand_l", "hand_r"]   # forearm planks: elbows/forearms carry the load
for _n in ("crunch", "swiss-ball-crunch", "lateral-walk", "machine-crunch", "cable-crunch"):
    next(x for x in SPECS if x["name"] == _n)["hands"] = "relaxed"
next(x for x in SPECS if x["name"] == "hip-abduction")["handR"] = "relaxed"
next(x for x in SPECS if x["name"] == "side-plank")["handR"] = "relaxed"

for _s in SPECS:
    if _s["name"] in ("glute-bridge", "single-leg-bridge", "reverse-crunch"): _s["palm"] = "down"; _s["hands"] = "flat"
    if _s["name"] in ("childs-pose",): _s["slide"] = {"hand_l": 0.03, "hand_r": 0.03}
    if _s["name"] in ("glute-bridge", "single-leg-bridge", "reverse-crunch"): _s["slide"] = {"hand_l": 0.03, "hand_r": 0.03}; _s.pop("free", None)
    if _s["name"] in ("pallof-press", "pallof-rotation", "woodchop", "cable-lift"): _s["hands"] = "grip"
    if _s["name"] in ("plank", "plank-reach"): _s["hands"] = "flat"
