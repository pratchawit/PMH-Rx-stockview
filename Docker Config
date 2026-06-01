# ใช้ Python 3.10 เป็นฐาน
FROM python:3.10-slim

# ตั้งค่า Working Directory ใน Container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt และติดตั้ง
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์โค้ดทั้งหมดของเราเข้าไป
COPY . .

# เปิด Port 8080 (Cloud Run บังคับใช้ Port นี้)
EXPOSE 8080

# คำสั่งสำหรับรัน Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false"]
