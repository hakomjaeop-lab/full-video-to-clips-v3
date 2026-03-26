from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import subprocess
import shutil
import logging
import threading
import time
from werkzeug.utils import secure_filename

# إعداد السجلات (Logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
CLIPS_FOLDER = os.path.join(UPLOAD_FOLDER, "clips")

# التأكد من وجود المجلدات
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLIPS_FOLDER'] = CLIPS_FOLDER

# حالة المعالجة (In-memory state)
processing_status = {
    "is_processing": False,
    "current_clip": 0,
    "total_clips": 10,
    "message": ""
}

def get_video_duration(filepath):
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', filepath
    ]
    try:
        output = subprocess.check_output(cmd).decode().strip()
        return float(output)
    except Exception as e:
        logger.error(f"Error getting duration: {e}")
        return 0

def process_video_async(filepath):
    global processing_status
    try:
        processing_status["is_processing"] = True
        processing_status["message"] = "جاري قراءة طول الفيديو..."
        
        duration = get_video_duration(filepath)
        if duration <= 0:
            processing_status["message"] = "خطأ في قراءة طول الفيديو"
            processing_status["is_processing"] = False
            return

        clip_duration = duration / 10
        
        # تنظيف المقاطع القديمة
        if os.path.exists(app.config['CLIPS_FOLDER']):
            shutil.rmtree(app.config['CLIPS_FOLDER'])
        os.makedirs(app.config['CLIPS_FOLDER'], exist_ok=True)

        for i in range(10):
            processing_status["current_clip"] = i + 1
            processing_status["message"] = f"جاري معالجة المقطع {i+1} من 10..."
            
            start_time = i * clip_duration
            output_filename = f"clip_{i+1:02d}.mp4"
            output_path = os.path.join(app.config['CLIPS_FOLDER'], output_filename)
            
            cmd = [
                'ffmpeg', '-y', '-ss', str(start_time), '-t', str(clip_duration),
                '-i', filepath,
                '-vf', 'crop=ih*(9/16):ih,scale=720:1280',
                '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', 
                '-c:a', 'aac', '-b:a', '64k', 
                output_path
            ]
            subprocess.run(cmd, capture_output=True, text=True)

        processing_status["message"] = "تم الانتهاء من المعالجة بنجاح!"
    except Exception as e:
        logger.error(f"Processing error: {e}")
        processing_status["message"] = f"خطأ: {str(e)}"
    finally:
        processing_status["is_processing"] = False
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route("/", methods=["GET", "POST"])
def index():
    global processing_status
    if request.method == "POST":
        if processing_status["is_processing"]:
            return "هناك عملية معالجة جارية بالفعل", 400

        # التحقق من رفع ملف أو رابط يوتيوب
        youtube_url = request.form.get("youtube_url")
        if youtube_url:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], "yt_video.mp4")
            try:
                processing_status["is_processing"] = True
                processing_status["message"] = "جاري تحميل الفيديو من يوتيوب..."
                cmd = ['yt-dlp', '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4', '-o', filepath, youtube_url]
                subprocess.run(cmd, check=True)
                threading.Thread(target=process_video_async, args=(filepath,)).start()
                return redirect(url_for('index'))
            except Exception as e:
                processing_status["is_processing"] = False
                return f"خطأ في تحميل يوتيوب: {str(e)}", 500

        if 'video' in request.files:
            file = request.files['video']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                threading.Thread(target=process_video_async, args=(filepath,)).start()
                return redirect(url_for('index'))

    clips_data = []
    if os.path.exists(app.config['CLIPS_FOLDER']):
        clips = sorted([c for c in os.listdir(app.config['CLIPS_FOLDER']) if c.endswith('.mp4')])
        clips_data = [{"name": c, "url": f"uploads/clips/{c}"} for c in clips]
        
    return render_template("index.html", clips=clips_data, status=processing_status)

@app.route("/status")
def get_status():
    return jsonify(processing_status)

@app.route("/delete_all", methods=["POST"])
def delete_all():
    try:
        if os.path.exists(app.config['CLIPS_FOLDER']):
            shutil.rmtree(app.config['CLIPS_FOLDER'])
            os.makedirs(app.config['CLIPS_FOLDER'], exist_ok=True)
        return jsonify({"status": "success", "message": "تم حذف كافة المقاطع بنجاح"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
