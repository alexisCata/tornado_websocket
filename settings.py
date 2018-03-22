import logging
import os
import motor.motor_tornado

# LOGGING
path = './school_tornado.log'

logger = logging.getLogger('school_tornado')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

fh = logging.FileHandler(path)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# VARIABLES
try:
    import secret_settings

    VALIDATE_TOKEN_API = secret_settings.VALIDATE_TOKEN_API

    ANDROID_PUSH_SERVICE_URL = secret_settings.ANDROID_PUSH_SERVICE_URL
    ANDROID_PUSH_SERVICE_KEY = secret_settings.ANDROID_PUSH_SERVICE_KEY

    # CHAT DB
    DB_HOST = secret_settings.DB_HOST
    DB_PORT = int(secret_settings.DB_PORT)
    DB_USER = secret_settings.DB_USER
    DB_PASS = secret_settings.DB_PASS

except ImportError:
    VALIDATE_TOKEN_API = 'http://{}:{}/api/auth/user/'.format(
        os.environ.get('SERVER_PORT_8000_TCP_ADDR', 'server'),
        os.environ.get('SERVER_PORT_8000_TCP_PORT', '8000'),
    )

    ANDROID_PUSH_SERVICE_URL = 'https://fcm.googleapis.com/fcm/send'
    ANDROID_PUSH_SERVICE_KEY = 'AIzaSyB0_60LfwfxIqWvx34d_-Tqd7TPFhMcwJ4'

    # CHAT DB
    DB_HOST = os.environ.get('MONGO_PORT_27017_TCP_ADDR', 'mongo')
    DB_PORT = int(os.environ.get('MONGO_PORT_27017_TCP_PORT', '27017'))
    DB_USER = os.environ.get('MONGO_INITDB_ROOT_USERNAME', '')
    DB_PASS = os.environ.get('MONGO_INITDB_ROOT_PASSWORD', '')

db_client = motor.motor_tornado.MotorClient(DB_HOST, DB_PORT)
db_client.chats_db.authenticate(DB_USER, DB_PASS)
chats_db = db_client.chats_db
