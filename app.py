from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import subprocess
import shutil
import math
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
CLIPS_FOLDER = os.path.join(UPLOAD_FOLDER, "clips")

# التأكد من وجود المجلدات
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLIPS_FOLDER'] = CLIPS_FOLDER

def get_video_duration(filepath):
    """الحصول على طول الفيديو بالثواني باستخدام ffprobe"""
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filepath}"'
    try:
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        return float(output)
    except:
        return 0

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'video' not in request.files:
            return "لم يتم اختيار ملف"
        file = request.files['video']
        if file.filename == '':
            return "اسم الملف فارغ"
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 1. الحصول على طول الفيديو
        duration = get_video_duration(filepath)
        if duration <= 0:
            return "خطأ في قراءة طول الفيديو"
        
        # 2. حساب طول كل مقطع (لتقسيمه إلى 10 مقاطع)
        clip_duration = duration / 10
        
        # 3. تنظيف مجلد المقاطع القديم
        if os.path.exists(app.config['CLIPS_FOLDER']):
            shutil.rmtree(app.config['CLIPS_FOLDER'])
        os.makedirs(app.config['CLIPS_FOLDER'], exist_ok=True)
        
        # 4. تقسيم الفيديو إلى 10 مقاطع بتنسيق TikTok (9:16)
        # -vf "crop=ih*(9/16):ih,scale=1080:1920" يقوم بقص الفيديو من المنتصف وتغيير أبعاده
        for i in range(10):
            start_time = i * clip_duration
            output_filename = f"clip_{i+1:02d}.mp4"
            output_path = os.path.join(app.config['CLIPS_FOLDER'], output_filename)
            
            cmd = (
                f'ffmpeg -ss {start_time} -t {clip_duration} -i "{filepath}" '
                f'-vf "crop=ih*(9/16):ih,scale=1080:1920" '
                f'-c:v libx264 -crf 23 -preset veryfast -c:a aac -b:a 128k "{output_path}" -y'
            )
            subprocess.call(cmd, shell=True)
        
        # 5. حذف الفيديو الأصلي فور الانتهاء
        if os.path.exists(filepath):
            os.remove(filepath)
        
        clips = sorted(os.listdir(app.config['CLIPS_FOLDER']))
        clips_data = [{"name": c, "url": f"uploads/clips/{c}"} for c in clips if c.endswith('.mp4')]
        
        return render_template("index.html", clips=clips_data)

    # عرض المقاطع الموجودة حالياً إن وجدت
    clips_data = []
    if os.path.exists(app.config['CLIPS_FOLDER']):
        clips = sorted(os.listdir(app.config['CLIPS_FOLDER']))
        clips_data = [{"name": c, "url": f"uploads/clips/{c}"} for c in clips if c.endswith('.mp4')]
        
    return render_template("index.html", clips=clips_data)

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
