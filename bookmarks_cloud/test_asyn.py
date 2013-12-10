import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.httpclient
import urllib
import json
import datetime
import time

from tornado.options import define, options
define("port", default=8080, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        url = self.get_argument('url')
        request = tornado.httpclient.HTTPRequest(
            url,
            method='GET',
            headers={"content-type": "text/html", 'Referer': 'http://www.google.com', "Accept": "*/*"},
            request_timeout=10,
            follow_redirects=True,
            user_agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1485.0 Safari/537.36',
            allow_ipv6=True
        )
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield client.fetch(url)
        self.write(response.body)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", IndexHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    tornado.ioloop.IOLoop.instance().start()
