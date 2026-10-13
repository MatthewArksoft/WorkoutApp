# Demo catalogue: every app exercise name -> one animation template built from reference photos
# (free-exercise-db, public domain) via MediaPipe pose landmarks (tools/extract_poses.py + tools/retarget.py),
# with matching equipment from tools/machines.py. Loaded last into the shared Blender namespace.
from mathutils import Vector as V

CAT = []          # templates
def T(tid, names, keys, props=None, **opt):
    opt.update(name=tid, names=names, keys=keys, props=props); CAT.append(opt)

K = LM
def two(ref, **kw): return [K(ref, 0, **kw), K(ref, 1, **kw)]
def alt(ref, **kw): return [K(ref, 0, **kw), K(ref, 1, **kw), K(ref, 0, mirror_post=True, **kw), K(ref, 1, mirror_post=True, **kw)]
def gait(ref, i, **kw): return [K(ref, i, **kw), K(ref, i, mirror_post=True, **kw)]
def hold(ref, i, **kw): return [K(ref, i, **kw), K(ref, i, curve=4, **kw)]
def P_(*fs):
    def f(J, J0, *a):
        for g in fs: g(J, J0, *a)
    return f

SEATED = {}
SUP = "Butt_Lift_Bridge"                       # clean supine base: lying, knees bent, feet flat (head toward -X, feet +X)
ARMS_SIDE = dict(fk_armL=[95, 18, 95, 18], fk_armR=[95, 18, 95, 18])                                    # ground anchor: feet on the floor, seat fitted under the hips
BENCH = {"z": ("torso", 0.46)}                 # lying on a flat bench
SEATZ = lambda h: {"z": ("seat", h)}

# shorthand equipment
DB = lambda which="lr": lambda J, J0, *a: [dumbbell("db_" + s, J["hand_" + s], J["gax_" + s]) for s in which]
KB = lambda which="lr": lambda J, J0, *a: [kettlebell("kb_" + s, J["hand_" + s], up=J["elbow_" + s] - J["hand_" + s], side=J["gax_" + s]) for s in which]
BB = lambda length=1.6: lambda J, J0, *a: barbell("bb", J["hands"], (J["hand_l"] - J["hand_r"]).normalized(), length)
MAT = lambda J, J0, *a: mat("mat", J0)
def COL(pz=None, y=0.0, dx=0.85, hand="hands", handle="rope"):
    """Cable tower in front of the body (+X) with the pulley at hand height (or pz), cable to the hand(s)."""
    def f(J, J0, *a):
        h0 = J0[hand]; p = cable_column("col", h0.x + dx, y, pz if pz is not None else h0.z)
        h = J[hand]; cable("cab", p, h + V((0.04, 0, 0)))
        if handle == "rope":
            rod("rope_l", h, J["hand_l"], 0.012, "cable"); rod("rope_r", h, J["hand_r"], 0.012, "cable")
        elif handle == "bar": handle_bar("hbar", J["hand_l"] + V((0, 0.1, 0)), J["hand_r"] + V((0, -0.1, 0)))
        elif handle == "d": d_handle("dh", J[hand], (0, 0, 1))
    return f
def COL_SIDE(side_y, pz=None, hand="hands", handle="d"):
    """Cable tower beside the body (Pallof press, external rotation, chops)."""
    def f(J, J0, *a):
        h0 = J0[hand]; p = cable_column("cols", h0.x, side_y, pz if pz is not None else h0.z)
        cable("cabs", p, J[hand]); d_handle("dhs", J[hand], (0, 0, 1))
    return f

TOP_HAND = lambda J0: "hand_l" if J0["shoulder_l"].z > J0["shoulder_r"].z else "hand_r"     # upper arm when side-lying

# ======================= PULL =======================
T("seated-cable-row", ["Seated cable row (neutral grip)", "Seated cable row (wide grip)"], two("Seated_Cable_Rows"),
  lambda J, J0, *a: low_row_machine("m", J0, J, "v"), hands="grip", anchor=SEATZ(0.42))
T("single-arm-cable-row", ["Single-arm cable row"], two("Seated_One-arm_Cable_Pulley_Rows"),
  lambda J, J0, *a: low_row_machine("m", J0, J, single=True), hands="grip", anchor=SEATZ(0.42))
T("machine-row", ["Chest-supported machine row", "Chest-supported machine row / T-bar row", "Plate-loaded low row"], two("Leverage_Iso_Row"),
  lambda J, J0, *a: lever_machine("m", J0, J, "row"), hands="grip")
T("tbar-row", ["Chest-supported T-bar row"], two("Lying_T-Bar_Row"), lambda J, J0, *a: tbar_machine("m", J0, J), hands="grip")
T("db-incline-row", ["Chest-supported dumbbell row", "Chest-supported dumbbell lat row"], two("Dumbbell_Incline_Row"),
  P_(lambda J, J0, *a: chest_down_incline("bench", J0, 40), DB()), hands="grip")
T("seal-row", ["Seal row"], two("Lying_Cambered_Barbell_Row"),
  P_(lambda J, J0, *a: flat_bench("bench", J0["hips"].x - 0.45, J0["shoulders"].x + 0.25, region_low("torso")), DB()), hands="grip", anchor={"z": ("torso", 0.72)})
T("one-arm-db-row", ["Single-arm dumbbell row", "Single-arm dumbbell row (bench-supported)"], two("One-Arm_Dumbbell_Row"),
  P_(lambda J, J0, *a: flat_bench("bench", J0["knee_l"].x - 0.2, J0["hand_l"].x + 0.2, min(J0["knee_l"].z, J0["hand_l"].z) - 0.04), DB("r")),
  handR="grip", handL="flat")
T("landmine-row", ["Landmine row (single arm)"], two("One-Arm_Long_Bar_Row"),
  lambda J, J0, *a: landmine("lm", V((J0["hand_r"].x + 1.3, J0["hand_r"].y, 0.0)), J["hand_r"]), handR="grip")
T("door-towel-row", ["Door towel row", "Door towel row (both hands)"], two("Suspended_Row"),
  lambda J, J0, *a: (door("door", J0["hands"].x + 0.62), rod("towel_l", J["hand_l"], V((J0["hands"].x + 0.56, -0.33, 1.0)), 0.02, "towel"),
                     rod("towel_r", J["hand_r"], V((J0["hands"].x + 0.56, -0.33, 1.0)), 0.02, "towel")), hands="grip", cam=dict(az=-95))
T("door-towel-row-1arm", ["Single-arm door towel row"], [K("Suspended_Row", 0, fk_armL=[10, 14, 30, 10]), K("Suspended_Row", 1, fk_armL=[10, 14, 30, 10])],
  lambda J, J0, *a: (door("door", J0["hand_r"].x + 0.62), rod("towel", J["hand_r"], V((J0["hand_r"].x + 0.56, -0.33, 1.0)), 0.02, "towel")),
  handR="grip", cam=dict(az=-95))
T("prone-towel-pulldown", ["Prone towel pulldown"],
  [K("Superman", 0, fk_armL=[104, 22, 104, 22], fk_armR=[104, 22, 104, 22]), K("Superman", 0, fk_armL=[-100, 62, 104, 26], fk_armR=[-100, 62, 104, 26])],
  P_(MAT, lambda J, J0, *a: rod("towel", J["hand_l"], J["hand_r"], 0.02, "towel")), hands="grip", cam=dict(el=18))
T("lat-pulldown", ["Lat pulldown (neutral or wide grip, to chest)", "Lat pulldown (light, slow)"], two("Wide-Grip_Lat_Pulldown"),
  lambda J, J0, *a: lat_machine("m", J0, J, "wide"), hands="grip", palm="forward", cam=dict(az=-150, el=12))
T("machine-high-row", ["Machine high row"], two("Leverage_High_Row"), lambda J, J0, *a: lever_machine("m", J0, J, "high_row", pivot_dx=0.35), hands="grip")
T("kneel-cable-pulldown", ["Single-arm kneeling cable pulldown"], two("Kneeling_Single-Arm_High_Pulley_Row"),
  P_(MAT, lambda J, J0, *a: (cable("cab", cable_column("col", J0["hand_r"].x + 0.35, J0["hand_r"].y, 2.15), J["hand_r"]), d_handle("dh", J["hand_r"], (0, 0, 1)))), handR="grip")
T("assisted-pullup", ["Assisted pull-up machine"], two("Band_Assisted_Pull-Up"), lambda J, J0, *a: pullup_station("m", J0, J, assisted=True),
  hands="grip", palm="forward", anchor={"z": ("hand_r", 2.05), "x": ("hand_r", None)}, cam=dict(az=-140))
T("pullup-negative", ["Pull-up bar negatives"], [K("Band_Assisted_Pull-Up", 1), K("Band_Assisted_Pull-Up", 0)],
  lambda J, J0, *a: pullup_station("m", J0, J), hands="grip", palm="forward", anchor={"z": ("hand_r", 2.05), "x": ("hand_r", None)}, cam=dict(az=-140))
T("db-pullover", ["Dumbbell pullover (on bench)", "Dumbbell pullover (bench)"], two("Bent-Arm_Dumbbell_Pullover"),
  P_(lambda J, J0, *a: flat_bench("bench", J0["shoulders"].x - 0.0, J0["shoulders"].x + 0.0, region_low("torso"), w=1.1) if False else
     flat_bench("bench", J0["shoulders"].x - 0.18, J0["shoulders"].x + 0.18, J0["shoulders"].z - 0.08, w=1.0),
     lambda J, J0, *a: dumbbell("db", J["hands"] + V((0, 0, 0.03)), (J["hand_l"] - J["hand_r"]).cross(V((0, 0, 1))).normalized() if False else V((0, 0, 1)), 0.3)), hands="grip")
T("kb-pullover", ["Kettlebell pullover"], two("Bent-Arm_Dumbbell_Pullover"),
  P_(lambda J, J0, *a: flat_bench("bench", J0["shoulders"].x - 0.18, J0["shoulders"].x + 0.18, J0["shoulders"].z - 0.08, w=1.0),
     lambda J, J0, *a: kettlebell("kb", J["hands"] + V((0, 0, 0.05)))), hands="grip")
T("straight-arm-pulldown", ["Cable straight-arm pulldown"], two("Straight-Arm_Pulldown"), COL(pz=2.1, handle="bar"), hands="grip", palm="feet")
T("face-pull", ["Cable face pull (rope, eye height)", "Cable face pull (rope)", "Cable face pull"], two("Face_Pull"), COL(handle="rope"), hands="grip", cam=dict(az=-50))
T("cable-rear-delt-fly", ["Cable rear-delt fly"], two("Cable_Rear_Delt_Fly"),
  lambda J, J0, *a: [ (lambda p: (cable("c" + s, p, J["hand_" + s]), d_handle("h" + s, J["hand_" + s], (0, 0, 1))))(
      cable_column("col" + s, J0["shoulders"].x + 0.9, (-0.9 if s == "l" else 0.9), J0["shoulders"].z + 0.15)) for s in "lr"], hands="grip", cam=dict(az=-130))
T("reverse-pec-deck", ["Reverse pec deck", "Reverse pec deck (light)"], two("Reverse_Machine_Flyes"), lambda J, J0, *a: reverse_pec_deck("m", J0, J), hands="grip",
  cam=dict(az=-150, el=14))
T("incline-rear-delt", ["Chest-supported rear-delt fly", "Incline prone rear-delt raise"],
  [K("Reverse_Flyes", 0), K("Reverse_Flyes", 0, fk_armL=[10, 84, 10, 84], fk_armR=[10, 84, 10, 84])],
  P_(lambda J, J0, *a: chest_down_incline("bench", J0, 35), DB()), hands="grip")
T("bentover-rear-delt", ["Bent-over rear-delt raise"],
  [K("Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench", 0),
   K("Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench", 0, fk_armL=[6, 82, 6, 82], fk_armR=[6, 82, 6, 82])],
  P_(lambda J, J0, *a: incline_bench("bench", J0, 38, J0["head"].x + 0.55), DB()), hands="grip")
