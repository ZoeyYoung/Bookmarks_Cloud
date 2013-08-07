#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .auth import *
from .bookmarks_handlers import *

handlers = [
    (r'/', IndexHandler),
    (r'/auth/login', AuthLoginHandler),
    (r'/auth/logout', AuthLogoutHandler),
    (r'/bookmark/page/([0-9]+)', BookmarkHandler),
    (r'/bookmark', AjaxBookmarkHandler),
    (r'/bookmark/get_detail', BookmarkGetDetailHandler),
    (r'/bookmark/refresh', BookmarkRefreshHandler),
    (r'/bookmark/get_article', BookmarkGetArticleHandler),
    (r'/bookmark/get_info', BookmarkGetInfoHandler),
    (r'/bookmark/add', BookmarkAddHandler),
    (r'/bookmark/del', BookmarkDelHandler),
    (r'/tag/([0-9]+)/(.*)', TagBookmarksHandler),
    (r'/tags_cloud', TagsCloudHandler),
    (r'/randombookmark', RandomBookmarkHandler),
    (r'/random', RandomBookmarksHandler),
    (r'/search', SearchHandler),
    (r'/ftxsearch', FullTextSearchHandler),
    (r'/tags', TagsHandler),
    (r'/segmentation/(.*)', SegmentationHandler)
]
