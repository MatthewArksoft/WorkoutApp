# Parametric gym equipment for the demo renders (loaded after rig.py / exercises.py into the same namespace).
# Every builder takes the current joints J and the first-key joints J0 and is called each frame, so static frames are
# built from J0 (they never move) and moving parts (handles, pads, pedals, seats on rails) follow J.
# Coordinates: the body faces +X, its left is +Y, Z is up.
from mathutils import Vector as V, Matrix
import math

def tube(n, a, b, r=0.03, c="frame"): return rod(n, V(a), V(b), r, c)
def pad(n, center, size, pitch=0.0, yaw=0.0, c="uphol"): return box(n, center, size, c, pitch, yaw)
def foot_base(n, x0, x1, y=0.0, w=0.6):
    box(n + "_a", ((x0 + x1) / 2, y, 0.035), (abs(x1 - x0), 0.09, 0.07), "frame")
    box(n + "_b", (x0, y, 0.035), (0.09, w, 0.07), "frame"); box(n + "_c", (x1, y, 0.035), (0.09, w, 0.07), "frame")

def stack(n, x, y, h=1.75, top_pulley=True):
    """Weight stack: two chrome guide rods, plates, top plate, pulley housing."""
    box(n + "_shroud_b", (x, y, 0.06), (0.32, 0.30, 0.12), "frame")
    for k, dy in enumerate((-0.07, 0.07)): tube(n + f"_guide{k}", (x, y + dy, 0.12), (x, y + dy, h - 0.12), 0.011, "chrome")
    for i in range(12):                                      # individual stack plates with a small gap
        box(n + f"_pl{i}", (x, y, 0.14 + i * 0.034), (0.26, 0.20, 0.028), "plate")
    box(n + "_top", (x, y, 0.56), (0.24, 0.18, 0.04), "steel")
    rod(n + "_pin", V((x - 0.09, y, 0.14 + 7 * 0.034)), V((x - 0.17, y, 0.14 + 7 * 0.034)), 0.008, "chrome")
    rod(n + "_pinhead", V((x - 0.17, y, 0.14 + 7 * 0.034)), V((x - 0.19, y, 0.14 + 7 * 0.034)), 0.016, "accent")
    rod(n + "_rod", V((x, y, 0.12)), V((x, y, 0.6)), 0.007, "chrome")
    box(n + "_cap", (x, y, h - 0.06), (0.32, 0.30, 0.12), "frame")
    for k, dx in enumerate((-0.19, 0.19)): tube(n + f"_post{k}", (x + dx, y, 0.0), (x + dx, y, h), 0.035)
    if top_pulley: rod(n + "_pul", V((x, y - 0.03, h + 0.04)), V((x, y + 0.03, h + 0.04)), 0.06, "steel")
    return V((x, y, h + 0.04))

def pulley(n, p, axis=(0, 1, 0)):
    p = V(p); ax = V(axis).normalized() * 0.025
    rod(n, p - ax, p + ax, 0.055, "steel"); rod(n + "_hub", p - ax * 1.4, p + ax * 1.4, 0.015, "chrome")
    return p

def cable(n, *pts):
    for i in range(len(pts) - 1): rod(f"{n}_{i}", V(pts[i]), V(pts[i + 1]), 0.006, "cable")

def handle_bar(n, a, b, r=0.016):
    a, b = V(a), V(b); rod(n, a, b, r, "chrome")
    rod(n + "_g1", a + (b - a) * 0.0, a + (b - a) * 0.22, r * 1.35, "rubber"); rod(n + "_g2", a + (b - a) * 0.78, b, r * 1.35, "rubber")

def d_handle(n, p, axis):
    p = V(p); ax = V(axis).normalized() * 0.065; rod(n, p - ax, p + ax, 0.017, "rubber")

def seat_pad(n, J0, kind="seat", h=None, depth=0.40, width=0.38, back=None, back_pitch=-12):
    """Seat under the hips (top at the body's seat contact); optional back pad (back_pitch deg from vertical)."""
    hips = J0["hips"]; top = h if h is not None else region_low("seat")
    pad(n, (hips.x - 0.03, 0, top - 0.04), (depth, width, 0.08))
    tube(n + "_post", (hips.x - 0.03, 0, 0.07), (hips.x - 0.03, 0, top - 0.08), 0.04)
    if back:
        c = V((hips.x - 0.20, 0, top + 0.30)); pad(n + "_back", c, (0.08, width, back), pitch=back_pitch)
        tube(n + "_bpost", (hips.x - 0.27, 0, 0.07), (hips.x - 0.27, 0, top + 0.10), 0.035)
    return top

def flat_bench(n, x0, x1, top, y=0.0, w=0.30):
    pad(n, ((x0 + x1) / 2, y, top - 0.045), (abs(x1 - x0), w, 0.09))
    for k, x in enumerate((min(x0, x1) + 0.12, max(x0, x1) - 0.12)):
        tube(n + f"_leg{k}", (x, y, 0.04), (x, y, top - 0.09), 0.03)
        box(n + f"_foot{k}", (x, y, 0.025), (0.08, w + 0.12, 0.05), "frame")
    tube(n + "_rail", (min(x0, x1) + 0.12, y, 0.08), (max(x0, x1) - 0.12, y, 0.08), 0.03)