T("band-pull-apart", ["Mini-band pull-apart"], two("Band_Pull_Apart"), lambda J, J0, *a: mini_band("band", J["hand_l"], J["hand_r"]), hands="grip", cam=dict(az=-30))
T("band-w", ["Mini-band W pull-apart"], two("External_Rotation_with_Band"), lambda J, J0, *a: mini_band("band", J["hand_l"], J["hand_r"]), hands="grip", cam=dict(az=-30))
T("cable-er", ["Cable external rotation"], two("External_Rotation_with_Cable"), COL_SIDE(-0.95, hand="hand_l"), handL="grip", cam=dict(az=-25))
T("side-lying-er", ["Side-lying dumbbell external rotation"], two("External_Rotation"),
  P_(lambda J, J0, *a: flat_bench("bench", min(J0["head"].x, J0["ankle_l"].x) - 0.1, max(J0["head"].x, J0["ankle_l"].x) + 0.1, 0.46),
     lambda J, J0, *a: dumbbell("db", J[TOP_HAND(J0)], J["gax_" + TOP_HAND(J0)[-1]])), hands="grip", anchor=BENCH,
  slide={"foot_l": 0.5, "foot_r": 0.56})

# ======================= POSTURE / SHOULDER CARE =======================
STAND_SIDE = "Upper_Back_Stretch"
T("scap-squeeze", ["Shoulder blade squeezes"],
  [K(STAND_SIDE, 0, fk_armL=[4, 12, 90, 8], fk_armR=[4, 12, 90, 8]), K(STAND_SIDE, 0, fk_armL=[-32, 22, 88, 14], fk_armR=[-32, 22, 88, 14])], None, cam=dict(az=-40, el=15))
T("cable-y-raise", ["Cable Y-raise (low pulley, single arm)", "Cable Y-raise, both arms"], two("Standing_Low-Pulley_Deltoid_Raise"),
  lambda J, J0, *a: (cable("c", cable_column("col", J0["hips"].x + 0.1, 0.75, 0.15), J["hand_r"]), d_handle("h", J["hand_r"], (0, 0, 1))), handR="grip", cam=dict(az=-20))
T("incline-y-raise", ["Incline dumbbell Y-raise"],
  [K("Reverse_Flyes", 0), K("Reverse_Flyes", 0, fk_armL=[132, 32, 132, 32], fk_armR=[132, 32, 132, 32])],
  P_(lambda J, J0, *a: chest_down_incline("bench", J0, 35), DB()), hands="grip")
T("incline-ytw", ["Incline prone Y-T-W", "Prone Y-T-W on incline bench (1–2 kg)"],
  [K("Reverse_Flyes", 0), K("Reverse_Flyes", 0, fk_armL=[132, 32, 132, 32], fk_armR=[132, 32, 132, 32]),
   K("Reverse_Flyes", 0, fk_armL=[60, 86, 60, 86], fk_armR=[60, 86, 60, 86]), K("Reverse_Flyes", 0, fk_armL=[20, 70, 120, 70], fk_armR=[20, 70, 120, 70])],
  P_(lambda J, J0, *a: chest_down_incline("bench", J0, 35), DB()), hands="grip")
PR = "Superman"
T("floor-ytw", ["Floor Y-T-W, no weight"],
  [K(PR, 0, fk_armL=[90, 34, 90, 34], fk_armR=[90, 34, 90, 34]), K(PR, 0, fk_armL=[104, 34, 104, 34], fk_armR=[104, 34, 104, 34]),
   K(PR, 0, fk_armL=[92, 86, 92, 86], fk_armR=[92, 86, 92, 86]), K(PR, 0, fk_armL=[100, 76, 30, 60], fk_armR=[100, 76, 30, 60])], MAT, cam=dict(az=-50, el=24))
T("prone-t", ["Prone T raise"], [K(PR, 0, fk_armL=[88, 86, 88, 86], fk_armR=[88, 86, 88, 86]), K(PR, 0, fk_armL=[100, 86, 100, 86], fk_armR=[100, 86, 100, 86])], MAT, cam=dict(az=-50, el=24))
T("prone-w", ["Prone W lift"], [K(PR, 0, fk_armL=[80, 70, 30, 60], fk_armR=[80, 70, 30, 60]), K(PR, 0, fk_armL=[100, 74, 40, 60], fk_armR=[100, 74, 40, 60])], MAT, cam=dict(az=-50, el=24))
T("prone-row", ["Prone floor row"], [K(PR, 0, fk_armL=[80, 50, 90, 10], fk_armR=[80, 50, 90, 10]), K(PR, 0, fk_armL=[-60, 40, 88, 14], fk_armR=[-60, 40, 88, 14])], MAT, cam=dict(az=-50, el=24))
T("swimmers", ["Prone swimmers"], [K(PR, 0, fk_armL=[102, 16, 102, 16], fk_armR=[102, 16, 102, 16]), K(PR, 0, fk_armL=[102, 84, 102, 84], fk_armR=[102, 84, 102, 84]),
   K(PR, 0, fk_armL=[-102, 84, -102, 84], fk_armR=[-102, 84, -102, 84]), K(PR, 0, fk_armL=[-102, 16, -102, 16], fk_armR=[-102, 16, -102, 16])], MAT, cam=dict(az=-50, el=24))
T("chin-tuck", ["Chin tucks"], [K(STAND_SIDE, 0, fk_N=156, fk_H=186), K(STAND_SIDE, 0, fk_N=190, fk_H=174)], None,
  focus=["pelvis", "head", "shoulder_l", "shoulder_r"], cam=dict(az=-88, el=10, margin=1.3))
T("wall-chin-tuck", ["Wall chin tuck"], [K(STAND_SIDE, 0, fk_N=156, fk_H=186), K(STAND_SIDE, 0, fk_N=190, fk_H=174)],
  lambda J, J0, *a: wall("wall", J0["shoulders"].x - 0.2), focus=["pelvis", "head", "shoulder_l", "shoulder_r"], cam=dict(az=-80, el=10, margin=1.3))
T("cable-chin-tuck", ["Seated cable chin tuck (light)"], [K("Chair_Upper_Body_Stretch", 0, fk_N=156, fk_H=186), K("Chair_Upper_Body_Stretch", 0, fk_N=190, fk_H=174)],
  lambda J, J0, *a: (chair("chair", J0), cable("strap", J["head"] + V((-0.08, 0, -0.08)), cable_column("col", J0["head"].x + 0.9, 0, J0["head"].z - 0.08))),
  focus=["hips", "head", "shoulder_l", "shoulder_r", "knee_r"], cam=dict(az=-80, el=10, margin=1.3))
T("supine-chin-tuck", ["Supine chin tuck + head lift"], [K("Dead_Bug", 0, **ARMS_SIDE, fk_legL=[150, 6, 30, 6], fk_legR=[150, 6, 30, 6], fk_N=-90, fk_H=-90),
   K("Dead_Bug", 0, **ARMS_SIDE, fk_legL=[150, 6, 30, 6], fk_legR=[150, 6, 30, 6], fk_N=-112, fk_H=-124)],
  MAT, hands="flat", palm="down", cam=dict(az=-80, el=12))
T("wall-slides", ["Wall slides", "Wall slide with lift-off", "Wall slide with reach", "Wall Y-slide with lift-off"],
  [K(STAND_SIDE, 0, fk_armL=[180, 88, 180, 4], fk_armR=[180, 88, 180, 4]), K(STAND_SIDE, 0, fk_armL=[180, 34, 180, 22], fk_armR=[180, 34, 180, 22])],
  lambda J, J0, *a: wall("wall", J0["shoulders"].x - 0.2), hands="flat", handdir=180, palm="forward", cam=dict(az=-22, el=12))

# ======================= PRESS =======================
T("push-up", ["Pause push-up", "Push-up plus"], two("Pushups"), None, hands="flat")
T("push-up-db", ["Push-up on dumbbell handles"], two("Pushups"), DB(), hands="grip")
T("incline-push-up", ["Push-up (hands elevated if needed)"], two("Incline_Push-Up"),
  lambda J, J0, *a: box_step("box", J0["hands"].x, J0["hands"].z - 0.03, d_=0.45, w=0.62), hands="flat")
T("chest-press-machine", ["Chest press machine (neutral grip)"], two("Machine_Bench_Press"),
  lambda J, J0, *a: lever_machine("m", J0, J, "press_back", chest_pad=False, back_pad=True), hands="grip")
T("db-bench-1arm", ["Single-arm dumbbell bench press"], two("One_Arm_Dumbbell_Bench_Press", fk_armL=[80, 20, 70, 20]),
  P_(lambda J, J0, *a: flat_bench("bench", J0["head"].x - 0.05, J0["hips"].x + 0.35, region_low("torso")), DB("r")), handR="grip", anchor=BENCH, slide={"foot_l": 0.085, "foot_r": 0.085})
T("incline-db-press", ["Low-incline dumbbell press (15–30°, neutral grip)"], two("Hammer_Grip_Incline_DB_Bench_Press"),
  P_(lambda J, J0, *a: incline_bench("bench", J0, 28, J0["hips"].x + 0.05, region_low("seat")), DB()), hands="grip")
T("smith-incline", ["Low-incline Smith press", "High-incline Smith press"], two("Smith_Machine_Incline_Bench_Press"),
  P_(lambda J, J0, *a: incline_bench("bench", J0, 45, J0["hips"].x + 0.05, region_low("seat")), lambda J, J0, *a: smith("sm", J0, J)), hands="grip", cam=dict(az=-35))
T("floor-press", ["Dumbbell floor press"], two("Dumbbell_Floor_Press"), P_(MAT, DB()), hands="grip")
T("standing-cable-press", ["Standing cable chest press"], two("Standing_Cable_Chest_Press"),
  lambda J, J0, *a: [ (lambda p: (cable("c" + s, p, J["hand_" + s]), d_handle("h" + s, J["hand_" + s], (0, 0, 1))))(
      cable_column("col" + s, J0["shoulders"].x - 0.55, (0.7 if s == "l" else -0.7), J0["hand_" + s].z)) for s in "lr"], hands="grip")
T("single-arm-cable-press", ["Single-arm cable press (low-to-high)"],
  [K("Standing_Cable_Chest_Press", 0, fk_armL=[4, 10, 4, 8]), K("Standing_Cable_Chest_Press", 1, fk_armL=[4, 10, 4, 8])],
  lambda J, J0, *a: (cable("c", cable_column("col", J0["shoulders"].x - 0.55, -0.7, 0.35), J["hand_r"]), d_handle("h", J["hand_r"], (0, 0, 1))), handR="grip")
T("shoulder-press-machine", ["Neutral-grip machine shoulder press (partial)"], two("Leverage_Shoulder_Press"),
  lambda J, J0, *a: lever_machine("m", J0, J, "press_back", chest_pad=False, back_pad=True), hands="grip", cam=dict(az=-35))
HK = "Kneeling_Hip_Flexor"
T("landmine-press", ["Half-kneeling landmine press"],
  [K(HK, 0, fk_armR=[18, 22, 162, 6], fk_armL=[4, 8, 4, 6]), K(HK, 0, fk_armR=[140, 12, 140, 6], fk_armL=[4, 8, 4, 6])],
  P_(MAT, lambda J, J0, *a: landmine("lm", V((J0["pelvis"].x - 1.2, J0["hand_r"].y, 0.0)), J["hand_r"], end=True, plate=False)), handR="grip")
T("hk-db-press", ["Half-kneeling single-arm dumbbell press"],
  [K(HK, 0, fk_armR=[10, 40, 170, 10], fk_armL=[4, 8, 4, 6]), K(HK, 0, fk_armR=[172, 10, 172, 6], fk_armL=[4, 8, 4, 6])], P_(MAT, DB("r")), handR="grip")
T("kb-press", ["Bottoms-up kettlebell press (light)"], two("Alternating_Kettlebell_Press"),
  lambda J, J0, *a: [kettlebell("kb_" + s, J["hand_" + s], up=(0, 0, -1), side=J["gax_" + s]) for s in "lr"], hands="grip", cam=dict(az=-30))
T("supine-punch", ["Supine dumbbell punch"],
  [K("Dumbbell_Floor_Press", 1), K("Dumbbell_Floor_Press", 1, elevL=0, elevR=0, fk_armR=[180, 4, 180, 4])], P_(MAT, DB("r")), handR="grip")
T("cable-serratus", ["Cable serratus punch"],
  [K("Standing_Cable_Chest_Press", 1, fk_armL=[4, 10, 4, 8]), K("Standing_Cable_Chest_Press", 1, fk_armL=[4, 10, 4, 8], fk_armR=[90, 6, 90, 6])],
  lambda J, J0, *a: (cable("c", cable_column("col", J0["shoulders"].x - 0.6, -0.4, J0["hand_r"].z), J["hand_r"]), d_handle("h", J["hand_r"], (0, 0, 1))), handR="grip")

