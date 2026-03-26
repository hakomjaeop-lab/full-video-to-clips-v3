# استخدام صورة Python الرسمية
FROM python:3.11-slim

# تثبيت ffmpeg و ffprobe
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# إعداد مجلد العمل
WORKDIR /app

# نسخ ملف التبعات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات المشروع
COPY . .

# التأكد من وجود المجلدات المطلوبة
RUN mkdir -p static/uploads/clips

# تعريض المنفذ (Render يمرر PORT تلقائياً)
EXPOSE 10000

# أمر التشغيل باستخدام gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