def incline_bench(n, J0, angle, seat_x, seat_top=0.46, back_len=0.95, w=0.30, under="back"):
    """Adjustable bench: seat + back pad at `angle` deg above horizontal, back pad rising toward -X from the seat."""
    pad(n + "_seat", (seat_x, 0, seat_top - 0.045), (0.36, w, 0.09))
    a = math.radians(angle); d_ = V((-math.cos(a), 0, math.sin(a)))
    c = V((seat_x - 0.2, 0, seat_top)) + d_ * (back_len / 2) + V((math.sin(a), 0, math.cos(a))) * -0.045
    pad(n + "_back", c, (back_len, w, 0.09), pitch=angle)
    tube(n + "_spine", (seat_x + 0.25, 0, 0.06), (seat_x - 0.75, 0, 0.06), 0.035)
    tube(n + "_strut", (seat_x - 0.35, 0, 0.06), c + V((math.sin(a), 0, math.cos(a))) * -0.12, 0.03)
    tube(n + "_spost", (seat_x, 0, 0.06), (seat_x, 0, seat_top - 0.09), 0.035)
    for k, x in enumerate((seat_x + 0.25, seat_x - 0.75)): box(n + f"_foot{k}", (x, 0, 0.025), (0.08, 0.42, 0.05), "frame")

def chest_down_incline(n, J0, angle=40):
    """Incline bench for chest-supported work: the pad lies under the chest, seat under the hips/knees."""
    sh, hp = J0["shoulders"], J0["hips"]
    a = math.radians(angle); up = V((math.cos(a), 0, math.sin(a)))
    nrm = V((math.sin(a), 0, -math.cos(a)))                        # pad normal, pointing down/forward under the chest
    c = (sh + hp) / 2 + nrm * 0.15
    pad(n + "_pad", c, (0.95, 0.30, 0.09), pitch=-angle)
    low = c - up * 0.48
    tube(n + "_post", (low.x, 0, 0.06), low, 0.04); tube(n + "_strut", (c.x + 0.2, 0, 0.06), c + up * 0.2 + nrm * 0.05, 0.03)
    foot_base(n + "_base", low.x - 0.35, c.x + 0.35)

def slab(n, a, b, width, thick, normal_hint=(0, 0, 1), c="uphol", extend=0.1):
    """Box spanning a->b (e.g. a back pad along the spine), `width` across Y-ish, `thick` along the normal."""
    a, b = V(a), V(b); ax = (b - a); L = ax.length + 2 * extend; ax.normalize()
    side = V((0, 1, 0)); nrm = ax.cross(side).normalized()
    if nrm.dot(V(normal_hint)) < 0: nrm = -nrm
    side = nrm.cross(ax).normalized()
    o = box(n, (a + b) / 2, (L, width, thick), c)
    o.rotation_quaternion = Matrix((ax, side, nrm)).transposed().to_quaternion()
    return o

def mat(n, J0, length=1.9):
    box(n, (J0["pelvis"].x, 0, 0.006), (length, 0.68, 0.012), "mat")

def wall(n, x, z=1.2, h=2.4, w=2.4, y=0.0):
    box(n, (x, y, z), (0.12, w, h), "wall")

def door(n, x, y=0.0):
    box(n + "_l", (x, y + 0.45, 1.05), (0.12, 0.08, 2.1), "wood"); box(n + "_r", (x, y - 0.45, 1.05), (0.12, 0.08, 2.1), "wood")
    box(n + "_top", (x, y, 2.12), (0.12, 0.98, 0.08), "wood"); box(n + "_door", (x + 0.02, y, 1.03), (0.045, 0.82, 2.04), "wood")
    rod(n + "_knob1", V((x - 0.04, y - 0.33, 1.0)), V((x + 0.08, y - 0.33, 1.0)), 0.025, "chrome")

def chair(n, J0, top=None, back=True):
    hips = J0["hips"]; top = top or region_low("seat")
    box(n + "_seat", (hips.x - 0.02, 0, top - 0.025), (0.44, 0.44, 0.05), "wood")
    for k, (dx, dy) in enumerate(((0.18, 0.18), (0.18, -0.18), (-0.2, 0.18), (-0.2, -0.18))):
        tube(n + f"_leg{k}", (hips.x - 0.02 + dx, dy, 0.0), (hips.x - 0.02 + dx, dy, top - 0.05), 0.018, "steel")
    if back: box(n + "_back", (hips.x - 0.23, 0, top + 0.25), (0.04, 0.42, 0.4), "wood")
    return top

def box_step(n, x, h, y=0.0, d_=0.42, w=0.5):
    box(n, (x, y, h / 2), (d_, w, h), "wood")

def stairs(n, x0, rise=0.18, run=0.28, steps=3, w=1.0):
    for i in range(steps):
        box(f"{n}_{i}", (x0 + run * (i + 0.5), 0, rise * (i + 1) / 2), (run, w, rise * (i + 1)), "wood")

def roller(n, p, axis=(0, 1, 0), length=0.9, r=0.075):
    p = V(p); ax = V(axis).normalized() * length / 2; rod(n, p - ax, p + ax, r, "foam")

def swiss_ball(n, p, r=0.33): ball(n, V(p), r, "ball")

def landmine(n, floor_pt, hand, end=False, plate=True):
    """Landmine bar from a floor pivot to the hands. end=True: the hands hold the sleeve end (press, pallof, rainbow), so a
    10 kg plate sits just below them toward the pivot; otherwise (row) the handle is under the bar and the plates are beyond."""
    floor_pt, hand = V(floor_pt), V(hand); u = (hand - floor_pt).normalized()
    box(n + "_base", floor_pt + V((0, 0, 0.03)), (0.25, 0.25, 0.06), "frame")
    rod(n + "_bar", floor_pt + V((0, 0, 0.06)), hand, 0.022, "chrome")
    if end:
        rod(n + "_sleeve", hand - u * 0.36, hand + u * 0.03, 0.025, "steel"); c, r = hand - u * 0.25, 0.13   # 5 kg plate
    else:
        rod(n + "_sleeve", hand, hand + u * 0.18, 0.025, "steel"); c, r = hand + u * 0.18, 0.2
    if plate: plate_between(n + "_plate", c - u * 0.025, c + u * 0.025, r)
    else: rod(n + "_collar", hand - u * 0.36, hand - u * 0.33, 0.04, "steel")      # unloaded: just the collar