# ======================= HIPS / GLUTES =======================
T("hip-thrust", ["Barbell or dumbbell hip thrust"], two("Barbell_Hip_Thrust"),
  P_(lambda J, J0, *a: flat_bench("bench", J0["shoulders"].x - 0.2, J0["shoulders"].x + 0.2, region_low("torso") if False else J0["shoulders"].z - 0.07, w=1.1),
     lambda J, J0, *a: barbell("bb", J["hips"] + V((0, 0, 0.13)), V((0, 1, 0)))), hands="grip")
T("smith-hip-thrust", ["Smith machine hip thrust"], two("Barbell_Hip_Thrust"),
  P_(lambda J, J0, *a: flat_bench("bench", J0["shoulders"].x - 0.2, J0["shoulders"].x + 0.2, J0["shoulders"].z - 0.07, w=1.1),
     lambda J, J0, *a: smith("sm", {**J0, "hands": J0["hips"] + V((0, 0, 0.13))}, {**J, "hands": J["hips"] + V((0, 0, 0.13))})), hands="grip")
T("glute-drive", ["Hip thrust / glute drive machine"], two("Barbell_Hip_Thrust"),
  lambda J, J0, *a: (pad("gd_back", J0["shoulders"] + V((-0.05, 0, -0.12)), (0.3, 0.5, 0.1), pitch=-15),
                     pad("gd_belt", J["hips"] + V((0.02, 0, 0.12)), (0.25, 0.5, 0.05)), foot_base("gd_base", J0["shoulders"].x - 0.3, J0["ankle_r"].x + 0.3, w=0.8),
                     tube("gd_arm_l", J["hips"] + V((0, 0.28, 0.12)), V((J0["shoulders"].x, 0.32, 0.6))), tube("gd_arm_r", J["hips"] + V((0, -0.28, 0.12)), V((J0["shoulders"].x, -0.32, 0.6)))),
  hands="grip")
T("single-leg-hip-thrust", ["Single-leg hip thrust"],
  [K("Barbell_Hip_Thrust", 0, fk_legL=[150, 8, 150, 8]), K("Barbell_Hip_Thrust", 1, fk_legL=[110, 8, 110, 8])],
  P_(lambda J, J0, *a: flat_bench("bench", J0["shoulders"].x - 0.2, J0["shoulders"].x + 0.2, J0["shoulders"].z - 0.07, w=1.1),
     lambda J, J0, *a: dumbbell("db", J["hip_r"] + V((0, 0, 0.1)), V((0, 1, 0)))), hands="grip")
T("glute-bridge", ["Glute bridge"], two("Butt_Lift_Bridge", **ARMS_SIDE), MAT, hands="flat", palm="down")
T("db-glute-bridge", ["Dumbbell glute bridge"], two("Barbell_Glute_Bridge"), P_(MAT, lambda J, J0, *a: dumbbell("db", J["hips"] + V((0.02, 0, 0.2)), V((0, 1, 0)), 0.4)), hands="grip")
T("band-bridge-couch", ["Banded glute bridge, feet on couch"], two("Butt_Lift_Bridge", **ARMS_SIDE),
  P_(MAT, lambda J, J0, *a: (box("couch", ((J0["ankle_l"].x + J0["ankle_r"].x) / 2 + 0.12, 0, 0.21), (0.6, 0.95, 0.42), "foam"),
                             mini_band("band", J["knee_l"] + V((0, 0.03, 0)), J["knee_r"] + V((0, -0.03, 0))))), hands="flat", palm="down", feet_z=0.5)
T("single-leg-bridge", ["Single-leg glute bridge"], two("Single_Leg_Glute_Bridge", **ARMS_SIDE), MAT, hands="flat", palm="down")
T("glute-squeeze", ["Glute squeezes"], [K("Dumbbell_Shrug", 0), K("Dumbbell_Shrug", 0, curve=-3)], None, cam=dict(az=-50))
T("db-rev-lunge", ["Dumbbell reverse lunge"], two("Dumbbell_Rear_Lunge"), DB(), hands="grip")
T("rev-lunge", ["Reverse lunge", "Slow reverse lunge"], two("Dumbbell_Rear_Lunge"), None, hands="relaxed")
T("goblet-rev-lunge", ["Goblet reverse lunge"], [K("Dumbbell_Rear_Lunge", 0, fk_armL=[-5, 10, 140, -25], fk_armR=[-5, 10, 140, -25]),
   K("Dumbbell_Rear_Lunge", 1, fk_armL=[-5, 10, 140, -25], fk_armR=[-5, 10, 140, -25])],
  lambda J, J0, *a: dumbbell("db", J["hands"] + V((0.03, 0, -0.04)), V((0, 0, 1)), 0.28), hands="grip")
T("smith-split", ["Smith machine split squat"], two("Smith_Single-Leg_Split_Squat"),
  lambda J, J0, *a: smith("sm", J0, J, bar_at="shoulders"), hands="grip", palm="forward", cam=dict(az=-30))
T("supported-split", ["Supported split squat"], two("Split_Squats"),
  lambda J, J0, *a: box("support", (J0["hips"].x + 0.45, -0.45, 0.5), (0.06, 0.06, 1.0), "steel"), plant=["foot_l", "foot_r"])
T("goblet-split", ["Goblet split squat"], [K("Split_Squats", 0, fk_armL=[-5, 10, 140, -25], fk_armR=[-5, 10, 140, -25]),
   K("Split_Squats", 1, fk_armL=[-5, 10, 140, -25], fk_armR=[-5, 10, 140, -25])],
  lambda J, J0, *a: dumbbell("db", J["hands"] + V((0.03, 0, -0.04)), V((0, 0, 1)), 0.28), hands="grip", plant=["foot_l", "foot_r"])
T("rfess", ["Rear-foot-elevated split squat"], two("Split_Squats"),
  P_(lambda J, J0, *a: (lambda b: flat_bench("bench", b.x - 0.35, b.x + 0.22, 0.45, y=b.y, w=0.32))(min(J0["ankle_l"], J0["ankle_r"], key=lambda v: v.x)), DB()),
  hands="grip", rear_foot_z=0.5)
T("db-rdl", ["Dumbbell Romanian deadlift", "Dumbbell RDL"], two("Stiff-Legged_Dumbbell_Deadlift"), DB(), hands="grip")
T("bb-rdl", ["Barbell RDL (light)"], [K("Romanian_Deadlift", 1), K("Romanian_Deadlift", 0)], BB(), hands="grip", palm="back")
T("smith-rdl", ["Smith machine RDL"], two("Smith_Machine_Stiff-Legged_Deadlift"), lambda J, J0, *a: smith("sm", J0, J), hands="grip", palm="back", cam=dict(az=-30))
T("kb-deadlift", ["Kettlebell deadlift"], [K("Trap_Bar_Deadlift", 1), K("Trap_Bar_Deadlift", 0)], KB(), hands="grip")
T("trap-bar-deadlift", ["Trap-bar deadlift (or kettlebell deadlift)"], [K("Trap_Bar_Deadlift", 1), K("Trap_Bar_Deadlift", 0)],
  lambda J, J0, *a: trap_bar("tb", J), hands="grip")
T("pull-through", ["Cable pull-through", "Heavy cable pull-through"], two("Pull_Through"),
  lambda J, J0, *a: (cable("cab", cable_column("col", J0["hips"].x - 1.0, 0, 0.25), J["hands"]), rod("rope_l", J["hands"], J["hand_l"], 0.012, "cable"), rod("rope_r", J["hands"], J["hand_r"], 0.012, "cable")),
  hands="grip")
T("hip-hinge-wall", ["Hip hinge to wall"], [K("Stiff-Legged_Dumbbell_Deadlift", 0, fk_armL=[4, 10, 70, 30], fk_armR=[4, 10, 70, 30]), K("Stiff-Legged_Dumbbell_Deadlift", 1)],
  lambda J, J0, *a: wall("wall", J0["hips"].x - 0.42))
T("loaded-hinge-wall", ["Loaded hip hinge to wall"], two("Stiff-Legged_Dumbbell_Deadlift"),
  lambda J, J0, *a: (wall("wall", J0["hips"].x - 0.42), backpack("pack", J)))
T("back-extension", ["45° back extension (glute-focused)", "45° back extension (glute bias)"], two("Hyperextensions_Back_Extensions"),
  lambda J, J0, *a: back_ext_bench("m", J0, J), anchor={"z": ("ankle_r", 0.55), "x": ("ankle_r", None)})
T("single-leg-rdl", ["Single-leg RDL"], two("Kettlebell_One-Legged_Deadlift"), KB("r"), handR="grip")
T("single-leg-rdl-support", ["Single-leg RDL (hold a support)"], two("Kettlebell_One-Legged_Deadlift"),
  lambda J, J0, *a: box("support", (J0["hand_l"].x + 0.05, J0["hand_l"].y + 0.05, J0["hand_l"].z / 2), (0.06, 0.06, J0["hand_l"].z), "steel"), handL="grip")
T("kb-swing", ["Kettlebell swing intervals"], two("One-Arm_Kettlebell_Swings"), KB("r"), handR="grip", cam=dict(az=-55))

# ======================= SQUAT / KNEE =======================
T("goblet-box-squat", ["Goblet box squat"], two("Goblet_Squat"),
  P_(lambda J, J0, *a: box_step("box", J0["hips"].x - 0.2, 0.42), lambda J, J0, *a: dumbbell("db", J["hands"] + V((0.03, 0, -0.04)), V((0, 0, 1)), 0.28)), hands="grip", cam=dict(az=-50))
T("heels-up-goblet", ["Heels-elevated goblet squat to box"], two("Goblet_Squat"),
  P_(lambda J, J0, *a: box_step("box", J0["hips"].x - 0.2, 0.42), lambda J, J0, *a: box("wedge", ((J0["ankle_l"].x + J0["ankle_r"].x) / 2, 0, 0.012), (0.18, 0.7, 0.025), "plate"),
     lambda J, J0, *a: dumbbell("db", J["hands"] + V((0.03, 0, -0.04)), V((0, 0, 1)), 0.28)), hands="grip", cam=dict(az=-50))
T("kb-complex", ["Dumbbell / kettlebell complex", "Kettlebell tempo circuit"], two("Goblet_Squat"),
  lambda J, J0, *a: kettlebell("kb", J["hands"] + V((0.04, 0, 0.0))), hands="grip", cam=dict(az=-50))
T("chair-squat", ["Wall sit or slow squat to a chair"], two("Dumbbell_Squat_To_A_Bench"), lambda J, J0, *a: chair("chair", {**J0, "hips": J0["hips"] + V((-0.05, 0, 0))}, top=0.45),
  hands="relaxed")
T("leg-press", ["Leg press (feet mid-to-high on platform)", "Leg press (feet high)", "Single-leg leg press"], two("Leg_Press"),
  lambda J, J0, *a: leg_press("m", J0, J), anchor=SEATZ(0.42))
T("hack-squat", ["Hack or pendulum squat (feet high)"], two("Hack_Squat"), lambda J, J0, *a: hack_squat_machine("m", J0, J), hands="grip", cam=dict(az=-60))
T("leg-extension", ["Leg extension (partial range)"], two("Leg_Extensions"), lambda J, J0, *a: leg_extension("m", J0, J), hands="grip", anchor=SEATZ(0.5))
T("step-up", ["Dumbbell step-up (box knee-height or lower)", "Lateral step-up (low box)"], two("Dumbbell_Step_Ups"),
  P_(lambda J, J0, *a: box_step("box", J0["ankle_l"].x, 0.38, d_=0.5, w=0.65), DB()), hands="grip")
T("stair-step", ["Stair step-up", "Slow step-down from stairs", "Dumbbell step-down (low step)"], two("Dumbbell_Step_Ups"),
  lambda J, J0, *a: stairs("st", J0["ankle_l"].x - 0.14, rise=0.38 / 2, run=0.3, steps=2), hands="relaxed")
T("stair-climber", ["Stair climber (slow)"], two("Stairmaster"), lambda J, J0, *a: stair_climber("m", J0, J), hands="grip")
T("step-mill", ["Stair intervals"], two("Stairmaster"), lambda J, J0, *a: stair_climber("m", J0, J, mill=True), hands="grip")
T("abductor-machine", ["Seated hip abduction machine"], two("Thigh_Abductor"), lambda J, J0, *a: abductor("m", J0, J), hands="grip", cam=dict(az=-20, el=25))
T("cable-hip-abd", ["Cable standing hip abduction"], two("Side_Leg_Raises"),
  lambda J, J0, *a: (cable("c", cable_column("col", J0["hips"].x + 0.2, 0.9, 0.12), J["ankle_r"] + V((0, 0, 0.05))), ankle_weight("strap", J, "r")),
  handL="grip", cam=dict(az=-15))
