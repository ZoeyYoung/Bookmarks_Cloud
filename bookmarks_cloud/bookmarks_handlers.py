import tornado.web
import tornado.template
from .base import BaseHandler
import json
import time
import random
from .utils import get_keywords
from .utils import format_tags
from .utils import get_tags_cloud
from .models import Page, Bookmark


class BookmarkModule(tornado.web.UIModule):

    def render(self, bookmark):
        try:
            return self.render_string('modules/bookmark.html', bookmark=bookmark)
        except KeyError:
            print('KeyError ->', bookmark)


class PagerModule(tornado.web.UIModule):

    def render(self, page):
        try:
            return self.render_string('modules/pager.html', page=page)
        except KeyError:
            print('KeyError ->', page)


class IndexHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, page=1):
        bookmarks = Bookmark.get_page(page)
        page = Page(Bookmark.get_count(), page)
        tags = Bookmark.get_tags()
        tags_cloud = get_tags_cloud(tags)
        self.render('index.html', tags_cloud=tags_cloud,
                    bookmarks=bookmarks, count=Bookmark.get_count(), page=page)


class BookmarkHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, page):
        tags = Bookmark.get_tags()
        bookmarks = Bookmark.get_page(int(page))
        page = Page(Bookmark.get_count(), int(page))
        tags_cloud = get_tags_cloud(tags)
        self.render('index.html', tags_cloud=tags_cloud,
                    bookmarks=bookmarks, count=Bookmark.get_count(), page=page)


class AjaxBookmarkHandler(BaseHandler):

    def post(self):
        page = self.get_argument('page')
        tag = self.get_argument('tag')
        keywords = self.get_argument('keywords')
        if tag:
            bookmarks = Bookmark.get_by_tag(tag, int(page))
            page = Page(bookmarks.count(), int(page))
        elif keywords:
            results = Bookmark.whoose_ftx(keywords, int(page))
            bookmarks = results['results']
            page = Page(results['total'], int(page))
        else:
            bookmarks = Bookmark.get_page(int(page))
            page = Page(bookmarks.count(), int(page))
        self.render('list.html', bookmarks=bookmarks, page=page)


class BookmarkGetInfoHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        info = Bookmark.get_info(url)
        if info:
            self.write(json.dumps({
                'success': 'true',
                'favicon': info['favicon'],
                'title': info['title'],
                'description': info['description'],
                'tags': info['tags'],
                'note': info['note']
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkGetDetailHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = Bookmark.get_by_url(url)
        suggest_tags = get_keywords(bookmark['article'])
        if bookmark:
            self.write(json.dumps({
                'success': 'true',
                'title': bookmark['title'],
                'favicon': bookmark['favicon'],
                'description': bookmark['description'],
                'tags': ','.join(bookmark['tags']),
                'note': bookmark['note'],
                'article': bookmark['article'],
                'suggest_tags': suggest_tags
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkRefreshHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = Bookmark.get_by_url(url)
        if bookmark:
            bookmark = Bookmark.refresh(bookmark)
            bookmark = Bookmark.insert_or_update(bookmark)
            bookmark_module = tornado.escape.to_basestring(
                self.render_string('modules/bookmark.html', bookmark=bookmark))
            self.write(
                json.dumps({'success': 'true', 'bookmark_module': bookmark_module, 'title': bookmark['title'], 'article': tornado.escape.to_basestring(bookmark['article'])}))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkGetArticleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = Bookmark.get_by_url(url)
        if bookmark:
            if bookmark['article'] == '':
                bookmark = Bookmark.refresh(bookmark)
            self.write(json.dumps({
                'success': 'true',
                'title': bookmark['title'],
                'article': bookmark['article']
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkAddHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        note = self.get_argument('note')
        post_time = int(time.time())
        bookmark = dict(
            url=self.get_argument('url'),
            title=self.get_argument('title'),
            favicon=self.get_argument('favicon'),
            tags=format_tags(self.get_argument('tags')),
            note=note,
            post_time=post_time,
            random=random.random(),
            html=self.get_argument('html')
        )
        bookmark = Bookmark.insert_or_update(bookmark)
        bookmark_module = tornado.escape.to_basestring(
            self.render_string('modules/bookmark.html', bookmark=bookmark))
        self.write(json.dumps({'success': 'true', 'bookmark_module': bookmark_module, 'article': tornado.escape.to_basestring(bookmark['article'])}))


class BookmarkDelHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        url = self.get_argument('url')
        Bookmark.delete(url)
        self.write(json.dumps({'success': 'true'}))


class TagBookmarksHandler(BaseHandler):

    def get(self, page, tag):
        tags = Bookmark.get_tags()
        tags_cloud = get_tags_cloud(tags)
        bookmarks = Bookmark.get_by_tag(tag, int(page))
        page = Page(bookmarks.count(), int(page))
        self.render('tags_bookmarks.html', tags_cloud=tags_cloud, bookmarks=bookmarks, count=Bookmark.get_count(), page=page, cur_tag=tag, tag_count=bookmarks.count())


class TagsCloudHandler(BaseHandler):

    def get(self):
        tags = Bookmark.get_tags()
        tags_cloud = get_tags_cloud(tags)
        self.render('tags_cloud.html', tags_cloud=tags_cloud)


class RandomBookmarksHandler(BaseHandler):

    def get(self):
        tags = Bookmark.get_tags()
        tags_cloud = get_tags_cloud(tags)
        bookmarks = Bookmark.get_random_bookmarks()
        self.render('random_bookmarks.html', tags_cloud=tags_cloud,
                    bookmarks=bookmarks, count=Bookmark.get_count())


class RandomBookmarkHandler(BaseHandler):

    def get(self):
        bookmark = Bookmark.get_random_one()
        bookmark_module = tornado.escape.to_basestring(
            self.render_string('modules/bookmark.html', bookmark=bookmark))
        self.write(json.dumps({
            'success': 'true',
            'url': bookmark['url'],
            'title': bookmark['title'],
            'article': bookmark['article'],
            'bookmark_module': bookmark_module
        }))


class SearchHandler(BaseHandler):
    """搜索书签
    """
    def get(self):
        tags = Bookmark.get_tags()
        tags_cloud = get_tags_cloud(tags)
        keywords = self.get_argument('keywords')
        result = Bookmark.get_by_keywords(keywords)
        count = result.count()
        self.render('search_result.html', keywords=keywords, tags_cloud=tags_cloud, bookmarks=result, count=count)


class FullTextSearchHandler(BaseHandler):
    """搜索书签
    """
    @tornado.web.authenticated
    def get(self):
        keywords = self.get_argument('keywords')
        tags = Bookmark.get_tags()
        tags_cloud = get_tags_cloud(tags)
        results = Bookmark.whoose_ftx(keywords, 1)
        page = Page(results['total'], 1)
        self.render('search_result.html', keywords=keywords, tags_cloud=tags_cloud, bookmarks=results['results'], count=results['total'], page=page)


class TagsHandler(BaseHandler):

    def get(self):
        tags = Bookmark.get_tags()
        tagslist = []
        for tag in tags:
            tagslist.append(tag['_id'])
        tagsstr = ','.join(tagslist)
        self.write(json.dumps({
            'tags': tagsstr
        }))


class SegmentationHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, url):
        bookmark = Bookmark.get_by_url(url)
        self.render('segmentation.html', bookmark=bookmark)
