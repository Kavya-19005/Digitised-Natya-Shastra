from flask import Flask, request, jsonify, send_file, render_template
import cv2
import mediapipe as mp
import numpy as np
import tempfile
import os

app = Flask(__name__)
# FIX: Increase file size limit to 50MB to avoid 413 error
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

mp_pose = mp.solutions.pose
POSE_CONNECTIONS = [
    (11, 13), (13, 15), # Left arm
    (12, 14), (14, 16), # Right arm
    (11, 12), (23, 24), # Shoulders, Hips
    (11, 23), (12, 24), # Torso sides
    (23, 25), (25, 27), # Left leg
    (24, 26), (26, 28), # Right leg
]

# Helper function to convert hex color to BGR tuple for OpenCV
def hex_to_bgr(hex_color):
    """Converts a hex color string (e.g., #RRGGBB) to an OpenCV BGR tuple."""
    h = hex_color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return rgb[::-1]

def draw_stick_figure(frame, landmarks, style):
    h, w, _ = frame.shape
    
    line_color = hex_to_bgr(style.get("lineColor", "#00ff00"))
    joint_color = hex_to_bgr(style.get("jointColor", "#ff0000"))
    
    # Draw connections (lines)
    for i, j in POSE_CONNECTIONS:
        lm_i = landmarks[i]
        lm_j = landmarks[j]
        
        if lm_i.visibility > 0.5 and lm_j.visibility > 0.5:
            pt_i = (int(lm_i.x * w), int(lm_i.y * h))
            pt_j = (int(lm_j.x * w), int(lm_j.y * h))
            cv2.line(frame, pt_i, pt_j, line_color, style.get("thickness", 3))

    # Draw joints (circles)
    for lm in landmarks:
        if lm.visibility > 0.5:
            (cx, cy) = (int(lm.x * w), int(lm.y * h))
            cv2.circle(frame, (cx, cy), style.get("radius", 5), joint_color, -1)


@app.route("/")
def index():
    """Route to serve the main HTML page (Stick Figure Animator)."""
    return render_template("index.html")

# NEW ROUTE: For the Hand Gesture Recognizer
@app.route("/mudra")
def mudra_recognizer():
    """Route to serve the Hand Gesture Recognition page."""
    return render_template("mudra.html")

@app.route("/process", methods=["POST"])
def process_video():
    tmp_in_path = None
    tmp_out_path = None
    
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
            
        video_file = request.files["video"]
        
        style = {
            "lineColor": request.form.get("lineColor", "#00ff00"),
            "jointColor": request.form.get("jointColor", "#ff0000"),
            "bgColor": request.form.get("bgColor", "#000000"),
            "thickness": int(request.form.get("thickness", 3)),
            "radius": int(request.form.get("radius", 5))
        }
        
        bg_color_bgr = hex_to_bgr(style["bgColor"])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
            video_file.save(tmp_in)
            tmp_in_path = tmp_in.name

        cap = cv2.VideoCapture(tmp_in_path)
        if not cap.isOpened():
            return jsonify({"error": "Could not open video file. Check format."}), 500

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0 

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
            tmp_out_path = tmp_out.name
            
        fourcc = cv2.VideoWriter_fourcc(*'XVID') 
        out = cv2.VideoWriter(tmp_out_path, fourcc, fps, (width, height))

        with mp_pose.Pose(static_image_mode=False,
                         min_detection_confidence=0.5,
                         min_tracking_confidence=0.5) as pose:

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)

                skeleton_frame = np.full((height, width, 3), bg_color_bgr, dtype=np.uint8)

                if results.pose_landmarks:
                    draw_stick_figure(skeleton_frame, results.pose_landmarks.landmark, style)

                out.write(skeleton_frame)

        cap.release()
        out.release()
        
        if os.path.getsize(tmp_out_path) == 0:
            return jsonify({"error": "Video processing resulted in an empty file. Try a different video."}), 500

        return send_file(tmp_out_path, mimetype='video/mp4')

    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": f"Internal Server Error: {e}"}), 500
    
    finally:
        if tmp_in_path and os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        pass

if __name__ == "__main__":
    # Ensure necessary directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/models', exist_ok=True) # New models directory
    print("Starting Flask app. Go to http://127.0.0.1:5000")
    app.run(debug=True)
