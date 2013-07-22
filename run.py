#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
import tornado.ioloop
import tornado.web
from tornado.options import options
from tornado import httpserver

from bookmarks_cloud.define_options import define_options
from bookmarks_cloud import indexes, application, config


if __name__ == "__main__":
    define_options(options)
    options.parse_command_line()
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'baseFilename'):
            print('Logging to', handler.baseFilename)
            break

    # db = motor.MotorClient().open_sync().links
    # db = pymongo.Connection().links
    # cache.startup(db)

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
    logging.info(msg)
    tornado.ioloop.IOLoop.instance().start()
