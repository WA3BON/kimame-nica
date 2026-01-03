# Python イメージをベースにする
FROM python:3.13

# Python の出力をバッファリングせず即座にログに出す
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリを設定
WORKDIR /app

# 依存パッケージをコピーしてインストール
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 本番では Tailwind は無効化済みなので collectstatic のみ実行
RUN python manage.py collectstatic --noinput

# Gunicorn でアプリ起動（Cloud Run / Render 想定）
CMD ["gunicorn", "config.wsgi:application", "--bind", ":8080"]