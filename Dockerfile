FROM python:3.13

WORKDIR /app

# python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# node
RUN apt-get update && apt-get install -y nodejs npm

# project
COPY . .

# tailwind build
RUN python manage.py tailwind install
RUN python manage.py tailwind build

# static
RUN python manage.py collectstatic

CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8080"]