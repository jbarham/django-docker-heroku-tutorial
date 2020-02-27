# Django Docker Heroku Tutorial

This tutorial demonstrates how to configure a [Django](https://www.djangoproject.com/)
app for development in [Docker](https://en.wikipedia.org/wiki/Docker_%28software%29)
and deployment to [Heroku](https://www.heroku.com/what).

While the app is intentionally very simple&mdash;it generates random tokens that can
be used as Django secret keys&mdash;the configuration is relatively complex:

* [Postgres](https://www.postgresql.org/) is used for the database
* [Redis](https://redis.io/) is used for the cache
* [Django-RQ](https://github.com/rq/django-rq) is used to process background jobs

Additionally [WhiteNoise](http://whitenoise.evans.io/en/stable/django.html) is
used to manage static files and [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)
is configured to run in the Docker development environment.

Please note that this is *not* a general tutorial on Django development or using
Docker. I assume that you're familiar with Django and are at least aware of
Docker, and the benefits of containerization more generally, but would benefit
from seeing a simple but real-world Django application configured for
development in Docker, and, as a bonus, deployment to Heroku.

## Developing in Docker

### Quick Start

Prerequisites:

* [Git](https://git-scm.com/)
* [Docker](https://docs.docker.com/install/)
* [Docker Compose](https://docs.docker.com/compose/install/)

Download the tutorial code into a new directory:

```
git clone git@github.com:jbarham/django-docker-heroku-tutorial.git djheroku
cd djheroku
```

Run `docker-compose up -d --build` to download the Docker images and bring
up the development environment in Docker Compose. This will take a while the
first time, but on subsequent runs will be much quicker as the Docker images
will be cached.

Assuming the above step succeeded, you should now have a Django app running
in a Docker container service named `web`, connected to other container
services running Postgres and Redis, and a separate background task runner.

However, the Postgres database will be empty. Populate it by running:

```
docker-compose exec web python manage.py migrate
```

The above command runs the command `python manage.py migrate` in the Django
Docker container. You could accomplish the same by running:

```
$ docker-compose exec web bash
# python manage.py migrate
# exit
```

All going well you should now be able to open the Django app at
http://localhost:8000/.

![App Screenshot](./screenshot.png)

Obviously it doesn't take two seconds to generate a random
key but the background task sleeps for two seconds to simulate a real-world
time consuming operation such as sending an email or generating a PDF.

When you're finished with the app just run `docker-compose down` to stop
the app and its supporting services.

### Django Dockerfile

At the heart of Docker is the `Dockerfile`, a simple plain text file that
defines how to build a Docker *image* which can be run as a Docker *container*.

Here is the `Dockerfile` for our Django app in its entirety:

```
# Pull base image
FROM python:3.6-slim

# Install psql so that "python manage.py dbshell" works
RUN apt-get update -qq && apt-get install -y postgresql-client

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy project
COPY . /app/
```

By itself, though, this Dockerfile doesn't provide much more than we
could get from developing our Django app in a traditional Python virtual
environment.

This is where Docker Compose comes in.

### Docker Compose Services

Here is a summary of Docker Compose from the [official
documentation](https://docs.docker.com/compose/):

> Compose is a tool for defining and running multi-container Docker
applications. With Compose, you use a YAML file to configure your application’s
services. Then, with a single command, you create and start all the services
from your configuration.

Our Docker Compose configuration file, [`docker-compose.yml`](./docker-compose.yml),
defines four services, `web`, `worker`, `db` and `redis`, each of which runs in
a separate Docker container. (Note that the internal hostname for each service
is same as the service name. So to connect to the Redis server from Django we
use `redis:6379` as the *hostname:port* pair.)

Taking each service in turn:

```
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      DEBUG: 1
    volumes:
      - .:/app
    ports:
      - 8000:8000
    depends_on:
      - db
      - redis
```

The `web` service runs our Django app in a Docker container defined by our
`Dockerfile`.

We set the environment variable `DEBUG=1` which sets the `DEBUG` variable in the
app's [`settings.py`](djheroku/settings.py) file to `True`.

The `volumes` section says that we want to map the current directory to the
`/app` mountpoint in the Docker container. This means that any changes made to
the application code while the container is running cause the Django server to
reload, as it would it if were running outside of Docker. (Tangentially, this 
also explains why we set the `PYTHONDONTWRITEBYTECODE` flag in our Dockerfile.
Since Django is run by the `root` user inside the `web` container, we don't
want the root user to save cached bytecode files to our application directory.)

```
  worker:
    build: .
    command: python manage.py rqworker default
    environment:
      DEBUG: 1
    volumes:
      - .:/app
    depends_on:
      - web
```

The `worker` service runs [Django-RQ](https://github.com/rq/django-rq) to
process background tasks. Since Django-RQ runs as a Django management command,
it's configured very similarly to the Django app server,
with the notable exception that we don't define a port mapping since it doesn't
have a web interface.

```
  db:
    image: postgres:latest
    restart: always
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: djheroku
    volumes:
      - pgdata:/var/lib/postgresql/data/
```

The `db` service installs and configures a full-blown Postgres database server,
creating a database for our Django app, using the most recent Postgres Docker
image. This is where using Docker really shines.

For more details on the configuration environment variables see the
[Docker Postgres documentation](https://hub.docker.com/_/postgres/).

We define a `volumes` section for our database so that the data itself is saved
outside of the database container. Otherwise when the container is shut down
we'd lose the contents of our database!

```
  redis:
    image: redis:latest
```

Short and sweet, the `redis` service says that we want a Redis server in our
Docker Compose environment, and we're happy with the default configuration.

### Running Django Debug Toolbar in Docker Compose

[Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)
is an invaluable plugin for Django developers as it provides very detailed
runtime profiling information that you can use to optimize your app's database
queries and templates.

By default Django Debug Toolbar only runs if the Django settings `DEBUG`
flag is set to `True` and the development server's IP address is defined in the
[INTERNAL_IPS](https://docs.djangoproject.com/en/dev/ref/settings/#internal-ips)
list. In development `INTERNAL_IPS` is typically set to `['localhost', '127.0.0.1']`.

However, services running in Docker Compose are assigned an ephemeral IP address
so Django Debug Toolbar won't run. To enable Django Debug Toolbar in Docker
Compose we instead used the following configuration option in our
[`settings.py`](djheroku/settings.py):

```python
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}
```

See the [Django Debug Toolbar documentation](https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#show-toolbar-callback) for more details.

## Deploying to Heroku

### Quick Start

Prerequisites:

* [Create a free Heroku account](https://signup.heroku.com/)
* [Install and log into the Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

Run `heroku create` to create a new Heroku app with a randomly generated name.

Create a new Heroku Postgres database:

```
heroku addons:create heroku-postgresql:hobby-dev
```

Create a new Heroku Redis server:

```
heroku addons:create heroku-redis:hobby-dev
```

Upload our app to Heroku:

```
git push heroku master
```

Start a background task worker dyno:

```
heroku ps:scale worker=1
```

### Why Deploy to Heroku

### Why Not Deploy to Heroku

## Further Reading

* Will Vincent
* Two Scoops of Django
* [Getting Started on Heroku with Python](https://devcenter.heroku.com/articles/getting-started-with-python)
