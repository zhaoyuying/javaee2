# coding: utf-8
from __future__ import unicode_literals
from middleware import TestMiddle


import socket
import StringIO
import sys
import datetime


class WSGIServer(object):
    socket_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 10

    def __init__(self, address):
        self.socket = socket.socket(self.socket_family, self.socket_type)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(address)
        self.socket.listen(self.request_queue_size)
        host, port = self.socket.getsockname()[:2]
        self.host = host
        self.port = port

    def set_application(self, application):
        self.application = application

    def serve_forever(self):
        while 1:
            self.connection, client_address = self.socket.accept()
            self.handle_request()

    def handle_request(self):
        self.request_data = self.connection.recv(1024)
        self.request_lines = self.request_data.splitlines()
        try:
            self.get_url_parameter()
            env = self.get_environ()
            app_data = self.application(env, self.start_response)
            self.finish_response(app_data)
            print '[{0}] &quot;{1}&quot; {2}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                           self.request_lines[0], self.status)
        except Exception, e:
            pass

    def get_url_parameter(self):
        self.request_dict = {'Path': self.request_lines[0]}
        for itm in self.request_lines[1:]:
            if ':' in itm:
                self.request_dict[itm.split(':')[0]] = itm.split(':')[1]
        self.request_method, self.path, self.request_version = self.request_dict.get('Path').split()

    def get_environ(self):
        env = {
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': StringIO.StringIO(self.request_data),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'REQUEST_METHOD': self.request_method,
            'PATH_INFO': self.path,
            'SERVER_NAME': self.host,
            'SERVER_PORT': self.port,
            'USER_AGENT': self.request_dict.get('User-Agent')
        }
        return env

    def start_response(self, status, response_headers):
        headers = [
            ('Date', datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')),
            ('Server', 'RAPOWSGI0.1'),
        ]
        self.headers = response_headers + headers
        self.status = status

    def finish_response(self, app_data):
        try:
            response = 'HTTP/1.1 {status}\r\n'.format(status=self.status)
            for header in self.headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in app_data:
                response += data
            self.connection.sendall(response)
        finally:
            self.connection.close()


if __name__ == '__main__':
    port = 8888
    if len(sys.argv) < 2:
       sys.exit('请提供可用的wsgi应用程序, 格式为: 模块名.应用名 端口号【eg：python server.py app.application 8080】')
    elif len(sys.argv) > 2:
        port = sys.argv[2]
		


def generate_server(address, application):
        server = WSGIServer(address)
        server.set_application(TestMiddle(application))
        return server


app_path = sys.argv[1]
module, application = app_path.split('.')
module = __import__(module)
application = getattr(module, application)
httpd = generate_server(('', int(port)), application)
print 'RAPOWSGI Server Serving HTTP service on port {0}'.format(port)
print '{0}'.format(datetime.datetime.now().
                       strftime('%a, %d %b %Y %H:%M:%S GMT'))
httpd.serve_forever()

from __future__ import unicode_literals


class TestMiddle(object):
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        if 'postman' in environ.get('USER_AGENT'):
            start_response('403 Not Allowed', [])
            return ['not allowed!']
        return self.application(environ, start_response)


URL_PATTERNS= (
    ('hi/','say_hi'),
    ('aaa/','say_hello'),
    )

class Dispatcher(object):

    def _match(self,path):
        path = path.split('/')[1]
        for url,app in URL_PATTERNS:
            if path in url:
                return app

    def __call__(self,environ, start_response):
        path = environ.get('PATH_INFO','/')
        app = self._match(path)
        if app :
            app = globals()[app]
            return app(environ, start_response)
        else:
            start_response("404 NOT FOUND",[('Content-type', 'text/plain')])
            return ["404 NOT FOUND"]

def say_hi(environ, start_response):
    start_response("200 OK",[('Content-type', 'text/html')])
    return ["hi"]
def say_hello(environ, start_response):
    start_response("200 OK",[('Content-type', 'text/html')])
    return ["hello aaa"]

app = Dispatcher()
