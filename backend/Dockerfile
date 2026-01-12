FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
# Expose default port
EXPOSE 5000
# Initialize DB on container start if DB missing, then start gunicorn
CMD ["/bin/sh", "-c", "python db_init.py || true && gunicorn -w 4 -b 0.0.0.0:5000 app:app"]
