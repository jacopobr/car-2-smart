FROM python:3

WORKDIR /app

ARG ARG_PLATE="AX1245531"

ENV PLATE=${ARG_PLATE}

RUN apt-get update -y 

#Install libraries needed to process sound
RUN apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 -y

#RUN apt-get install gcc -y

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3",  "main.py"]