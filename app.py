import os
import uuid
import subprocess
from flask import Flask, request, render_template, send_from_directory, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")



@app.route("/process", methods=["POST"])
def process():
    video = request.files.get("video")
    fps = request.form.get("fps", "600")

    if not video:
        return jsonify({"error": "No video selected"}), 400

    if fps not in ["60", "120", "240", "600"]:
        return jsonify({"error": "Invalid FPS target"}), 400

    job_id = uuid.uuid4().hex
    input_file = os.path.join(UPLOADS_DIR, f"{job_id}.mp4")
    output_file = os.path.join(OUTPUTS_DIR, f"JXDE_{fps}FPS_{job_id}.mp4")

    video.save(input_file)

    filter_string = (
        f"minterpolate="
        f"fps={fps}:"
        f"mi_mode=mci:"
        f"mc_mode=aobmc:"
        f"me_mode=bidir:"
        f"vsbmc=1"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-vf", filter_string,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        if os.path.exists(input_file):
            os.remove(input_file)
    except Exception:
        pass

    if result.returncode != 0:
        return jsonify({
            "error": "Video processing failed",
            "details": result.stderr[-2000:]
        }), 500

    return jsonify({
        "download": f"/download/{os.path.basename(output_file)}"
    })

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(
        OUTPUTS_DIR,
        filename,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)
