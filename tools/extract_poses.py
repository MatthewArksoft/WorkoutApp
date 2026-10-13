# Runs MediaPipe Pose Landmarker (heavy) on reference photos and saves 3D world landmarks + 2D image landmarks.
# Usage: <venv python> tools/extract_poses.py <frames dir> <model.task> <out.json> <overlay dir>
# Frames are free-exercise-db start/end photos named <ID>_0.jpg / <ID>_1.jpg (public domain).
import glob, json, os, sys
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
from PIL import Image, ImageDraw

frames, model, out_json, overlay = sys.argv[1:5]
os.makedirs(overlay, exist_ok=True)
opts = vision.PoseLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=model), running_mode=vision.RunningMode.IMAGE,
                                    num_poses=1, min_pose_detection_confidence=0.3, min_pose_presence_confidence=0.3)
det = vision.PoseLandmarker.create_from_options(opts)
EDGES = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
         (27, 29), (29, 31), (27, 31), (28, 30), (30, 32), (28, 32), (15, 19), (15, 17), (17, 19), (16, 20), (16, 18), (18, 20), (15, 21), (16, 22), (0, 7), (0, 8)]
res, missing = {}, []
for f in sorted(glob.glob(os.path.join(frames, "*.jpg"))):
    key = os.path.basename(f)[:-4]
    img = mp.Image.create_from_file(f)
    r = det.detect(img)
    if not r.pose_world_landmarks:
        missing.append(key); continue
    wl = [[p.x, p.y, p.z, p.visibility] for p in r.pose_world_landmarks[0]]
    il = [[p.x, p.y, p.z, p.visibility] for p in r.pose_landmarks[0]]
    res[key] = {"world": wl, "img": il, "w": img.width, "h": img.height}
    im = Image.open(f).convert("RGB"); d = ImageDraw.Draw(im)
    pts = [(p[0] * im.width, p[1] * im.height) for p in il]
    for a, b in EDGES:
        col = (255, 60, 60) if a % 2 else (60, 160, 255)     # odd = left side (red), even = right (blue)
        d.line([pts[a], pts[b]], fill=col, width=4)
    for p in pts: d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=(255, 255, 0))
    im.thumbnail((480, 320)); im.save(os.path.join(overlay, key + ".jpg"), quality=85)
json.dump(res, open(out_json, "w"))
print(json.dumps({"detected": len(res), "missing": missing}))
