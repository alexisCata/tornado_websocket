# Tornado websocket #

It uses Tornado WebSocketHandler to open a communication channel between the client and the server.

To manage notifications it uses RequestHandler. 

```
localhost:8888/notification?id=1&message=notification_message
```


### Dependencies ###
* [Docker](https://www.docker.com/)
* [Tornado](http://www.tornadoweb.org)

### Tests ###
```shell
python3 test/handlers_test.py
```

### How do I use it? ###
- Build
```shell
docker build -t school_tornado .
```

- Run
```shell
docker run -d -p 8888:8888 -e API_VALIDATION_IP='API_IP' -e API_VALIDATION_PORT=API_PORT --name=school school_tornado
```

