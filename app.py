from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import subprocess
import shutil
import math
import logging
from werkzeug.utils import secure_filename

# إعداد السجلات (Logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# استخدام مسار مطلق لضمان الوصول للمجلدات في بيئة Render
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
CLIPS_FOLDER = os.path.join(UPLOAD_FOLDER, "clips")

# التأكد من وجود المجلدات
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLIPS_FOLDER'] = CLIPS_FOLDER

def get_video_duration(filepath):
    """الحصول على طول الفيديو بالثواني باستخدام ffprobe"""
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', filepath
    ]
    try:
        output = subprocess.check_output(cmd).decode().strip()
        return float(output)
    except Exception as e:
        logger.error(f"Error getting duration for {filepath}: {e}")
        return 0

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'video' not in request.files:
            return "لم يتم اختيار ملف", 400
        file = request.files['video']
        if file.filename == '':
            return "اسم الملف فارغ", 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            logger.info(f"Saving uploaded file to {filepath}")
            file.save(filepath)
            
            # 1. الحصول على طول الفيديو
            duration = get_video_duration(filepath)
            logger.info(f"Video duration: {duration}s")
            
            if duration <= 0:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return "خطأ في قراءة طول الفيديو، تأكد من أن الملف فيديو صالح", 400
            
            # 2. حساب طول كل مقطع (لتقسيمه إلى 10 مقاطع)
            clip_duration = duration / 10
            
            # 3. تنظيف مجلد المقاطع القديم
            if os.path.exists(app.config['CLIPS_FOLDER']):
                shutil.rmtree(app.config['CLIPS_FOLDER'])
            os.makedirs(app.config['CLIPS_FOLDER'], exist_ok=True)
            
            # 4. تقسيم الفيديو إلى 10 مقاطع بتنسيق TikTok (9:16)
            for i in range(10):
                start_time = i * clip_duration
                output_filename = f"clip_{i+1:02d}.mp4"
                output_path = os.path.join(app.config['CLIPS_FOLDER'], output_filename)
                
                logger.info(f"Processing clip {i+1}/10: {output_filename}")
                
                # استخدام قائمة بدلاً من سلسلة نصية لتجنب مشاكل الهروب (Shell Injection)
                # استخدام إعدادات أسرع لتقليل استهلاك الموارد في Render
                cmd = [
                    'ffmpeg', '-y', '-ss', str(start_time), '-t', str(clip_duration),
                    '-i', filepath,
                    '-vf', 'crop=ih*(9/16):ih,scale=720:1280', # تقليل الدقة قليلاً لتوفير الموارد
                    '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', 
                    '-c:a', 'aac', '-b:a', '64k', 
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"FFmpeg error for clip {i+1}: {result.stderr}")
                    raise Exception(f"FFmpeg failed at clip {i+1}")

        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return f"خطأ أثناء معالجة المقاطع: {str(e)}", 500
        finally:
            # 5. حذف الفيديو الأصلي فور الانتهاء
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted original file: {filepath}")
        
        return redirect(url_for('index'))

    # عرض المقاطع الموجودة حالياً إن وجدت
    clips_data = []
    if os.path.exists(app.config['CLIPS_FOLDER']):
        clips = sorted([c for c in os.listdir(app.config['CLIPS_FOLDER']) if c.endswith('.mp4')])
        clips_data = [{"name": c, "url": f"uploads/clips/{c}"} for c in clips]
        
    return render_template("index.html", clips=clips_data)

@app.route("/delete_all", methods=["POST"])
def delete_all():
    try:
        if os.path.exists(app.config['CLIPS_FOLDER']):
            shutil.rmtree(app.config['CLIPS_FOLDER'])
            os.makedirs(app.config['CLIPS_FOLDER'], exist_ok=True)
        return jsonify({"status": "success", "message": "تم حذف كافة المقاطع بنجاح"})
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Render يمرر المنفذ عبر متغير البيئة PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
