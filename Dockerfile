FROM python:3.7-alpine
# Create app directory
COPY src/requirements.txt /.
RUN pip3 install -r /requirements.txt

RUN mkdir -p /usr/src/announcements_service
WORKDIR /usr/src/announcements_service

COPY . /usr/src/announcements_service

WORKDIR src

CMD ["gunicorn","-c","gunicorn_config.py","web_server:app"]