FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

# EXAMSPRINT_ACCESS_TOKEN should be set as a secret on the hosting platform.
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "10000", "--no-browser"]
