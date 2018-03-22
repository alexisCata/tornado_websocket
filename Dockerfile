FROM python:3.5

# RUN apt-get update && apt-get install python3-pip -y

RUN mkdir -p /usr/src/tornado_server
WORKDIR /usr/src/tornado_server

COPY . /usr/src/tornado_server/
RUN pip3 install -r requirements.txt

EXPOSE 8888

CMD python3 server.py
