FROM resin/rpi-raspbian:buster

ARG ARG_PLATE="AX1245531"

ARG ARG_WEATHER_API_KEY

ARG ARG_CITY="torino"

ENV PLATE=${ARG_PLATE}

ENV WEATHER_API_KEY=${ARG_WEATHER_API_KEY}

ENV CITY={$ARG_CITY}

# Install dependencies
RUN apt-get update && apt-get install -y \
    git-core \
    build-essential \
    libgpiod2 \
    gcc \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools\
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3",  "main.py"]