FROM python:3.8-slim-buster

ARG ARG_PLATE="AX1245531"

ENV PLATE=${ARG_PLATE}

WORKDIR /app

RUN apt-get update -y 

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3",  "main.py"]