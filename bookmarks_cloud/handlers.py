#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
__about__ = """
    请求处理器
"""
from .auth import *
from .bookmarks_handlers import *

handlers = [
    (r'/', IndexHandler),
    (r'/auth/signin', SignInHandler),
    (r'/auth/signup', SignUpHandler),
    (r'/auth/logout', LogoutHandler),
    (r'/bookmark/page/([0-9]+)', IndexHandler),
    (r'/bookmark', AjaxBookmarkHandler),
    (r'/bookmark/get_detail', BookmarkGetDetailHandler),
    (r'/bookmark/refresh', BookmarkRefreshHandler),
    (r'/bookmark/get_article', BookmarkGetArticleHandler),
    (r'/bookmark/get_info', BookmarkGetInfoHandler),
    (r'/bookmark/add', BookmarkAddHandler),
    (r'/bookmark/del', BookmarkDelHandler),
    (r'/bookmark/set_star', BookmarkSetStarHandler),
    (r'/tag/([^/]+)/([0-9]+)', AuthTagBookmarksHandler),
    (r'/tags_cloud', TagsCloudHandler),
    (r'/randombookmark', RandomBookmarkHandler),
    (r'/random', RandomBookmarksHandler),
    # (r'/search', SearchHandler),
    (r'/ftxsearch', FullTextSearchHandler),
    (r'/tags', TagsHandler),
    (r'/segmentation/([^/]+)', SegmentationHandler),
    # (r'/readability/(.*)', ReadabilityHandler)
    (r'/api/v1/u-u', UserAPIHandler),
    (r'/api/v1/u-u/([^/]+)', UserAPIHandler),
    (r'/api/v1/u-b/([^/]+)', UserBookmarkAPIHandler),
    (r'/api/v1/u-bl/([^/]+)', UserBookmarksAPIHandler),
    (r'/api/v1/u-bl/([^/]+)/([0-9]+)', UserBookmarksAPIHandler),
    (r'/api/v1/ut-bl/([^/]+)/(.*)', UserTagBookmarksAPIHandler),
    (r'/api/v1/ut-bl/([^/]+)/([^/]+)/([0-9]+)', UserTagBookmarksAPIHandler),
    (r'/api/v1/t-bl/([^/]+)', TagBookmarksAPIHandler),
    (r'/api/v1/t-bl/([^/]+)/([0-9]+)', TagBookmarksAPIHandler),
    (r'/api/v1/w-w', WebpageAPIHandler),
    (r'/api/v1/w-w/([^/]+)', WebpageAPIHandler),
    (r'/api/v1/w-ul', WebpageUsersAPIHandler),
    (r'/api/v1/w-ul/([^/]+)', WebpageUsersAPIHandler),
    (r'/api/v1/bl/recent', RecentBookmarksAPIHandler),
    (r'/api/v1/bl/recent/([0-9]+)', RecentBookmarksAPIHandler),
    (r'/api/v1/u-tl/([^/]+)', UserTagsAPIHandler),
    (r'/api/v1/u-tl/([^/]+)/([0-9]+)', UserTagsAPIHandler)
]
