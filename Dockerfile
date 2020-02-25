# Pull base image
FROM python:3.6-slim

# Install psql so that "python manage.py dbshell" works
RUN apt-get update -qq && apt-get install -y postgresql-client

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements/ /app/requirements/
RUN pip install -r /app/requirements/local.txt

# Copy project
COPY . /app/
