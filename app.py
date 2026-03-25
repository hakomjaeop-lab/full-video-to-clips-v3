from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import subprocess
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
CLIPS_FOLDER = os.path.join(UPLOAD_FOLDER, "clips")

# التأكد من وجود المجلدات
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLIPS_FOLDER'] = CLIPS_FOLDER

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
        
        # تنظيف مجلد المقاطع القديم قبل البدء
        if os.path.exists(app.config['CLIPS_FOLDER']):
            shutil.rmtree(app.config['CLIPS_FOLDER'])
        os.makedirs(app.config['CLIPS_FOLDER'], exist_ok=True)
        
        # تقسيم الفيديو إلى clips صغيرة كل 30 ثانية
        # استخدام -reset_timestamps 1 لضمان توافق التوقيت في المقاطع
        cmd = f'ffmpeg -i "{filepath}" -c copy -map 0 -segment_time 30 -f segment -reset_timestamps 1 "{app.config["CLIPS_FOLDER"]}/clip%03d.mp4"'
        subprocess.call(cmd, shell=True)
        
        # حذف الفيديو الأصلي فور الانتهاء من التقسيم (المطلب الأول)
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
    """حذف كافة المقاطع (المطلب الثاني)"""
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
