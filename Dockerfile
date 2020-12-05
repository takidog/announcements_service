FROM python:3.7-alpine
# Create app directory
RUN mkdir -p /usr/src/announcements_service
WORKDIR /usr/src/announcements_service

COPY . /usr/src/announcements_service

RUN pip3 install -r src/requirements.txt


WORKDIR src

CMD ["gunicorn","-c","gunicorn_config.py","web_server:app"]