T("multi-hip", ["Multi-hip machine (abduction)"], two("Side_Leg_Raises"),
  lambda J, J0, *a: (pad("mh_pad", J["knee_r"] + V((0, -0.08, 0)), (0.2, 0.06, 0.2)), tube("mh_arm", J["knee_r"] + V((0, -0.1, 0)), V((J0["hips"].x, -0.25, 0.9))),
                     cable_column("col", J0["hips"].x + 0.0, -0.45, 1.0), pad("mh_hand", J0["hand_l"] + V((0, 0, -0.03)), (0.15, 0.1, 0.04))), handL="grip", cam=dict(az=-15))
T("lateral-walk", ["Banded lateral walk", "Mini-band lateral walk or clamshell"], two("Monster_Walk"),
  lambda J, J0, *a: mini_band("band", J["knee_l"] + V((0.02, 0.0, 0.06)), J["knee_r"] + V((0.02, 0.0, 0.06))), cam=dict(az=-15, el=8))
SL = "On_Your_Side_Quad_Stretch"
T("side-lying-abd", ["Side-lying hip abduction (ankle weight)"],
  [K(SL, 0), K(SL, 0, fk_legR=[-100, 0, -100, 0])], P_(MAT, lambda J, J0, *a: ankle_weight("aw", J, "r")), cam=dict(az=-80, el=18))
T("clamshell", ["Side plank clamshell"], two("Side_Bridge"), MAT, cam=dict(az=-85, el=10))

# ======================= CORE =======================
T("mcgill", ["McGill curl-up"], [K("Dead_Bug", 0, **ARMS_SIDE, fk_legL=[92, 6, 92, 6, 178], fk_legR=[150, 6, 30, 6], fk_N=-90, fk_H=-90),
   K("Dead_Bug", 0, **ARMS_SIDE, fk_legL=[92, 6, 92, 6, 178], fk_legR=[150, 6, 30, 6], curve=6, fk_N=-104, fk_H=-110)], MAT, hands="flat", palm="down",
  cam=dict(az=-75, el=10))
T("side-plank", ["Side plank (knees or feet)", "Side hold on 45° back-extension bench"], hold("Side_Bridge", 1), MAT, cam=dict(az=-85, el=10))
T("suitcase", ["Suitcase hold", "Suitcase carry", "Single-arm farmer carry"], gait("Walking_Treadmill", 0, fk_armL=[10, 12, 18, 8], fk_armR=[1, 9, 1, 8]), DB("r"), handR="grip", steps=10)
T("cable-hold", ["Single-arm cable hold"], hold("Upper_Back_Stretch", 0, fk_armL=[1, 9, 1, 8], fk_armR=[8, 8, 14, 6]),
  lambda J, J0, *a: (cable("c", cable_column("col", J0["hips"].x, 0.85, 0.2), J["hand_l"]), d_handle("h", J["hand_l"], (0, 0, 1))),
  handL="grip", stance="stand", cam=dict(az=-25))
QD = "All_Fours_Quad_Stretch"
BD = dict(fk_armR=[92, 4, 92, 4], fk_legL=[-90, 4, -90, 4, -80])
BD2 = dict(fk_armL=[92, 4, 92, 4], fk_legR=[-90, 4, -90, 4, -80])
T("bird-dog", ["Bird dog", "Bird dog with light ankle weight"], [K(QD, 0), K(QD, 0, **BD), K(QD, 0), K(QD, 0, **BD2)],
  P_(MAT, lambda J, J0, *a: None), hands="flat", cam=dict(az=-62, el=12))
T("cable-bird-dog", ["Cable bird dog (ankle strap)"], [K(QD, 0), K(QD, 0, **BD)],
  P_(MAT, lambda J, J0, *a: (cable("c", cable_column("col", J0["hips"].x - 1.6, J0["ankle_l"].y, 0.15), J["ankle_l"] + V((0, 0, 0.04))), ankle_weight("strap", J, "l"))),
  hands="flat", cam=dict(az=-62, el=12))
T("pallof-press", ["Cable Pallof press", "Band Pallof press"], two("Pallof_Press"), COL_SIDE(0.95), hands="grip", cam=dict(az=-20))
T("hk-pallof", ["Half-kneeling cable Pallof press"],
  [K(HK, 0, fk_armL=[12, 20, 100, -55], fk_armR=[12, 20, 100, -55]), K(HK, 0, fk_armL=[88, 4, 88, -6], fk_armR=[88, 4, 88, -6])],
  P_(MAT, COL_SIDE(0.95)), hands="grip", cam=dict(az=-20))
T("landmine-pallof", ["Landmine Pallof / anti-rotation"], two("Pallof_Press"),
  lambda J, J0, *a: landmine("lm", V((J0["hips"].x + 1.4, 0, 0)), J["hands"], end=True), hands="grip", cam=dict(az=-30))
T("pallof-rotation", ["Pallof press with rotation"], two("Pallof_Press_With_Rotation"), COL_SIDE(-0.95), hands="grip", cam=dict(az=-30))
T("shoulder-taps", ["Plank shoulder taps"], [K("Pushups", 0), K("Pushups", 0, fk_armR=[40, -30, 150, -60]), K("Pushups", 0), K("Pushups", 0, fk_armL=[40, -30, 150, -60])],
  MAT, hands="flat", cam=dict(az=-50, el=14))
T("bear-taps", ["Bear plank shoulder taps"], [K(QD, 0), K(QD, 0, fk_armR=[40, -30, 150, -60])], MAT, hands="flat", cam=dict(az=-50, el=14))
T("dead-bug", ["Dead bug", "Dead bug (slow)"], alt("Dead_Bug"), MAT, hands="relaxed", palm="in", cam=dict(az=-62, el=14))
T("cable-dead-bug", ["Cable dead bug"], two("Dead_Bug"),
  P_(MAT, lambda J, J0, *a: cable("c", cable_column("col", J0["head"].x - 0.9, 0, 0.6), J["hands"])), hands="grip", cam=dict(az=-62, el=14))
T("db-dead-bug", ["Dumbbell dead bug"], two("Dead_Bug"), P_(MAT, lambda J, J0, *a: dumbbell("db", J["hands"], V((0, 1, 0)))), hands="grip", cam=dict(az=-62, el=14))
T("ball-dead-bug", ["Swiss-ball dead bug"], two("Dead_Bug"),
  P_(MAT, lambda J, J0, *a: swiss_ball("ball", (J["hands"] + (J["knee_l"] + J["knee_r"]) / 2) / 2, 0.3)), cam=dict(az=-62, el=14))
T("front-plank", ["Front plank"], hold("Plank", 1), MAT, hands="relaxed", cam=dict(el=14))
T("plank-reach", ["Plank with reach"], [K("Plank", 1), K("Plank", 1, fk_armR=[92, 6, 92, 4])], MAT, hands="relaxed", cam=dict(el=14))
T("tuck-hollow", ["Tucked hollow hold"], hold("Tuck_Crunch", 1), MAT, cam=dict(az=-70, el=10))
T("crunch", ["Crunch (small range)"], two("Crunches"), MAT)
T("plate-crunch", ["Plate crunch"], two("Weighted_Crunches"), P_(MAT, lambda J, J0, *a: plate_between("plate", J["hands"] + V((0, 0, 0.0)), J["hands"] + V((0, 0, 0.03)), 0.16)), hands="grip")
T("cross-crunch", ["Cross-body crunch"], two("Cross-Body_Crunch"), MAT)
T("ball-crunch", ["Swiss-ball crunch"], two("Exercise_Ball_Crunch"),
  lambda J, J0, *a: swiss_ball("ball", J0["pelvis"] + V((-0.05, 0, -0.3)), 0.32))
T("cable-crunch", ["Kneeling cable crunch"], two("Cable_Crunch"),
  P_(MAT, lambda J, J0, *a: (cable("c", cable_column("col", J0["head"].x + 0.45, 0, 2.1), J["hands"]),
                             rod("rope_l", J["hands"], J["hand_l"], 0.012, "cable"), rod("rope_r", J["hands"], J["hand_r"], 0.012, "cable"))), hands="grip")
T("machine-crunch", ["Ab crunch machine"], two("Ab_Crunch_Machine"), crunch_machine, hands="grip")
T("reverse-crunch", ["Reverse crunch"], two("Reverse_Crunch"), MAT, hands="flat", palm="down")
T("captains-chair", ["Captain's chair knee raise"],
  [K("Hanging_Leg_Raise", 0, fk_armL=[2, 22, 92, 6], fk_armR=[2, 22, 92, 6], fk_legL=[2, 5, 0, 5], fk_legR=[2, 5, 0, 5]),
   K("Hanging_Leg_Raise", 0, fk_armL=[2, 22, 92, 6], fk_armR=[2, 22, 92, 6], fk_legL=[92, 6, 6, 6], fk_legR=[92, 6, 6, 6])],
  lambda J, J0, *a: captains_chair("m", J0, J), hands="grip", anchor={"z": ("pelvis", 1.15), "x": ("pelvis", 0)})
T("bench-pull-in", ["Bench leg pull-in"], two("Flat_Bench_Leg_Pull-In"),
  lambda J, J0, *a: flat_bench("bench", J0["shoulders"].x - 0.3, J0["hips"].x + 0.35, region_low("torso")), anchor=BENCH, hands="grip")
T("seated-pull-in", ["Seated leg pull-in"], two("Seated_Flat_Bench_Leg_Pull-In"), MAT, hands="flat")
T("lying-leg-raise", ["Lying leg raise on bench (knees bent)"], two("Flat_Bench_Lying_Leg_Raise"),
  lambda J, J0, *a: flat_bench("bench", J0["head"].x - 0.1, J0["hips"].x + 0.3, region_low("torso")), anchor=BENCH, hands="grip")
T("ab-wheel", ["Ab wheel rollout (from knees)", "Ab roller"], two("Ab_Roller"),
  P_(MAT, lambda J, J0, *a: (rod("wheel", V((J["hands"].x, 0.05, 0.1)), V((J["hands"].x, -0.05, 0.1)), 0.1, "plate"),
                             rod("hub", V((J["hands"].x, 0.06, 0.1)), V((J["hands"].x, -0.06, 0.1)), 0.03, "steel"),
                             rod("hdl", V((J["hands"].x, J["hand_l"].y, 0.1)), V((J["hands"].x, J["hand_r"].y, 0.1)), 0.016, "rubber"))),
  hands="grip", slide={"hand_l": 0.115, "hand_r": 0.115}, cam=dict(margin=1.25))
T("bb-rollout", ["Barbell rollout (from knees)"], two("Barbell_Ab_Rollout_-_On_Knees"),
  P_(MAT, lambda J, J0, *a: (rod("bar", V((J["hands"].x, 0.7, 0.225)), V((J["hands"].x, -0.7, 0.225)), 0.016, "chrome"),
                             plate_between("p1", V((J["hands"].x, 0.55, 0.225)), V((J["hands"].x, 0.6, 0.225)), 0.225),
                             plate_between("p2", V((J["hands"].x, -0.55, 0.225)), V((J["hands"].x, -0.6, 0.225)), 0.225))),
  hands="grip", slide={"hand_l": 0.24, "hand_r": 0.24}, cam=dict(margin=1.3))
T("mountain-climbers", ["Mountain climbers (slow)", "Low-impact interval circuit", "Bodyweight tempo circuit"], alt("Mountain_Climbers"), MAT, hands="flat", cam=dict(el=14))
T("push-up-side-plank", ["Push-up to side plank"], [K("Push_Up_to_Side_Plank", 0), K("Push_Up_to_Side_Plank", 1), K("Side_Bridge", 1)], MAT, hands="flat")
T("woodchop", ["Cable woodchop (high to low)"], two("Standing_Cable_Wood_Chop"), COL_SIDE(-0.95, pz=2.0), hands="grip", cam=dict(az=-35))
T("cable-lift", ["Cable lift (low to high)"], two("Standing_Cable_Lift"), COL_SIDE(0.95, pz=0.25), hands="grip", cam=dict(az=-35))
T("landmine-rainbow", ["Landmine rainbows (180s)"], two("Landmine_180s"),
  lambda J, J0, *a: landmine("lm", V((J0["hips"].x + 1.4, 0, 0)), J["hands"], end=True), hands="grip", cam=dict(az=-45))

