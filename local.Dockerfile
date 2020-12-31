FROM python:3.9

ENV PYTHONUTF8 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./ /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install pipenv
COPY Pipfile Pipfile.lock /app/
RUN pipenv install --system --dev --deploy
