#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import tornado.web

from .handlers import handlers
from .link import LinkModule
from .link import PagerModule
from .config import config


def get_application(root_dir, db, option_parser):
    return tornado.web.Application(
        handlers,
        template_path=os.path.join(root_dir, 'templates'),
        static_path=os.path.join(root_dir, "static"),
        db=db,
        ui_modules={'Link': LinkModule, 'Pager': PagerModule},
        cookie_secret=config['cookie_secret'],
        xsrf_cookies=False,
        gzip=True,
        login_url="/auth/login",
        title=config['title'],
        url=config['url'],
        keywords=config['keywords'],
        desc=config['description'],
        autoescape=None,
        analytics=config['analytics'],
        **{k: v.value() for k, v in list(option_parser._options.items())}
    )