# ======================= STRETCH / MOBILITY =======================
T("cat-cow", ["Cat–cow", "Cat-cow + thread the needle"], two("Cat_Stretch"), MAT, hands="flat", cam=dict(az=-80, el=10))
T("childs-pose", ["Child's pose with side reach", "Bench lat stretch"], two("Childs_Pose"), MAT, hands="flat", cam=dict(az=-75, el=12))
T("cable-lat-stretch", ["Cable lat stretch"], [K("Pull_Through", 0, fk_armL=[140, 6, 140, 6], fk_armR=[140, 6, 140, 6]),
   K("Pull_Through", 0, fk_armL=[150, 6, 150, 6], fk_armR=[150, 6, 150, 6], curve=8)],
  lambda J, J0, *a: (cable("c", cable_column("col", J0["hands"].x + 0.4, 0, 1.9), J["hands"]), handle_bar("h", J["hand_l"] + V((0, 0.05, 0)), J["hand_r"] + V((0, -0.05, 0)))),
  hands="grip")
T("pec-stretch", ["Doorway pec stretch", "Doorway or seated pec stretch"], two("One_Arm_Against_Wall"),
  lambda J, J0, *a: door("door", J0["hand_r"].x + 0.06, J0["hand_r"].y - 0.45), handR="flat", cam=dict(az=-140, el=10))
T("cable-pec-stretch", ["Cable pec stretch"], two("One_Arm_Against_Wall"),
  lambda J, J0, *a: (cable("c", cable_column("col", J0["hand_r"].x + 0.5, J0["hand_r"].y - 0.3, J0["hand_r"].z), J["hand_r"]), d_handle("h", J["hand_r"], (0, 0, 1))),
  handR="grip", cam=dict(az=-140, el=10))
T("hk-hip-flexor", ["Half-kneeling hip flexor stretch"], two(HK), MAT, cam=dict(az=-80))
T("standing-hip-flexor", ["Standing hip flexor stretch"], two("Standing_Hip_Flexors"), None, cam=dict(az=-80))
T("couch-stretch", ["Couch stretch"], [K(HK, 0, fk_legR=[-10, 6, 172, 4, 200]), K(HK, 1, fk_legR=[-18, 6, 168, 4, 200])],
  P_(MAT, lambda J, J0, *a: wall("wall", J0["knee_r"].x - 0.17, z=0.55, h=1.1, w=1.6)), cam=dict(az=-80))
T("couch-stretch-bench", ["Couch stretch (bench version)"], [K(HK, 0, fk_legR=[-10, 6, 140, 4, 200]), K(HK, 1, fk_legR=[-18, 6, 136, 4, 200])],
  P_(MAT, lambda J, J0, *a: (lambda b: flat_bench("bench", b.x - 0.35, b.x + 0.22, 0.45, y=b.y, w=0.32))(min(J0["ankle_l"], J0["ankle_r"], key=lambda v: v.x))),
  rear_foot_z=0.5, cam=dict(az=-80))
T("lying-ham-towel", ["Lying hamstring stretch (towel) + couch stretch"], two("Leg-Up_Hamstring_Stretch"),
  P_(MAT, lambda J, J0, *a: rod("towel", J["hands"], (J["toe_r"] + J["ankle_r"]) / 2, 0.018, "towel")), hands="grip", cam=dict(az=-70))
T("bench-ham", ["Hamstring stretch on bench + couch stretch"], two("Standing_Hamstring_and_Calf_Stretch"), None, cam=dict(az=-70))
T("figure-4", ["Figure-4 stretch + hip flexor stretch"],
  [K(SUP, 0, **ARMS_SIDE, fk_legR=[128, 40, 98, -62]),
   K(SUP, 0, fk_legL=[162, 8, 100, 8], fk_legR=[140, 40, 108, -62], fk_armL=[150, 6, 150, -6], fk_armR=[150, 6, 150, -6])],
  MAT, cam=dict(az=-55, el=20))
T("pigeon-bench", ["Bench pigeon stretch"], hold("IT_Band_and_Glute_Stretch", 0), MAT, cam=dict(az=-55, el=15))
T("t-spine-chair", ["Thoracic extension over chair", "Chair T-spine extension + world's greatest stretch + child's pose lat stretch"],
  [K("Spinal_Stretch", 0), K("Spinal_Stretch", 0, curve=-28, fk_N=210, fk_H=220)], lambda J, J0, *a: chair("chair", J0), cam=dict(az=-80, el=10))
T("t-spine-roller", ["Foam roller T-spine + world's greatest stretch + child's pose lat stretch"],
  [K(SUP, 0, fk_N=-80, fk_H=-75), K(SUP, 0, curve=-16, fk_N=-100, fk_H=-110)], P_(MAT, lambda J, J0, *a: roller("roller", J0["chest"] + V((0.05, 0, -0.17)))), cam=dict(az=-70, el=10))
T("open-book", ["Thoracic open book"], [K("Side-Lying_Floor_Stretch", 0), K("Side-Lying_Floor_Stretch", 1)], MAT, hands="flat", cam=dict(az=-60, el=40))
T("snow-angel", ["Floor snow angels"], [K(SUP, 0, fk_armL=[92, 22, 92, 22], fk_armR=[92, 22, 92, 22]),
   K(SUP, 0, fk_armL=[92, 86, 92, 86], fk_armR=[92, 86, 92, 86]), K(SUP, 0, fk_armL=[-92, 30, -92, 30], fk_armR=[-92, 30, -92, 30])],
  MAT, hands="flat", palm="up", cam=dict(az=-50, el=42), pingpong=True)
T("pec-opener", ["Foam roller pec opener"], [K(SUP, 0, fk_armL=[100, 55, 100, 55], fk_armR=[100, 55, 100, 55]), K(SUP, 0, fk_armL=[98, 86, 98, 86], fk_armR=[98, 86, 98, 86])],
  P_(MAT, lambda J, J0, *a: roller("roller", (J0["pelvis"] + J0["head"]) / 2 + V((0, 0, -0.16)), axis=(1, 0, 0), length=0.95)), hands="flat", palm="up", cam=dict(az=-50, el=42))
HS_A = dict(fk_legL=[88, 42, 88, -48, 120], fk_legR=[88, 78, -88, 10, 120], fk_armL=[-35, 28, -35, 28], fk_armR=[-35, 28, -35, 28])
HS_B = dict(fk_legR=[88, 42, 88, -48, 120], fk_legL=[88, 78, -88, 10, 120], fk_armL=[-35, 28, -35, 28], fk_armR=[-35, 28, -35, 28])
T("hip-switch", ["90/90 hip switches"],
  [P(T=186, armL=[-36, 18, -14, 18], armR=[-36, 18, -14, 18], legL=[88, 42, 88, -48, 120], legR=[88, 78, -88, 10, 120]),
   P(T=186, armL=[-36, 18, -14, 18], armR=[-36, 18, -14, 18], legR=[88, 42, 88, -48, 120], legL=[88, 78, -88, 10, 120])],
  MAT, hands="flat", cam=dict(az=-30, el=28))

# ======================= CARRY / CARDIO =======================
T("farmer-carry", ["Dumbbell farmer carry", "Dumbbell or kettlebell farmer carry"], gait("Walking_Treadmill", 0, fk_armL=[1, 9, 1, 8], fk_armR=[1, 9, 1, 8]), DB(), hands="grip", steps=10)
T("plate-pinch", ["Plate pinch carry"], gait("Walking_Treadmill", 0, fk_armL=[1, 9, 1, 8], fk_armR=[1, 9, 1, 8]), lambda J, J0, *a: [plate_between("pl" + s, J["hand_" + s] + V((0, 0, -0.18)), J["hand_" + s] + V((0, 0.03 if s == "l" else -0.03, -0.18)), 0.2) for s in "lr"],
  hands="grip", steps=10)
T("trap-bar-carry", ["Trap-bar carry"], gait("Walking_Treadmill", 0, fk_armL=[1, 14, 1, 14], fk_armR=[1, 14, 1, 14]), lambda J, J0, *a: trap_bar("tb", J), hands="grip", steps=10)
T("bag-carry", ["Loaded backpack or shopping-bag carry"], gait("Walking_Treadmill", 0, fk_armL=[1, 12, 1, 10], fk_armR=[1, 12, 1, 10]),
  lambda J, J0, *a: (backpack("pack", J), shopping_bag("bag_l", J["hand_l"], V((0, 0.12, 0))), shopping_bag("bag_r", J["hand_r"], V((0, -0.12, 0)))), hands="grip", steps=10)
T("walk", ["Brisk outdoor walk"], gait("Walking_Treadmill", 0), None, steps=10)
T("ruck-walk", ["Ruck walk (backpack 5–10 kg)"], gait("Walking_Treadmill", 0), lambda J, J0, *a: backpack("pack", J), steps=10)
T("treadmill", ["Incline treadmill walk", "Incline treadmill walk (5–10%)", "Incline treadmill intervals", "Ski erg or incline treadmill tempo"],
  gait("Walking_Treadmill", 0), lambda J, J0, *a: treadmill("tm", J0, incline=5), steps=10)
T("elliptical", ["Elliptical or incline treadmill", "Ski erg or elliptical intervals", "Elliptical or bike"], gait("Elliptical_Trainer", 0),
  lambda J, J0, *a: elliptical("el", J0, J), hands="grip", steps=10)
T("bike", ["Elliptical or stationary bike", "Stationary bike or rower"], [K("Bicycling_Stationary", 0), K("Bicycling_Stationary", 0, mirror=True)],
  lambda J, J0, *a: upright_bike("bk", J0, J), hands="grip", steps=10)
T("air-bike", ["Air bike or rower intervals"], [K("Bicycling_Stationary", 0), K("Bicycling_Stationary", 0, mirror=True)],
  lambda J, J0, *a: upright_bike("bk", J0, J, air=True), hands="grip", steps=10)
T("rower", ["Rower (easy)", "Rower, bike or elliptical tempo"], two("Rowing_Stationary"), lambda J, J0, *a: rower("rw", J0, J), hands="grip",
  anchor={"x": ("ankle_r", None)})
T("battle-ropes", ["Battle rope intervals"], two("Battling_Ropes"),
  lambda J, J0, *a: [rod("rope" + s, J["hand_" + s], V((J0["pelvis"].x + 2.4, 0.15 if s == "l" else -0.15, 0.08)), 0.02, "cable") for s in "lr"], hands="grip", steps=5)

# ---------- pose cleanup flags (legs out of frame / pointing at the camera in the photos) ----------
STANDING = """straight-arm-pulldown face-pull cable-rear-delt-fly band-pull-apart band-w cable-er scap-squeeze cable-y-raise chin-tuck wall-chin-tuck
wall-slides standing-cable-press single-arm-cable-press kb-press cable-serratus pallof-press landmine-pallof pallof-rotation woodchop cable-lift
landmine-rainbow glute-squeeze cable-hold cable-pec-stretch pec-stretch""".split()
SEATED_LEGS = """machine-row machine-high-row reverse-pec-deck chest-press-machine shoulder-press-machine lat-pulldown abductor-machine cable-chin-tuck
t-spine-chair incline-db-press smith-incline""".split()
for _s in CAT:
    if _s["name"] in STANDING: _s["stance"] = "stand"
    if _s["name"] in SEATED_LEGS: _s["stance"] = "seated"

# ---------- two-sided exercises: occluded limbs mirror the visible side ----------
SYMMETRIC = """seated-cable-row machine-row tbar-row db-incline-row seal-row lat-pulldown machine-high-row assisted-pullup pullup-negative db-pullover
kb-pullover straight-arm-pulldown face-pull cable-rear-delt-fly reverse-pec-deck incline-rear-delt bentover-rear-delt band-pull-apart band-w
incline-y-raise incline-ytw push-up push-up-db incline-push-up chest-press-machine incline-db-press smith-incline floor-press standing-cable-press
shoulder-press-machine hip-thrust smith-hip-thrust glute-drive glute-bridge db-glute-bridge band-bridge-couch db-rdl bb-rdl smith-rdl kb-deadlift
trap-bar-deadlift pull-through hip-hinge-wall loaded-hinge-wall back-extension goblet-box-squat heels-up-goblet kb-complex chair-squat leg-press
hack-squat leg-extension abductor-machine lateral-walk crunch plate-crunch ball-crunch cable-crunch machine-crunch reverse-crunch captains-chair
bench-pull-in seated-pull-in lying-leg-raise ab-wheel bb-rollout front-plank cat-cow childs-pose cable-lat-stretch pallof-press landmine-pallof
farmer-carry trap-bar-carry plate-pinch tuck-hollow""".split()
MULTI = """push-up push-up-db shoulder-taps mountain-climbers push-up-side-plank""".split()
for _s in CAT:
    sym, multi = _s["name"] in SYMMETRIC, _s["name"] in MULTI
    if not (sym or multi): continue
    for _P in _s["keys"]:
        if "_ref" not in _P: continue
        _L, _R = landmarks(POSES[_P["_ref"]]["world"], mirror=_P.get("_mirror", False) and not _P.get("_post"), sym=sym, multi=multi)
        _P["lm"], _P["_R"] = (swap_limbs(_L) if _P.get("_post") else _L), _R

