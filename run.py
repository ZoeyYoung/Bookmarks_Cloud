#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import os
import logging
# from mongolog.handlers import MongoHandler
import tornado.ioloop
import tornado.web
from tornado.options import options
from tornado import httpserver
from bookmarks_cloud import indexes
from bookmarks_cloud.config import *
from bookmarks_cloud.handlers import handlers
from bookmarks_cloud.bookmarks_handlers import BookmarkModule
from bookmarks_cloud.bookmarks_handlers import PagerModule
from bookmarks_cloud.define_options import define_options
import pymongo

log = logging.getLogger(LOG)
log.setLevel(logging.DEBUG)


class Application(tornado.web.Application):

    def __init__(self, options):
        settings = dict(
            title=TITLE,
            keywords=KEYWORDS,
            desc=DESCRIPTION,
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={'Bookmark': BookmarkModule, 'Pager': PagerModule},
            xsrf_cookies=False,
            cookie_secret=COOKIE_SECRET,
            login_url="/auth/login",
            gzip=True,
            # autoescape=None,
            **{k: v.value() for k, v in options._options.items()}
        )
        self.db=pymongo.MongoClient()[DB_NAME]
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    # log.addHandler(MongoHandler.to(db='bookmarks_cloud', collection='log'))
    define_options(options)
    options.parse_command_line()
    for handler in logging.getLogger(LOG).handlers:
        if hasattr(handler, 'baseFilename'):
            print('Logging to', handler.baseFilename)
            break
    if options.rebuild_indexes or options.ensure_indexes:
        indexes.ensure_indexes(DB, drop=options.rebuild_indexes)
    http_server = httpserver.HTTPServer(Application(options), xheaders=True)
    http_server.listen(options.port)
    log.info('Listening on port %s' % options.port)
    # TODO: Can't Work In Windows
    # httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
