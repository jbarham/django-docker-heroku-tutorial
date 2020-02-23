release: python manage.py migrate

web: gunicorn djheroku.wsgi --log-file -

worker: python manage.py rqworker default
