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
from bookmarks_cloud.define_options import define_options
from bookmarks_cloud import indexes, application, config


if __name__ == "__main__":
    log = logging.getLogger('bookmarks_cloud_log')
    log.setLevel(logging.DEBUG)
    # log.addHandler(MongoHandler.to(db='bookmarks_cloud', collection='log'))
    define_options(options)
    options.parse_command_line()
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'baseFilename'):
            print('Logging to', handler.baseFilename)
            break
    if options.rebuild_indexes or options.ensure_indexes:
        indexes.ensure_indexes(
            config.config['db'],
            drop=options.rebuild_indexes)
    this_dir = os.path.dirname(__file__)
    application = application.get_application(this_dir, config.config['db'], options)
    http_server = httpserver.HTTPServer(application, xheaders=True)
    http_server.listen(options.port)
    msg = 'Listening on port %s' % options.port
    print(msg)
    log.info(msg)
    # TODO: Can't Work In Windows
    # httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    tornado.ioloop.IOLoop.instance().start()
