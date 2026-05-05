FROM python:3.11-slim
LABEL maintainer="Dennis Hulett khulett@uoregon.edu"
WORKDIR /app
COPY . /app
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
RUN apt-get update -y
RUN apt-get install -y --no-install-recommends build-essential libpq-dev 
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
