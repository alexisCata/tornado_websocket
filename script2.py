from tornado import websocket, web, httpclient, gen
import requests
import json
from datetime import datetime, date

r = requests.get('http://localhost:8888/notification',
                 params={
                     'student': 1,

                     'owner': 1,
                     'title': "titulo",
                     'description': "message",
                     'timestamp': datetime.now(),
                     'date': date.today(),
                     'target_class': 1,
                     'target_student': 1,
                 })

my_user = 0