def trap_bar(n, J):
    """Hex trap bar: hexagonal frame around the lifter, neutral handles in the hands, sleeves with plates out to the sides."""
    hl, hr = J["hand_l"], J["hand_r"]; c = (hl + hr) / 2
    fwd = (hl - hr).cross(V((0, 0, 1))).normalized(); lat = (hl - hr).normalized()
    hw = max((hl - hr).length / 2, 0.24)
    pts = [c + fwd * 0.48, c + fwd * 0.22 + lat * (hw + 0.05), c - fwd * 0.22 + lat * (hw + 0.05), c - fwd * 0.48,
           c - fwd * 0.22 - lat * (hw + 0.05), c + fwd * 0.22 - lat * (hw + 0.05)]
    for k in range(6): rod(n + f"_hex{k}", pts[k], pts[(k + 1) % 6], 0.016, "chrome")
    for s_, sg in (("l", 1), ("r", -1)):
        h = J["hand_" + s_]
        rod(n + "_hdl" + s_, h - fwd * 0.09, h + fwd * 0.09, 0.017, "chrome")
        rod(n + "_k" + s_, h - fwd * 0.055, h + fwd * 0.055, 0.0175, "steel")
        rod(n + "_st" + s_, h - fwd * 0.09, c - fwd * 0.22 + lat * sg * (hw + 0.05), 0.016, "chrome")
        rod(n + "_st2" + s_, h + fwd * 0.09, c + fwd * 0.22 + lat * sg * (hw + 0.05), 0.016, "chrome")
        base = c + lat * sg * (hw + 0.05)
        rod(n + "_sl" + s_, base, base + lat * sg * 0.36, 0.025, "chrome")
        plate(n + "_pa" + s_, base + lat * sg * 0.14, lat)
        plate(n + "_pb" + s_, base + lat * sg * 0.195, lat, 0.165, 0.035)

def ankle_weight(n, J, s): rod(n, J["ankle_" + s] + V((0, 0.06 if s == "l" else -0.06, 0.05)), J["ankle_" + s] + V((0, -0.06 if s == "l" else 0.06, 0.05)), 0.055, "uphol")

def backpack(n, J, front=False):
    """Rucksack on the back (or chest): padded body, front pocket, shoulder straps over both shoulders."""
    fwd, left, up = body_frame(J)
    b = fwd if front else -fwd
    c = J["chest"] + b * 0.2 - up * 0.18
    box(n, c, (0.18, 0.32, 0.42), "pack", *_pitch_yaw(b, up))
    box(n + "_pocket", c + b * 0.1 - up * 0.07, (0.05, 0.24, 0.2), "pack", *_pitch_yaw(b, up))
    box(n + "_zip", c + b * 0.126 - up * 0.07 + up * 0.1, (0.006, 0.2, 0.012), "accent", *_pitch_yaw(b, up))
    for s, sg in (("l", 1), ("r", -1)):
        sh = J["shoulder_" + s] - left * sg * 0.03
        top, front_ = sh + up * 0.08 - b * 0.02, sh - b * 0.13 - up * 0.02
        rod(n + "_st" + s + "0", c + b * -0.08 + up * 0.19 + left * sg * 0.08, top, 0.018, "uphol")
        rod(n + "_st" + s + "1", top, front_, 0.018, "uphol")
        rod(n + "_st" + s + "2", front_, front_ - up * 0.24 + b * 0.04, 0.018, "uphol")

def _pitch_yaw(f, up):
    """box() angles that align a box's +X with the horizontal part of f."""
    import math
    return 0.0, math.degrees(math.atan2(f.y, f.x))

def shopping_bag(n, hand, out=V((0, 0, 0))):
    """Paper carrier bag hanging from the hand: body below (shifted `out` so it clears the leg), rope handles to the grip."""
    top = hand - V((0, 0, 0.16)) + out
    box(n, top - V((0, 0, 0.17)), (0.30, 0.12, 0.34), "bag")
    for k, dx in enumerate((-0.07, 0.07)):
        rod(n + f"_h{k}", top + V((dx, 0, 0)), hand, 0.006, "uphol")

def mini_band(n, a, b): rod(n, V(a), V(b), 0.018, "band")

# ---------------- machines ----------------
def cable_column(n, x, y, pulley_z, h=2.2):
    """Single cable tower with an adjustable pulley carriage; returns the pulley point."""
    for k, dy in enumerate((-0.14, 0.14)): tube(n + f"_up{k}", (x, y + dy, 0), (x, y + dy, h), 0.04)
    box(n + "_cap", (x, y, h), (0.16, 0.38, 0.08), "frame"); box(n + "_base", (x, y, 0.04), (0.5, 0.5, 0.08), "frame")
    box(n + "_carriage", (x - 0.03, y, pulley_z), (0.10, 0.22, 0.16), "steel")
    stack(n + "_stack", x + 0.24, y, h - 0.05, top_pulley=False)
    return pulley(n + "_pul", (x - 0.09, y, pulley_z), (0, 0, 1))

