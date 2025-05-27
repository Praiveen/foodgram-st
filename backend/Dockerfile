FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

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