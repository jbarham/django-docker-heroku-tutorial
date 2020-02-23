release: python manage.py migrate

web: gunicorn config.wsgi --log-file -

worker: python manage.py rqworker default