def lat_machine(n, J0, J, bar="wide", seat_top=None):
    top = seat_pad(n + "_seat", J0, h=seat_top)
    kn = (J0["knee_l"] + J0["knee_r"]) / 2
    rod(n + "_thighpad", V((kn.x - 0.02, 0.22, kn.z + 0.11)), V((kn.x - 0.02, -0.22, kn.z + 0.11)), 0.06, "uphol")
    tube(n + "_padpost", (kn.x + 0.12, 0, 0.07), (kn.x + 0.12, 0, kn.z + 0.11), 0.035)
    cx = J0["hips"].x + 0.62
    tube(n + "_col", (cx, 0, 0), (cx, 0, 2.45), 0.05); foot_base(n + "_base", J0["hips"].x - 0.3, cx + 0.3)
    hx = J0["hands"].x
    tube(n + "_beam", (cx, 0, 2.42), (hx - 0.05, 0, 2.42), 0.045)
    p = pulley(n + "_pul", (hx, 0, 2.38))
    stack(n + "_stack", cx + 0.25, 0, 2.2)
    cable(n + "_cab", p, J["hands"] + V((0, 0, 0.05)))
    if bar == "wide": handle_bar(n + "_bar", J["hand_l"] + V((0, 0.16, 0.0)), J["hand_r"] + V((0, -0.16, 0.0)))
    elif bar == "single": d_handle(n + "_h", J["hand_r"], (0, 1, 0))
    else: handle_bar(n + "_bar", J["hand_l"] + V((0, 0.05, 0)), J["hand_r"] + V((0, -0.05, 0)))

def low_row_machine(n, J0, J, handle="v", single=False):
    hips = J0["hips"]
    top = region_low("seat")
    pad(n + "_bench", (hips.x + 0.1, 0, top - 0.05), (1.3, 0.34, 0.1))
    for k, x in enumerate((hips.x - 0.45, hips.x + 0.65)): tube(n + f"_leg{k}", (x, 0, 0.04), (x, 0, top - 0.1), 0.035)
    an = (J0["ankle_l"] + J0["ankle_r"]) / 2
    box(n + "_foot", (an.x + 0.07, 0, an.z + 0.02), (0.05, 0.62, 0.3), "steel", pitch=-20)
    cx = an.x + 0.45
    s = J0["hand_r"] if single else J0["hands"]
    p = cable_column(n + "_tower", cx, s.y if single else 0.0, s.z)
    hand = J["hand_r"] if single else J["hands"]
    cable(n + "_cab", p, hand + V((0.06, 0, 0)))
    if single: d_handle(n + "_h", J["hand_r"], (0, 0, 1))
    elif handle == "v":
        rod(n + "_v1", J["hand_l"], J["hands"] + V((0.08, 0, 0)), 0.014, "chrome"); rod(n + "_v2", J["hand_r"], J["hands"] + V((0.08, 0, 0)), 0.014, "chrome")
    else: handle_bar(n + "_bar", J["hand_l"] + V((0, 0.12, 0)), J["hand_r"] + V((0, -0.12, 0)))

def lever_machine(n, J0, J, kind="row", seat_top=None, chest_pad=True, back_pad=False, pivot_dx=0.45, pivot_z=None):
    """Lever machines. kind 'row' (iso/chest-supported row): levers hang from a pivot above-front, handles at the bottom,
    plate horns on the levers. 'high_row': pivot above-front, handles high. 'press_back' (chest / shoulder press):
    selectorized, levers swing from a pivot behind the shoulders to the handles, weight stack behind the seat."""
    hips, ch, sh = J0["hips"], J0["chest"], J0["shoulders"]
    top = seat_pad(n + "_seat", J0, h=seat_top, back=0.66 if back_pad else None, back_pitch=-14)
    foot_base(n + "_base", hips.x - 0.55, hips.x + 0.85, w=0.9)
    if kind in ("row", "high_row"):
        if chest_pad:
            pad(n + "_chest", (ch.x + 0.17, 0, ch.z - 0.1), (0.1, 0.36, 0.42), pitch=6)
            tube(n + "_cpost", (ch.x + 0.24, 0, 0.07), (ch.x + 0.24, 0, ch.z - 0.25), 0.04)
        pz = (pivot_z if pivot_z is not None else max(sh.z, J0["hands"].z) + 0.45)
        for s, sg in (("l", 1), ("r", -1)):
            piv = V((hips.x + pivot_dx + 0.15, sg * 0.36, pz)); hnd = J["hand_" + s]
            tube(n + f"_up{s}", (piv.x + 0.05, sg * 0.36, 0.06), piv + V((0.05, 0, 0.05)), 0.045)
            rod(n + f"_axle{s}", piv - V((0, 0.05, 0)), piv + V((0, 0.05, 0)), 0.05, "steel")
            tube(n + f"_lever{s}", piv, hnd + V((0.02, sg * 0.06, 0)), 0.035)
            d_handle(n + f"_h{s}", hnd, (0, 0, 1) if kind == "row" else (0, sg, 0))
            dirl = (hnd - piv).normalized(); horn = hnd + dirl * 0.06 + V((0, sg * 0.1, 0))
            tube(n + f"_horn{s}", horn, horn + V((0, sg * 0.2, 0)), 0.025, "chrome")
            plate_between(n + f"_plt{s}", horn + V((0, sg * 0.06, 0)), horn + V((0, sg * 0.12, 0)), 0.2)
        tube(n + "_crossbar", (hips.x + pivot_dx + 0.2, 0.36, pz + 0.05), (hips.x + pivot_dx + 0.2, -0.36, pz + 0.05), 0.04)
    else:
        pz = sh.z + 0.12
        for s, sg in (("l", 1), ("r", -1)):
            piv = V((sh.x - 0.22, sg * 0.42, pz)); hnd = J["hand_" + s]
            tube(n + f"_up{s}", (sh.x - 0.25, sg * 0.42, 0.06), piv, 0.045)
            rod(n + f"_axle{s}", piv - V((0, 0.05, 0)), piv + V((0, 0.05, 0)), 0.05, "steel")
            mid_ = piv + V((0.25, 0, 0.12)) if kind == "press_back" and J0["hands"].z < sh.z + 0.2 else piv + V((0.1, 0, 0.25))
            tube(n + f"_lever{s}", piv, mid_, 0.035); tube(n + f"_lever2{s}", mid_, hnd + V((0, sg * 0.06, 0)), 0.035)
            d_handle(n + f"_h{s}", hnd, (0, 0, 1))
        stack(n + "_stack", hips.x - 0.55, 0.0, 1.9)
        cable(n + "_cab", V((hips.x - 0.55, 0, 1.94)), V((sh.x - 0.25, 0, pz + 0.05)))

