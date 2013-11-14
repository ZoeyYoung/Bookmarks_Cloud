#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
import tornado.template
from .base import BaseHandler
from .utils import fetch_webpage
from .utils import get_keywords
from .models import Page
from tornado import gen
from tornado.escape import json_encode, json_decode

class BookmarkModule(tornado.web.UIModule):
    """书签UI模块
    """
    def render(self, bookmark):
        try:
            return self.render_string('modules/bookmark.html', bookmark=bookmark)
        except KeyError:
            print('KeyError ->', bookmark)

class PagerModule(tornado.web.UIModule):
    """分页UI模块
    """
    def render(self, page):
        try:
            return self.render_string('modules/pager.html', page=page)
        except KeyError:
            print('KeyError ->', page)

class IndexHandler(BaseHandler):
    """登录后主页，显示当前用户保存的书签，默认显示第一页
    """
    @tornado.web.authenticated
    def get(self, page=1):
        bookmarks = self.bm.get_by_page(page)
        page = Page(self.total, page)
        self.render('index.html', bookmarks=bookmarks, page=page)

class AjaxBookmarkHandler(BaseHandler):
    """翻页处理, 不刷新页面, 而是通过Ajax获取
    """
    @tornado.web.authenticated
    def post(self):
        page = self.get_argument('page')
        tag = self.get_argument('tag')
        keywords = self.get_argument('keywords')
        if tag:
            bookmarks = self.bm.get_by_tag_page(tag, page)
            page = Page(bookmarks.count(), page)
        elif keywords:
            results = self.bm.whoose_ftx(keywords, page)
            bookmarks = results['results']
            page = Page(results['total'], page)
        else:
            bookmarks = self.bm.get_by_page(page)
            page = Page(bookmarks.count(), page)
        self.render('list.html', bookmarks=bookmarks, page=page)

class BookmarkGetInfoHandler(BaseHandler):
    """通过网址获取书签信息，通过Ajax调用，返回JSON字符串
    在添加书签时，点击“获取信息”时有调用
    """
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, *args):
        url = self.get_argument('url')
        # 首先判断用户是否已收藏过该书签，或已解析过该页面
        (bookmark, webpage) = self.bm.get_bookmark_webpage_by_url(url)

        if webpage is None:  # 如果未解析过该页面
            # 默认使用readability的parser API
            # 教程: http://www.readability.com/developers/api/parser
            try:
                http_client = tornado.httpclient.AsyncHTTPClient()
                response = yield http_client.fetch("https://readability.com/api/content/v1/parser?token=7f579fc61973e200632c9e43ff2639234817fbb3&url=" + tornado.escape.url_escape(url))
                if response.body:
                    webpage = self.bm.get_webpage_by_readability(url, readability=response.body)
            except tornado.httpclient.HTTPError:
                # print("Error:", response.error)
                # 备用，处理readability无法识别的网页
                response = yield fetch_webpage(url)
                if response.body:
                    webpage = self.bm.get_webpage_by_html(url, html=response.body)
                else:
                    print("Error:", response.error)
                    self.write(json_encode({'success': 'false'}))

        if bookmark is None:  # 如果用户未收藏过该书签，则新建书签对象
            bookmark_info = {
                'success': 'true',
                'favicon': webpage['favicon'], # 需要吗?
                'title': webpage['title'],
                'description': webpage['excerpt'],
                'suggest_tags': webpage['tags'],
                'tags': '',
                'note': '',
                'article': webpage['content']
            }
            self.write(json_encode(bookmark_info))
        elif bookmark is not None:  # 如果用户收藏过该书签，则更新信息
            bookmark_info = {
                'success': 'true',
                'favicon': webpage['favicon'], # 需要吗?
                'title': webpage['title'],
                'description': webpage['excerpt'],
                'suggest_tags': webpage['tags'],
                'tags': bookmark['tags'],
                'note': bookmark['note'],
                'article': webpage['content']
            }
            self.write(json_encode(bookmark_info))
        else:
            self.write(json_encode({'success': 'false'}))

class BookmarkGetDetailHandler(BaseHandler):
    """编辑时获取当前书签信息，通过Ajax调用，返回JSON字符串
    """
    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        (bookmark, webpage) = self.bm.get_bookmark_webpage_by_url(url)
        if bookmark:
            self.write(json_encode({
                'success': 'true',
                'title': bookmark['title'],
                'favicon': bookmark['favicon'],
                'description': bookmark['excerpt'],
                'tags': ','.join(bookmark['tags']),
                'suggest_tags': webpage['tags'],
                'note': bookmark['note'],
                'article': webpage['content']
            }))
        else:
            self.write(json_encode({'success': 'false'}))