# ---------- floor poses with stable ground contact: hand-posed (FK) keys matched to the reference photos ----------
SB = dict(T=270, H=270, legL=[135, 8, -48, 8], legR=[135, 8, -48, 8], armL=[81, 14, 81, 14], armR=[81, 14, 81, 14])
def sb(**kw):
    d_ = dict(SB); d_.update(kw); return P(**d_)
def OLD(n): return next(x for x in SPECS if x["name"] == n)
_FK = {
    "glute-bridge": OLD("glute-bridge")["keys"], "db-glute-bridge": OLD("glute-bridge")["keys"], "band-bridge-couch": OLD("glute-bridge")["keys"],
    "single-leg-bridge": OLD("single-leg-bridge")["keys"], "reverse-crunch": OLD("reverse-crunch")["keys"],
    "supine-chin-tuck": [sb(), sb(N=244, H=228)],
    "mcgill": [sb(legL=[90, 6, 90, 6]), sb(legL=[90, 6, 90, 6], S=258, N=250, H=246)],
    "figure-4": [sb(legR=[128, 40, 98, -62]), sb(legL=[175, 8, 95, 8], legR=[150, 40, 112, -62], armL=[150, 6, 150, -6], armR=[150, 6, 150, -6])],
    "snow-angel": [sb(armL=[90, 22, 90, 22], armR=[90, 22, 90, 22]), sb(armL=[90, 88, 90, 88], armR=[90, 88, 90, 88]),
                   sb(armL=[-90, 30, -90, 30], armR=[-90, 30, -90, 30])],
    "pec-opener": [sb(armL=[96, 55, 96, 55], armR=[96, 55, 96, 55]), sb(armL=[96, 86, 96, 86], armR=[96, 86, 96, 86])],
    "t-spine-roller": [sb(armL=[-70, 40, 150, 40], armR=[-70, 40, 150, 40]), sb(S=292, N=296, H=300, armL=[-70, 40, 150, 40], armR=[-70, 40, 150, 40])],
    "side-plank": OLD("side-plank")["keys"], "clamshell": OLD("side-plank")["keys"],
}
for _s in CAT:
    if _s["name"] in _FK:
        _s["keys"] = _FK[_s["name"]]
        _s.pop("stance", None)
for _n in ("side-plank", "clamshell"):
    _sp = next(x for x in CAT if x["name"] == _n); _sp["anchor"] = OLD("side-plank")["anchor"]; _sp["hands"] = "relaxed"
    _sp["reach"] = {"hand_r": ("hip_r", (0.0, -0.10, 0.08))}
_t = next(x for x in CAT if x["name"] == "pec-opener"); _t["anchor"] = {"z": ("torso", 0.15)}
_t["props"] = lambda J, J0, *a: (mat("mat", J0), roller("roller", V(((J0["pelvis"].x + J0["head"].x) / 2, 0, 0.075)), axis=(1, 0, 0), length=0.95))
_t = next(x for x in CAT if x["name"] == "t-spine-roller")
_t["props"] = lambda J, J0, *a: (mat("mat", J0), roller("roller", V((J0["chest"].x, 0, 0.075))))
for _n in ("glute-bridge", "single-leg-bridge", "band-bridge-couch", "db-glute-bridge"):
    _t = next(x for x in CAT if x["name"] == _n); _t["free"] = ["hand_l", "hand_r"]; _t.pop("slide", None)

# ---------- round 8: remaining reference mismatches ----------
PRONE_LEGS = dict(fk_legL=[-90, 4, -90, 4, -80], fk_legR=[-90, 4, -90, 4, -80])      # prone: legs straight along the floor
for _n in ("floor-ytw", "prone-t", "prone-w", "prone-row", "swimmers", "prone-towel-pulldown"):
    for _P in next(x for x in CAT if x["name"] == _n)["keys"]: _P.update(PRONE_LEGS)

SIDE_BASE = dict(T=90, roll=-90, H=90, armL=[90, 0, 90, 0], legL=[-90, 0, -90, 0], legR=[-90, 0, -90, 0])   # lying on the left side
_t = next(x for x in CAT if x["name"] == "side-lying-er")
_t["keys"] = [P(**SIDE_BASE, armR=[-88, 0, 2, 0]), P(**SIDE_BASE, armR=[-88, 0, 175, 0])]
_t["anchor"] = {}; _t.pop("slide", None); _t["hands"] = "relaxed"; _t["handR"] = "grip"
_t["props"] = lambda J, J0, *a: (mat("mat", J0), dumbbell("db", J["hand_r"], J["gax_r"]))
_t["cam"] = dict(az=-80, el=18)
_t = next(x for x in CAT if x["name"] == "side-lying-abd")
_t["keys"] = OLD("side-lying-abduction")["keys"]; _t["props"] = lambda J, J0, *a: (mat("mat", J0), ankle_weight("aw", J, "r")); _t["cam"] = dict(az=-80, el=18)

CHILD_FK = dict(T=96, S1=118, S2=96, S3=74, S=96, H=50, N=62, legL=[64, 5, -90, 4, -95], legR=[64, 5, -90, 4, -95])
_t = next(x for x in CAT if x["name"] == "childs-pose")
_t["keys"] = [P(**CHILD_FK, armL=[70, 8, 70, 8], armR=[70, 8, 70, 8]), P(**CHILD_FK, armL=[70, -12, 70, -12], armR=[70, 28, 70, 28])]
_t["anchor"] = {"z": ("knee_r", 0.055)}

_fig = next(x for x in CAT if x["name"] == "figure-4")
_t = next(x for x in CAT if x["name"] == "pigeon-bench"); _t["keys"] = _fig["keys"]; _t["props"] = _fig["props"]; _t["cam"] = _fig.get("cam")

_t = next(x for x in CAT if x["name"] == "couch-stretch-bench")
_t.pop("rear_foot_z", None)
for _P in _t["keys"]: _P["fk_legR"] = [-8, 6, -152, 4, -100]
_t = next(x for x in CAT if x["name"] == "band-pull-apart")
_t["keys"] = [K("Band_Pull_Apart", 0, fk_armL=[90, 8, 90, 8], fk_armR=[90, 8, 90, 8]), K("Band_Pull_Apart", 1, fk_armL=[90, 84, 90, 84], fk_armR=[90, 84, 90, 84])]
_t = next(x for x in CAT if x["name"] == "smith-split")
_t["keys"] = [K("Split_Squats", 0, fk_armL=[-40, 70, 170, 20], fk_armR=[-40, 70, 170, 20]), K("Split_Squats", 1, fk_armL=[-40, 70, 170, 20], fk_armR=[-40, 70, 170, 20])]
_t["plant"] = ["foot_l", "foot_r"]

_t = next(x for x in CAT if x["name"] == "incline-push-up"); _o = OLD("incline-push-up")
_t["keys"] = _o["keys"]; _t["anchor"] = _o["anchor"]; _t["props"] = _o["props"]; _t.pop("plant", None)

# ---------- round 9: stiffer reference poses replaced with hand-posed keys verified against the photos ----------
_ht = OLD("hip-thrust")
def _thrust_bench(J, J0, *a):
    flat_bench("bench", J0["chest"].x - 0.55, J0["chest"].x + 0.05, 0.42, w=0.34)
def _bar_on_hips(J, J0, *a):
    c = (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, 0, 0.13))
    barbell("bb", c, V((0, 1, 0)))
    rod("bbpad", c - V((0, 0.16, 0)), c + V((0, 0.16, 0)), 0.045, "foam")
for _n, _props in (("hip-thrust", P_(_thrust_bench, _bar_on_hips)),
                   ("smith-hip-thrust", P_(_thrust_bench, lambda J, J0, *a: smith("sm", {**J0, "hands": (J0["hip_l"] + J0["hip_r"]) / 2 + V((0.04, 0, 0.13))},
                                                                                     {**J, "hands": (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, 0, 0.13))}))),
                   ("single-leg-hip-thrust", P_(_thrust_bench, lambda J, J0, *a: dumbbell("db", J["hip_r"] + V((0.03, 0, 0.14)), V((0, 1, 0)))))):
    _t = next(x for x in CAT if x["name"] == _n)
    _t["keys"] = [dict(k) for k in _ht["keys"]]; _t["anchor"] = _ht["anchor"]; _t["props"] = _props; _t["hands"] = "grip"
    if _n == "single-leg-hip-thrust":
        _t["keys"][0]["legL"] = [150, 8, 150, 8]; _t["keys"][1]["legL"] = [110, 8, 110, 8]
_t = next(x for x in CAT if x["name"] == "glute-drive"); _t["keys"] = [dict(k) for k in _ht["keys"]]; _t["anchor"] = _ht["anchor"]
_t["props"] = lambda J, J0, *a: (pad("gd_back", V((J0["chest"].x - 0.25, 0, 0.38)), (0.5, 0.5, 0.08), pitch=-12),
                                 rod("gd_belt", (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, 0.3, 0.12)), (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, -0.3, 0.12)), 0.05, "uphol"),
                                 foot_base("gd_base", J0["chest"].x - 0.6, J0["ankle_r"].x + 0.35, w=0.9),
                                 tube("gd_arm_l", (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, 0.3, 0.12)), V((J0["chest"].x - 0.2, 0.34, 0.45))),
                                 tube("gd_arm_r", (J["hip_l"] + J["hip_r"]) / 2 + V((0.04, -0.3, 0.12)), V((J0["chest"].x - 0.2, -0.34, 0.45))))
BEAR = dict(T=90, H=112, armL=[0, 4, 0, 4], armR=[0, 4, 0, 4], legL=[4, 4, -72, 4, -20], legR=[4, 4, -72, 4, -20])
_t = next(x for x in CAT if x["name"] == "bear-taps")
_t["keys"] = [P(**BEAR), P(**{**BEAR, "armR": [40, -30, 150, -60]}), P(**BEAR), P(**{**BEAR, "armL": [40, -30, 150, -60]})]
_t["anchor"] = {}; _t["hands"] = "flat"

# ---------- round 10: QA sweep fixes ----------
# side plank clamshell: forearm + bottom knee on the mat, knees bent 90 deg (shins behind), top knee opens with feet together
CLAM = dict(T=107, H=107, roll=-90, armL=[0, 0, 90, -90], armR=[-10, 0, 40, 0])
_t = next(x for x in CAT if x["name"] == "clamshell")
_t["keys"] = [P(**CLAM, legL=[-73, 0, 0, 88, 0, 88], legR=[-66, 0, 0, -88, 0, -88]),
              P(**CLAM, legL=[-73, 0, 0, 88, 0, 88], legR=[-105, 0, 0, -43, 0, -43])]
_t["anchor"] = {"z": ("elbow_l", 0.045), "x": ("knee_l", None)}
# forearm plank with reach: the support forearm stays planted
_t = next(x for x in CAT if x["name"] == "plank-reach")
_t["keys"] = OLD("plank-reach")["keys"]; _t["anchor"] = OLD("plank-reach")["anchor"]; _t["free"] = ["hand_l", "hand_r"]
# crunch: lying, knees bent, fingertips at the temples (as in the reference)
_t = next(x for x in CAT if x["name"] == "crunch")
_t["keys"] = OLD("crunch")["keys"]; _t["anchor"] = {}; _t["hands"] = "relaxed"
_t["reach"] = {"hand_l": ("head", (0.03, 0.09, -0.11)), "hand_r": ("head", (0.03, -0.09, -0.11))}
_t["cam"] = dict(az=-70, el=10)