def tbar_machine(n, J0, J):
    chest_down_incline(n + "_bench", J0, angle=38)
    an = (J0["ankle_l"] + J0["ankle_r"]) / 2
    box(n + "_platform", (an.x, 0, max(an.z - 0.05, 0.05)), (0.42, 0.62, 0.1), "steel")
    piv = V((J0["hands"].x + 1.15, 0, 0.12)); box(n + "_pivot", piv - V((0, 0, 0.06)), (0.2, 0.2, 0.12), "frame")
    tube(n + "_lever", piv, J["hands"] + V((0.05, 0, 0.04)), 0.03, "chrome")
    handle_bar(n + "_handles", J["hand_l"] + V((0, 0.04, 0)), J["hand_r"] + V((0, -0.04, 0)))
    for k, s in enumerate((1, -1)): plate_between(n + f"_pl{k}", J["hands"] + V((0.18, s * 0.1, 0.06)), J["hands"] + V((0.18, s * 0.14, 0.06)), 0.2)

def leg_press(n, J0, J, angle=45):
    """45° sled: back pad along the trunk, seat under the hips, footplate under the feet riding on rails."""
    sh, hp = J0["shoulders"], J0["hips"]
    fwd, left, up = body_frame(J0)
    slab(n + "_back", hp - up * 0.05 - fwd * 0.13, sh - fwd * 0.13, 0.46, 0.08, normal_hint=-fwd)
    seat_pad(n + "_seat", J0)
    an = (J["ankle_l"] + J["ankle_r"]) / 2; to = (J["toe_l"] + J["toe_r"]) / 2
    sole = (to - an).normalized(); pc = (an + to) / 2
    rail = V((math.cos(math.radians(angle)), 0, math.sin(math.radians(angle))))
    nrm = -rail
    pl = pc - nrm * 0.0 + V((0, 0, 0)) + (-nrm) * 0.0
    o = box(n + "_plate", pc + rail * 0.04, (0.06, 0.72, 0.62), "steel")
    o.rotation_quaternion = Matrix((rail, V((0, 1, 0)), rail.cross(V((0, 1, 0))).normalized())).transposed().to_quaternion()
    r0 = V((hp.x + 0.25, 0, 0.12)); r1 = V((pc.x + 0.5 * rail.x, 0, pc.z + 0.5 * rail.z)) + rail * 0.4
    for k, s_ in enumerate((0.34, -0.34)):
        tube(n + f"_rail{k}", r0 + V((0, s_, 0)), r1 + V((0, s_, 0)), 0.035, "chrome")
        tube(n + f"_leg{k}", V((r1.x, s_, 0.0)), r1 + V((0, s_, 0)), 0.04)
        rod(n + f"_horn{k}", pc + rail * 0.12 + V((0, s_ * 1.2, -0.15)), pc + rail * 0.12 + V((0, s_ * 1.6, -0.15)), 0.025, "chrome")
        plate_between(n + f"_plt{k}", pc + rail * 0.12 + V((0, s_ * 1.35, -0.15)), pc + rail * 0.12 + V((0, s_ * 1.45, -0.15)), 0.21)
    foot_base(n + "_base", hp.x - 0.7, r1.x + 0.15, w=0.85)
    tube(n + "_spine", (hp.x - 0.7, 0, 0.06), (r1.x, 0, 0.06), 0.045)

def hack_squat_machine(n, J0, J):
    """Hack squat: back pad + shoulder pads ride on rails angled ~70°; footplate at the bottom."""
    fwd, left, up = body_frame(J)
    sh, hp = J["shoulders"], J["hips"]
    slab(n + "_back", hp - fwd * 0.12, sh - fwd * 0.12, 0.44, 0.08, normal_hint=-fwd)
    for s_, sg in (("l", 1), ("r", -1)):
        p = J["shoulder_" + s_] + up * 0.08 - fwd * 0.02
        rod(n + f"_shpad{s_}", p - fwd * 0.08, p + fwd * 0.1, 0.045, "uphol")
    for s_ in ("l", "r"):                                   # grips beside the shoulder pads
        h = J["hand_" + s_]
        rod(n + f"_grip{s_}", h - up * 0.07, h + up * 0.07, 0.017, "rubber")
        tube(n + f"_gripa{s_}", h - up * 0.07, J["shoulder_" + s_] + up * 0.08 - fwd * 0.1, 0.018, "frame")
    an = (J0["ankle_l"] + J0["ankle_r"]) / 2
    plate_c = V((an.x + 0.03, 0, 0.02))
    box(n + "_plate", plate_c, (0.6, 0.78, 0.04), "steel")
    # rails run parallel to the back pad, just behind it; the carriage slides along them
    f0, l0, u0 = body_frame(J0)
    b0 = J0["hips"] - f0 * 0.26
    t0, t1 = (0.12 - b0.z) / u0.z, (2.05 - b0.z) / u0.z
    lo, hi = b0 + u0 * t0, b0 + u0 * t1
    for k, s_ in enumerate((0.3, -0.3)):
        tube(n + f"_rail{k}", lo + V((0, s_, 0)), hi + V((0, s_, 0)), 0.035, "chrome")
        tube(n + f"_post{k}", hi + V((0, s_, 0)), V((hi.x, s_, 0.0)), 0.045)
        tube(n + f"_foot{k}", lo + V((0, s_, 0)), V((plate_c.x, s_, 0.04)), 0.035)
    box(n + "_cap", hi, (0.12, 0.7, 0.08), "frame")
    foot_base(n + "_base", min(plate_c.x, hi.x) - 0.3, max(plate_c.x, hi.x) + 0.35, w=0.95)

