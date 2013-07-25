#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .auth import *
from .link import *

handlers = [
    (r'/', IndexHandler),
    (r'/auth/login', AuthLoginHandler),
    (r'/auth/logout', AuthLogoutHandler),
    (r'/link/page/([0-9]+)', LinkHandler),
    (r'/link', AjaxLinkHandler),
    (r'/link/get_detail', LinkGetDetailHandler),
    (r'/link/refresh', LinkRefreshHandler),
    (r'/link/get_article', LinkGetArticleHandler),
    (r'/link/get_info', LinkGetInfoHandler),
    (r'/link/add', LinkAddHandler),
    (r'/link/del', LinkDelHandler),
    (r'/tag/([0-9]+)/(.*)', TagLinksHandler),
    (r'/tags_cloud', TagsCloudHandler),
    (r'/randomlink', RandomLinkHandler),
    (r'/random', RandomLinksHandler),
    (r'/search', SearchHandler)
]
