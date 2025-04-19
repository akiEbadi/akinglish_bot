FROM python:3.11-slim-bullseye

# جلوگیری از interactive mode در نصب
ENV DEBIAN_FRONTEND=noninteractive

# نصب پکیج‌های مورد نیاز سیستم
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# پوشه پروژه
WORKDIR /app

# کپی فایل‌های پروژه
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# اجرای بات
CMD ["python", "main.py"]