def hack_squat_old(n, J0, J):
    sh, hp = J["shoulders"], J["hips"]
    up = (sh - hp).normalized(); back = -V((up.z, 0, -up.x)) if up.x < 0 else V((-up.z, 0, up.x))
    pad(n + "_back", (sh + hp) / 2 - body_frame(J)[0] * 0.13, ((sh - hp).length + 0.35, 0.44, 0.08), pitch=-math.degrees(math.atan2(up.x, up.z)) + 90)
    for s, sg in (("l", 1), ("r", -1)): rod(n + f"_shpad{s}", J["shoulder_" + s] + V((0, 0, 0.09)), J["shoulder_" + s] + V((0.12, 0, 0.09)), 0.045, "uphol")
    an = (J0["ankle_l"] + J0["ankle_r"]) / 2
    box(n + "_plate", (an.x + 0.05, 0, 0.12), (0.6, 0.75, 0.06), "steel", pitch=-20)
    for k, s in enumerate((0.36, -0.36)): tube(n + f"_rail{k}", (an.x - 0.3, s, 0.1), (hp.x - 0.9, s, 2.0), 0.035, "chrome")
    foot_base(n + "_base", an.x - 0.3, hp.x - 0.9, w=0.9)

def leg_extension(n, J0, J):
    top = seat_pad(n + "_seat", J0, back=0.6, back_pitch=-10)
    kn = (J0["knee_l"] + J0["knee_r"]) / 2
    piv = V((kn.x, 0.3, kn.z))
    an = (J["ankle_l"] + J["ankle_r"]) / 2
    roller(n + "_shin", an + V((0.05, 0, 0.02)), length=0.42, r=0.055)
    tube(n + "_lever", piv, an + V((0.05, 0.27, 0.02)), 0.03)
    rod(n + "_axle", V((kn.x, 0.3, kn.z)), V((kn.x, 0.4, kn.z)), 0.05, "steel")
    stack(n + "_stack", J0["hips"].x - 0.35, 0.45, 1.5)
    foot_base(n + "_base", J0["hips"].x - 0.45, kn.x + 0.35)

def abductor(n, J0, J):
    top = seat_pad(n + "_seat", J0, back=0.6, back_pitch=-8)
    for s, sg in (("l", 1), ("r", -1)):
        k = J["knee_" + s]
        pad(n + f"_pad{s}", (k.x - 0.08, k.y + sg * 0.09, k.z), (0.34, 0.06, 0.16), yaw=0)
        tube(n + f"_arm{s}", (J0["hips"].x + 0.05, sg * 0.05, top - 0.12), (k.x - 0.08, k.y + sg * 0.12, k.z - 0.04), 0.03)
        an = J["ankle_" + s]; box(n + f"_peg{s}", (an.x + 0.08, an.y, an.z - 0.05), (0.18, 0.12, 0.04), "steel")
    stack(n + "_stack", J0["hips"].x - 0.42, 0.0, 1.6)
    foot_base(n + "_base", J0["hips"].x - 0.5, J0["knee_l"].x + 0.4)

def reverse_pec_deck(n, J0, J):
    top = seat_pad(n + "_seat", J0)
    ch = J0["chest"]
    pad(n + "_chest", (ch.x + 0.17, 0, ch.z - 0.1), (0.1, 0.36, 0.5), pitch=6)
    piv = V((ch.x + 0.25, 0, J0["shoulders"].z + 0.05))
    tube(n + "_col", (piv.x + 0.1, 0, 0), (piv.x + 0.1, 0, 2.0), 0.05)
    for s, sg in (("l", 1), ("r", -1)):
        h = J["hand_" + s]; tube(n + f"_arm{s}", piv, h + V((0, 0, 0.03)), 0.028); d_handle(n + f"_h{s}", h, (0, 0, 1))
    stack(n + "_stack", piv.x + 0.38, 0, 1.9)
    foot_base(n + "_base", J0["hips"].x - 0.3, piv.x + 0.55)

def smith(n, J0, J, bar_at="hands"):
    hx = J0["hands"].x if bar_at == "hands" else J0["shoulders"].x - 0.05
    for k, s in enumerate((0.62, -0.62)):
        tube(n + f"_rail{k}", (hx, s, 0), (hx, s, 2.25), 0.03, "chrome")
        tube(n + f"_post{k}", (hx - 0.15, s * 1.12, 0), (hx - 0.15, s * 1.12, 2.3), 0.045)
        tube(n + f"_post2{k}", (hx + 0.15, s * 1.12, 0), (hx + 0.15, s * 1.12, 2.3), 0.045)
    tube(n + "_top", (hx, 0.7, 2.3), (hx, -0.7, 2.3), 0.04)
    c = J["hands"] if bar_at == "hands" else J["shoulders"] + V((-0.07, 0, 0.07))
    rod(n + "_bar", V((hx, 0.75, c.z)), V((hx, -0.75, c.z)), 0.016, "chrome")
    for k, s in enumerate((0.62, -0.62)): box(n + f"_carr{k}", (hx, s, c.z), (0.08, 0.06, 0.1), "steel")
    for k, s in enumerate((0.82, -0.82)): plate_between(n + f"_pl{k}", V((hx, s - 0.03, c.z)), V((hx, s + 0.03, c.z)), 0.2)

