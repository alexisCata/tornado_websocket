from tornado import websocket, web, httpclient, gen
import requests
import json

r = requests.post('http://192.168.1.35:8000/api/auth/',
                         data={
                             'email': 'team@cathedralsw.com',
                             'password': 'password123',
                         })

my_user = 0
token = eval(r.content.decode())['token']



def handle_async_response(response):
    print(response.body)
    if response and response.code == 200:
        print(response)
        my_user = json.loads(response.body.decode())['user']


def func():
    header = {'Authorization': "JWT {}".format(token)}
    http = httpclient.AsyncHTTPClient()
    try:
        # response = yield http.fetch('http://localhost:8888/test')
        http.fetch('http://192.168.1.35:8000/api/auth/user/', handle_async_response, headers=header)

    except Exception as e:
        print(e.args[0])




func()



from tornado import ioloop




ioloop.IOLoop.instance().start()