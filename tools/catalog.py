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
T("seated-cable-row", ["Seated cable row (neutral grip)"], two("Seated_Cable_Rows"),
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
# over-the-top towel: anchored at the door's TOP EDGE (trapped by the closed door), not a rigid mid-door rod - two taut
# strands run from the top down to the hands, with a short crest rod showing the fold draped over the edge. fk_N/fk_H
# keep the neck/head sagittal-only (d() has no side term) so there's no lateral tilt or twist, in line with the lean.
T("door-towel-row", ["Door towel row", "Door towel row (both hands)"],
  [K("Suspended_Row", 0, fk_N=-134, fk_H=-130), K("Suspended_Row", 1, fk_N=-161, fk_H=-165)],
  lambda J, J0, *a: DOOR_TOWEL(("hand_l", "hand_r"), "hands")(J, J0), hands="grip", cam=dict(az=-108, margin=1.2), prop_headroom=0.7)
T("door-towel-row-1arm", ["Single-arm door towel row"],
  [K("Suspended_Row", 0, fk_armL=[10, 14, 30, 10], fk_N=-134, fk_H=-130), K("Suspended_Row", 1, fk_armL=[10, 14, 30, 10], fk_N=-161, fk_H=-165)],
  lambda J, J0, *a: DOOR_TOWEL(("hand_r",), "hand_r")(J, J0), handR="grip", cam=dict(az=-108, margin=1.2), prop_headroom=0.7)
T("prone-towel-pulldown", ["Prone towel pulldown"],
  [K("Superman", 0, fk_armL=[104, 22, 104, 22], fk_armR=[104, 22, 104, 22]), K("Superman", 0, fk_armL=[-100, 62, 104, 26], fk_armR=[-100, 62, 104, 26])],
  P_(MAT, lambda J, J0, *a: rod("towel", J["hand_l"], J["hand_r"], 0.02, "towel")), hands="grip", cam=dict(el=18))
T("lat-pulldown", ["Lat pulldown (neutral or wide grip, to chest)", "Lat pulldown (light, slow)"], two("Wide-Grip_Lat_Pulldown"),
  lambda J, J0, *a: lat_machine("m", J0, J, "wide"), hands="grip", palm="forward", cam=dict(az=-150, el=12))
# high row: hand-posed square to the machine (photo keys twisted the torso): start reach forward-up, end elbows down/back, handles at upper chest
HR_LEGS = dict(legL=[90, 6, 0, 6], legR=[90, 6, 0, 6])
HR_START = P(T=180, S=180, H=180, N=180, **HR_LEGS, armL=[118, 12, 122, 10], armR=[118, 12, 122, 10])
HR_END = P(T=184, S=184, H=180, N=180, **HR_LEGS, armL=[-10, 18, 112, 8], armR=[-10, 18, 112, 8])
HR_MID = P(T=182, S=182, H=180, N=180, **HR_LEGS, armL=[17, 8, 136.5, 8], armR=[17, 8, 136.5, 8])   # keeps the hands on the lever's arc
T("machine-high-row", ["Machine high row"], [HR_START, HR_MID, HR_END], pingpong=True, steps=3, props= lambda J, J0, *a: hr_machine("m", J0, J), hands="grip", anchor=SEATZ(0.45), cam=dict(az=-70, el=10, margin=1.12))
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
T("wall-slides", ["Wall slides", "Wall slide with reach"],
  [K(STAND_SIDE, 0, fk_armL=[180, 88, 180, 4], fk_armR=[180, 88, 180, 4]), K(STAND_SIDE, 0, fk_armL=[180, 34, 180, 22], fk_armR=[180, 34, 180, 22])],
  lambda J, J0, *a: wall("wall", J0["shoulders"].x - 0.2), hands="flat", handdir=180, palm="forward", cam=dict(az=-22, el=12))

# ======================= PRESS =======================
T("push-up", ["Pause push-up"], two("Pushups"), None, hands="flat")
T("push-up-db", ["Push-up on dumbbell handles"], two("Pushups"), DB(), hands="grip")
T("incline-push-up", ["Push-up (hands elevated if needed)"], two("Incline_Push-Up"),
  lambda J, J0, *a: box_step("box", J0["hands"].x, J0["hands"].z - 0.03, d_=0.45, w=0.62), hands="flat")
T("chest-press-machine", ["Chest press machine (neutral grip)"], two("Machine_Bench_Press"),
  lambda J, J0, *a: lever_machine("m", J0, J, "press_back", chest_pad=False, back_pad=True), hands="grip")
T("db-bench-1arm", ["Single-arm dumbbell bench press"], two("One_Arm_Dumbbell_Bench_Press", fk_armL=[80, 20, 70, 20]),
  P_(lambda J, J0, *a: flat_bench("bench", J0["head"].x - 0.05, J0["hips"].x + 0.35, region_low("torso")), DB("r")), handR="grip", anchor=BENCH, slide={"foot_l": 0.085, "foot_r": 0.085})
T("incline-db-press", ["Low-incline dumbbell press (15–30°, neutral grip)"], two("Hammer_Grip_Incline_DB_Bench_Press"),
  P_(lambda J, J0, *a: incline_bench("bench", J0, 28, J0["hips"].x + 0.05, region_low("seat")), DB()), hands="grip")
T("smith-incline-high", ["High-incline Smith press"], two("Smith_Machine_Incline_Bench_Press"),
  P_(lambda J, J0, *a: incline_bench("bench", J0, 45, J0["hips"].x + 0.05, region_low("seat")), lambda J, J0, *a: smith("sm", J0, J)), hands="grip", palm="feet", cam=dict(az=-35))
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
T("leg-press", ["Leg press (feet mid-to-high on platform)", "Leg press (feet high)"], two("Leg_Press"),
  lambda J, J0, *a: leg_press("m", J0, J), anchor=SEATZ(0.42))
T("hack-squat", ["Hack or pendulum squat (feet high)"], two("Hack_Squat"), lambda J, J0, *a: hack_squat_machine("m", J0, J), hands="grip", cam=dict(az=-60))
T("leg-extension", ["Leg extension (partial range)"], two("Leg_Extensions"), lambda J, J0, *a: leg_extension("m", J0, J), hands="grip", anchor=SEATZ(0.5))
T("step-up", ["Dumbbell step-up (box knee-height or lower)"], two("Dumbbell_Step_Ups"),
  P_(lambda J, J0, *a: box_step("box", J0["ankle_l"].x, 0.38, d_=0.5, w=0.65), DB()), hands="grip")
T("stair-step", ["Stair step-up"], two("Dumbbell_Step_Ups"),
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
T("side-plank", ["Side plank (knees or feet)"], hold("Side_Bridge", 1), MAT, cam=dict(az=-85, el=10), still=True)
T("suitcase", ["Suitcase carry", "Single-arm farmer carry"], gait("Walking_Treadmill", 0, fk_armL=[10, 12, 18, 8], fk_armR=[1, 9, 1, 8]), DB("r"), handR="grip", steps=10)
T("cable-hold", ["Single-arm cable hold"], hold("Upper_Back_Stretch", 0, fk_armL=[1, 9, 1, 8], fk_armR=[8, 8, 14, 6]),
  lambda J, J0, *a: (cable("c", cable_column("col", J0["hips"].x, 0.85, 0.2), J["hand_l"]), d_handle("h", J["hand_l"], (0, 0, 1))),
  handL="grip", stance="stand", cam=dict(az=-25), still=True)
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
T("front-plank", ["Front plank"], hold("Plank", 1), MAT, hands="relaxed", cam=dict(el=14), still=True)
T("plank-reach", ["Plank with reach"], [K("Plank", 1), K("Plank", 1, fk_armR=[92, 6, 92, 4])], MAT, hands="relaxed", cam=dict(el=14))
T("tuck-hollow", ["Tucked hollow hold"], hold("Tuck_Crunch", 1), MAT, cam=dict(az=-70, el=10), still=True)
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
T("seated-pull-in", ["Seated leg pull-in"], two("Seated_Flat_Bench_Leg_Pull-In"),
  lambda J, J0, *a: flat_bench("bench", J0["hips"].x - 0.25, J0["hips"].x + 0.4, 0.46), anchor=SEATZ(0.46), hands="grip")
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
T("pigeon-bench", ["Bench pigeon stretch"], hold("IT_Band_and_Glute_Stretch", 0), MAT, cam=dict(az=-55, el=15), still=True)
T("t-spine-chair", ["Thoracic extension over chair", "Chair T-spine extension + world's greatest stretch + child's pose lat stretch"],
  [K("Spinal_Stretch", 0), K("Spinal_Stretch", 0, curve=-28, fk_N=210, fk_H=220)], lambda J, J0, *a: chair("chair", J0), cam=dict(az=-80, el=10))
T("t-spine-roller", ["Foam roller T-spine + world's greatest stretch + child's pose lat stretch"],
  [K(SUP, 0, fk_N=-80, fk_H=-75), K(SUP, 0, curve=-16, fk_N=-100, fk_H=-110)], P_(MAT, lambda J, J0, *a: roller("roller", J0["chest"] + V((0.05, 0, -0.17)))), cam=dict(az=-70, el=10))
T("open-book", ["Thoracic open book"], [K("Side-Lying_Floor_Stretch", 0), K("Side-Lying_Floor_Stretch", 1)], MAT, hands="flat", cam=dict(az=-60, el=40))
T("snow-angel", ["Floor snow angels"], [K(SUP, 0, fk_armL=[92, 22, 92, 22], fk_armR=[92, 22, 92, 22]),
   K(SUP, 0, fk_armL=[92, 86, 92, 86], fk_armR=[92, 86, 92, 86]), K(SUP, 0, fk_armL=[-92, 30, -92, 30], fk_armR=[-92, 30, -92, 30])],
  lambda J, J0, *a: box("mat", (J0["pelvis"].x - 0.4, 0, 0.006), (2.1, 1.6, 0.012), "mat"),   # mat just wider than the arm sweep (~0.75 m out)
  hands="flat", palm="up", cam=dict(az=-90, el=42, margin=1.3), focus=["head", "hand_l", "hand_r", "toe_l", "toe_r", "knee_l", "knee_r", "pelvis"], pingpong=True, free=["hand_l", "hand_r"], anchor={"x": ("pelvis", None)})
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
SB = dict(T=270, H=270, legL=[153, 8, 29, 8], legR=[153, 8, 29, 8], armL=[81, 14, 81, 14], armR=[81, 14, 81, 14])
def sb(**kw):
    d_ = dict(SB); d_.update(kw); return P(**d_)
def OLD(n): return next(x for x in SPECS if x["name"] == n)
_FK = {
    "glute-bridge": OLD("glute-bridge")["keys"], "db-glute-bridge": OLD("glute-bridge")["keys"], "band-bridge-couch": OLD("glute-bridge")["keys"],
    "single-leg-bridge": OLD("single-leg-bridge")["keys"], "reverse-crunch": OLD("reverse-crunch")["keys"],
    "supine-chin-tuck": [sb(), sb(N=244, H=228)],
    "figure-4": [sb(legR=[128, 40, 98, -62]), sb(legL=[175, 8, 95, 8], legR=[150, 40, 112, -62], armL=[150, 6, 150, -6], armR=[150, 6, 150, -6])],
    "snow-angel": [sb(armL=[74, 22, 74, 22], armR=[74, 22, 74, 22], legL=[153, 8, 29, 8], legR=[153, 8, 29, 8]), sb(armL=[50, 74, 50, 74], armR=[50, 74, 50, 74], legL=[153, 8, 29, 8], legR=[153, 8, 29, 8]),   # arms sweep in the floor plane (l past 90 = toward the head); hook-lying legs, knees up not splayed
                   sb(armL=[106, 158, 106, 158], armR=[106, 158, 106, 158], legL=[153, 8, 29, 8], legR=[153, 8, 29, 8])],
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
_t["keys"] = [K("Band_Pull_Apart", 0, fk_armL=[90, 8, 90, 8], fk_armR=[90, 8, 90, 8]), K("Band_Pull_Apart", 1, fk_armL=[90, 84, 90, 84], fk_armR=[90, 84, 90, 84])]  # superseded by the "QA fix: band-pull-apart" block at the end
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
     hands="flat", plant=["hand_l", "hand_r"], cam=dict(az=0, el=38))

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

# ---------- QA fixes: G3 ----------
# ski erg: standing facing the machine, reach tall to the handles overhead, then hinge at the hips with a soft
# knee bend and drive the handles down past the thighs (double-pole pull); cyclic 2-key loop, smooth both ways.
SKI_UP = dict(T=172, armL=[152, 9, 152, 9], armR=[152, 9, 152, 9], legL=[4, 4, -6, 4], legR=[4, 4, -6, 4])
SKI_DN = dict(T=136, armL=[-16, 7, -16, 7], armR=[-16, 7, -16, 7], legL=[14, 5, -16, 5], legR=[14, 5, -16, 5])
T("ski-erg", ["Ski erg or elliptical intervals", "Ski erg or incline treadmill tempo"],
  [P(**SKI_UP), P(**SKI_DN)], lambda J, J0, *a: ski_erg("ski", J0, J), hands="grip", palm="forward", cam=dict(az=-55, el=10))

# frozen/near-static sweep: genuine timed holds (index.html dose has no rep count, just a sustained "Xs")
# rendered as a single full-quality PNG still instead of a 12-frame animation that reads as broken when it loops.
# where the two photo-derived keys differ (a deeper settle into the stretch), the fuller position becomes key 0
# (pec-opener keeps its original order: reversing it pins the flat-hand contact at the wider-reach pose and
# drives the other key's fingertips through the floor).
for _n in ("cable-lat-stretch", "childs-pose"):
    _s = _t(_n); _s["keys"] = list(reversed(_s["keys"])); _s["still"] = True
for _n in ("hk-hip-flexor", "couch-stretch", "couch-stretch-bench", "pec-opener"):
    _t(_n)["still"] = True

# ---------- QA fixes: G1 ----------
# prone row / towel pulldown: distinct end poses, both clearly different from prone-t/prone-w and from each other.
# Row: elbows drive straight back and stay close to the ribs (tight), hands finish beside the chest.
# Pulldown: elbows swing wide (W) as the towel comes down behind the head; the towel stays taut and visible.
# QA fix: prone-row: elbows bend early and stay close to the body (no straight-arm T sweep): reach -> elbows bent, pulling -> elbows at ribs, hands beside chest
PRONE_ROW_K1 = ARMS((0.62, 0.3, 0.1), (0.95, 0.12, 0.0))
PRONE_ROW_K2 = ARMS((0.0, 0.3, 0.12), (0.8, 0.3, -0.12))
PRONE_ROW_END = ARMS((-0.85, 0.22, 0.12), (0.72, 0.3, -0.2))
_set("prone-row", [prone(**REACH), prone(**PRONE_ROW_K1, S=95, H=94), prone(**PRONE_ROW_K2, S=96, H=95), prone(**PRONE_ROW_END, S=98, H=96)],
     pingpong=True, cam=dict(az=-155, el=32))
PRONE_PULLDOWN_END = ARMS((-0.3, 0.65, 0.0), (0.42, 0.0, 0.05))
_set("prone-towel-pulldown", [prone(**ARMS((0.96, 0.24, 0.12))), prone(**PRONE_PULLDOWN_END, S=98, H=96)], cam=dict(az=-155, el=32))
_t("prone-towel-pulldown")["props"] = P_(MAT, lambda J, J0, *a: rod("towel", J["hand_l"], J["hand_r"], 0.024, "towel"))

# t-spine-roller: supine, knees bent/feet flat (bridge-style, NOT a crunch tuck). Only the upper spine is propped up
# (resting on the roller) while the pelvis/legs stay at normal floor height - a uniform whole-body lift (like
# pec-opener's torso anchor) would also float the planted feet, so the prop-up lives in S2/S3/N/H instead, and the
# hips/legs are left on the ground. Hands are reach-targeted to the head (cradling the neck) so they land right
# behind it regardless of the arm's fk angle. The upper back extends further back over the roller for the 2nd key.
# round 2: the neutral key itself was already half-flexed (S/N/H well off the flat T=270 line) so the "extend"
# key only added a little more on top - barely any net motion, and the already-curled neutral read as a crunch.
# Neutral is now fully flat (S1=S2=S3=N=H=T, lying flat along the roller); the extend key dips the trunk well
# below that baseline, concentrated at the upper spine/neck/head (S1 barely moves), for a large, clearly visible
# arch of the head and shoulders back over the roller.
TSR_BASE = dict(T=270, legL=[153, 8, 29, 8], legR=[153, 8, 29, 8], armL=[100, 35, 205, 20], armR=[100, 35, 205, 20])
# NOTE: S/N/H values ABOVE the flat T=270 line arch the head/chest DOWN toward and over the roller (extension);
# values BELOW it lift the head/chest UP (a crunch) - the first attempt had the sign backwards.
# S1-S3 (upper spine) left untouched: any change there, or an N/H swing much past this, drags enough of the torso
# mesh low enough to trip the rig's unconditional per-key floor-safety lift (nothing in a template spec can opt
# out of it - confirmed via direct render tests at larger deltas: the whole body, hips included, floats off the
# mat like a bridge). This N/H-only, modest delta is the largest that stays clean: a real, visible dip of the
# head/neck back toward the mat with the hips and roller staying put.
_t("t-spine-roller")["keys"] = [P(**TSR_BASE), P(**TSR_BASE, N=290, H=310)]
_t("t-spine-roller")["anchor"] = {"x": ("ankle_r", None)}
_t("t-spine-roller")["props"] = lambda J, J0, *a: (mat("mat", J0), roller("roller", V((J0["chest"].x, 0, 0.14))))

# band-w: fuller external rotation range (forearms were barely leaving the forward/neutral position)
_w0, _w1 = V2((0.12, 0.12, -1.0)) + V2((1.0, 0.18, 0.05)), V2((0.12, 0.12, -1.0)) + V2((0.3, 0.92, 0.05))
_t("band-w")["keys"] = [K("External_Rotation_with_Band", 0, fk_armL=_w0, fk_armR=list(_w0)), K("External_Rotation_with_Band", 0, fk_armL=_w1, fk_armR=list(_w1))]

# wall-slides: true W (elbows bent ~90 deg at shoulder height) sliding into a Y overhead (was stuck overhead throughout)
WS_W, WS_Y = [90, 88, 155, 15], [180, 34, 180, 22]
_t("wall-slides")["keys"] = [K(STAND_SIDE, 0, fk_armL=WS_W, fk_armR=WS_W), K(STAND_SIDE, 0, fk_armL=WS_Y, fk_armR=WS_Y)]

# new: wall-slide-liftoff ("Wall slide with lift-off", "Wall Y-slide with lift-off"). Per index.html these two name
# only the forearms on the wall (no "back ... on wall" like the plain Wall slides), and the Thu body-option note
# ("Forearms on a wall, slide up into a Y, lift hands off 2 cm") is confirmed facing the wall - so this is a
# facing-the-wall slide (forearms on a wall ahead), not the back-to-wall version. Same W -> Y slide, then the
# forearms lift ~2 cm clear of the wall at the top before sliding back down.
WSL_W, WSL_Y, WSL_LIFT = [78, 76, 160, 10], [158, 30, 158, 18], [185, 28, 185, 16]
T("wall-slide-liftoff", ["Wall slide with lift-off", "Wall Y-slide with lift-off"],
  [P(T=180, H=180, **both(WSL_W)), P(T=180, H=180, **both(WSL_Y)), P(T=180, H=180, **both(WSL_LIFT))],   # round 4: symmetric hand-built stance (photo base pose had uneven shoulders)
  lambda J, J0, *a: wall("wall", J0["hand_l"].x + 0.1), hands="flat", handdir=180, palm="forward",
  stance="stand", pingpong=True, focus=["head", "hand_l", "hand_r", "ankle_l", "ankle_r", "hips"], cam=dict(az=165, el=11, margin=1.3))   # round 3: tighter 3/4; round 2: rear 3/4 (was a side view
  # that made the W/Y/lift-off hard to read, with the person small next to a big wall), tighter margin too

# push-up / push-up-plus: round 3 rework per explicit user spec - the body is ONE rigid straight line (heels to
# head) that pivots about the fixed toes; hands are ALSO fixed (planted) on the floor; the arms are the only thing
# that moves, bending via 2-bone IK to bridge the (rotating) shoulder to the (fixed) hand - so the FK arm hint only
# needs to be a reasonable bend-plane hint (same both keys works fine, IK does the rest), not a hand-position
# calculation. Both keys are plain FK on the HIGH_PLANK straight body shape (not blended with the noisy "Pushups"
# photo landmarks), legs/head shifted by the same T delta as the pivot so the plank line never changes shape -
# only its overall angle. T=96 (not HIGH_PLANK's own 109) so the straight-arm top key's hands reach the floor
# fully instead of hovering ~7cm short of the already-grounded toes (measured via a direct probe).
PU_DT = 6
PU_TOP_ARM = [-7, 8, -7, 8]
PU_LEG_OFF, PU_HEAD_OFF = HIGH_PLANK["legL"][0] - HIGH_PLANK["T"], HIGH_PLANK["H"] - HIGH_PLANK["T"]
def _pu_body(t):
    return dict(T=t, H=t + PU_HEAD_OFF, legL=[t + PU_LEG_OFF, 10, t + PU_LEG_OFF, 10, 15], legR=[t + PU_LEG_OFF, 10, t + PU_LEG_OFF, 10, 15])
PU_TOP, PU_BTM_BODY = _pu_body(105.8), _pu_body(105.8 - PU_DT)
PU_KEYS = [P(**PU_TOP, **both(PU_TOP_ARM)), P(**PU_BTM_BODY, **both(PU_TOP_ARM))]
PU_BTM_ARM = [-65, 10, 0, 6]   # bottom FK arm: elbows back, forearm vertical (straight FK arms would sink through the floor and settle() would lift the body)
PU_PIV = {"z": ("ankle_r", None), "x": ("ankle_r", None)}   # toes/ankles fixed: later keys pivot about the key-0 foot (no foot-IK pike)
_t("push-up")["keys"] = [P(**PU_TOP, **both(PU_TOP_ARM)), dict(P(**PU_BTM_BODY, **both(PU_BTM_ARM)), anchor=PU_PIV)]
def _pu_flat(J, J0, *a):   # after IK the hands inherit the forearm tilt: re-level palms flat, fingers forward, every frame
    for s in "lr":
        sg = SIDE[s]; hd = d(92, 12, sg); fd = bone_dir("lowerarm_" + s)
        set_palm(s, fd, hd, palm_target(None, s, sg, "flat", 105, fd, hd)); aim("hand_" + s, hd); vl.update()
_t("push-up")["props"] = _pu_flat
_t("push-up")["plant"] = ["foot_l", "foot_r", "hand_l", "hand_r"]

# push-up-db: same defect (feet floating ~6-9cm, hovering grip hand, flared elbows) and the same clean fix -
# reuse the push-up body/arm keys verbatim (push-up-db only swaps hands="grip" + dumbbell props, already set by
# its own T() call), with hands+feet explicitly planted.
# (keys: see the "QA fix: push-up-db" block at the end of this file)
_t("push-up-db")["plant"] = ["foot_l", "foot_r", "hand_l", "hand_r"]

# push-up-side-plank: same symptom (hover_hand_l/r, hover_foot_r in the baseline) on its transition from a high
# plank into a side plank - explicit planting of the support hand/feet through the transition.
_t("push-up-side-plank")["plant"] = ["foot_l", "foot_r", "hand_l"]
# its high-plank start key inherited HIGH_PLANK's own T=109 verbatim, same straight-arm-hand-short-of-the-floor
# gap push-up's fix addressed by retuning T to 96; reuse that same tuned key here (its 2nd/side-plank key is
# untouched).
_t("push-up-side-plank")["keys"][0] = P(**PU_TOP, **both(PU_TOP_ARM))

# new: push-up-plus ("Push-up plus") - a push-up rep, then at the top an extra scapular push: the upper spine
# rounds up slightly (S2/S3/H move off the straight T line) before settling back to the start. Camera raised to a
# higher 3/4 angle so the upper-back rounding reads clearly.
PU_PLUS_TOP = dict(PU_TOP, S1=PU_TOP["T"] - 4, S2=PU_TOP["T"] - 22, S3=PU_TOP["T"] - 32, H=PU_TOP["H"] - 26)
T("push-up-plus", ["Push-up plus"],
  [P(**PU_TOP, **both(PU_TOP_ARM)), P(**PU_BTM_BODY, **both(PU_TOP_ARM)), P(**PU_PLUS_TOP, **both(PU_TOP_ARM))],
  None, hands="flat", plant=["foot_l", "foot_r", "hand_l", "hand_r"], cam=dict(az=-55, el=24))

# chin-tuck family: more headroom above the head (was cropped tight against the top edge)
for _n in ("chin-tuck", "wall-chin-tuck", "cable-chin-tuck"):
    _t(_n)["cam"] = {**_t(_n)["cam"], "margin": 2.0}   # round 2: female's hair bun still clipped the top at 1.75

# pec-stretch / cable-pec-stretch: a clean single still (was a 12-frame loop stuck on 1-2 near-identical poses,
# reads as broken/frozen in a looping player). Hand-posed classic doorway stretch: upper arm to the side at
# shoulder height, forearm vertical against the door/cable column, forearm clearly on the frame.
# Round 2: pec-stretch's door was a CLOSED door (box filling the opening) - doesn't read as a doorway stretch.
# Build an open doorway instead (jambs + header, no leaf), step one foot through, and lean the chest gently
# forward through the opening; camera moved to a 3/4 FRONT-side angle so the open chest is visible (was mostly
# a back view).
# Round 3 (user feedback): the door jamb needs to be where the hand actually is - handdir=180 points the fingers
# straight up along the vertical forearm, palmR="out" faces the palm sideways (toward the jamb), and the jamb's
# near face is placed exactly at the hand's y (verified via a direct joint-position probe) so the whole palm +
# forearm lie flat against it instead of poking past the edge with a gap.
PEC_POSE = dict(T=172, armL=[4, 8, 4, 6], armR=[90, 88, 180, 2], legR=[22, 6, -6, 6], handdir=180, palmR="out")
# Round 4: staggered stance (R foot through the door, soft front knee) + gentle forward lean so the arm trails the chest.
PEC_ST = dict(PEC_POSE, T=164, H=176, N=173, legR=[44, 4, -2, 4], legL=[-16, 4, -28, 4])
_t("pec-stretch")["keys"] = [P(**PEC_ST), P(**PEC_ST)]
_t("pec-stretch")["still"] = True
_t("pec-stretch")["props"] = lambda J, J0, *a: (   # round 5: jamb + wall panel behind it + short header stub (edge of a doorway in a wall)
    box("doorway_r", (J0["hand_r"].x, J0["hand_r"].y - 0.075, 1.05), (0.16, 0.08, 2.1), "wood"),
    box("doorway_wall", (J0["hand_r"].x - 0.02, J0["hand_r"].y - 0.115 - 0.5, 1.08), (0.12, 1.0, 2.16), "wood"),
    box("doorway_top", (J0["hand_r"].x, J0["hand_r"].y + 0.05, 2.12), (0.16, 0.32, 0.08), "wood"))
_t("pec-stretch")["cam"] = dict(az=62, el=10)
PEC_CB = dict(T=176, H=176, N=174, armL=[4, 8, 4, 6], armR=[-90, 62, -80, 66], legR=[24, 5, -6, 5], legL=[-12, 4, -22, 4], twist=-30, handR="grip")
_t("cable-pec-stretch")["keys"] = [P(**PEC_CB), P(**PEC_CB)]
_t("cable-pec-stretch")["still"] = True
_t("cable-pec-stretch")["props"] = lambda J, J0, *a: (   # QA fix cable-pec-stretch: pulley at hand height on the working-arm side, cable straight to the handle
    cable("c", cable_column("col", J["hand_r"].x - 0.55, J["hand_r"].y - 0.55, J["hand_r"].z), J["hand_r"]), d_handle("h", J["hand_r"], (0, 0, 1)))
_t("cable-pec-stretch")["cam"] = dict(az=-64, el=12)

# ---------- QA fixes: G2 ----------
# step-down family: standing tall on a low box/step (stance leg L fixed in place), the free leg (R) lowers slowly
# until the heel lightly grazes the floor beside the step, then back up to standing tall. Hand-posed (no photo
# shows this), 3 keys + pingpong. Explicit x+z anchor on ankle_l: without an explicit "x" the retarget.py place()
# wrapper auto-tracks whichever foot is lower that frame, which flips to the free foot once it nears the floor.
SD_BOXH, SD_OFF = 0.20, 0.095          # low step top height; ankle-above-sole offset for this stance (measured)
SD_ANCHOR = {"z": ("ankle_l", SD_BOXH + SD_OFF), "x": ("ankle_l", None)}
SD_ARMS = dict(armL=[4, 16, 4, 6], armR=[4, 16, 4, 6])
SD_TOP = P(T=180, H=180, **SD_ARMS, legL=[4, 4, -4, 4], legR=[18, 4, -10, 4], anchor=SD_ANCHOR)
SD_MID = P(T=178, H=179, **SD_ARMS, legL=[20, 4, -24, 4], legR=[4, 4, 2, 4], anchor=SD_ANCHOR)
SD_BOTTOM = P(T=176, H=178, **SD_ARMS, legL=[38, 5, -46, 5], legR=[3, 4, -9, 4], anchor=SD_ANCHOR)
T("db-step-down", ["Dumbbell step-down (low step)"], [SD_TOP, SD_MID, SD_BOTTOM],
  P_(lambda J, J0, *a: box_step_at("box", J0["ankle_l"], SD_BOXH, d_=0.42, w=0.42), DB()),
  hands="grip", pingpong=True, cam=dict(az=-62, el=10))
T("stair-step-down", ["Slow step-down from stairs"], [SD_TOP, SD_MID, SD_BOTTOM],
  lambda J, J0, *a: stairs_at("st", J0["ankle_l"], rise=SD_BOXH / 2, run=0.28, steps=2, w=0.42),
  hands="relaxed", pingpong=True, cam=dict(az=-62, el=10))

# lateral step-up, round 2: the box used to be centred close enough to the body's own centreline that a normal
# standing stance already overlapped it (straddle); it's now offset from the START key's own ankle_l Y (read at
# render time, not hardcoded) by a gap + half the box width so it sits entirely to one side. The near leg (L)
# only gets its big hip-abduction angle in the TOP key (foot actually on the box) - previously that abduction sat
# on the START key instead, throwing the stepping leg out sideways before any motion even began. The trailing/free
# leg (R) keeps a small, steady lateral angle (5-8 deg) in both keys so it swings close under the body through
# every in-between frame instead of abducting out to the side; H=180 matches T (neutral head, this exercise never
# moves the head).
LSU_BOXH, LSU_OFF = 0.30, 0.095
LSU_GAP, LSU_HALF, LSU_SH = 0.10, 0.225, 0.25   # near foot - box edge gap; half of the 0.45 m box footprint; sideways body shift onto the box
LSU_ANCHOR = {"z": ("ankle_l", LSU_BOXH + LSU_OFF), "x": ("ankle_l", None), "y": ("pelvis", None, LSU_SH)}
LSU_ARMS = dict(armL=[2, 10, 2, 8], armR=[2, 10, 2, 8])
LSU_START = P(T=180, H=180, **LSU_ARMS, legL=[2, 6, -2, 4], legR=[2, 6, -2, 4])
LSU_TOP = P(T=180, H=180, **LSU_ARMS, legL=[2, 6, -2, 4], legR=[8, 2, -22, 3], anchor=LSU_ANCHOR)
LSU_MID = P(T=180, H=180, **LSU_ARMS, legL=[60, 6, -75, 4], legR=[2, 6, -2, 4], anchor={"y": ("pelvis", None, LSU_SH * 0.2)})   # near foot lifted clear above the box edge, body still on the floor
T("lateral-step-up", ["Lateral step-up (low box)"], [LSU_START, LSU_MID, LSU_TOP],
  lambda J, J0, *a: box_step_at("box", V((J0["ankle_l"].x, J0["ankle_l"].y + LSU_GAP + LSU_HALF, 0)), LSU_BOXH, d_=0.45, w=0.45),
  pingpong=True, steps=4, hands="relaxed", cam=dict(az=-25, el=10))

# single-leg leg press: same machine/landmarks, the left leg relaxed off the platform (foot resting on the
# machine's frame) while the right leg (driven by the photo landmarks, unchanged) presses. The footplate is drawn
# from the pressing (right) ankle/toe only - mirrored onto "ankle_l"/"toe_l" - so it never tracks the relaxed leg.
LP_RELAX = [150, 14, 60, 8]
def _lp_single_props(J, J0, *a):
    leg_press("m", {**J0, "ankle_l": J0["ankle_r"], "toe_l": J0["toe_r"]}, {**J, "ankle_l": J["ankle_r"], "toe_l": J["toe_r"]})
    pad("lp_foot_rest", J["ankle_l"] + V((0.02, 0, -0.06)), (0.16, 0.14, 0.04), c="steel")
T("leg-press-single", ["Single-leg leg press"],
  [K("Leg_Press", 0, fk_legL=LP_RELAX), K("Leg_Press", 1, fk_legL=LP_RELAX)], _lp_single_props, anchor=SEATZ(0.42))

# glute-drive: build a real hip-thrust/glute-drive machine (low base, back pad at shoulder-blade height that
# rides with the body so it never gaps or clips, padded lever/belt across the hips) in place of the old flat
# pad; keeps the hip-thrust motion (same keys/anchor -> hips already travel low-to-full-extension).
_t("glute-drive")["props"] = lambda J, J0, *a: glute_drive_machine("gd", J0, J)
# the inherited photo landmarks tip the head back at full extension (neck hyperextension, chin away from the body).
# Override the neck/head on both keys to neutral with the chin slightly tucked (gaze forward/down the body), same
# fix at the bottom - these poses are supine/reclined the whole rep so the head direction is the same -90 (level,
# continuing the body line) at both ends, just nudged off -90 toward the chest for the slight tuck.
for _k, (_n, _h) in zip(_t("glute-drive")["keys"], ((226, 202), (268, 242))): _k["N"], _k["H"] = _n, _h   # keys are T/H-style (no landmarks): N/H, not fk_N/fk_H
# hands grip short handles on the lever arms at hip-pad level, riding with the hips (see glute_drive_machine)
for _k in _t("glute-drive")["keys"]: _k["armL"] = _k["armR"] = [75, 14, 115, 14]   # elbows bent and relaxed; IK only trims to the grips
_t("glute-drive")["reach"] = {"hand_l": ("hips", (0.0, 0.29, 0.16), "world"), "hand_r": ("hips", (0.0, -0.29, 0.16), "world")}

# smith incline press, low variant: the reused landmark pose sat upright in front of the pad (photo torso angle
# didn't match the shallow bench), leaving a visible gap. Hand-posed instead so the trunk pitch is solved exactly
# for a 22 deg (from horizontal) backrest: T = 180 + (90 - 22) keeps the trunk's own axis flush against the pad's
# own incline direction at any point along the rep, so the back lies on it every frame, clearly shallower than the
# 45 deg high-incline version. Seated legs (thigh horizontal, shin down) reach the floor under ground anchoring.
SIL_T = 248
SIL_SEAT = dict(legL=[90, 6, 0, 6], legR=[90, 6, 0, 6])
SIL_TOP = P(T=SIL_T, H=SIL_T - 60, **SIL_SEAT, armL=[145, 20, 150, 12], armR=[145, 20, 150, 12])
SIL_BOTTOM = P(T=SIL_T, H=SIL_T - 60, **SIL_SEAT, armL=[70, 20, 85, 10], armR=[70, 20, 85, 10])
T("smith-incline-low", ["Low-incline Smith press"], [SIL_TOP, SIL_BOTTOM],
  P_(lambda J, J0, *a: incline_bench("bench", J0, 22, J0["hips"].x + 0.05, region_low("seat"), back_len=1.2), lambda J, J0, *a: smith("sm", J0, J)),
  hands="grip", cam=dict(az=-35, margin=1.12))

# seated cable row, wide grip (rounds 2-3): elbows travel back (upper-arm pitch ~300) and below shoulder height, forearms
# down-forward to the lower chest.
# round 3: the landmark-based keys kept the photo's torso/head yaw (head turned ~60 deg, bar diagonal). Now fully
# hand-posed (rig apply_pose starts from a square, +X-facing rest): torso square to the column, N=H=180 level head,
# arms mirrored L/R. Start = reach (slight forward lean), end = elbows back/flared 55 deg, bar at the lower chest.
SCRW_LEGS = dict(legL=[78, 6, 62, 6], legR=[78, 6, 62, 6])
SCRW_START = P(T=168, S=172, H=180, N=180, **SCRW_LEGS, armL=[84, 22, 84, 20], armR=[84, 22, 84, 20])
SCRW_PULL = P(T=182, S=184, H=180, N=180, **SCRW_LEGS, armL=[300, 55, 80, 15], armR=[300, 55, 80, 15])
T("seated-cable-row-wide", ["Seated cable row (wide grip)"], [SCRW_START, SCRW_PULL],
  lambda J, J0, *a: low_row_machine("m", J0, J, "bar", wide=True), hands="grip", anchor=SEATZ(0.42), cam=dict(az=-65, el=14))

# suitcase hold: still, standing tall, one dumbbell at the side, shoulders level, no lean (the old "suitcase"
# template is a walking carry, wrong for a static hold).
SH_POSE = P(T=180, H=180, armL=[2, 8, 2, 6], armR=[8, 10, 14, 6], legL=[2, 4, -2, 4], legR=[2, 4, -2, 4])
T("suitcase-hold", ["Suitcase hold"], [SH_POSE, SH_POSE], DB("r"), handR="grip", still=True, cam=dict(az=-20, el=10))

# side hold on a 45 deg back-extension bench, round 2: the Side_Bridge landmark pose is a horizontal floor plank -
# laying it on the bench never matched the bench's own 45 deg slope (rejected). Hand-posed instead as a straight
# "plank" line rotated bodily into the bench's side-lying orientation: trunk T=135 (d(135) = 45 deg between
# straight-up and horizontal-forward, i.e. the bench's own incline direction), legs continue the SAME line below
# the hips (pitch = T-180 = -45, lateral=0) so hips/knees/ankles never bend away from the slope. roll=-90 (not
# +90: matches the clamshell/SIDE_BASE convention - lateral=0 on the thighs at that roll sign is what keeps the
# hip joint's swing/twist inside the calibrated hinge limits, avoiding the thigh_twist flag the old FK attempts hit
# when the thigh had any lateral component). H=T (head continues the body line, neutral). Arms: top hand reaches
# the near hip (reach IK, exact placement), bottom arm folds loosely across the front of the chest. Reuses
# back_ext_bench's own pad/footplate (built straight off J0 hips/ankles, no manual offset needed now that hips and
# ankles actually sit on the bench's 45 deg line).
SHB_POSE = P(T=135, roll=-90, H=135, armL=[0, 0, 100, -75], armR=[0, 0, 100, -75], legL=[-45, 0, -45, 0, 90, -90], legR=[-45, 0, -45, 0, 90, 90],
             reach={"hand_l": ("shoulder_r", (0.09, 0.07, -0.04)), "hand_r": ("shoulder_l", (0.12, -0.07, -0.04))}, anchor={"z": ("ankle_l", 0.5), "x": ("ankle_l", None)})
T("side-hold-bench", ["Side hold on 45° back-extension bench"], [SHB_POSE, SHB_POSE],
  lambda J, J0, *a: side_hold_bench("m", J0, J), still=True, cam=dict(az=-80, el=12))

# cable-bird-dog / cable-dead-bug: the cable column was placed/sized for a standing person (tall tower, far
# offset) so for these floor poses the real column and stack rendered beyond the auto-framed window and got cut
# off at the frame edge. Move the column close enough to read as attached, and draw it only as tall as these
# low, short-pulley setups actually need, so the whole column + stack fits in frame with the person still large.
_t("cable-bird-dog")["props"] = P_(MAT, lambda J, J0, *a: (
    cable("c", cable_column("col", J0["hips"].x - 1.15, J0["ankle_l"].y, 0.15, h=1.1), J["ankle_l"] + V((0, 0, 0.04))),
    ankle_weight("strap", J, "l")))
_t("cable-bird-dog")["cam"] = dict(az=-62, el=12, margin=1.25)
_t("cable-dead-bug")["props"] = P_(MAT, lambda J, J0, *a: cable("c", cable_column("col", J0["head"].x - 0.6, 0, 0.6, h=1.1), J["hands"]))
_t("cable-dead-bug")["cam"] = dict(az=-62, el=14, margin=1.25)

# smith-incline-low/high, round 2: both pressed the bar down to the waist/belly with the head lifted off the pad -
# wrong movement for a bench press (the bar must travel a dead-straight VERTICAL line down to the UPPER chest,
# forearms roughly vertical/wrists stacked under it throughout) and the real fault, not the bench-flush fit which
# was already correct. Re-solved both arms numerically (tools/probe.py) against each body's actual chest/shoulder
# height: forearm pitch 180 (= pure vertical, lat 0) at the bottom key keeps the wrists stacked under the bar
# whatever the backrest angle; the upper arm pitch/lat pulls the elbow back and down so the hand lands within 1-2
# cm (x) of the TOP key's hand x - that's where smith()'s bar_at="hands" fixes the rail column - and within a few
# cm (z) of chest height (upper chest, just below the collarbone), never the belly. Top key: arms straight,
# continuing the same near-vertical line overhead. Legs/seat/bench unchanged (already flush on the pad, high and
# low). H = T - 60 unchanged too: that already keeps the head a neutral continuation of the reclined trunk, pad
# lying flat under it - this round's bug was the ARMS carrying the bar too low and too far off the rail column,
# not the head; re-verified it stays down on the pad at this H every frame.
SI_BOTTOM = lambda T_: dict(armL=[0, 30, 180, 0], armR=[0, 30, 180, 0])
SI_TOP = lambda T_: dict(armL=[178, 15, 178, 15], armR=[178, 15, 178, 15])
SIL_H = SIL_T - 2                                # head down on the (lengthened) pad, neutral neck
_t("smith-incline-low")["keys"] = [P(T=SIL_T, H=SIL_H, **SIL_SEAT, **SI_TOP(SIL_T)), P(T=SIL_T, H=SIL_H, **SIL_SEAT, **SI_BOTTOM(SIL_T))]

SIH_T = 225                                     # T = 180 + (90 - 45): same flush-pad formula as the low version
SIH_SEAT = SIL_SEAT
# round 3: rail column + arms re-solved (probe) so the bar lands on the UPPER chest at the bottom: rails ~12cm toward the feet
# from the shoulder line (x ~ -0.31), arms lean that way a few deg at lockout, forearms vertical at the bottom, elbows ~45deg
# off the torso. H = T-10 keeps the head on the pad. palm=feet (pronated press grip) removes the forearm_twist flags.
SIH_TOP = P(T=SIH_T, H=SIH_T - 10, **SIH_SEAT, armL=[170, 17, 170, 17], armR=[170, 17, 170, 17])
SIH_BOTTOM = P(T=SIH_T, H=SIH_T - 10, **SIH_SEAT, armL=[20, 36, 180, 0], armR=[20, 36, 180, 0])
_t("smith-incline-high")["keys"] = [SIH_TOP, SIH_BOTTOM]

# ---------- QA fixes: G6 ----------
# couch-stretch (wall): the back calf's hand-posed pitch (172/168) leaned the shin FORWARD (away from the wall,
# toward the groin) instead of up the wall, so the shin never touched it while the toe (pitch 200, correctly
# aimed back toward the wall) stuck out past the knee - from this camera angle the wall plane sat right in the
# gap and visually swallowed the lower leg. Flip the calf/foot pitch the other way (188, same magnitude lean but
# toward the wall) so shin+foot form one flush near-vertical line that actually meets the wall surface, and bring
# the wall itself in (offset 0.17 -> 0.12, i.e. its near face sits one knee-radius off the knee x instead of
# floating 11cm clear of it) so the knee also reads as planted at the wall base, heel close to (not through) the
_t("couch-stretch")["cam"] = dict(az=-80, margin=1.3)   # headroom (framing only)
# glute. Thigh pitch -10/-18 -> single -20 (slightly more backward lean) keeps the knee near that tightened wall.
_t("couch-stretch")["props"] = P_(MAT, lambda J, J0, *a: wall("wall", J0["knee_r"].x - 0.17, z=0.55, h=1.1, w=1.6, y=-0.75))
for _P in _t("couch-stretch")["keys"]: _P["fk_legR"] = [-36, 6, 188, 4, 188]

# couch-stretch-bench: same forward-leaning-calf defect, worse here because the bench top sits 0.425m above the
# floor-planted back knee - at that pitch (-152) the shin spent its reach going sideways along the pad instead of
# climbing to it, landing the ankle ~2cm under the top (the "into_prop bench 0.04" baseline flag). Steepen the
# calf (-152 -> -162, same foot pitch) so it actually reaches the top with a hair of clearance for the shin's own
# radius. That shortens the horizontal reach, so the bench (previously centered reactively off the now-wrong
# ankle x) is repositioned off the stable, floor-planted knee instead: near edge = knee.x - 0.12 (the knee itself
# sits just in front of/at the bench's end, with its 0.09 m thick pad tucked behind the knee instead of overlapping
# the thigh on its way up to the hip - a flush near edge measured a 0.044 m thigh/bench clip there), same ~0.5 m
# pad length.
_t("couch-stretch-bench")["props"] = P_(MAT, lambda J, J0, *a: flat_bench("bench", J0["knee_r"].x - 0.67, J0["knee_r"].x - 0.16, 0.45, y=J0["knee_r"].y, w=0.32))
for _P in _t("couch-stretch-bench")["keys"]: _P["fk_legR"] = [-8, 6, -162, 4, -100]
_t("couch-stretch-bench")["cam"] = dict(az=-80, margin=1.3)   # headroom (framing only)

# ---------- QA fixes: G5b ----------
# door towel row: a real flat towel (7 cm band) thrown over the TOP of the closed door (trapped by the leaf), a strand from each
# contact on the front edge straight down to the hand(s), a short tail hanging behind. Ribbons run to the hand centre and end just past it (wrapped in the fist).
def towel_band(n, a, b, w=0.07, t=0.012, wd=(0, 1, 0)):
    a, b = V(a), V(b); z = b - a; L = z.length; z = z.normalized()
    o = box(n, (a + b) / 2, (w, t, L), "towel"); x = (V(wd) - z * V(wd).dot(z)).normalized()
    o.rotation_quaternion = Matrix((x, z.cross(x), z)).transposed().to_quaternion(); return o
def DOOR_TOWEL(hands, x0):
    def f(J, J0, *a):
        dx = J0[x0].x + 0.62; fx, zt = dx - 0.06, 2.171; door("door", dx)
        box("tw_crest", (dx, 0, zt), (0.125, 0.21, 0.012), "towel")
        box("tw_tail", (dx + 0.066, 0, zt - 0.17), (0.012, 0.21, 0.34), "towel")
        for i, h in enumerate(hands):
            p = J[h]; yy = 0.07 if len(hands) == 1 else (0.07 if p.y >= J[hands[1 - i]].y else -0.07)
            for k, y in enumerate((0.07, -0.07) if len(hands) == 1 else (yy,)):
                c = V((fx, y, zt)); u = (c - p).normalized(); towel_band(f"tw{i}{k}", p - u * 0.05, c, wd=(0, 1, 0))
    return f

# ---------- QA fixes: G4b ----------
# mcgill: lying FLAT on the mat (head, shoulder blades, buttocks touching), curl lifts head + shoulders only. Spine/neck angles are tuned per sex
# (the female mesh has a different back profile): _SexKeys resolves the "_f" overrides when the key list is read, i.e. after set_character().
class _SexKeys(list):
    def __iter__(self):
        f = body.name == CHARS["f"][1]
        return iter([{**{a: b for a, b in k.items() if a != "_f"}, **(k["_f"] if f else {})} for k in list.__iter__(self)])
_MG = dict(legL=[90, 6, 90, 6], legR=[150, 8, 26, 8], armL=[72, 25, 95, -75], armR=[72, 25, 95, -75], T=270, anchor={"z": ("pelvis", 0.1195)})   # straight leg on the mat, other foot flat beside that knee
_MGF = dict(armL=[72, 38, 90, -75], armR=[72, 38, 90, -75], anchor={"z": ("pelvis", 0.1298)}, S1=276, S2=284, S3=266, N=274, H=274)
_t("mcgill")["keys"] = _SexKeys([P(**_MG, S1=262, S2=266, S3=282, N=278, H=278, _f=_MGF),
                       P(**_MG, S1=262, S2=258, S3=274, N=270, H=266, _f=dict(_MGF, S2=276, S3=258, N=266, H=262))])


# ---------- QA fix: push-up-db ----------
# own constants (independent of the shared push-up tuning): rigid straight body pivoting about planted toes, planted grip hands, only arms move
PUDB_T, PUDB_DT, PUDB_DTF, PUDB_ARM, PUDB_ARM1 = 110, 10, 8, [0, 6, 0, 4], [-25, 6, 5, 4]   # bottom key: elbows tucked back; DT = how far the rigid plank tips about the toes (chest just clear of the floor, no lift = no hip pike); f: shorter torso clears less
def _pudb(t): return dict(T=t, H=t + 20, N=t + 14, legL=[t - 180, 10, t - 180, 10, 15], legR=[t - 180, 10, t - 180, 10, 15])   # head/neck a little above the spine line: gaze just ahead of the hands
PUDB_PIV = {"z": ("toe_r", None), "x": ("toe_r", None)}   # later keys pivot about the key-0 toes
next(x for x in CAT if x["name"] == "push-up-db")["keys"] = _SexKeys([dict(P(**_pudb(PUDB_T), **both(PUDB_ARM)), _f={}), dict(P(**_pudb(PUDB_T - PUDB_DT), **both(PUDB_ARM1)), anchor=PUDB_PIV, _f=_pudb(PUDB_T - PUDB_DTF))])
next(x for x in CAT if x["name"] == "push-up-db")["props"] = lambda J, J0, *a: [dumbbell("db_" + s, J0["hand_" + s], V((J0["gax_" + s].x, J0["gax_" + s].y, 0)).normalized()) for s in "lr"]   # dumbbells stay level, handle along the body axis, where key 0 gripped them

# ---------- QA fix: door-towel-row ----------
# rigid straight body pivoting about planted feet at the door base (like push-up-db): starts leaning back (A0) with FULLY STRAIGHT arms up the
# towel strands, rows to a still-leaning A1 (elbows past the ribs, chest short of the door). Door/anchor x is derived from the planted ankle.
import math as _m
DTR_A0, DTR_A1, DTR_DX, DTR_LF = 50, 28, 0.28, 1.26   # DTR_LF: female shoulder height along the body line (male 1.38)
def _dtr_key(a, bent, L=1.38):
    sx, sz = -L * _m.sin(_m.radians(a)), 0.07 + L * _m.cos(_m.radians(a)); p = _m.degrees(_m.atan2(DTR_DX - 0.06 - sx, -(2.171 - sz)))
    arm = [a - 30, 14, 122, 8] if bent else [p, 6, p, 6]
    return P(T=180 + a, N=168 + a, H=168 + a, legL=[a, 4, a, 4, 15], legR=[a, 4, a, 4, 15], **both(arm))
def _dtr_props(J, J0, *a):
    dx = J0["ankle_r"].x + DTR_DX; fx, zt = dx - 0.06, 2.171; door("door", dx)
    box("tw_crest", (dx, 0, zt), (0.125, 0.21, 0.012), "towel"); box("tw_tail", (dx + 0.066, 0, zt - 0.17), (0.012, 0.21, 0.34), "towel")
    for i, h in enumerate(("hand_l", "hand_r")):
        p = J[h]; y = 0.07 if p.y >= J[("hand_l", "hand_r")[1 - i]].y else -0.07
        c = V((fx, y, zt)); u = (c - p).normalized(); towel_band(f"tw{i}", p - u * 0.05, c, wd=(0, 1, 0))
_d = next(x for x in CAT if x["name"] == "door-towel-row")
_d["keys"] = _SexKeys([{**_dtr_key(A, b), "_f": _dtr_key(A, b, DTR_LF)} for A, b in ((DTR_A0, False), (DTR_A1, True))]); _d["props"] = _dtr_props
_d["plant"] = ["foot_l", "foot_r"]; _d["cam"] = {"az": -108, "margin": 1.0}; _d["prop_headroom"] = 0.5

# ---------- QA fix: cable-chin-tuck ----------
# frame feet too (legs/feet were cut by the bottom edge) with clear headroom for the female bun
for _c in CAT:
    if _c["name"] == "cable-chin-tuck": _c["focus"] = ["hips", "head", "shoulder_l", "shoulder_r", "ankle_r"]; _c["cam"] = dict(az=-88, el=10, margin=1.7)
# Resisted chin tuck: head band (forehead + around the sides to the occiput), cable clipped to the band at the front, pulling
# the head forward so the tuck works against it. Hands rest on the thighs.
def _cct_props(J, J0, *a):
    chair("chair", J0); n = 20
    gi = [g.index for g in body.vertex_groups if g.name == "Head"][0]       # fit the band to THIS sex's skull (deformed mesh)
    co = body_coords(); hv = [i for i, v in enumerate(body.data.vertices) if v.groups and max(v.groups, key=lambda g: g.weight).group == gi]
    hc = co[hv]; zc = float(hc[:, 2].max()) - 0.075; sl = hc[abs(hc[:, 2] - zc) < 0.02]
    cx, cy = (sl[:, 0].max() + sl[:, 0].min()) / 2, (sl[:, 1].max() + sl[:, 1].min()) / 2
    ra, rb = (sl[:, 0].max() - sl[:, 0].min()) / 2 + 0.004, (sl[:, 1].max() - sl[:, 1].min()) / 2 + 0.006
    for r_, dz in enumerate((-0.012, 0.0, 0.012)):                           # ~3.5 cm tall, ~1 cm thick band hugging the head
        pts = [V((cx + ra * _m.cos(2 * _m.pi * k / n), cy + rb * _m.sin(2 * _m.pi * k / n), zc + dz)) for k in range(n)]
        for k in range(n): rod(f"hband{r_}_{k}", pts[k], pts[(k + 1) % n], 0.007, "rubber")
    pul = cable_column("col", J0["head"].x + 0.9, 0, zc)
    cable("strap", V((cx + ra, cy, zc)), pul)
for _c in CAT:
    if _c["name"] == "cable-chin-tuck":
        _c["props"] = _cct_props
        for _k in _c["keys"]:                                                # torso square to the column: shoulder line parallel to the hip line
            _L = _k["lm"]; _sc = (_L["sh_l"] + _L["sh_r"]) / 2; _w = (_L["sh_l"] - _L["sh_r"]).length / 2
            _hd = _L["hip_l"] - _L["hip_r"]; _hd.z = 0; _hd.normalize()
            _L["sh_l"] = _sc + _hd * _w; _L["sh_r"] = _sc - _hd * _w
        _c["reach"] = {"hand_l": ("knee_l", (-0.14, 0.0, 0.105), "world"), "hand_r": ("knee_r", (-0.14, 0.0, 0.135), "world")}

# ---------- QA fix: t-spine-roller ----------
# roller across the shoulder blades, hips + feet on the floor, hands cradling the head with elbows up/out; the head and upper back
# extend BACK over the roller and return to neutral (no crunch: head never comes forward of the neutral line)
_tsr = next(x for x in CAT if x["name"] == "t-spine-roller")
TSR2 = dict(T=270, S1=262, S2=252, S3=250, legL=[153, 8, 29, 8], legR=[153, 8, 29, 8], armL=[190, 82, 250, 30], armR=[190, 82, 250, 30])
_tsr["keys"] = [P(**TSR2, N=256, H=258), P(**{**TSR2, "S1": 263, "S2": 257, "S3": 258}, N=264, H=267), P(**{**TSR2, "S1": 264, "S2": 263, "S3": 266}, N=274, H=278)]
_tsr["pingpong"] = True; _tsr["steps"] = 3   # 3 keys out and back = 12 frames; the mid key keeps the lifted-body guard from detaching the hands
_tsr["anchor"] = {"x": ("ankle_r", None)}
_tsr["reach"] = {"hand_l": ("head", (-0.04, 0.10, 0.03)), "hand_r": ("head", (-0.04, -0.10, 0.03))}
_tsr["props"] = lambda J, J0, *a: (mat("mat", J0), roller("roller", V((J0["chest"].x + 0.14, 0, 0.075))))
_tsr["cam"] = dict(az=-85, el=8)

# ---------- QA fix: lying-ham-towel ----------
# soft flat towel (towel_band, 7 cm) slung under the ball of the RAISED foot, one end in each fist; arms reach up toward the foot. Raised foot = the higher ankle.
# parametric supine key (same flat-on-the-mat torso as mcgill, per-sex via _SexKeys): floor leg L straight on the mat, raised leg R, arms up to the towel
LHT_AZ = (0.1195, 0.1298)  # pelvis height above the mat (m, f), same as mcgill
LHT_FL, LHT_FLF = (150, 26), (150, 26)  # floor leg thigh/calf pitch: hook-lying, knee bent, foot flat on the mat (a straight leg can't lie flat with the back on this mesh)
def _lht_key(thigh, calf, arm, fore, f=False):
    return dict(P(T=270, legL=[LHT_FL[0], 6, LHT_FL[1], 6], legR=[thigh, 8, calf, 8], armL=[arm, 12, fore, 8], armR=[arm, 12, fore, 8], anchor={"z": ("pelvis", LHT_AZ[0])}, **dict(S1=262, S2=266, S3=282, N=278, H=278)), _f=dict(_MGF, anchor={"z": ("pelvis", LHT_AZ[1])}, legL=[LHT_FLF[0], 6, LHT_FLF[1], 6], armL=[arm, 12, fore, 8], armR=[arm, 12, fore, 8]))
LHT_KEYS = [_lht_key(190, 118, 150, 130), _lht_key(186, 184, 165, 158)]
def _lht_props(J, J0, *a):
    mat("mat", J0); s = "l" if J["ankle_l"].z > J["ankle_r"].z else "r"; f = (J["toe_" + s] - J["ankle_" + s]).normalized()
    n = f.cross(V((0, 1, 0))).normalized(); n = n if n.dot(J["knee_" + s] - J["ankle_" + s]) < 0 else -n   # sole normal (faces away from the shin)
    c = J["toe_" + s] + n * 0.02 - f * 0.05; ends = (c + V((0, 0.065, 0)), c - V((0, 0.065, 0)))
    towel_band("tw_sole", ends[0], ends[1], wd=f)
    for h in ("hand_l", "hand_r"):
        p = J[h]; e = min(ends, key=lambda q: (q - p).length); e = e + (c - e).normalized() * 0.035; u = (e - p).normalized(); towel_band("tw_" + h, p - u * 0.05, e, wd=(0, 1, 0))
_l = next(x for x in CAT if x["name"] == "lying-ham-towel")
_l["keys"] = _SexKeys(LHT_KEYS); _l["props"] = _lht_props; _l["hands"] = "grip"; _l["palm"] = "feet"; _l.pop("anchor", None)

# ---------- QA fix: door-towel-row-1arm ----------
# same rigid body pivoting about planted feet as door-towel-row; right hand alone holds ONE towel strand (over the door top), left arm hangs relaxed
def _d1_key(a, bent, L=1.38):   # free arm rests along the side of the leaning body (same pitch as the body line), not hanging plumb
    k = _dtr_key(a, bent, L); k["armL"] = [a, 10, a, 10]; return k
def _d1_props(J, J0, *a):
    dx = J0["ankle_r"].x + DTR_DX; fx, zt = dx - 0.06, 2.171; door("door", dx)
    box("tw_crest", (dx, 0, zt), (0.125, 0.21, 0.012), "towel"); box("tw_tail", (dx + 0.066, 0, zt - 0.17), (0.012, 0.21, 0.34), "towel")
    p = J["hand_r"]; c = V((fx, 0.07 if p.y >= 0 else -0.07, zt)); u = (c - p).normalized(); towel_band("tw_r", p - u * 0.05, c, wd=(0, 1, 0))
_d = next(x for x in CAT if x["name"] == "door-towel-row-1arm")
_d["keys"] = _SexKeys([{**_d1_key(A, b), "_f": _d1_key(A, b, DTR_LF)} for A, b in ((DTR_A0, False), (DTR_A1, True))]); _d["props"] = _d1_props
_d["plant"] = ["foot_l", "foot_r"]; _d["cam"] = {"az": -108, "margin": 1.0}; _d["prop_headroom"] = 0.5; _d.pop("handR", None); _d["handR"] = "grip"

# ---------- QA fix: mcgill ----------
# own copies of the shared _MG/_MGF torso (other supine templates use those): arms rest beside the body with elbows on the mat, hands tucked under the low back
_MCG = dict(legL=[90, 6, 91, 6], legR=[150, 8, 26, 8], armL=[84, 25, 80, -45], armR=[84, 25, 80, -45], T=270, anchor={"z": ("pelvis", 0.1065)})
_MCGF = dict(armL=[84, 38, 80, -45], armR=[84, 38, 80, -45], anchor={"z": ("pelvis", 0.1168)}, S1=276, S2=284, S3=266, N=274, H=274)
_t("mcgill")["keys"] = _SexKeys([P(**_MCG, S1=262, S2=266, S3=282, N=278, H=278, _f=_MCGF),
                                 P(**_MCG, S1=262, S2=254, S3=268, N=262, H=256, _f=dict(_MCGF, S2=272, S3=252, N=258, H=252))])
_t("mcgill")["free"] = ["foot_l"]

# ---------- QA fix: pigeon-bench ----------
# still shows the folded pose: front shin lies flat across a wide bench top, torso folded over it, rear leg back to the floor
PIGB_L = LEG("l", (0.82, 0.5, -0.2), (-0.15, -0.98, 0.0), (-0.15, -0.98, 0.0))
PIGB_R = LEG("r", (-0.86, -0.1, -0.5), (-0.86, -0.1, -0.5))
_t("pigeon-bench")["keys"] = [P(T=122, S=114, H=116, legL=PIGB_L, legR=PIGB_R, armL=[25, 4, 20, 6], armR=[50, 20, 60, 15])]
def _pigb_props(J, J0, *a):
    k, an = J0["knee_l"], J0["ankle_l"]
    flat_bench("bench", k.x - 0.45, k.x + 0.25, min(k.z, an.z) - 0.05, y=(k.y + an.y) / 2 - 0.05, w=0.7)
_t("pigeon-bench")["props"] = _pigb_props
_t("pigeon-bench")["anchor"] = {"z": ("knee_l", 0.42)}
_t("pigeon-bench")["cam"] = dict(az=-38, el=16)

# ---------- QA fix: treadmill ----------
# figure is gait-posed on flat ground, then lifted onto the belt; each foot is IK'd onto the inclined belt plane, weighted by its floor clearance (swing foot stays FK)
def treadmill_track(ctx):
    L = TM_B0; arm.location.z += L; vl.update(); J = joints(); hx = J["hips"].x
    for l in ("foot_l", "foot_r"):
        s_ = l[-1]; st = limb_state(l, J, V((1, 0, 0)))
        clr = max(0.0, limb_low(l) - L); w = 1 - min(1.0, clr / 0.12); w = w * w * (3 - 2 * w)
        dz = TM_S * (st["tip"].x - hx) * w
        toe = st["toe"] + V((0, 0, dz + TM_S * (st["toe"].x - st["tip"].x) * w))
        ik_on(l, st["tip"] + V((0, 0, dz)), st["pole"] + V((0, 0, dz)), toe)    # own IK call: drive() would pass the tip as the knee pole
    vl.update(); return {}
def _tm_props(J, J0, *a):
    treadmill_qa("tm", J0["hips"].x)
    box("tm_ref", (J["head"].x, 0, J["head"].z + (-0.04 if a else 0.12 + TM_B0)), (0.01, 0.01, 0.01), "frame")   # keeps the lifted head inside the camera framing
_t("treadmill").update(props=_tm_props, track=treadmill_track)

# ---------- QA fix: dead-bug ----------
# hand-posed FK: tabletop (hips/knees 90, arms to ceiling); then opposite arm overhead + opposite leg out just above the mat (legs split in y so they never cross)
DBUG_TAB = [180, 16, 90, 16]; DBUG_UP = [180, 12, 180, 12]; DBUG_OH = [243, 8, 243, 8]; DBUG_EXT = [104, 16, 100, 16]
def _dbug(armL=DBUG_UP, armR=DBUG_UP, legL=DBUG_TAB, legR=DBUG_TAB): return sb(armL=armL, armR=armR, legL=legL, legR=legR)
_t("dead-bug")["keys"] = [_dbug(), _dbug(armR=DBUG_OH, legL=DBUG_EXT), _dbug(), _dbug(armL=DBUG_OH, legR=DBUG_EXT)]
_t("dead-bug").pop("stance", None); _t("dead-bug")["cam"] = dict(az=-62, el=28)

# ---------- QA fix: air-bike ----------
# hand-posed FK (upright, slight forward lean, head neutral); pedals and lever grips are scripted by air_bike_track, body anchored on the saddle
_t("air-bike")["keys"] = [P(T=168, H=172, armL=[50, 14, 85, 6], armR=[50, 14, 85, 6], legL=[72, 6, -12, 6], legR=[72, 6, -12, 6])] * 2
_t("air-bike").pop("stance", None)
_t("air-bike").update(anchor={"z": ("pelvis", 0.95), "x": ("pelvis", 0.0)}, track=air_bike_track, driven=["foot_l", "foot_r", "hand_l", "hand_r"], linear=True,
                      props=lambda J, J0, *a: air_bike("ab", J0, J), cam=dict(az=-70, el=10))

# ---------- QA fix: bb-rollout ----------
# hand-posed FK, knees stay on the mat in every frame (anchor on the knee, shins flat behind, tops of the feet down); hips+arms extend to a straight knee-to-head line
BBR_LEG = [-8, 5, -90, 4, -95]; BBR_LEG2 = [-66, 5, -90, 4, -95]
def bbr_mat(J, J0, *a): box("mat", (J0["knee_r"].x + 0.3, 0, 0.006), (2.6, 0.7, 0.012), "mat")   # long enough for the whole roll-out
_t("bb-rollout")["keys"] = [P(T=140, H=150, N=146, armL=[15, 8, 30, 8], armR=[15, 8, 30, 8], legL=BBR_LEG, legR=BBR_LEG),
                            P(T=100, H=104, N=102, armL=[78, 14, 92, 14], armR=[78, 14, 92, 14], legL=BBR_LEG2, legR=BBR_LEG2)]
_t("bb-rollout").pop("stance", None)
_t("bb-rollout").update(anchor={"z": ("knee_r", 0.062), "x": ("knee_r", None)},
  props=P_(bbr_mat, lambda J, J0, *a: (rod("bar", V((J["hands"].x, 0.7, 0.225)), V((J["hands"].x, -0.7, 0.225)), 0.016, "chrome"),
                                       plate_between("p1", V((J["hands"].x, 0.55, 0.225)), V((J["hands"].x, 0.6, 0.225)), 0.225),
                                       plate_between("p2", V((J["hands"].x, -0.55, 0.225)), V((J["hands"].x, -0.6, 0.225)), 0.225))))

# ---------- QA fix: open-book ----------
# side-lying on the left (SIDE_BASE convention, head +X), hips ~90 flexed and knees ~90 flexed, thighs forward (+Y), knees stacked;
# bottom arm reaches forward on the mat, top arm starts on top of it, sweeps up over the chest and opens out behind (-Y) while the
# upper trunk rotates (twist); hips/knees do not move.
OB_LEG = dict(legL=[48.7, -62, -90, 0, -90, 0], legR=[31, 50, -90, 0, -90, 0])   # the body's front is -Y (toward the camera); top thigh drops onto the bottom one
OB_BASE = dict(T=90, roll=-90, H=64, N=68, armL=[90, -72, 100, -72], handL="flat", handR="relaxed", **OB_LEG)
# hand targets are world offsets from hip_l (it never moves): every key carries BOTH hands so reach_lerp interpolates them smoothly
class OBArm(list):
    """Arm angles that differ per character (the female shoulder sits ~5 cm higher over the mat): resolved on every index, loop_keys keeps the object."""
    def __init__(self, m, f): super().__init__(m); self.f = f
    def __getitem__(self, i): return self.f[i] if arm.name == CHARS["f"][0] else list.__getitem__(self, i)
def OB_K(armL, armR, tw=0, fL=None, fR=None, **kw):   # pure FK (IK gave reversed elbows). clavL = -twist keeps the bottom shoulder in place (y) while the chest turns; armL pitches down to absorb the remaining lift
    p = P(**{**OB_BASE, "armL": armL}, armR=armR, **({"twist": tw, "clavL": -tw} if tw else {}), **kw)
    p["armL"] = OBArm(armL, fL or armL); p["armR"] = OBArm(armR, fR or armR); return p
OB_START = OB_K([70, -75, 70, -75], [18.4, 42.3, 18.4, 42.3], fL=[63, -65, 63, -65], fR=[30, 50, 30, 50], palmR="down")
def ob_mat(J, J0, *a):
    box("mat", (J0["pelvis"].x + 0.2, 0.05, 0.006), (2.0, 1.8, 0.012), "mat")
    h = J0["head"].z - 0.14; box("pillow", (J0["head"].x, J0["head"].y, h / 2 + 0.006), (0.3, 0.26, h - 0.012), "pad")   # thin folded towel: the head rests on it (a bare mat is ~0.1 m too low for the shoulder width)
OB_MID = OB_K([54.5, -75, 54.5, -75], [180, 0, 180, 0], -25, fL=[58, -62, 58, -62], palmR="feet")
OB_END = OB_K([40, -75, 40, -75], [0, -50, 0, -50], -49, fL=[54, -60, 54, -60], fR=[0, -45, 0, -45], palmR="up")
_t("open-book").update(keys=[OB_START, OB_MID, OB_END], pingpong=True, anchor={"z": ("knee_l", 0.075), "x": ("hip_l", None)}, props=ob_mat,
                       cam=dict(az=-80, el=52), free=["hand_l", "hand_r", "foot_l", "foot_r"])
_t("open-book").pop("focus", None)

# ---------- QA fix: bike ----------
# hand-posed FK (upright, slight forward lean, head neutral); pedals and grips scripted by bike_track, body anchored on the saddle
_t("bike")["keys"] = [P(T=172, H=174, armL=[55, 14, 85, 6], armR=[55, 14, 85, 6], legL=[72, 6, -12, 6], legR=[72, 6, -12, 6])] * 2
_t("bike").pop("stance", None)
_t("bike").update(anchor={"z": ("pelvis", 0.95), "x": ("pelvis", 0.0)}, track=bike_track, driven=["foot_l", "foot_r", "hand_l", "hand_r"], linear=True,
                  props=lambda J, J0, *a: bike_up("bk", J0, J), cam=dict(az=-70, el=10))

# ---------- QA fix: battle-ropes ----------
# hip-width quarter squat, chest up; alternating arm drive (one hand shoulder height while the other is at the hip); each rope is a chain
# of short 4 cm segments following a travelling sine wave (phase = loop phase, opposite for the two arms) from the fist to a floor anchor post.
BR_BASE = dict(T=166, H=176, legL=[48, 12, -26, 10], legR=[48, 12, -26, 10])
BR_K = lambda l, r: P(**BR_BASE, armL=l, armR=r)
BR_D, BR_U = [20, 8, 62, 6], [96, 8, 118, 6]
BR_L, BR_N = 2.4, 30
def br_rope(n, h, A, ph, s):
    """Rope n from fist h to anchor A: travelling wave (wavelength 1 m, amplitude 0.22 m at the hand end, fading to the anchor)."""
    pts = []
    for i in range(BR_N + 1):
        u = i / BR_N; p = h * (1 - u) + A * u
        env = math.sin(min(u / 0.12, 1.0) * math.pi / 2) * (1 - u) ** 0.7
        z = h.z * (1 - u) + 0.06 * u + 0.22 * env * math.cos(2 * math.pi * (ph - u * BR_L + (0.0 if s > 0 else 0.5)))
        pts.append(V((p.x, p.y, max(z, 0.03))))
    for i in range(BR_N):
        d = (pts[i + 1] - pts[i]) * 0.12   # overlap neighbours so bends have no gaps (no ball joints: those banded the shading)
        rod(f"{n}_s{i}", pts[i] - (d if i else 0 * d), pts[i + 1] + (d if i < BR_N - 1 else 0 * d), 0.02, "accent")
def br_props(J, J0, *a):
    A = V((J0["pelvis"].x + BR_L, 0, 0.0)); J["rope_anchor"] = A
    ph = a[0]["phase"] if a else 0.0
    rod("br_post", V((A.x, 0, 0.0)), V((A.x, 0, 0.42)), 0.06, "frame"); ball("br_cap", V((A.x, 0, 0.42)), 0.06, "frame")
    for s, sg in (("l", 1), ("r", -1)):
        tip = V((A.x - 0.03, sg * 0.05, 0.12))
        br_rope("br_" + s, J["hand_" + s], tip, ph, sg)
_t("battle-ropes").update(keys=[BR_K(BR_U, BR_D), BR_K(BR_D, BR_U)], anchor={"x": ("ankle_r", None)}, props=br_props, steps=8, hands="grip",
                          focus=["head", "ankle_l", "ankle_r", "toe_l", "toe_r", "hand_l", "hand_r", "pelvis", "rope_anchor"], cam=dict(az=-70, el=8, margin=1.24))
_t("battle-ropes").pop("stance", None)

# ---------- QA fix: tbar-row ----------
# lying prone on the 38 deg chest pad (head up-forward), legs trailing to the foot platform; only the arms row (hang -> elbows back at the ribs)
TBR_BODY = dict(T=128, S=130, N=130, H=128, legL=[-52, 5, -60, 5, 64], legR=[-52, 5, -60, 5, 64])
TBR_HANG, TBR_ROW = ARMS((0.08, 0.2, -1.0)), ARMS((-0.968, 0.2, 0.254), (0.443, 0.2, -0.897))
TBR_MID = ARMS((-0.88, 0.2, -0.48), (0.55, 0.2, -0.83))      # hands on the lever's circular path halfway up (keeps the rigid lever's handles in the grip)
_set("tbar-row", [P(**TBR_BODY, **TBR_HANG), P(**TBR_BODY, **TBR_MID), P(**TBR_BODY, **TBR_ROW)], pingpong=True, steps=3, props=lambda J, J0, *a: tbar_chest_machine("m", J0, J),
     anchor={"z": ("ankle_l", 0.3)}, plant=["foot_l", "foot_r"], free=["hand_l", "hand_r"], hands="grip", cam=dict(az=-115, el=24, margin=1.25),
     focus=["head", "ankle_l", "ankle_r", "toe_l", "toe_r", "hand_l", "hand_r", "pelvis", "tbar_pivot"])

# ---------- QA fix: landmine-row ----------
# bar runs in a vertical plane OUTSIDE the working (right, -Y) leg: arm hangs out/forward to the bar, then rows elbow-back to the hip; free hand rests on the left thigh
# hand-posed: trunk ~45 deg from horizontal (T=135), flat back, hips back, soft knees; same trunk/legs in both keys, only the working arm moves.
# pivot in front, bar rises to the lifter beside the right leg (camera elevated front-right).
LMR_BODY = dict(T=135, S=136, N=146, H=150, legL=[24, 5, -16, 5], legR=[24, 5, -16, 5])
LMR_FREE = V2((-0.1, 0.35, -0.93)) + V2((-0.5, 0.2, -0.84))
LMR_A = lambda r: P(**LMR_BODY, armL=LMR_FREE[:4], armR=r)
_t("landmine-row")["keys"] = [LMR_A(V2((0.12, 0.42, -0.9)) + V2((0.12, 0.42, -0.9))), LMR_A(V2((-0.95, 0.55, -0.35)) + V2((-0.1, 0.5, -0.86)))]
_t("landmine-row")["anchor"] = {}; _t("landmine-row").pop("stance", None)
_t("landmine-row")["plant"] = ["foot_l", "foot_r"]
_t("landmine-row")["handdir"] = 30
# pivot on the floor IN FRONT (lifter faces the anchor); bar rises to the hand, plate at the lifter's end beside the hand. Measured plate-rim -> thigh gap: >=0.10 m (m), >=0.047 m (f)
def LMR_props(J, J0, *a):
    J["lm_pivot"] = V((J0["hand_r"].x + 1.4, J0["hand_r"].y, 0.0)); landmine("lm", J["lm_pivot"], J["hand_r"])
_t("landmine-row")["props"] = LMR_props
_t("landmine-row")["handL"] = "flat"
_t("landmine-row")["focus"] = ["head", "ankle_l", "ankle_r", "toe_l", "toe_r", "hand_l", "hand_r", "pelvis", "lm_pivot"]
_t("landmine-row")["cam"] = dict(az=-62, el=20, margin=1.25)

# ---------- QA fix: hip-switch ----------
# in-between keys: both legs keep the foot on the floor (ankle z ~ 0.09) while the thigh swings from 90/90 to knees-up, so no straight-leg split mid-switch
HSW_Z = 0.07 # pelvis height above the mat while seated
# windscreen wipers: both ankles planted at fixed world spots (wide, a little ahead of the hips); each knee rides the circle of points that are one
# thigh from the hip and one shin from the ankle, from knee-down on one side, through knees-up, to knee-down on the other side.
HSW_LT, HSW_LS = 0.43, 0.45                       # thigh / shin length measured on the rig
HSW_HIP = {"l": (-0.04, 0.11, HSW_Z + 0.04), "r": (-0.04, -0.11, HSW_Z + 0.04)}
HSW_ANK = {"l": (0.14, 0.48, 0.08), "r": (0.14, -0.48, 0.08)}   # fixed heel spots (0.96 m apart)
def HSW_leg(side, th):
    """th: knee angle about the hip-ankle axis in degrees (0 = knees up, +90 = knee down toward +Y (left), -90 = toward -Y)."""
    H, A = HSW_HIP[side], HSW_ANK[side]; ax = [a - h for a, h in zip(A, H)]; d = _m.sqrt(sum(c * c for c in ax)); u = [c / d for c in ax]
    a = (d * d + HSW_LT ** 2 - HSW_LS ** 2) / (2 * d); r = _m.sqrt(HSW_LT ** 2 - a * a); C = [h + a * c for h, c in zip(H, u)]
    e2 = [-u[1], u[0], 0.0]; n2 = _m.hypot(e2[0], e2[1]); e2 = [c / n2 for c in e2]
    if e2[1] < 0: e2 = [-c for c in e2]             # horizontal perpendicular pointing toward +Y
    e1 = [u[1] * e2[2] - u[2] * e2[1], u[2] * e2[0] - u[0] * e2[2], u[0] * e2[1] - u[1] * e2[0]]
    if e1[2] < 0: e1 = [-c for c in e1]             # perpendicular pointing up
    t = _m.radians(th); K = [c + r * (_m.cos(t) * p + _m.sin(t) * q) for c, p, q in zip(C, e1, e2)]
    thigh = tuple((k - h) / HSW_LT for k, h in zip(K, H)); shin = tuple((a_ - k) / HSW_LS for a_, k in zip(A, K))
    sg = 1 if side == "l" else -1
    return LEG(side, thigh, shin, (0.8, 0.35 * sg, -0.43))   # foot flat on the mat, toes forward and slightly out
HSW_TH = lambda f: 90 * _m.cos(2 * _m.pi * f / 24)  # 24 frames: knees down left, up, down right, up
_hk = _t("hip-switch")["keys"]   # only used as the template for the per-frame keys below
# seated hip is ~0.10 above the mat; torso reclines ~16 deg and arms hang almost straight down behind so both palms actually reach the mat
HSW_ARMS = ARMS((-0.25, 0.32, -0.92))
for _P in _hk: _P.update(T=209, H=192, S=207, handdir=-72, clavL=50, clavR=50, **HSW_ARMS)
_t("hip-switch")["anchor"] = {"z": ("pelvis", HSW_Z)}
_t("hip-switch")["props"] = lambda J, J0, *a: box("mat", (J0["pelvis"].x - 0.05, 0, 0.006), (1.5, 1.8, 0.012), "mat")   # wide square mat under both feet
_t("hip-switch")["cam"] = dict(az=-40, el=15)
_t("hip-switch")["keys"] = [dict(_hk[0], legL=HSW_leg("l", HSW_TH(f)), legR=HSW_leg("r", HSW_TH(f)), frollL=0, frollR=0) for f in range(24)]   # 24 explicit per-frame keys, no angle-lerped in-betweens
_t("hip-switch")["steps"] = 1

# ---------- QA fix: incline-db-press ----------
# same flush-pad solution as smith-incline-low: 28 deg back pad -> T = 180 + (90 - 28) = 242 keeps the trunk on the pad every
# frame; head down on the pad (H = T - 2); seated legs; forearms vertical at the bottom (dumbbells touch down at the upper chest),
# press straight up over the shoulders. Neutral grip (palms facing in) from the template's hands="grip" default.
IDP_T = 242
IDP_SEAT = dict(legL=[90, 6, 0, 6], legR=[90, 6, 0, 6])
IDP_TOP = P(T=IDP_T, H=IDP_T - 2, **IDP_SEAT, armL=[172, 32, 172, 32], armR=[172, 32, 172, 32])
IDP_BOTTOM = P(T=IDP_T, H=IDP_T - 2, **IDP_SEAT, armL=[105, 36, 180, 0], armR=[105, 36, 180, 0])
_t("incline-db-press")["keys"] = [IDP_TOP, IDP_BOTTOM]
_t("incline-db-press")["props"] = P_(lambda J, J0, *a: incline_bench("bench", J0, 28, J0["hips"].x + 0.05, region_low("seat"), back_len=1.2), DB())

# ---------- QA fix: assisted-pullup ----------
# hand-posed FK, fully symmetric: kneeling on ONE pad (thighs down, shins back along the pad), torso upright; arms hang wide -> elbows down/out, chin over the bar
APU_LEG = dict(legL=[0, 3, -90, 3, -100], legR=[0, 3, -90, 3, -100])
APU_HANG, APU_TOP = ARMS((0.0, 0.2, 0.98), (0.0, 0.15, 0.99)), ARMS((-0.1, 0.75, -0.55), (0.1, -0.35, 0.93))
APU_MID = ARMS((0.15, 0.6, 0.1), (0.2, 0.0, 0.97))      # mid-pull: elbows out to the side and slightly forward, forearms up (the arc between hang and top)
_t("assisted-pullup").update(keys=[P(T=180, N=180, H=180, **APU_LEG, **APU_HANG), P(T=176, N=176, H=176, **APU_LEG, **APU_MID), P(T=172, N=172, H=172, **APU_LEG, **APU_TOP)], pingpong=True, steps=3,
  props=lambda J, J0, *a: apu_station("m", J0, J), anchor={"z": ("hand_r", 2.05), "x": ("hand_r", None)}, free=["foot_l", "foot_r"], hands="grip", palm="forward", cam=dict(az=-50, el=10))
_t("assisted-pullup").pop("stance", None)

# ---------- QA fix: supine-punch ----------
# flat on the mat (own copy of the mcgill torso), hook-lying feet flat, free arm resting on the mat, right arm straight up; the punch = scapular protraction (elevR) only
SPU_B = dict(legL=[150, 8, 26, 8], legR=[150, 8, 26, 8], armL=[86, 14, 86, 14], armR=[180, 4, 180, 4], T=270, S1=262, S2=266, S3=282, N=278, H=278, anchor={"z": ("pelvis", 0.1065)})
SPU_F = dict(legL=[156, 8, 34, 8], legR=[156, 8, 34, 8], anchor={"z": ("pelvis", 0.1168)}, S1=276, S2=284, S3=266, N=274, H=274)
SPU_TWF = 15
SPU_TW = 11 # upper-trunk roll (deg about the trunk axis) at the punch: lifts the right shoulder blade off the mat
_t("supine-punch")["keys"] = _SexKeys([P(**SPU_B, elevR=0, _f=SPU_F), P(**SPU_B, elevR=14, twist=SPU_TW, _f=dict(SPU_F, elevR=14, twist=SPU_TWF))])

# ---------- QA fix: rfess ----------
# rear foot pointed back (pitch ~-92, laces down) and the pad top set to just under the pinned ankle so the instep rests ON the pad
RFESS_FP, RFESS_DZ = -92, 0.045
_set("rfess", [P(T=182, H=184, legL=[28, 6, 15, 6], legR=[-35, 4, -90, 4, RFESS_FP], armL=[2, 9, 2, 8], armR=[2, 9, 2, 8]),
               P(T=172, H=178, legL=[80, 8, 5, 8], legR=[-35, 4, -150, 4, RFESS_FP], armL=[2, 9, 2, 8], armR=[2, 9, 2, 8])],
     props=P_(lambda J, J0, *a: flat_bench("bench", J0["ankle_r"].x - 0.32, J0["ankle_r"].x + 0.08, J0["ankle_r"].z - RFESS_DZ, y=J0["ankle_r"].y, w=0.32), DB()),
     anchor={"x": ("ankle_l", None)}, plant=["foot_l", "foot_r"], cam=dict(az=-72, el=8))

# ---------- QA fix: push-up ----------
# Why deeper pivots used to fail: simulate()/settle() raise the whole body whenever trunk_low() (which counts the ARMS) is
# below the floor, and the straight FK arm hint sinks through the floor at a low body angle -> body lifted -> pike. Fix: the
# template opts out with nolift=True (rig.simulate/audit skip settle()/the sink guard; default off for every other template),
# hands+toes stay pinned by contact IK, the body is a rigid plank pivoting about the toes. Hands are planted ~0.2 m behind the
# (rev 1 only; superseded by rev 2 below: hands under the top shoulders).
# Rev 2: top arms straight with wrists under the shoulders; same planted hands at the bottom (rigid pivot only moves the shoulders ~5 cm forward).
PUX_TT, PUX_BT, PUX_TOP_ARM, PUX_BTM_ARM = 105.8, 94.3, [-6, 8, -6, 8], [-65, 35, 0, 6]
def _pux_flat(J, J0, *a):   # palms flat + fingers forward every frame, then seat each palm exactly on the floor (IK z only)
    for s in "lr":
        sg = SIDE[s]; hd = d(92, 12, sg)
        for _ in range(2):
            fd = bone_dir("lowerarm_" + s); set_palm(s, fd, hd, palm_target(None, s, sg, "flat", 105, fd, hd)); aim("hand_" + s, hd); vl.update()
            dip = limb_low("hand_" + s)
            if abs(dip) < 0.004: break
            ik_on("hand_" + s, jw(EFF["hand_" + s], True) + Vector((0, 0, -dip)), J["elbow_" + s]); vl.update()
_t("push-up").update(keys=[P(**_pu_body(PUX_TT), **both(PUX_TOP_ARM)), dict(P(**_pu_body(PUX_BT), **both(PUX_BTM_ARM)), anchor=PU_PIV)],
                     props=_pux_flat, plant=["foot_l", "foot_r", "hand_l", "hand_r"], nolift=True)

# ---------- QA fix: kb-deadlift ----------
# ONE bell on the floor between the feet, both hands on its handle; hip hinge (hips back, soft knees, flat back), stand tall at the top.
KBD_ARMS = lambda x, y=-0.3: ARMS((x, y, -0.95))
KBD_TOP = dict(T=178, S=178, N=178, H=178, legL=[2, 4, -1, 4], legR=[2, 4, -1, 4], **KBD_ARMS(0.2, -0.16))
KBD_BTM = dict(T=100, S=102, N=112, H=120, legL=[48, 7, -38, 7], legR=[48, 7, -38, 7], **KBD_ARMS(-0.3, -0.22))
_kbd_bell = lambda J, J0, *a: kettlebell("kb", J["hands"], up=(0, 0, 1), side=J["hand_l"] - J["hand_r"])
_t("kb-deadlift").update(keys=[P(**KBD_TOP), P(**KBD_BTM)], props=_kbd_bell, anchor={}, plant=["foot_l", "foot_r"], cam=dict(az=-60, el=10))

# ---------- QA fix: seal-row ----------
# prone + flat on a raised flat bench (torso/legs on the pad), head neutral, arms hang straight down, then row the DBs to the ribs.
SEAL_BENCH_Z, SEAL_LIFT = 0.86, -0.04   # pad top / torso-joint height above the pad (calibrated by eye)
SEAL_LEG = dict(legL=[-83, 3, -86, 3, -76], legR=[-83, 3, -86, 3, -76])
SEAL_DN = ARMS((0.0, 0.3, -1.0))
SEAL_UP = ARMS((-0.6, 0.62, 0.45), (0.1, 0.3, -1.0))
def _seal_gap(J, J0, *a):    # key pass: lateral gap between each dumbbell's inner edge and the pad edge (half width 0.18)
    if a: return
    g = []
    for n in ("db_l", "db_r"):
        os_ = [o for o in bpy.data.objects if n in o.name and o.type == "MESH"]
        if not os_: print("SEALGAP names", [o.name for o in bpy.data.objects if "db" in o.name.lower()][:12])
        if os_: g.append(min(abs((o.matrix_world @ V(c)).y) for o in os_ for c in o.bound_box))
    print("SEALGAP min|y| of DB bbox", [round(x, 3) for x in g], "gap to pad", [round(x - 0.18, 3) for x in g])
SEAL_TOP = [SEAL_BENCH_Z]   # pad top = lowest torso point over the key poses (per character), set in the key pass
def _seal_bench(J, J0, *a):
    if not a:                                  # key pass (no ctx): fit the pad under the torso of both keys
        lo = min(p.z for p in body_bbox() if abs(p.y) < 0.12 and J["pelvis"].x - 0.05 < p.x < J["shoulders"].x - 0.04)   # trunk strip (arms hang outside it)
        SEAL_TOP[0] = lo if J is J0 else min(SEAL_TOP[0], lo)
    flat_bench("bench", min(J0["ankle_l"].x, J0["ankle_r"].x) - 0.32, J0["shoulders"].x + 0.14, SEAL_TOP[0], w=0.36)
_t("seal-row").update(keys=[prone(**SEAL_DN, **SEAL_LEG, S=90, N=90, H=82), prone(**SEAL_UP, **SEAL_LEG, S=90, N=90, H=82)], anchor={"z": ("pelvis", SEAL_BENCH_Z + 0.04)}, nolift=True,
                      props=P_(_seal_bench, DB(), _seal_gap), free=["foot_l", "foot_r", "hand_l", "hand_r"], hands="grip", cam=dict(az=-50, el=20))

# ---------- QA fix: chair-squat ----------
# hand-posed: stand tall -> sit back and down (hips back, knees over toes, chest up, neutral head) until the buttocks just touch the seat.
# The chair is fitted to the lowest hips of the key poses (seat top = hips - CHSQ_DZ), complete with posts up to the backrest.
CHSQ_DZ, CHSQ_ARMS, CHSQ_H = 0.10, [66, 8, 82, 8], []
CHSQ_TOP = dict(T=178, S=178, N=178, H=178, legL=[2, 4, -1, 4], legR=[2, 4, -1, 4], armL=CHSQ_ARMS, armR=CHSQ_ARMS)
CHSQ_BTM = dict(T=140, S=146, N=156, H=166, legL=[78, 5, -14, 5], legR=[78, 5, -14, 5], armL=CHSQ_ARMS, armR=CHSQ_ARMS)
def _chsq_chair(J, J0, *a):
    if not a:
        if J is J0: CHSQ_H.clear()
        CHSQ_H.append(J["hips"].copy())
    h = min(CHSQ_H, key=lambda p: p.z); top = h.z - CHSQ_DZ; x = h.x - 0.06
    box("chair_seat", (x, 0, top - 0.025), (0.44, 0.44, 0.05), "wood")
    for k, (dx, dy) in enumerate(((0.18, 0.18), (0.18, -0.18), (-0.2, 0.18), (-0.2, -0.18))):
        tube(f"chair_leg{k}", (x + dx, dy, 0.0), (x + dx, dy, top - 0.05), 0.018, "steel")
    for dy in (0.18, -0.18): tube(f"chair_post{dy > 0}", (x - 0.2, dy, top - 0.05), (x - 0.2, dy, top + 0.46), 0.018, "steel")
    box("chair_back", (x - 0.2, 0, top + 0.30), (0.035, 0.42, 0.3), "wood")
_t("chair-squat").update(keys=[P(**CHSQ_TOP), P(**CHSQ_BTM)], props=_chsq_chair, anchor={"x": ("ankle_l", None)}, plant=["foot_l", "foot_r"], cam=dict(az=-70, el=8))

# ---------- QA fix: step-mill ----------
# StepMill: the lifter stands at a fixed height (hips lifted SMILL_P0 onto the machine); the treads revolve down-and-back (stepmill_qa, one tread per half cycle).
# Foot on the upper tread rides it down (bent -> straight leg); the other foot, behind on the lower tread, trails back with it, lifts clear of the
# riser, swings over and lands on the next tread up exactly as that tread arrives at the upper-tread position -> the two half cycles are mirror images (seamless loop).
SMILL_ARM = [10, 20, 45, 8]; SMILL_PO = -0.4
SMILL_B = [(0, -0.16, 0.0), (.15, -0.19, 0.05), (.30, -0.20, 0.15), (.45, -0.14, 0.24), (.62, -0.05, 0.29), (.80, 0.09, 0.27), (1, 0.14, 0.20)]   # swing foot (s, x rel hips, sole z rel lowest tread top); peak only ~9 cm over the next step
def _smill_hz(J0, a_h=0.09):
    """Fixed hip height (world): the trailing foot (ankle 0.16 behind the hips, on the lowest tread) reaches with a nearly straight knee (97 % of the leg)."""
    L = (J0["hip_l"] - J0["knee_l"]).length + (J0["knee_l"] - J0["ankle_l"]).length
    return SMILL_P0 + SMILL_ZB + a_h + math.sqrt((0.97 * L) ** 2 - (SMILL_XC - 0.09) ** 2)
SMILL_V = (-0.30, -0.20)      # tread velocity per half cycle (the end tangents of the swing path: lands moving with the tread, leaves moving with it)
def _smill_pos(s):
    """Swing-foot (x, z) at s: cubic Hermite through SMILL_B, end tangents = tread velocity, interior tangents Catmull-Rom."""
    W = SMILL_B; n = len(W); m = [SMILL_V] + [tuple((W[k + 1][c] - W[k - 1][c]) / (W[k + 1][0] - W[k - 1][0]) for c in (1, 2)) for k in range(1, n - 1)] + [SMILL_V]
    k = min(max(sum(1 for w in W if w[0] <= s) - 1, 0), n - 2); h = W[k + 1][0] - W[k][0]; t = (s - W[k][0]) / h
    a, b, c, e = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
    return tuple(a * W[k][1 + q] + b * h * m[k][q] + c * W[k + 1][1 + q] + e * h * m[k + 1][q] for q in (0, 1))
def _smill_s(ctx): return ((ctx["i"] % 2) + ctx["t"]) / 2      # progress through the current half cycle (4 keys, 2 per half)
def _smill_track(ctx):
    a_h = min(ctx["states"][k][l]["tip"].z for k in range(4) for l in ("foot_l", "foot_r"))                      # the lowest key's ankle is the flat foot's
    arm.location.z += _smill_hz(ctx["J0"], a_h) - joints()["hips"].z; vl.update(); J = joints()      # hips held at one fixed height whatever the FK hint pose
    hx = ctx["J0"]["hips"].x; s = _smill_s(ctx); A = "foot_l" if ctx["i"] < 2 else "foot_r"
    zb = SMILL_P0 + SMILL_ZB; ao = 0.09
    for l in ("foot_l", "foot_r"):
        st = min((ctx["states"][k][l] for k in range(4)), key=lambda q: q["tip"].z); off = st["toe"] - st["tip"]
        if l == A: x = hx + SMILL_XC + SMILL_RUN * (1 - s) - ao; z = zb + SMILL_RISE * (1 - s)                          # rides the upper tread down
        else: bx, bz = _smill_pos(s); x = hx + bx; z = zb + bz
        sg = 1 if l == "foot_l" else -1; hip = J["hip_" + l[-1]]; tip = V((x, hip.y, z + a_h))
        ax = (tip - hip).normalized(); bend = (V((1, SMILL_PO * sg, 0)) - ax * (ax.x + SMILL_PO * sg * ax.y)).normalized()          # knee points forward, perpendicular to the leg
        ik_on(l, tip, (hip + tip) / 2 + bend * 0.6, tip + off)
    vl.update(); return {}
def _smill_props(J, J0, *a):
    stepmill_qa("sm", J0, _smill_s(a[0]) if a else 0.0, _smill_hz(J0))
    box("sm_ref", (J["head"].x, 0, _smill_hz(J0) + (J["head"].z - J["hips"].z) + 0.05), (0.01, 0.01, 0.01), "frame")     # keeps the lifted head inside the framing
SMILL_UP, SMILL_BK, SMILL_MID, SMILL_SW = [45, 3, -10, 3], [-8, 3, -6, 3], [20, 3, -5, 3], [35, 3, -40, 3]    # FK hints (IK sets the feet): foot on the upper tread / trailing / riding down / swinging
_t("step-mill").update(keys=[P(T=178, H=178, legL=SMILL_UP, legR=SMILL_BK, armL=SMILL_ARM, armR=SMILL_ARM), P(T=178, H=178, legL=SMILL_MID, legR=SMILL_SW, armL=SMILL_ARM, armR=SMILL_ARM),
                             P(T=178, H=178, legR=SMILL_UP, legL=SMILL_BK, armL=SMILL_ARM, armR=SMILL_ARM), P(T=178, H=178, legR=SMILL_MID, legL=SMILL_SW, armL=SMILL_ARM, armR=SMILL_ARM)],
                       props=_smill_props, track=_smill_track, steps=4,
                       anchor={"x": ("pelvis", None)}, free=["foot_l", "foot_r"], hands="grip", cam=dict(az=-74, el=16),
                       reach={"hand_l": ("hips", (0.10, 0.34, -0.04), "world"), "hand_r": ("hips", (0.10, -0.34, -0.04), "world")})     # hands on the hip-height side rails, beside the hips
_t("step-mill").pop("stance", None)

# ---------- QA fix: push-up-plus ----------
# straight-arm top plank of the accepted push-up (PUX_TT, PUX_TOP_ARM, planted hands/toes, nolift); only the spine above the lumbar moves:
# protraction = upper back domes up, retraction = chest sinks between the shoulders. Hips/legs/lumbar identical in every key.
PUP_PRO, PUP_RET = [(0, 22, -10)], [(0, -14, 8)]   # arms stay straight (app cues): the visible motion is the mid-back dome; S2 range widened so it reads at card size   # S2 up / S3 down = mid-back dome with the shoulder joints (arm reach) unchanged   # S3 (shoulder girdle) barely tilts so the arms/palms see no twist flip   # (S1, S2, S3) offsets from T
def _pup(o, t=PUX_TT):
    b = _pu_body(t); a, b2, c = o
    return dict(b, S1=t + a, S2=t + b2, S3=t + c, N=b["H"], H=b["H"])   # head/neck keep the same world pitch every frame
_t("push-up-plus").update(keys=[P(**_pup(PUP_RET[0]), **both(PUX_TOP_ARM)), P(**_pup(PUP_PRO[0]), **both(PUX_TOP_ARM))],
                          props=_pux_flat, plant=["foot_l", "foot_r", "hand_l", "hand_r"], nolift=True, cam=dict(az=-72, el=9))

# ---------- QA fix: band-pull-apart ----------
# Hand-built symmetric stance (photo base twisted the torso): upright, neutral head, straight arms at shoulder height, palms down,
# pull to a T just ahead of the shoulder line so the band meets the chest. Band = thin rod hand to hand, radius shrinks as it stretches.
BPA_ARM0, BPA_ARM1 = [90, 9, 90, 9], [90, 75, 90, 75]
def bpa_band(J, J0, *a):
    p, q = V(J["hand_l"]), V(J["hand_r"]); L = (p - q).length; u = (q - p).normalized() * 0.02; p, q = p + u, q - u   # ends tucked just inside the fists
    rod("band", p, q, min(0.02, max(0.006, 0.0125 * (0.4 / max(L, 0.2)) ** 0.5)), "band")
_t("band-pull-apart").update(keys=[P(T=180, S=180, H=180, N=180, **both(BPA_ARM0)), P(T=180, S=180, H=180, N=180, **both(BPA_ARM1))],
                             props=bpa_band, hands="grip", palm="down", stance="stand", cam=dict(az=-40, el=12))

# ---------- QA fix: db-glute-bridge ----------
# own copy of the mcgill flat-on-the-mat torso; hook-lying feet; dumbbell (axis across) rests on the hip crease, both hands on the handle (reach-driven).
DGB_B = dict(legL=[150, 8, 26, 8], legR=[150, 8, 26, 8], armL=[86, 14, 86, 14], armR=[86, 14, 86, 14], T=270, S1=262, S2=266, S3=282, N=278, H=278, anchor={"z": ("pelvis", 0.1065)})
DGB_BF = dict(legL=[156, 8, 34, 8], legR=[156, 8, 34, 8], S1=276, S2=284, S3=266, N=274, H=274, anchor={"z": ("pelvis", 0.1168)})
DGB_TOP = dict(legL=[110, 8, -2, 8], legR=[110, 8, -2, 8], T=304, S1=308, S2=304, S3=290, N=282, H=276)   # trunk slopes down to the shoulder blades, which stay on the mat
DGB_TOPF = dict(DGB_TOP, T=292, S1=294, S2=292, S3=282, N=278, H=274)
DGB_DZ = (0.27, 0.21)# dumbbell centre above the hip joint (world, per key): resting on the hip crease
def _dgb_reach(dz): return {"hand_l": ("hips", (0.0, 0.07, dz), "world"), "hand_r": ("hips", (0.0, -0.07, dz), "world")}
def _dgb_props(J, J0, *a):   # dumbbell sits exactly between the two driven hands
    mat("mat", J0); dumbbell("db", (J["hand_l"] + J["hand_r"]) / 2, V((0, 1, 0)), 0.4)
_t("db-glute-bridge").update(keys=_SexKeys([P(**DGB_B, reach=_dgb_reach(DGB_DZ[0]), _f=DGB_BF), P(**{**DGB_B, **DGB_TOP, "anchor": {}}, reach=_dgb_reach(DGB_DZ[1]), _f=dict(DGB_BF, **DGB_TOPF, anchor={"z": ("shoulder_l", 0.075)}))]), props=_dgb_props, hands="grip",
  reach=_dgb_reach(DGB_DZ[0]), free=["hand_l", "hand_r"], cam=dict(az=-35, el=24))
_t("db-glute-bridge").pop("stance", None)

# ---------- QA fix: hk-pallof ----------
# Hand-posed FK (the photo base twisted the torso and tilted the head): upright square torso, neutral head, LEFT (inside, tower-side) knee
# on the pad, right foot flat in front (90/90), hands clasped at the sternum -> pressed straight out (reach-driven). Own cable tower on the
# left with the pulley on the face towards the body, so the cable runs straight from pulley to handle without crossing any upright.
HKP_B = dict(T=180, S=180, H=180, N=180, legL=[0, 8, -90, 8, -80], legR=[90, 8, 0, 8])
HKP_IN, HKP_OUT = [14, 22, 102, -52], [88, 4, 88, -6]
HKP_TY = 0.95   # tower centre y (left of the body)
def hkp_props(J, J0, *a):
    mat("mat", J0); x, z = J0["hands"].x + 0.21, J0["hands"].z; y = HKP_TY
    for k, dx in enumerate((-0.14, 0.14)): tube(f"hkp_up{k}", (x + dx, y, 0), (x + dx, y, 2.2), 0.04)
    box("hkp_cap", (x, y, 2.2), (0.38, 0.16, 0.08), "frame"); box("hkp_base", (x, y, 0.04), (0.5, 0.5, 0.08), "frame")
    box("hkp_carriage", (x, y - 0.03, z), (0.22, 0.10, 0.16), "steel"); stack("hkp_stack", x, y + 0.26, 2.15, top_pulley=False)
    p = pulley("hkp_pul", (x, y - 0.10, z), (0, 0, 1))
    cable("hkp_cab", p, J["hands"]); d_handle("hkp_dh", J["hands"], (0, 0, 1))
_t("hk-pallof").update(keys=[P(**HKP_B, armL=HKP_IN, armR=HKP_IN, reach=PALLOF_IN), P(**HKP_B, armL=HKP_OUT, armR=HKP_OUT, reach=PALLOF_OUT)],
                       props=hkp_props, hands="grip", cam=dict(az=-38, el=10))

# ---------- QA fix: cable-hip-abd ----------
# Standing side-on to a cable tower (on the figure's left, +Y): left hand on the front post, torso upright, right leg (cuffed, far from the tower) abducts straight out ~38 deg and back; low pulley -> cable straight to the cuff D-ring.
CHA_ARM = dict(armL=[28, 40, 50, 40], armR=[4, 10, 6, 8])
CHA_STAND = dict(T=180, legL=[0, 3, 0, 3], **CHA_ARM)
def _cha_props(J, J0, *a):
    h0 = J0["hand_l"]; xt, y0, pz = h0.x - 0.14, h0.y, 0.32          # tower centred behind the front post the hand grips
    for k, dx in enumerate((-0.14, 0.14)): tube(f"cha_up{k}", (xt + dx, y0, 0), (xt + dx, y0, 2.2), 0.04)
    box("cha_cap", (xt, y0, 2.2), (0.38, 0.16, 0.08), "frame"); box("cha_base", (xt - 0.05, y0 + 0.05, 0.04), (0.55, 0.55, 0.08), "frame")
    box("cha_carr", (xt, y0 - 0.04, pz), (0.22, 0.10, 0.16), "steel"); stack("cha_stack", xt, y0 + 0.24, 2.15, top_pulley=False)
    pp = V((xt + 0.30, y0 - 0.10, pz))                                   # pulley bracket reaches forward so the cable clears the standing foot
    rod("cha_arm", V((xt + 0.1, y0 - 0.04, pz)), pp, 0.02, "steel"); rod("cha_pul", pp - V((0, 0, 0.03)), pp + V((0, 0, 0.03)), 0.05, "steel")
    k, a = J["knee_r"], J["ankle_r"]; sh = (k - a).normalized(); c = a + sh * 0.07
    n = V((0, 1, 0)) - sh * sh.y; n.normalize(); ring = c + n * 0.062
    rod("cha_cuff", a + sh * 0.02, a + sh * 0.12, 0.055, "uphol"); rod("cha_ring", ring - sh * 0.02, ring + sh * 0.02, 0.014, "chrome")
    cable("cha_c", pp, ring); d_handle("cha_h", J["hand_l"], (0, 0, 1))
_t("cable-hip-abd").update(keys=[P(**CHA_STAND, legR=[0, 3, 0, 3]), P(**CHA_STAND, legR=[0, 38, 0, 38])], props=_cha_props, handL="grip", stance="stand", cam=dict(az=-38, el=10))

# ---------- QA fix: multi-hip ----------
# Facing the machine (+X), both hands on its front handlebar, torso upright, head neutral; the lever hub sits at hip height in front of the
# right hip (abduction axis runs front-to-back), its arm drops to a roller pad on the OUTSIDE of the right thigh just above the knee.
# Was: photo keys with the head bowed, the left hand gripping a floating pad and the leg swinging through a column beside the hip.
MH_GRIP = {"hand_l": ("hips", (0.40, 0.2, 0.26), "world"), "hand_r": ("hips", (0.40, -0.2, 0.26), "world")}
MH_STAND = dict(T=180, legL=[0, 3, 0, 3], **both([35, 12, 75, 10]))
def _mh_props(J, J0, *a):
    h = J0["hip_r"]; xc, yc = J0["hips"].x + 0.55, h.y; hub = V((xc - 0.12, yc, h.z))
    for k, dy in enumerate((-0.14, 0.14)): tube(f"mh_up{k}", (xc, yc + dy, 0), (xc, yc + dy, 1.9), 0.04)
    box("mh_cap", (xc, yc, 1.9), (0.16, 0.38, 0.08), "frame"); box("mh_base", (xc + 0.1, yc, 0.04), (0.6, 0.6, 0.08), "frame")
    stack("mh_stack", xc + 0.24, yc, 1.85, top_pulley=False); box("mh_hub", hub + V((0.06, 0, 0)), (0.12, 0.16, 0.16), "steel")
    zb = J0["hips"].z + 0.26; xb = J0["hips"].x + 0.40
    rod("mh_bar", V((xb, 0.26, zb)), V((xb, -0.26, zb)), 0.02, "steel")
    for k, y in enumerate((0.26, -0.26)): tube(f"mh_bar{k}", (xb, y, zb), (xc, yc + (0.14 if y > 0 else -0.14), zb), 0.025)
    k_, hp = J["knee_r"], J["hip_r"]; th = (k_ - hp).normalized(); n = V((0, -1, 0)) - th * th.y; n.normalize()
    c = k_ - th * 0.12 + n * 0.09                                          # pad centre: outside of the thigh, just above the knee
    rod("mh_pad", c - th * 0.1, c + th * 0.1, 0.055, "uphol")
    e = V((hub.x, c.y, c.z)); tube("mh_lever", hub, e); tube("mh_lever2", e, c)
_t("multi-hip").update(keys=[P(**MH_STAND, legR=[0, 3, 0, 3]), P(**MH_STAND, legR=[0, 35, 0, 35])], props=_mh_props, hands="grip",
                       reach=MH_GRIP, stance="stand", cam=dict(az=-155, el=12))
_t("multi-hip").pop("handL", None)

# ---------- QA fix: cable-crunch ----------
# the tower (pulley at 2.1 m, stack behind it) was cropped at the top and right edge: frame the whole column like cable-bird-dog/dead-bug
_t("cable-crunch").update(prop_headroom=1.5, cam=dict(az=-70, el=8, margin=1.3))

# ---------- QA fix: glute-drive head ----------
# same N/H reads ~25 deg more extended on the female rig (chin to the ceiling at both ends): tuck hers to match; male top gets a slight extra tuck (gaze toward the knees)
_t("glute-drive")["keys"] = _SexKeys([{**k, **({"N": k["N"] - 4, "H": k["H"] - 8} if i else {}), "_f": {"N": k["N"] - 12, "H": k["H"] - 26}}
                                      for i, k in enumerate(_t("glute-drive")["keys"])])

# ---------- live-site sweep fixes (checked against the original free-exercise-db GIFs and the app's own cues) ----------
_STAND = dict(T=180, N=180, H=180, legL=[0, 5, 0, 5], legR=[0, 5, 0, 5])
# glute squeezes: an isometric squeeze, nothing visibly moves -> a single still (PNG), standing tall
_t("glute-squeeze").update(keys=[P(**_STAND, **both([4, 8, 4, 6])), P(**_STAND, **both([4, 8, 4, 6]))], still=True, anchor={}, cam=dict(az=-30, el=8))
# bottoms-up kettlebell press: ONE bell, bell above the fist; rack (upper arm down-forward, forearm vertical) -> straight overhead; free arm relaxed
_t("kb-press").update(keys=[P(**_STAND, armL=[4, 10, 4, 8], armR=[22, 28, 176, 10]), P(**_STAND, armL=[4, 10, 4, 8], armR=[172, 12, 176, 10])],
                      props=lambda J, J0, *a: kettlebell("kb_r", J["hand_r"], up=(0, 0, -1), side=(1, 0, 0)), hands=None, handR="grip", handL="relaxed",
                      anchor={}, cam=dict(az=-30, el=8))
# cable Y-raise: low pulley on the left, right hand starts in front of the left hip and rises up and out to a Y (~135 deg, scapular plane)
_t("cable-y-raise").update(keys=[P(**_STAND, armL=[4, 10, 4, 8], armR=[22, -28, 26, -26]), P(**_STAND, armL=[4, 10, 4, 8], armR=[154, 36, 156, 36])],
                           anchor={}, cam=dict(az=-10, el=8))
# seated hip abduction: head neutral against the back pad (photo landmarks hung the head forward and tilted it)
for _k in _t("abductor-machine")["keys"]: _k["fk_N"], _k["fk_H"] = 186, 184
# lying leg raise, knees bent (app cue: hold the bench behind your head; raise bent knees, lower slowly)
LLR = dict(T=270, N=268, H=264, anchor=BENCH)
LLR_HANDS = {"hand_l": ("head", (-0.13, 0.15, -0.11), "world"), "hand_r": ("head", (-0.13, -0.15, -0.11), "world")}
_t("lying-leg-raise").update(keys=[P(**LLR, **both([255, 22, 330, 10]), **legs([88, 4, 72, 4])), P(**LLR, **both([255, 22, 330, 10]), **legs([176, 4, 94, 4]))],
                             reach=LLR_HANDS, hands="grip", stance=None, cam=dict(az=-88, el=8))
# woodchop (high -> low) / cable lift (low -> high): a real diagonal, hands together on one handle, chest rotating with the arms, hips/feet square
def _chop(hi, lo):   # hi/lo: hands' world offset from the pelvis at the high and low end
    rh = lambda o: {"hand_l": ("pelvis", (o[0], o[1], o[2] - 0.035), "world"), "hand_r": ("pelvis", (o[0], o[1], o[2] + 0.035), "world")}
    sh, sl = (1 if hi[1] > 0 else -1), (1 if lo[1] > 0 else -1)
    hi_k = P(T=180, N=180, H=180, twist=34 * sh, legL=[2, 6, 0, 5], legR=[2, 6, 0, 5],
             armL=[145, 35 * sh, 150, 30 * sh], armR=[145, -35 * sh, 150, -30 * sh], reach=rh(hi))
    lo_k = P(T=160, N=158, H=158, twist=38 * sl, legL=[30, 6, -24, 5], legR=[30, 6, -24, 5],
             armL=[30, 30 * sl, 25, 30 * sl], armR=[30, -30 * sl, 25, -30 * sl], reach=rh(lo))
    return hi_k, lo_k
_hi, _lo = _chop((0.28, -0.46, 0.92), (0.40, 0.44, -0.55))
_t("woodchop").update(keys=[_hi, _lo], anchor={"x": ("ankle_r", None)}, stance=None, cam=dict(az=-12, el=8))
_hi, _lo = _chop((0.28, -0.46, 0.92), (0.40, 0.44, -0.55))
_t("cable-lift").update(keys=[_lo, _hi], anchor={"x": ("ankle_r", None)}, stance=None, cam=dict(az=-12, el=8))
_t("cable-lift")["props"] = COL_SIDE(0.95, pz=0.25)
# landmine rainbow: arms long, the sleeve end sweeps an arc hip -> over the forehead -> other hip; pelvis square, chest turns with the bar
def _rb(o, tw, arm_l, arm_r):
    return P(T=176, N=178, H=178, twist=tw, legL=[8, 8, -6, 6], legR=[8, 8, -6, 6], armL=arm_l, armR=arm_r,
             reach={"hand_l": ("pelvis", (o[0], o[1], o[2] - 0.035), "world"), "hand_r": ("pelvis", (o[0], o[1], o[2] + 0.035), "world")})
_t("landmine-rainbow").update(keys=[_rb((0.42, 0.40, 0.02), 25, [40, 30, 40, 30], [40, -10, 40, -10]), _rb((0.50, 0.0, 0.80), 0, [125, 6, 130, 6], [125, 6, 130, 6]),
                                    _rb((0.42, -0.40, 0.02), -25, [40, -10, 40, -10], [40, 30, 40, 30])],
                              pingpong=True, steps=6, anchor={"x": ("ankle_r", None)}, stance=None, cam=dict(az=-20, el=10))
_t("landmine-rainbow")["props"] = lambda J, J0, *a: landmine("lm", V((J0["pelvis"].x + 1.45, 0, 0)), J["hands"], end=True)
# elliptical: hands stay on the moving handles at chest height (one pushes while the other pulls), head up
_EP, _EL = [55, 14, 100, 10], [12, 14, 95, 10]
_EF, _EB = [30, 5, 0, 5], [-12, 5, -38, 5]   # front leg / rear leg (both feet on the pedals); torso tall, arms opposite the legs
_t("elliptical").update(keys=[P(T=178, N=182, H=182, legL=_EF, legR=_EB, armL=_EL, armR=_EP), P(T=178, N=182, H=182, legL=_EB, legR=_EF, armL=_EP, armR=_EL)],
                        anchor={}, stance=None)
# hip hinge to wall: hips travel straight back to the wall with a FLAT back and neutral neck, shins near vertical, arms hang
def _hinge(t): return P(T=t, S1=t, S2=t, S3=t, N=t + 4, H=t + 6, **both([0, 8, 0, 6]), **legs([15 if t < 170 else 2, 5, -4 if t < 170 else 0, 5]))
for _n in ("hip-hinge-wall", "loaded-hinge-wall"):
    _t(_n).update(keys=[_hinge(180), _hinge(118)], anchor={"x": ("ankle_r", None)}, stance=None, cam=dict(az=-70, el=8))
# 90/90 hip switch: front-high camera so the knees visibly drop to one side, then the other
_t("hip-switch")["cam"] = dict(az=-8, el=30)