def back_ext_bench(n, J0, J):
    hp = J0["hips"]; an = (J0["ankle_l"] + J0["ankle_r"]) / 2
    a = math.atan2(hp.z - an.z, hp.x - an.x)
    pad(n + "_hip", hp + V((0.1, 0, -0.1)), (0.12, 0.42, 0.3), pitch=-45)
    tube(n + "_frame", an + V((-0.05, 0, -0.1)), hp + V((0.06, 0, -0.22)), 0.04)
    box(n + "_footplate", an + V((0.0, 0, -0.08)), (0.26, 0.46, 0.05), "steel", pitch=-45)
    rod(n + "_heelpad", an + V((-0.09, 0.2, 0.05)), an + V((-0.09, -0.2, 0.05)), 0.045, "uphol")
    tube(n + "_leg", (hp.x + 0.06, 0, 0.05), hp + V((0.06, 0, -0.22)), 0.04)
    foot_base(n + "_base", an.x - 0.15, hp.x + 0.25, w=0.6)

def captains_chair(n, J0, J):
    hp = J0["hips"]; el = (J0["elbow_l"] + J0["elbow_r"]) / 2
    pad(n + "_back", (hp.x - 0.17, 0, hp.z + 0.35), (0.07, 0.4, 0.75))
    for s, sg in (("l", 1), ("r", -1)):
        e = J0["elbow_" + s]
        pad(n + f"_rest{s}", (e.x + 0.12, e.y + sg * 0.02, e.z - 0.07), (0.42, 0.12, 0.06))
        tube(n + f"_up{s}", (hp.x - 0.22, sg * 0.3, 0), (hp.x - 0.22, sg * 0.3, e.z + 0.1), 0.04)
        tube(n + f"_arm{s}", (hp.x - 0.22, sg * 0.3, e.z - 0.1), (e.x + 0.3, sg * 0.3, e.z - 0.1), 0.035)
        d_handle(n + f"_h{s}", J["hand_" + s], (0, 0, 1))
        tube(n + f"_front{s}", (e.x + 0.3, sg * 0.3, 0), (e.x + 0.3, sg * 0.3, e.z - 0.1), 0.035)
    box(n + "_step", (hp.x - 0.05, 0, 0.35), (0.25, 0.5, 0.05), "steel")
    foot_base(n + "_base", hp.x - 0.3, J0["elbow_l"].x + 0.4, w=0.8)

def pullup_station(n, J0, J, assisted=False):
    hx = J0["hands"].x; hz = J0["hands"].z + 0.03
    for k, s in enumerate((0.7, -0.7)):
        tube(n + f"_up{k}", (hx - 0.25, s, 0), (hx - 0.25, s, hz + 0.25), 0.05)
        tube(n + f"_arm{k}", (hx - 0.25, s, hz + 0.2), (hx + 0.05, s * 0.85, hz), 0.035)
    handle_bar(n + "_bar", V((hx, 0.62, hz)), V((hx, -0.62, hz)), 0.017)
    foot_base(n + "_base", hx - 0.6, hx + 0.4, w=1.5)
    if assisted:
        kn = (J["knee_l"] + J["knee_r"]) / 2
        pad(n + "_kneepad", kn + V((0, 0, -0.07)), (0.26, 0.42, 0.06))
        tube(n + "_kneearm", kn + V((0, 0, -0.1)), V((hx - 0.25, 0, kn.z - 0.15)), 0.03)
        stack(n + "_stack", hx - 0.55, 0, 1.6)

def treadmill(n, J0, incline=0.0):
    hp = J0["hips"]
    box(n + "_deck", (hp.x, 0, 0.09), (1.75, 0.82, 0.14), "frame", pitch=-incline)
    box(n + "_belt", (hp.x, 0, 0.165), (1.6, 0.6, 0.01), "rubber", pitch=-incline)
    fx = hp.x + 0.95
    for k, s in enumerate((0.38, -0.38)):
        tube(n + f"_up{k}", (fx, s, 0.15), (fx - 0.12, s, 1.3), 0.04)
        tube(n + f"_rail{k}", (fx - 0.12, s, 1.15), (fx - 0.55, s, 1.05), 0.025, "chrome")
    box(n + "_console", (fx - 0.12, 0, 1.35), (0.18, 0.82, 0.22), "frame", pitch=20)

def elliptical(n, J0, J):
    hp = J0["hips"]
    box(n + "_base", (hp.x, 0, 0.06), (1.7, 0.6, 0.12), "frame")
    fw = V((hp.x - 0.75, 0, 0.32)); rod(n + "_fly", fw + V((0, -0.12, 0)), fw + V((0, 0.12, 0)), 0.27, "frame")
    for s, sg in (("l", 1), ("r", -1)):
        f = (J["ankle_" + s] + J["toe_" + s]) / 2
        box(n + f"_pedal{s}", (f.x, f.y, f.z - 0.06), (0.34, 0.16, 0.04), "steel")
        tube(n + f"_link{s}", (f.x - 0.1, sg * 0.18, f.z - 0.07), fw + V((0, sg * 0.15, 0)), 0.025)
        tube(n + f"_pole{s}", (hp.x + 0.75, sg * 0.25, 0.3), J["hand_" + s] + V((0, 0, -0.05)), 0.025, "chrome")
        tube(n + f"_link2{s}", (hp.x + 0.75, sg * 0.25, 0.3), (f.x + 0.12, sg * 0.18, f.z - 0.07), 0.025)
    box(n + "_console", (hp.x + 0.8, 0, 1.35), (0.14, 0.4, 0.22), "frame", pitch=25)
    tube(n + "_mast", (hp.x + 0.8, 0, 0.1), (hp.x + 0.8, 0, 1.3), 0.045)