# ---------- round 11 ----------
# clamshell legs solved from the measured joint geometry: bottom knee/shin on the mat, top knee stacked, then abducts ~40 deg
_t = next(x for x in CAT if x["name"] == "clamshell")
_t["keys"] = [P(**CLAM, legL=[-64, 0, 0, 88, 0, 88], legR=[-47.5, 0, 0, -86, 0, -86]),
              P(**CLAM, legL=[-64, 0, 0, 88, 0, 88], legR=[-90, 0, 12.5, -47.7, 12.5, -47.7])]
# single-leg hip thrust: free leg tucked (thigh up, knee bent)
_t = next(x for x in CAT if x["name"] == "single-leg-hip-thrust")
_t["keys"][0]["legL"] = [155, 8, 80, 8]; _t["keys"][1]["legL"] = [172, 8, 90, 8]
# swing: hinge (bell between the legs) <-> standing tall, arm out level, bell in line with the arm
_t = next(x for x in CAT if x["name"] == "kb-swing")
_t["keys"] = [K("One-Arm_Kettlebell_Swings", 1), K("One-Arm_Kettlebell_Swings", 0, fk_armR=[88, 4, 88, 4])]
# hack squat: back flat on the pad (20 deg lean), hips travel along the rails, hands on the shoulder grips
HACK = dict(T=200, H=186, armL=[10, 40, 175, 15], armR=[10, 40, 175, 15])
_t = next(x for x in CAT if x["name"] == "hack-squat")
_t["keys"] = [P(**HACK, legL=[24, 7, 16, 7], legR=[24, 7, 16, 7]), P(**HACK, legL=[65, 9, -23, 9], legR=[65, 9, -23, 9])]
_t["anchor"] = {"x": ("ankle_r", None)}; _t.pop("stance", None); _t["plant"] = ["foot_l", "foot_r"]

# ---------- round 12: side planks rest on the forearm surface (not the joint); static bottom limbs are not IK-planted ----------
_t = next(x for x in CAT if x["name"] == "clamshell")
_t["keys"] = [P(**CLAM, legL=[-60.5, 0, 0, 88, 0, 88], legR=[-42.3, 0, 0, -86, 0, -86]),
              P(**CLAM, legL=[-60.5, 0, 0, 88, 0, 88], legR=[-90, 0, 15, -45, 15, -45])]
_t["anchor"] = {"z": ("elbow_l", 0.07), "x": ("knee_l", None)}
_t = next(x for x in CAT if x["name"] == "side-plank")
_t["anchor"] = {"z": ("elbow_l", 0.07), "x": ("ankle_l", None)}
for _n in ("clamshell", "side-plank"):
    next(x for x in CAT if x["name"] == _n)["free"] = ["foot_l", "foot_r", "hand_l"]

# ---------- round 13: prone floor family + bent-over rear delt, hand-posed from world-space limb directions ----------
import math as _m
def V2(v):
    """World direction for the LEFT limb (x forward, y out to the side, z up) -> [pitch, lateral] for d(); mirrored for the right."""
    x, y, z = v; n = _m.sqrt(x * x + y * y + z * z); x, y, z = x / n, y / n, z / n
    return [round(_m.degrees(_m.atan2(x, -z)), 2), round(_m.degrees(_m.asin(max(-1.0, min(1.0, y)))), 2)]
def ARMS(u, f=None):
    a = V2(u) + V2(f or u); return dict(armL=a, armR=list(a))
PRONE = dict(T=90, S=94, N=93, H=92, legL=[-90, 3, -90, 3, -66], legR=[-90, 3, -90, 3, -66])
def prone(**kw):
    d_ = dict(PRONE); d_.update(kw); return P(**d_)
Y_UP, Y_DN = ARMS((0.84, 0.48, 0.26)), ARMS((0.86, 0.5, -0.06))
T_UP, T_DN = ARMS((0.02, 0.96, 0.27)), ARMS((0.02, 0.99, -0.08))
W_UP, W_DN = ARMS((-0.55, 0.75, 0.36), (0.72, 0.55, 0.3)), ARMS((-0.6, 0.8, -0.05), (0.75, 0.62, -0.05))
REACH = ARMS((0.97, 0.2, 0.06))
ROW_B = ARMS((-0.5, 0.78, 0.36), (0.85, 0.3, 0.28))
def _set(name, keys, **opt):
    t = next(x for x in CAT if x["name"] == name)
    t["keys"] = keys; t["anchor"] = {}; t.pop("stance", None)
    t.update(opt)
_set("prone-t", [prone(**T_DN), prone(**T_UP, S=97, H=96)], cam=dict(az=-155, el=32))
_set("prone-w", [prone(**W_DN), prone(**W_UP, S=98, H=96)], cam=dict(az=-155, el=32))
_set("floor-ytw", [prone(**Y_UP, S=97, H=96), prone(**T_UP, S=97, H=96), prone(**W_UP, S=98, H=96)], pingpong=True, cam=dict(az=-155, el=32))
_set("prone-row", [prone(**REACH), prone(**ROW_B, S=98, H=96)], cam=dict(az=-155, el=32))
_set("swimmers", [prone(**ARMS((0.94, 0.18, 0.28)), S=97, H=96), prone(**ARMS((0.05, 0.95, 0.3)), S=97, H=96),
                  prone(**ARMS((-0.65, 0.68, 0.33)), S=97, H=96), prone(**ARMS((-0.95, 0.15, 0.27)), S=97, H=96)], pingpong=True, cam=dict(az=-155, el=32))
_set("prone-towel-pulldown", [prone(**ARMS((0.96, 0.24, 0.12))), prone(**ROW_B, S=98, H=96)], cam=dict(az=-155, el=32))
for _n in ("prone-t", "prone-w", "floor-ytw", "prone-row", "swimmers", "prone-towel-pulldown"):
    next(x for x in CAT if x["name"] == _n)["free"] = ["hand_l", "hand_r"]

# bent-over rear-delt raise: symmetric hip hinge, dumbbells hang then sweep out to the sides; front-quarter camera
HINGE_BO = dict(T=106, S=108, N=124, H=132, legL=[12, 7, -4, 7], legR=[12, 7, -4, 7])
_set("bentover-rear-delt", [P(**HINGE_BO, **ARMS((0.08, 0.16, -1.0), (0.1, 0.14, -1.0))),
                            P(**HINGE_BO, **ARMS((0.08, 0.97, -0.12), (0.12, 0.95, -0.2)))],
     props=DB(), plant=["foot_l", "foot_r"], cam=dict(az=-28, el=14))

# ---------- round 14: full-frame sweep fixes ----------
def _t(n): return next(x for x in CAT if x["name"] == n)
# seal row: the bench runs under the whole body (legs rested, not floating)
_t("seal-row")["props"] = P_(lambda J, J0, *a: flat_bench("bench", min(J0["ankle_l"].x, J0["ankle_r"].x) - 0.08, J0["shoulders"].x + 0.25,
                                                          region_low("torso"), w=0.34), DB())
# one-arm row: bench under the support knee/hand so the working dumbbell hangs clear beside it
_t("one-arm-db-row")["props"] = P_(lambda J, J0, *a: flat_bench("bench", J0["knee_l"].x - 0.2, J0["hand_l"].x + 0.2, min(J0["knee_l"].z, J0["hand_l"].z) - 0.04,
                                                                  y=(J0["knee_l"].y + J0["hand_l"].y) / 2 + 0.05), DB("r"))
# chest-supported raises: front-quarter camera so the sideways sweep reads (near arm no longer points at the lens)
for _n in ("incline-rear-delt", "incline-y-raise", "incline-ytw"): _t(_n)["cam"] = dict(az=-22, el=14)
# band W: elbows tucked at the sides, forearms rotate out against the band
_w0, _w1 = V2((0.12, 0.12, -1.0)) + V2((1.0, 0.18, 0.05)), V2((0.12, 0.12, -1.0)) + V2((0.5, 0.86, 0.05))
_t("band-w")["keys"] = [K("External_Rotation_with_Band", 0, fk_armL=_w0, fk_armR=list(_w0)), K("External_Rotation_with_Band", 0, fk_armL=_w1, fk_armR=list(_w1))]
_t("band-w")["cam"] = dict(az=-18, el=10)
# side-lying ER: top leg rests on the bottom leg
for _P in _t("side-lying-er")["keys"]: _P["legR"] = [-80, 0, -82, 0]

# ---------- round 15 ----------
# RFESS: rear instep on the bench where the rear leg can reach it at the bottom; dumbbells hang at the sides
_t("rfess")["keys"] = two("Split_Squats", fk_armL=[2, 9, 2, 8], fk_armR=[2, 9, 2, 8])
_t("rfess")["rear_foot_dx"] = 0.22
_t("rfess")["props"] = P_(lambda J, J0, *a: (lambda b: flat_bench("bench", b.x + 0.22 - 0.36, b.x + 0.22 + 0.2, 0.45, y=b.y, w=0.32))(
    min(J0["ankle_l"], J0["ankle_r"], key=lambda v: v.x)), DB())
# Smith RDL: the same hip hinge as the barbell RDL, bar guided by the Smith frame
_t("smith-rdl")["keys"] = [K("Romanian_Deadlift", 1), K("Romanian_Deadlift", 0)]
# supported single-leg RDL: the support hand stays on top of the post (fixed point reachable in both positions)
def _post(ctx):
    st = ctx["states"]; return (st[0]["hand_l"]["tip"] + st[1]["hand_l"]["tip"]) / 2
_t("single-leg-rdl-support")["track"] = lambda ctx: {"hand_l": (_post(ctx), None)}
_t("single-leg-rdl-support")["props"] = lambda J, J0, ctx=None, *a: (lambda P: (tube("support", V((P.x + 0.03, P.y + 0.03, 0.0)), V((P.x + 0.03, P.y + 0.03, P.z - 0.03)), 0.03, "steel"),
    box("support_base", (P.x + 0.03, P.y + 0.03, 0.02), (0.3, 0.3, 0.04), "frame")))(_post(ctx) if ctx else J0["hand_l"])
# box / chair squats: the seat sits behind the heels, hips land on it at the bottom
_heel = lambda J0: min(J0["ankle_l"].x, J0["ankle_r"].x)
_db_goblet = lambda J, J0, *a: dumbbell("db", J["hands"] + V((0.03, 0, -0.04)), V((0, 0, 1)), 0.28)
_t("goblet-box-squat")["props"] = P_(lambda J, J0, *a: box_step("box", _heel(J0) - 0.3, 0.42), _db_goblet)
_t("heels-up-goblet")["props"] = P_(lambda J, J0, *a: box_step("box", _heel(J0) - 0.3, 0.42),
    lambda J, J0, *a: box("wedge", ((J0["ankle_l"].x + J0["ankle_r"].x) / 2, 0, 0.012), (0.18, 0.7, 0.025), "plate"), _db_goblet)
_t("chair-squat")["props"] = lambda J, J0, *a: chair("chair", {**J0, "hips": V((_heel(J0) - 0.3, 0, J0["hips"].z))}, top=0.45)

# ---------- round 16 ----------
# plank with reach: lift the forearm first, then reach, so the arm arcs over the floor instead of through it
_k0, _k1 = OLD("plank-reach")["keys"]
_kh = dict(_k0); _kh["armR"] = [30, 6, 90, 4]
_t("plank-reach")["keys"] = [_k0, _kh, _k1]; _t("plank-reach")["pingpong"] = True
# push-up to side plank: high plank -> side plank on the left hand, top arm to the ceiling (hand-posed, feet stay down)
_t("push-up-side-plank")["keys"] = OLD("push-up-to-side-plank")["keys"]; _t("push-up-side-plank")["anchor"] = OLD("push-up-to-side-plank")["anchor"]
_t("push-up-side-plank")["cam"] = dict(az=-70, el=14)

# ---------- round 17: stretches rebuilt to match their names ----------
def R2(v):
    """World direction for the RIGHT limb (x forward, y left, z up) -> [pitch, lateral] for d(..., side=-1)."""
    return V2((v[0], -v[1], v[2]))
def LEG(side, thigh, shin, foot=None):
    f = V2 if side == "l" else R2
    return f(thigh) + f(shin) + (f(foot) if foot else [])

# hamstring stretch on a bench: right heel up on the bench, leg straight, hinge forward over it, hands slide down the shin
HAM = dict(legL=[1, 4, -1, 4], legR=[62, 3, 62, 3, 150])
_set("bench-ham", [P(T=172, S=170, H=176, **HAM, armL=[25, 14, 55, 8], armR=[25, 14, 55, 8]),
                   P(T=128, S=120, H=128, **HAM, armL=[68, 10, 74, 6], armR=[68, 10, 74, 6])],
     props=lambda J, J0, *a: flat_bench("bench", J0["ankle_r"].x - 0.25, J0["ankle_r"].x + 0.3, J0["ankle_r"].z - 0.07, y=J0["ankle_r"].y),
     plant=["foot_l", "foot_r"], cam=dict(az=-72, el=10))

