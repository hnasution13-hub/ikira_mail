FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8001

CMD ["gunicorn", "i-kira_mail.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "1", "--threads", "2", "--timeout", "120"]
