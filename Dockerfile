FROM python:3.12.2-slim

WORKDIR ./

ENV PYTHONDONTWRITEBITECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
