from tornado import websocket, web, httpclient, gen
from bson.objectid import ObjectId
from settings import (logger,
                      VALIDATE_TOKEN_API,
                      ANDROID_PUSH_SERVICE_URL,
                      ANDROID_PUSH_SERVICE_KEY,
                      chats_db,
                      )
import json
from datetime import datetime

WEBSOCKETS = {}
TOKENS = {}
TOKEN_VALIDATION_HEADER = 'Authorization'


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")


class SocketHandler(websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.user_id = 0
        self.token = None

    def check_origin(self, origin):
        # TO DO: check if the origin is any subdomain of our web
        return True

    def add_websocket(self, user_id):
        self.user_id = user_id
        if user_id not in WEBSOCKETS:
            WEBSOCKETS[user_id] = [self]
        else:
            WEBSOCKETS[user_id].append(self)

    @gen.coroutine
    def handle_token(self, token, device_id, app_token, device_type='WEB'):
        header = {TOKEN_VALIDATION_HEADER: "JWT {}".format(token)}

        self.token = token
        self.device_id = device_id
        self.device_type = device_type
        self.app_token = app_token

        http = httpclient.AsyncHTTPClient()
        try:
            http.fetch(VALIDATE_TOKEN_API, self.handle_async_response, headers=header)
        except Exception as e:
            logger.exception(e.args[0])

        http.close()

    # @gen.coroutine
    async def handle_async_response(self, response):
        if response and response.code == 200:
            user_id = json.loads(response.body.decode())['id']
            TOKENS[self.token] = user_id
            self.add_websocket(user_id)
            logger.info('WEBSOCKET VALIDATED TOKEN: user={}'.format(user_id))

            if self.device_type != 'WEB':
                db = self.settings['db']

                await db.test.find_one_and_delete({
                    'device_id': self.device_id,
                })

                await db.user_credentials.update_one(
                    {
                        'user_id': user_id,
                        'device_id': self.device_id,
                    },
                    {
                        '$set': {
                            'app_token': self.app_token,
                            'device_type': self.device_type,
                        }
                    },
                    upsert=True,
                )

        else:
            logger.error('Error on token validation: {}'.format(response.error))

    def open(self):
        # TO DO: Handle possible errors
        device_type = 'WEB'

        token = self.get_argument('token', None)
        app_token = self.get_argument('fbtoken', None)

        device_id = self.get_argument('idandroid', None)
        if device_id is not None:
            device_type = 'ANDROID'

        else:
            device_id = self.get_argument('idios', None)
            if device_id is not None:
                device_type = 'IOS'

        logger.info('WEBSOCKET OPEN: token={}'.format(token))

        if token:
            if token not in TOKENS:
                self.handle_token(token=token,
                                  device_id=device_id,
                                  device_type=device_type,
                                  app_token=app_token)
            else:
                user_id = TOKENS[token]
                self.add_websocket(user_id)
        else:
            logger.error("Websocket attempt without token : IP {} HOST {}".format(self.request.remote_ip,
                                                                                  self.request.host))

    def on_close(self):
        if self.user_id in WEBSOCKETS:
            WEBSOCKETS[self.user_id].remove(self)
            if not WEBSOCKETS[self.user_id]:
                del WEBSOCKETS[self.user_id]
                for token, user_id in TOKENS.copy().items():
                    if user_id == self.user_id:
                        del TOKENS[token]
            logger.info('WEBSOCKET CLOSED user:{}'.format(self.user_id))

    # def my_callback(self, result, error):
    #     logger.info("Chat message {} saved in DB".format(repr(result)))

    @web.asynchronous
    def confirm_msg(self, user_id):
        data = {'chat_saved_confirmation': True}
        if user_id in WEBSOCKETS:
            for s in WEBSOCKETS[user_id].copy():
                # check if ws connection is open
                if s.ws_connection:
                    s.write_message(data)
                    logger.info("Chat message confirmation: user_id: {}".format(user_id))
                else:
                    logger.error("Error sending chat message confirmation: user_id: {}".format(user_id))
                    s.on_close()

    @gen.coroutine
    def on_message(self, message):
        logger.info("Request received through websocket: user_id: {}".format(self.user_id))

        request = json.loads(message)

        if 'chat_message' in request:
            logger.info("Chat message: {}".format(message))
            user_from = self.user_id # request['chat_message']["user_from"]
            user_to = int(request['chat_message']["user_to"])
            message = request['chat_message']["message"]
            timestamp = datetime.now()

            db = self.settings['db']

            if user_from < user_to:
                conversation_id = '{}-{}'.format(user_from, user_to)

            else:
                conversation_id = '{}-{}'.format(user_to, user_from)

            document = {'user_from': user_from, 'user_to': user_to, 'conversation_id': conversation_id, 'message': message, "timestamp": timestamp}
            future = db.chats_history.insert_one(document)
            result = yield future

            self.confirm_msg(user_from)

            data = {'chat_message': {'id': str(result.inserted_id),
                                     "user_from": user_from,
                                     "user_to": user_to,
                                     "message": message,
                                     "timestamp": str(timestamp),
                                     }
                    }
            data_string = json.dumps(data)

            sent = False

            if user_to in WEBSOCKETS:
                for s in WEBSOCKETS[user_to].copy():
                    # check if ws connection is open
                    if s.ws_connection:
                        s.write_message(data_string)
                        logger.info("Chat message sent: user_from: {} - user_to: {} - message: {}"
                                    .format(user_from, user_to, message))
                        sent = True

                    else:
                        logger.error("WS connection lost for ID: {} - Closing WS".format(user_to))
                        s.on_close()

            if not sent:
                logger.info('Try PUSH')
                db = self.settings['db']
                cursor = db.user_credentials.find(
                    {
                        'user_id': user_to,
                    }
                )
                while (yield cursor.fetch_next):
                    r = cursor.next_object()

                    app_token = r['app_token']
                    device_type = r['device_type']

                    logger.info('DEVICE {} - {}'.format(app_token, device_type))

                    if device_type == 'ANDROID':
                        logger.info(
                            "PUSH: ANDROID - token={}".format(
                                app_token,
                            )
                        )

                        body = {
                            'to': app_token,
                            'notification': {
                                'body': data['chat_message']['message'],
                                # TODO From name
                                'title': 'Nuevo mensaje',
                            },
                        }
                        body_string = json.dumps(body)

                        http_client = httpclient.AsyncHTTPClient()

                        try:
                            logger.info('POST to ANDROID device')

                            r = httpclient.HTTPRequest(
                                ANDROID_PUSH_SERVICE_URL,
                                method='POST',
                                body=body_string,
                                headers={
                                    'Content-Type': 'application/json',
                                    'Authorization': 'key={}'.format(
                                        ANDROID_PUSH_SERVICE_KEY,
                                    )
                                })

                            http_client.fetch(r,
                                              self.handle_android_push_response)

                        except Exception as e:
                            logger.exception(e.args[0])

        if 'chat_read' in request:
            logger.info("Chat read: {}".format(message))

            db = self.settings['db']
            db.chats_history.update_one({
                '_id': ObjectId(request['chat_read']['id'])},
                {'$set': {'read': True}},
            )

    @gen.coroutine
    def handle_android_push_response(self, response):
        if response and response.code == 200:
            logger.info('PUSH - SUCCESS!')

        else:
            logger.info('PUSH - FAIL!')


class NotificationHandler(web.RequestHandler):

    @gen.coroutine
    def get(self, *args):
        logger.info("Notification received")
        self.finish()

        notification_id = int(self.get_argument("id"))
        students = [int(user_id) for user_id in self.get_argument("user").split(',') if user_id]
        owner = int(self.get_argument("owner"))
        title = self.get_argument("title")
        description = self.get_argument("description")
        # timestamp = datetime.strptime(self.get_argument("timestamp"), "%Y-%m-%d %H:%M:%S")
        # date = datetime.strptime(self.get_argument("date"), "%Y-%m-%d %H:%M:%S")
        timestamp = self.get_argument("timestamp")
        date = self.get_argument("date")
        target_class = self.get_argument("target_class", default=None)
        # target_student = int(self.get_argument("target_student"))

        logger.info("Notification: ids: {} - message: {}".format(students, description))
        # logger.info("WEBSOCKETS: {}".format(WEBSOCKETS))
        for user_id in students:
            data = {'notification': {"id": notification_id,
                                     "user": user_id,
                                     "owner": owner,
                                     "title": title,
                                     "description": description,
                                     "timestamp": timestamp,
                                     "date": date,
                                     "target_class": int(target_class) if target_class is not None else None,
                                     # "target_student": target_student
                                     }
                    }
            data = json.dumps(data)

            sent = False

            if user_id in WEBSOCKETS:
                for s in WEBSOCKETS[user_id].copy():
                    if s.ws_connection:
                        s.write_message(data)
                        logger.info("Notification sent. ID: {} MESSAGE: {}".format(user_id, description))
                        sent = True

                    else:
                        logger.error("WS connection lost for ID: {} - Closing WS".format(user_id))
                        s.on_close()
            if not sent:
                logger.info('Try PUSH')
                db = self.settings['db']
                cursor = db.user_credentials.find(
                    {
                        'user_id': user_id,
                    }
                )
                while (yield cursor.fetch_next):
                    r = cursor.next_object()

                    app_token = r['app_token']
                    device_type = r['device_type']

                    logger.info('DEVICE {} - {}'.format(app_token, device_type))

                    if device_type == 'ANDROID':
                        logger.info(
                            "PUSH: ANDROID - token={}".format(
                                app_token,
                            )
                        )

                        body = {
                            'to': app_token,
                            'notification': {
                                'body': title,
                                # TODO From name
                                'title': date,
                            },
                        }
                        body_string = json.dumps(body)

                        http_client = httpclient.AsyncHTTPClient()

                        try:
                            logger.info('POST to ANDROID device')

                            r = httpclient.HTTPRequest(
                                ANDROID_PUSH_SERVICE_URL,
                                method='POST',
                                body=body_string,
                                headers={
                                    'Content-Type': 'application/json',
                                    'Authorization': 'key={}'.format(
                                        ANDROID_PUSH_SERVICE_KEY,
                                    )
                                })

                            http_client.fetch(r,
                                              self.handle_android_push_response)

                        except Exception as e:
                            logger.exception(e.args[0])

    @gen.coroutine
    def handle_android_push_response(self, response):
        if response and response.code == 200:
            logger.info('PUSH - SUCCESS!')

        else:
            logger.info('PUSH - FAIL!')


    @web.asynchronous
    def post(self):
        pass


settings = {
    "template_path": "templates",
    "db": chats_db
    # "static_path": os.path.join(os.path.dirname(__file__), "static"),
    # "debug" : True
}

app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/notification', NotificationHandler),
], **settings)
