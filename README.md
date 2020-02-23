docker-compose up -d --build
docker-compose exec web python manage.py migrate

heroku create
heroku addons:create heroku-postgresql:hobby-dev
