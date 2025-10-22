from flask import Flask, request, jsonify, send_file
import cv2
import mediapipe as mp
import numpy as np
import tempfile
import os
from flask_cors import CORS   # ✅ add this

app = Flask(__name__)
CORS(app)   # ✅ enable CORS for all routes

mp_pose = mp.solutions.pose
POSE_CONNECTIONS = [
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 12), (23, 24),
    (11, 23), (12, 24),
    (23, 25), (25, 27),
    (24, 26), (26, 28),
]

def draw_stick_figure(frame, landmarks, style):
    h, w, _ = frame.shape
    points = [(int(lm[0] * w), int(lm[1] * h)) for lm in landmarks]

    # joints
    for (cx, cy) in points:
        cv2.circle(frame, (cx, cy), style["radius"], style["joint_color"], -1)

    # connections
    for i, j in POSE_CONNECTIONS:
        cv2.line(frame, points[i], points[j], style["line_color"], style["thickness"])

@app.route("/process", methods=["POST"])
def process_video():
    # 1. Get uploaded video
    video = request.files["video"]
    style = request.form.get("style")

    if style:
        style = eval(style)  # ⚠️ replace with json.loads in production
    else:
        style = {
            "line_color": (0, 255, 0),
            "joint_color": (0, 0, 255),
            "thickness": 3,
            "radius": 5,
            "bg_color": (0, 0, 0)
        }

    # Save temp video
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    video.save(tmp_in.name)

    cap = cv2.VideoCapture(tmp_in.name)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    out = cv2.VideoWriter(tmp_out.name,
                          cv2.VideoWriter_fourcc(*"mp4v"),
                          fps, (width, height))

    with mp_pose.Pose(static_image_mode=False,
                      min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            skeleton_frame = np.full_like(frame, style["bg_color"], dtype=np.uint8)

            if results.pose_landmarks:
                landmarks = [[lm.x, lm.y] for lm in results.pose_landmarks.landmark]
                draw_stick_figure(skeleton_frame, landmarks, style)

            out.write(skeleton_frame)

    cap.release()
    out.release()

    return send_file(tmp_out.name, as_attachment=True, download_name="stick_figure.mp4")

if __name__ == "__main__":
    app.run(debug=True)
