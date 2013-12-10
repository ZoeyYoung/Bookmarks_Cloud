#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
import json
import cgi
from tornado import httpclient
from tornado import escape
db = pymongo.Connection().bookmarks_cloud
bookmarks_collection = db.bookmarks
webpages_collection = db.webpages_col
new_bookmarks_collection = db.bookmarks_col
user = db.users.find_one({'name': 'Zoey'})
with open('error2', 'a+') as error_url:
    i = 1
    http_client = httpclient.HTTPClient()
    for webpage in webpages_collection.find(timeout=False):
        print("=====bookmark%d=====%s" % (i, webpage['url']))
        bookmark = new_bookmarks_collection.find_one({'url': webpage['url']})
        if bookmark is None:
            old_bookmark = bookmarks_collection.find_one({
                'url': webpage['url']
            })
            if old_bookmark:
                webpage['favicon'] = old_bookmark['favicon']
                webpage['segmentation'] = old_bookmark['segmentation']
                if webpage['excerpt'] is None:
                    webpage['excerpt'] = old_bookmark['description']
                bookmark = {
                    'owner': user['_id'],
                    'webpage': webpage['_id'],
                    'url': webpage['url'],
                    'favicon': old_bookmark['favicon'],
                    'lead_image_url': webpage['lead_image_url'],
                    'title': webpage['title'],
                    'excerpt': webpage['excerpt'],
                    'note': old_bookmark['note'],
                    'note_html': old_bookmark['note_html'],
                    'tags': old_bookmark['tags'],
                    'added_time': old_bookmark['post_time'],
                    'random': old_bookmark['random'],
                    'is_star': 0,
                    'is_readed': 0
                }
                new_bookmarks_collection.save(bookmark)
                webpages_collection.save(webpage)
            else:
                print("=====Error%d=====%s" % (i, webpage['url']), file=error_url)
        i = i + 1
print("=====Update Over=====")
