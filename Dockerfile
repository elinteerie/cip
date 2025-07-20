FROM python:3.10.14-alpine

ENV PYTHONUNBUFFERED 1


ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt --no-cache-dir


COPY . /app/


# Run migrations and collect static files
#RUN python manage.py collectstatic --noinput
#RUN python manage.py makemigrations
#RUN python manage.py migrate
#RUN python manage.py migrate django_celery_beat
#RUN python 

# Start the application
#CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "jiggy.asgi:application"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
