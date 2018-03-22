import os

IP = os.environ.get('SERVER_PORT_8000_TCP_ADDR', 'localhost')
PORT = os.environ.get('SERVER_PORT_8000_TCP_PORT', 8000)
HOST = IP + ':' + str(PORT)
API = '/api/auth/user/'

VALIDATE_TOKEN_API = HOST + API

DB_HOST = os.environ.get('MONGO_DB_HOST', 'localhost')
DB_PORT = os.environ.get('MONGO_DB_PORT', 27017)
DB_USER = os.environ.get('MONGO_DB_USER', 'myuser')
DB_PASS = os.environ.get('MONGO_DB_PASS', 'mypassword')