class BookmarkRefreshHandler(BaseHandler):

    @tornado.web.authenticated
    @gen.coroutine
    def get(self, *args):
        url = self.get_argument('url')
        # 默认使用readability的parser API
        # 教程: http://www.readability.com/developers/api/parser
        try:
            http_client = tornado.httpclient.AsyncHTTPClient()
            response = yield http_client.fetch("https://readability.com/api/content/v1/parser?token=7f579fc61973e200632c9e43ff2639234817fbb3&url=" + tornado.escape.url_escape(url))
            if response.body:
                (bookmark, webpage) = self.bm.refresh_by_readability(url, readability=response.body)
        except tornado.httpclient.HTTPError:
            # print("Error:", response.error)
            # 备用，处理readability无法识别的网页
            response = yield fetch_webpage(url)
            if response.body:
                (bookmark, webpage) = self.bm.refresh_by_html(url, html=response.body)
            else:
                print("Error:", response.error)
                self.write(json_encode({'success': 'false'}))
        if bookmark:
            bookmark_module = tornado.escape.to_basestring(
                    self.render_string('modules/bookmark.html', bookmark=bookmark))
            self.write(json_encode({
                'success': 'true',
                'bookmark_module': bookmark_module,
                'title': bookmark['title'],
                'article': tornado.escape.to_basestring(webpage['content'])
            }))
        else:
            self.write(json_encode({'success': 'false'}))


class BookmarkGetArticleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        webpage = self.bm.get_webpage_by_url(url)
        if webpage:
            if webpage['content'] == '':
                # TODO: 如果正文为空
                # webpage = self.bm.refresh(bookmark)
                print("TODO: 如果正文为空")
            else:
                self.write(json_encode({
                    'success': 'true',
                    'title': webpage['title'],
                    'article': webpage['content']
                }))
        else:
            self.write(json_encode({'success': 'false'}))


class BookmarkAddHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        bookmark = dict(
            url=self.get_argument('url'),
            favicon = self.get_argument('favicon'),
            tags=self.get_argument('tags'),
            note=self.get_argument('note')
        )
        bookmark = self.bm.insert_or_update(bookmark)
        bookmark_module = tornado.escape.to_basestring(
            self.render_string('modules/bookmark.html', bookmark=bookmark))
        self.write(json_encode({
            'success': 'true',
            'bookmark_module': bookmark_module
        }))


class BookmarkDelHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        url = self.get_argument('url')
        if self.bm.delete(url) == 1:
            self.write(json_encode({'success': 'true'}))
        else:
            self.write(json_encode({'success': 'false'}))


class BookmarkSetStarHandler(BaseHandler):
    """设置是否加星"""
    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = self.bm.get_by_url(url)
        if bookmark:
            if bookmark['is_star'] == 0:
                bookmark['is_star'] = 1
            else:
                bookmark['is_star'] = 0
            self.bm.save(bookmark)
            self.write(json_encode({
                'success': 'true',
                'is_star': bookmark['is_star']
            }))
        else:
            self.write(json_encode({'success': 'false'}))


class TagBookmarksHandler(BaseHandler):
    """获得当前用户指定标签下的书签"""
    @tornado.web.authenticated
    def get(self, tag, page):
        bookmarks = self.bm.get_by_tag_page(tag, page)
        page = Page(bookmarks.count(), page)
        self.render('tag_bookmarks.html', bookmarks=bookmarks, page=page, cur_tag=tag, tag_count=bookmarks.count())


class TagsCloudHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        self.render('tags_cloud.html', tags_cloud=self.tags_cloud)


class RandomBookmarksHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        bookmarks = self.bm.get_random_bookmarks()
        self.render('random_bookmarks.html', bookmarks=bookmarks)


class RandomBookmarkHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        bookmark = self.bm.get_random_one()
        bookmark_module = tornado.escape.to_basestring(
            self.render_string('modules/bookmark.html', bookmark=bookmark))
        self.write(json_encode({
            'success': 'true',
            'url': bookmark['url'],
            'title': bookmark['title'],
            'article': bookmark['article'],
            'bookmark_module': bookmark_module
        }))


# class SearchHandler(BaseHandler):
#     """搜索书签
#     """
#     @tornado.web.authenticated
#     def get(self):
#         tags = Bookmark.get_tags()
#         tags_cloud = get_tags_cloud(tags)
#         keywords = self.get_argument('keywords')
#         result = Bookmark.get_by_keywords(keywords)
#         count = result.count()
#         self.render('search_result.html', keywords=keywords, tags_cloud=tags_cloud, bookmarks=result, count=count)


class FullTextSearchHandler(BaseHandler):
    """搜索书签
    """
    @tornado.web.authenticated
    def get(self):
        keywords = self.get_argument('keywords')
        results = self.bm.whoose_ftx(keywords, 1)
        page = Page(results['total'], 1)
        self.render('search_result.html', keywords=keywords, bookmarks=results['results'], count=results['total'], page=page)


class TagsHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        tagsstr = ','.join([tag['_id'] for tag in self.tags])
        self.write(json_encode({
            'tags': tagsstr
        }))


class SegmentationHandler(BaseHandler):

    def get(self, url):
        bookmark = self.bm.get_by_url(url)
        self.render('segmentation.html', bookmark=bookmark)

# class ReadabilityHandler(BaseHandler):

#     @gen.coroutine
#     def get(self, url):
#         response = yield readability_parser(url)
#         self.render('readability.html', body=json_decode(response.body))
