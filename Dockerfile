<<<<<<< HEAD
=======
# ベースイメージ
>>>>>>> 71d00bd36224dfea5de2268af8a75656382328fa
FROM python:3.13

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV DEBUG=False

WORKDIR /app

# Node.js + npm を追加（Tailwind 用）
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs build-essential

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Tailwind の static を生成
RUN python manage.py tailwind install
RUN python manage.py tailwind build

# Django の static ファイル収集
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", ":8080"]