def rower(n, J0, J):
    hp = J0["hips"]; an = (J0["ankle_l"] + J0["ankle_r"]) / 2
    x0, x1 = hp.x - 0.9, an.x + 0.7
    box(n + "_rail", ((x0 + x1) / 2, 0, 0.28), (x1 - x0, 0.12, 0.06), "steel")
    tube(n + "_rleg", (x0 + 0.1, 0, 0.0), (x0 + 0.1, 0, 0.27), 0.035)
    box(n + "_rfoot", (x0 + 0.1, 0, 0.02), (0.08, 0.5, 0.04), "frame")
    seat_top = region_low("seat")
    box(n + "_seat", (J["hips"].x - 0.02, 0, seat_top - 0.03), (0.32, 0.28, 0.06), "uphol")
    fw = V((an.x + 0.55, 0, 0.42))
    box(n + "_housing", fw, (0.42, 0.42, 0.62), "frame")
    plate_between(n + "_fan", fw + V((0, -0.22, 0)), fw + V((0, 0.22, 0)), 0.27)
    box(n + "_footplate", (an.x + 0.06, 0, an.z), (0.06, 0.44, 0.28), "steel", pitch=-35)
    tube(n + "_mon", fw + V((0, 0, 0.3)), fw + V((-0.25, 0, 0.75)), 0.02); box(n + "_monitor", fw + V((-0.27, 0, 0.8)), (0.04, 0.2, 0.16), "frame")
    cable(n + "_chain", fw + V((-0.2, 0, 0.1)), J["hands"] + V((0.05, 0, 0)))
    handle_bar(n + "_handle", J["hand_l"] + V((0, 0.05, 0)), J["hand_r"] + V((0, -0.05, 0)))

def upright_bike(n, J0, J, air=False):
    hp = J0["hips"]; seat_top = region_low("seat")
    box(n + "_saddle", (hp.x - 0.01, 0, seat_top - 0.03), (0.27, 0.19, 0.06), "uphol")
    hz = J0["hands"]
    cr = V((hp.x + 0.22, 0, 0.36))
    tube(n + "_seat", (hp.x - 0.04, 0, seat_top - 0.06), cr, 0.04); tube(n + "_down", cr, (hz.x + 0.05, 0, 0.35), 0.04)
    tube(n + "_stem", (hz.x + 0.05, 0, 0.35), (hz.x + 0.03, 0, hz.z - 0.05), 0.04)
    if air:
        fan = V((hz.x + 0.3, 0, 0.55)); rod(n + "_fan", fan + V((0, -0.09, 0)), fan + V((0, 0.09, 0)), 0.33, "frame")
        rod(n + "_hub", fan + V((0, -0.11, 0)), fan + V((0, 0.11, 0)), 0.06, "steel")
        for s, sg in (("l", 1), ("r", -1)):
            tube(n + f"_lever{s}", (hz.x + 0.1, sg * 0.18, 0.45), J["hand_" + s] + V((0, 0, -0.06)), 0.024, "chrome")
            d_handle(n + f"_g{s}", J["hand_" + s], (0, 0, 1))
    else:
        rod(n + "_fly", V((hz.x + 0.08, -0.06, 0.38)), V((hz.x + 0.08, 0.06, 0.38)), 0.22, "frame")
        handle_bar(n + "_bars", J["hand_l"] + V((0, 0.06, 0)), J["hand_r"] + V((0, -0.06, 0)))
    box(n + "_console", (hz.x + 0.05, 0, hz.z + 0.12), (0.12, 0.24, 0.16), "frame", pitch=20)
    foot_base(n + "_base", hp.x - 0.45, hz.x + 0.4, w=0.6)
    tube(n + "_beam", (hp.x - 0.45, 0, 0.06), cr, 0.035)
    for s, sg in (("l", 1), ("r", -1)):
        f = (J["ankle_" + s] + J["toe_" + s]) / 2 + V((0, 0, -0.045))
        rod(n + f"_crank{s}", cr + V((0, sg * 0.1, 0)), f, 0.016, "steel")
        box(n + f"_pedal{s}", f, (0.11, 0.09, 0.02), "plate")

def stair_climber(n, J0, J, mill=False):
    hp = J0["hips"]
    box(n + "_body", (hp.x + 0.62, 0, 0.5), (0.22, 0.62, 1.0), "frame")
    for s, sg in (("l", 1), ("r", -1)):
        f = (J["ankle_" + s] + J["toe_" + s]) / 2
        if mill:
            for i in range(3): box(n + f"_st{s}{i}", (hp.x + 0.15 - 0.25 * i, 0, 0.2 + 0.2 * i), (0.25, 0.7, 0.05), "steel")
        else:
            box(n + f"_ped{s}", (f.x, f.y, f.z - 0.06), (0.32, 0.18, 0.04), "steel")
        tube(n + f"_rail{s}", (hp.x + 0.25, sg * 0.36, 1.05), (hp.x - 0.35, sg * 0.36, 1.05), 0.025, "chrome")
        tube(n + f"_up{s}", (hp.x + 0.55, sg * 0.36, 0.3), (hp.x + 0.25, sg * 0.36, 1.05), 0.035)
    box(n + "_console", (hp.x + 0.6, 0, 1.3), (0.14, 0.45, 0.22), "frame", pitch=25)
