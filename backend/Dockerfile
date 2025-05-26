# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir --progress-bar off -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["sh", "-c", "python manage.py makemigrations users recipes && \
                    python manage.py migrate && \
                    python manage.py load_ingredients && \
                    python manage.py load_initial_data && \
                    python manage.py collectstatic --noinput && \
                    cp -r /app/collected_static/. /backend_static/static/ && \
                    gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000"] 