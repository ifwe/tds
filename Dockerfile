FROM python:2.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt --allow-all-external --allow-unverified progressbar
COPY requirements-dev.txt /usr/src/app/
RUN pip install -r requirements-dev.txt

COPY . /usr/src/app
