import cv2
import mediapipe as mp
import json
import numpy as np

mp_pose = mp.solutions.pose

# Open video
cap = cv2.VideoCapture(r"C:\Users\kavya\Desktop\Programming\Natya Shastra\Video_test1.mp4")

pose = mp_pose.Pose()

landmarks_data = []

frame_index = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        frame_landmarks = []
        for lm in results.pose_landmarks.landmark:
            frame_landmarks.append([lm.x, lm.y])  # normalized coords (0-1)
        
        landmarks_data.append({
            "frame": frame_index,
            "landmarks": frame_landmarks
        })
    
    frame_index += 1

cap.release()

# Save to JSON
with open("dance_landmarks.json", "w") as f:
    json.dump(landmarks_data, f)

print("Pose landmarks saved to dance_landmarks.json")

import cv2
import json

# Load saved landmarks
with open("dance_landmarks.json", "r") as f:
    landmarks_data = json.load(f)

# Define connections (MediaPipe simplified)
POSE_CONNECTIONS = [
    (11, 13), (13, 15),   # left arm
    (12, 14), (14, 16),   # right arm
    (11, 12),             # shoulders
    (23, 24),             # hips
    (11, 23), (12, 24),   # torso
    (23, 25), (25, 27),   # left leg
    (24, 26), (26, 28),   # right leg
]

# Canvas size
width, height = 640, 480

for frame_data in landmarks_data:
    frame = 255 * np.ones((height, width, 3), dtype=np.uint8)  # white background
    points = []

    for lm in frame_data["landmarks"]:
        cx, cy = int(lm[0] * width), int(lm[1] * height)
        points.append((cx, cy))

    # Draw joints
    for (cx, cy) in points:
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    # Draw connections
    for (i, j) in POSE_CONNECTIONS:
        cv2.line(frame, points[i], points[j], (0, 255, 0), 3)

    cv2.imshow("Stick Figure Animation", frame)

    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
