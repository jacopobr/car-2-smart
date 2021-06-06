FROM python:3.7-slim-buster

EXPOSE 5000

ARG ARG_TOKEN
ARG ARG_USER
ARG ARG_PASSWORD
ARG ARG_DATABASE

ENV BOT_TOKEN=${ARG_TOKEN}
ENV USER=${ARG_USER}
ENV PASSWORD=${ARG_PASSWORD}
ENV DATABASE=${ARG_DATABASE}

RUN apt-get update -y 

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]
