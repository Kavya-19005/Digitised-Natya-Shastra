import tkinter as tk
from tkinter import filedialog, colorchooser, ttk
import cv2
import mediapipe as mp
import numpy as np
import threading

mp_pose = mp.solutions.pose

POSE_CONNECTIONS = [
    (11, 13), (13, 15),   # left arm
    (12, 14), (14, 16),   # right arm
    (11, 12),             # shoulders
    (23, 24),             # hips
    (11, 23), (12, 24),   # torso
    (23, 25), (25, 27),   # left leg
    (24, 26), (26, 28),   # right leg
]

# Default style
style = {
    "line_color": (0, 255, 0),
    "joint_color": (0, 0, 255),
    "thickness": 3,
    "radius": 5,
    "bg_color": (0, 0, 0)
}

video_path = None

# ---- Functions ----
def choose_video():
    global video_path
    video_path = filedialog.askopenfilename(title="Select Video",
                                            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
    if video_path:
        status_label.config(text=f"Selected: {video_path.split('/')[-1]}")

def choose_color(key):
    color = colorchooser.askcolor()[0]
    if color:
        style[key] = tuple(int(c) for c in color)

def draw_stick_figure(frame, landmarks):
    h, w, _ = frame.shape
    points = [(int(lm[0] * w), int(lm[1] * h)) for lm in landmarks]

    # Draw joints
    for (cx, cy) in points:
        cv2.circle(frame, (cx, cy), style["radius"], style["joint_color"], -1)

    # Draw connections
    for i, j in POSE_CONNECTIONS:
        cv2.line(frame, points[i], points[j], style["line_color"], style["thickness"])

def process_video():
    if not video_path:
        status_label.config(text="❌ Please select a video first")
        return

    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    out = cv2.VideoWriter("custom_stick_figure.mp4",
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
                draw_stick_figure(skeleton_frame, landmarks)

            cv2.imshow("Stick Figure Preview", skeleton_frame)
            out.write(skeleton_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    status_label.config(text="✅ Stick figure video saved as custom_stick_figure.mp4")

# Run processing in a thread to avoid freezing GUI
def start_processing():
    threading.Thread(target=process_video).start()

# ---- GUI Setup ----
root = tk.Tk()
root.title("Custom Stick Figure Animator")

tk.Button(root, text="Upload Video", command=choose_video).pack(pady=5)
tk.Button(root, text="Choose Line Color", command=lambda: choose_color("line_color")).pack(pady=5)
tk.Button(root, text="Choose Joint Color", command=lambda: choose_color("joint_color")).pack(pady=5)
tk.Button(root, text="Choose Background Color", command=lambda: choose_color("bg_color")).pack(pady=5)

tk.Label(root, text="Line Thickness").pack()
thickness_slider = tk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL)
thickness_slider.set(style["thickness"])
thickness_slider.pack()

tk.Label(root, text="Joint Radius").pack()
radius_slider = tk.Scale(root, from_=1, to=20, orient=tk.HORIZONTAL)
radius_slider.set(style["radius"])
radius_slider.pack()

status_label = tk.Label(root, text="Select a video to start")
status_label.pack(pady=10)

tk.Button(root, text="Generate Stick Figure Video", command=lambda: [style.update({"thickness": thickness_slider.get(),
                                                                               "radius": radius_slider.get()}),
                                                                    start_processing()]).pack(pady=10)

root.mainloop()
