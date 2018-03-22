from tornado import ioloop
from handlers.handlers import *


if __name__ == '__main__':
    app.listen(8888)
    ioloop.IOLoop.instance().start()
