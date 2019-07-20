FROM python:3.6-stretch

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /tgbot

RUN pip install pipenv
COPY requirements.txt Pipfile Pipfile.lock /tgbot/
RUN pipenv install -r requirements.txt

COPY . /tgbot/