# bench pigeon: left shin across the bench, right leg extended back to the floor; tall, then fold over the front shin
PIG = dict(legL=LEG("l", (0.96, -0.12, -0.25), (0.05, -1.0, -0.02), (0.05, -1.0, -0.3)),
           legR=LEG("r", (-0.62, -0.1, -0.78), (-0.62, -0.1, -0.78)))
_set("pigeon-bench", [P(T=180, S=180, H=182, **PIG, armL=[10, 18, 40, 10], armR=[10, 18, 40, 10]),
                      P(T=118, S=110, H=112, **PIG, armL=[72, 22, 80, 18], armR=[72, 22, 80, 18])],
     props=lambda J, J0, *a: flat_bench("bench", J0["knee_l"].x - 0.25, J0["knee_l"].x + 0.55, 0.45),
     anchor={"z": ("knee_l", 0.5)}, plant=["foot_r"], hands="flat", cam=dict(az=-35, el=16))

# figure-4: hands hold behind the supporting thigh as it is drawn in
_fk = _t("figure-4")["keys"]
_fk[1]["reach"] = {"hand_l": ("knee_l", (-0.08, 0.06, 0.07)), "hand_r": ("knee_l", (-0.08, -0.06, 0.07))}

# 90/90 hip switches: seated tall on the hands, legs swing through knees-up from one 90/90 to the other, hips stay down
ARMS_BACK = ARMS((-0.42, 0.26, -0.87))
def _ninety(front):
    if front == "r":
        return dict(legR=LEG("r", (0.72, -0.69, -0.05), (-0.2, 0.98, -0.02), (-0.2, 0.98, -0.3)),
                    legL=LEG("l", (-0.2, 0.98, -0.05), (-0.98, 0.1, -0.02), (-0.9, 0.1, -0.4)))
    return dict(legL=LEG("l", (0.72, 0.69, -0.05), (-0.2, -0.98, -0.02), (-0.2, -0.98, -0.3)),
                legR=LEG("r", (-0.2, -0.98, -0.05), (-0.98, -0.1, -0.02), (-0.9, -0.1, -0.4)))
_up = dict(legL=LEG("l", (0.6, 0.28, 0.75), (0.42, 0.1, -0.9)), legR=LEG("r", (0.6, -0.28, 0.75), (0.42, -0.1, -0.9)))
_set("hip-switch", [P(T=176, H=178, **ARMS_BACK, **_ninety("r")), P(T=172, H=176, **ARMS_BACK, **_up),
                    P(T=176, H=178, **ARMS_BACK, **_ninety("l")), P(T=172, H=176, **ARMS_BACK, **_up)],
     hands="flat", plant=["hand_l", "hand_r"], cam=dict(az=-24, el=22))

# ---------- round 18 ----------
# RFESS hand-posed: left foot forward, right instep planted on the bench behind for the whole rep
_set("rfess", [P(T=182, H=184, legL=[28, 6, 15, 6], legR=[-35, 4, -90, 4, -130], armL=[2, 9, 2, 8], armR=[2, 9, 2, 8]),
               P(T=172, H=178, legL=[80, 8, 5, 8], legR=[-35, 4, -150, 4, -150], armL=[2, 9, 2, 8], armR=[2, 9, 2, 8])],
     props=P_(lambda J, J0, *a: flat_bench("bench", J0["ankle_r"].x - 0.32, J0["ankle_r"].x + 0.22, J0["ankle_r"].z - 0.06, y=J0["ankle_r"].y, w=0.32), DB()),
     anchor={"x": ("ankle_l", None)}, plant=["foot_l", "foot_r"], cam=dict(az=-72, el=8))
_t("rfess").pop("rear_foot_z", None); _t("rfess").pop("rear_foot_dx", None)
# Smith RDL: symmetric hinge so both hands sit on the (horizontal) Smith bar
_t("smith-rdl")["keys"] = [K("Romanian_Deadlift", 1, sym=True), K("Romanian_Deadlift", 0, sym=True)]
# supported single-leg RDL: post top at waist height just ahead of the support shoulder (reachable standing and hinged)
def _post(ctx): return ctx["J0"]["shoulder_l"] + V((0.15, 0.06, -0.55))
# bench pigeon: front view shows the shin across the bench; bench extends back under the hips
_t("pigeon-bench")["props"] = lambda J, J0, *a: flat_bench("bench", J0["knee_l"].x - 0.55, J0["knee_l"].x + 0.4, 0.45)
_t("pigeon-bench")["cam"] = dict(az=-14, el=20)
# 90/90: hips stay seated on the floor through the switch
_t("hip-switch")["anchor"] = {"z": ("pelvis", 0.13)}
# one-arm row: a little more clearance for the working dumbbell
_t("one-arm-db-row")["props"] = P_(lambda J, J0, *a: flat_bench("bench", J0["knee_l"].x - 0.2, J0["hand_l"].x + 0.2, min(J0["knee_l"].z, J0["hand_l"].z) - 0.04,
                                                                  y=(J0["knee_l"].y + J0["hand_l"].y) / 2 + 0.1), DB("r"))

# ---------- round 19 ----------
_t("pigeon-bench")["cam"] = dict(az=-62, el=12)
_ab = ARMS((-0.45, 0.45, -0.77))
for _P in _t("hip-switch")["keys"]: _P["armL"], _P["armR"] = list(_ab["armL"]), list(_ab["armR"])

# ---------- round 20: audit follow-ups ----------
# 90/90: feet lie flat on the floor (no toes through it); hands behind with fingers pointing back
def _ninety(front):
    if front == "r":
        return dict(legR=LEG("r", (0.72, -0.69, -0.05), (-0.2, 0.98, -0.02), (-0.2, 0.98, -0.04)),
                    legL=LEG("l", (-0.05, 1.0, -0.05), (-0.98, 0.1, -0.02), (-0.97, 0.1, -0.05)))
    return dict(legL=LEG("l", (0.72, 0.69, -0.05), (-0.2, -0.98, -0.02), (-0.2, -0.98, -0.04)),
                legR=LEG("r", (-0.05, -1.0, -0.05), (-0.98, -0.1, -0.02), (-0.97, -0.1, -0.05)))
_hs = _t("hip-switch")["keys"]
for _i, _f in ((0, "r"), (2, "l")): _hs[_i].update(_ninety(_f))
for _P in _hs: _P["handdir"] = -92
# bench pigeon: back leg angled so the ball of the foot reaches the floor
for _P in _t("pigeon-bench")["keys"]: _P["legR"] = LEG("r", (-0.79, -0.1, -0.6), (-0.79, -0.1, -0.6))

# ---------- round 21: final-render review ----------
# deadlift family: arms hang straight from the shoulders so both hands meet the bar / handles evenly (the photo pose is one-sided)
HANG = dict(fk_armL=[0, 8, 0, 8], fk_armR=[0, 8, 0, 8])
for _n in ("bb-rdl", "smith-rdl"): _t(_n)["keys"] = [K("Romanian_Deadlift", 1, **HANG), K("Romanian_Deadlift", 0, **HANG)]
for _n in ("trap-bar-deadlift", "kb-deadlift"): _t(_n)["keys"] = [K("Trap_Bar_Deadlift", 1, **HANG), K("Trap_Bar_Deadlift", 0, **HANG)]
# front plank: the hand-posed forearm plank (elbows and toes on the mat)
_o = OLD("plank"); _t("front-plank")["keys"] = _o["keys"]; _t("front-plank")["anchor"] = _o["anchor"]
_t("front-plank")["free"] = ["hand_l", "hand_r"]; _t("front-plank")["hands"] = "flat"

# ---------- round 22 ----------
# forearm planks: hold the body still in x/y on the support elbow (the reaching arm must not drag the body)
for _n in ("plank-reach", "front-plank"):
    _t(_n)["anchor"] = {"z": ("elbow_l", 0.045), "x": ("elbow_l", None)}
_k0, _, _k1, _ = _t("plank-reach")["keys"] if len(_t("plank-reach")["keys"]) == 4 else (_t("plank-reach")["keys"][0], None, _t("plank-reach")["keys"][2], None)
_kh = dict(_k0); _kh["armR"] = [62, 6, 78, 4]     # elbow lifts clear of the mat before the arm reaches
_t("plank-reach")["keys"] = [_k0, _kh, _k1]

# ---------- round 23 ----------
# step-up (hand-posed): left foot up on the box -> stand tall on it (trailing leg clears the box edge) -> knee drive
SU_ARMS = dict(armL=[2, 9, 2, 8], armR=[2, 9, 2, 8])
_set("step-up", [P(T=178, H=180, **SU_ARMS, legL=[85, 5, -5, 5], legR=[2, 5, -2, 5]),
                 P(T=180, H=180, **SU_ARMS, legL=[2, 4, -2, 4], legR=[-15, 5, -60, 5], anchor={"z": ("ankle_l", None)}),
                 P(T=180, H=180, **SU_ARMS, legL=[2, 4, -2, 4], legR=[70, 5, -20, 5], anchor={"z": ("ankle_l", None)})],
     props=P_(lambda J, J0, *a: box_step("box", J0["ankle_l"].x + 0.05, J0["ankle_l"].z - 0.072, d_=0.45, w=0.6), DB()),
     pingpong=True, plant=["foot_l"], hands="grip", cam=dict(az=-62, el=10))
# supported split squat: the right hand stays on top of the post (reachable at the top and the bottom)
def _post_ss(J0): return V((J0["shoulder_r"].x + 0.22, J0["shoulder_r"].y - 0.12, J0["shoulder_r"].z - 0.32))
_t("supported-split")["track"] = lambda ctx: {"hand_r": (_post_ss(ctx["J0"]), None)}
_t("supported-split")["handR"] = "grip"
_t("supported-split")["props"] = lambda J, J0, *a: (lambda p: (tube("support", V((p.x + 0.03, p.y, 0.0)), V((p.x + 0.03, p.y, p.z - 0.03)), 0.03, "steel"),
    box("support_base", (p.x + 0.03, p.y, 0.02), (0.3, 0.3, 0.04), "frame")))(_post_ss(J0))

# ---------- round 24: hand-posed walk cycle (contact -> passing -> contact -> passing), arms counter-swing ----------
def WALK(arms=None):
    """4 keys. arms: None = natural counter-swing; (armL, armR) = held fixed (carries)."""
    fwdL = dict(legL=[22, 3, 2, 3], legR=[-14, 3, -38, 3, 35])          # left heel strike, right toe-off
    passL = dict(legL=[2, 3, -2, 3], legR=[18, 3, -45, 3])              # left stance, right knee swinging through
    fwdR = dict(legR=[22, 3, 2, 3], legL=[-14, 3, -38, 3, 35])
    passR = dict(legR=[2, 3, -2, 3], legL=[18, 3, -45, 3])
    if arms is None:
        sw = [dict(armL=[-14, 9, -6, 8], armR=[18, 9, 32, 8]), dict(armL=[2, 9, 8, 8], armR=[2, 9, 8, 8]),
              dict(armL=[18, 9, 32, 8], armR=[-14, 9, -6, 8]), dict(armL=[2, 9, 8, 8], armR=[2, 9, 8, 8])]
    else:
        sw = [dict(armL=list(arms[0]), armR=list(arms[1]))] * 4
    return [P(T=178, H=178, **legs_, **a) for legs_, a in zip((fwdL, passL, fwdR, passR), sw)]
for _n, _arms in (("walk", None), ("ruck-walk", None), ("treadmill", None),
                  ("farmer-carry", ([1, 9, 1, 8], [1, 9, 1, 8])), ("plate-pinch", ([1, 9, 1, 8], [1, 9, 1, 8])),
                  ("trap-bar-carry", ([1, 14, 1, 14], [1, 14, 1, 14])), ("bag-carry", ([1, 12, 1, 10], [1, 12, 1, 10])),
                  ("suitcase", ([10, 12, 18, 8], [1, 9, 1, 8]))):
    _s = _t(_n); _s["keys"] = WALK(_arms); _s["steps"] = 5; _s["anchor"] = {"x": ("pelvis", None)}
    _s.pop("stance", None); _s["free"] = ["foot_l", "foot_r"]
